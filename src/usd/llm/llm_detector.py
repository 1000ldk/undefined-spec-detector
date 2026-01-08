"""
LLM検出モジュール: OpenAI GPT-4oを使用した未定義要素検出
"""
import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from usd.schema import (
    UndefinedElement,
    Question,
    DetectionInfo,
    Context,
    Priority,
)


class LLMUnknownTermDetector:
    """未知の用語を検出するLLMクラス"""
    
    # プロンプト1: 未知の用語検出用
    SYSTEM_PROMPT = """あなたは要件定義の専門家です。以下の要件文から、定義が不明確な用語・概念を全て抽出してください。

抽出基準:
1. 固有名詞や専門用語で、文中で定義されていないもの
2. 一般的でない略語や造語（例：API、ECサイトは一般的なので除外）
3. システム名、コンポーネント名で詳細が不明なもの
4. 「既存の〜」「社内の〜」など外部参照しているが詳細不明のもの
5. 具体性を欠く表現（「〜的なもの」「〜のような」等）

除外すべきもの:
- 一般的なIT用語（ユーザー、システム、データベース、API、サーバー等）
- 文中で既に定義・説明されているもの
- 誰でも理解できる一般用語

出力形式: 必ずJSON形式
{
  "unknown_terms": [
    {
      "term": "用語名",
      "context": "その用語が使われている文の一部",
      "confidence": 0.95,
      "reasoning": "なぜこれが未定義と判断したか（50文字程度）",
      "questions": [
        "この用語を明確にするための質問1",
        "質問2",
        "質問3"
      ]
    }
  ]
}"""
    
    USER_PROMPT_TEMPLATE = """以下の要件文を分析してください:

{requirement_text}"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        max_cost: float = 1.00,
        timeout: int = 30
    ):
        """
        初期化
        
        Args:
            api_key: OpenAI API Key
            model: 使用するモデル（デフォルト: gpt-4o）
            max_cost: コスト上限（USD、デフォルト: $1.00）
            timeout: タイムアウト（秒、デフォルト: 30秒）
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("openai パッケージがインストールされていません。pip install openai を実行してください。")
        
        self.client = OpenAI(api_key=api_key, timeout=timeout)
        self.model = model
        self.max_cost = max_cost
        self.timeout = timeout
        self.total_cost = 0.0
        self.call_count = 0
        
        # トークン単価（GPT-4o 2024年1月時点の概算）
        self.price_per_1k_input = 0.005  # $0.005 per 1K input tokens
        self.price_per_1k_output = 0.015  # $0.015 per 1K output tokens
    
    def detect_unknown_terms(self, requirement_text: str) -> List[UndefinedElement]:
        """
        未知の用語を検出
        
        Args:
            requirement_text: 要件文
        
        Returns:
            未定義要素のリスト
        
        Raises:
            Exception: API呼び出し失敗時
        """
        # コスト上限チェック
        if self.total_cost >= self.max_cost:
            raise Exception(f"コスト上限（${self.max_cost}）を超過しました。現在のコスト: ${self.total_cost:.4f}")
        
        try:
            start_time = time.time()
            
            # ユーザープロンプトの作成
            user_prompt = self.USER_PROMPT_TEMPLATE.format(
                requirement_text=requirement_text
            )
            
            print(f"\n🤖 LLM（{self.model}）で未知の用語を検出中...")
            
            # API呼び出し
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=2000
            )
            
            elapsed_time = time.time() - start_time
            
            # レスポンスの取得
            content = response.choices[0].message.content
            
            # トークン数の記録
            usage = response.usage
            input_tokens = usage.prompt_tokens
            output_tokens = usage.completion_tokens
            
            # コストの計算
            cost = (input_tokens / 1000 * self.price_per_1k_input +
                   output_tokens / 1000 * self.price_per_1k_output)
            self.total_cost += cost
            self.call_count += 1
            
            print(f"✓ 完了（{elapsed_time:.1f}秒）")
            print(f"  入力トークン: {input_tokens}, 出力トークン: {output_tokens}")
            print(f"  コスト: ${cost:.4f} (累計: ${self.total_cost:.4f})")
            
            # JSONのパース
            try:
                result = json.loads(content)
            except json.JSONDecodeError as e:
                print(f"⚠️  JSON parse失敗: {e}")
                print(f"レスポンス: {content[:200]}")
                return []
            
            # UndefinedElementに変換
            elements = []
            for term_data in result.get("unknown_terms", []):
                element = self._convert_to_undefined_element(
                    term_data,
                    requirement_text
                )
                elements.append(element)
            
            print(f"✓ {len(elements)}個の未知の用語を検出")
            
            return elements
        
        except Exception as e:
            print(f"❌ LLM検出エラー: {e}")
            raise
    
    def _convert_to_undefined_element(
        self,
        term_data: Dict[str, Any],
        requirement_text: str
    ) -> UndefinedElement:
        """
        LLM検出結果をUndefinedElementに変換
        
        Args:
            term_data: LLMからの用語データ
            requirement_text: 元の要件文
        
        Returns:
            UndefinedElement
        """
        term = term_data.get("term", "不明な用語")
        context_text = term_data.get("context", "")
        confidence = term_data.get("confidence", 0.5)
        reasoning = term_data.get("reasoning", "")
        question_texts = term_data.get("questions", [])
        
        # Questionオブジェクトに変換
        questions = []
        for q_text in question_texts:
            questions.append(
                Question(
                    text=q_text,
                    type="clarification"
                )
            )
        
        # Contextの作成
        context = Context(
            source_text=term,
            surrounding_text=context_text if context_text else requirement_text[:100],
            line_number=1
        )
        
        # 信頼度に基づく重要度の決定
        if confidence >= 0.9:
            priority = Priority.HIGH
        elif confidence >= 0.7:
            priority = Priority.MEDIUM
        else:
            priority = Priority.LOW
        
        return UndefinedElement(
            id=f"LLM-{uuid.uuid4().hex[:8].upper()}",
            category="未知の用語・概念",
            subcategory="定義欠落",
            title=f"「{term}」の定義が不明",
            description=reasoning if reasoning else f"「{term}」は文中で定義されておらず、意味が不明確です。",
            questions=questions,
            detection=DetectionInfo(
                method="llm",
                confidence=confidence,
                reasoning=f"LLM（{self.model}）による検出: {reasoning}"
            ),
            context=context,
            estimated_severity=priority
        )


class LLMContextualAmbiguityDetector:
    """文脈依存の曖昧さを検出するLLMクラス"""
    
    # プロンプト2: 文脈依存の曖昧さ検出用
    SYSTEM_PROMPT = """あなたは要件定義レビューの専門家です。この要件を実装するエンジニアが「これだけでは実装できない」「判断に迷う」と困る点を全て指摘してください。

分析観点:
1. 振る舞いの曖昧さ
   - タイミング（いつ実行？）
   - 条件（どういう場合に？）
   - 頻度（どのくらいの頻度で？）

2. 状況説明の不足
   - 「〜が起きる」→ どの程度？常に？条件は？
   - 問題の再現条件が不明
   - エラーなのか、遅いのか、動かないのか曖昧

3. 解決策の具体性欠如
   - 「〜する予定」「〜しようと思っている」→ 具体的な方法は？
   - 代替案の有無
   - 制約条件が不明

4. 境界条件・環境依存
   - 対象デバイス・ブラウザ・OSの範囲
   - エッジケース（最大値、最小値、ゼロ、null等）

5. エラー処理
   - 失敗した場合の挙動
   - ユーザーへのフィードバック

出力形式: JSON
{
  "contextual_ambiguities": [
    {
      "category": "振る舞いの曖昧さ | 状況説明の不足 | 解決策の具体性欠如 | 境界条件・環境依存 | エラー処理",
      "issue": "問題の要約（30文字以内）",
      "quoted_text": "要件文からの該当箇所の引用",
      "explanation": "なぜ問題か、実装時に何が困るか（100文字程度）",
      "missing_information": [
        "不足している情報1",
        "不足している情報2",
        "不足している情報3"
      ],
      "clarification_questions": [
        "エンジニアが確認すべき具体的な質問1",
        "質問2",
        "質問3"
      ],
      "potential_risks": [
        "このまま実装した場合のリスク1",
        "リスク2"
      ],
      "severity": "critical | high | medium | low"
    }
  ]
}"""
    
    USER_PROMPT_TEMPLATE = """要件文:
{requirement_text}

既に他の方法で検出済みの問題（これらは除外してください）:
{already_detected_issues}"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        max_cost: float = 1.00,
        timeout: int = 30
    ):
        """
        初期化
        
        Args:
            api_key: OpenAI API Key
            model: 使用するモデル
            max_cost: コスト上限（USD）
            timeout: タイムアウト（秒）
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("openai パッケージがインストールされていません。")
        
        self.client = OpenAI(api_key=api_key, timeout=timeout)
        self.model = model
        self.max_cost = max_cost
        self.timeout = timeout
        self.total_cost = 0.0
        self.call_count = 0
        
        self.price_per_1k_input = 0.005
        self.price_per_1k_output = 0.015
    
    def detect_ambiguities(
        self,
        requirement_text: str,
        already_detected: List[UndefinedElement] = None
    ) -> List[UndefinedElement]:
        """
        文脈依存の曖昧さを検出
        
        Args:
            requirement_text: 要件文
            already_detected: 既に検出済みの未定義要素（重複回避用）
        
        Returns:
            未定義要素のリスト
        """
        # コスト上限チェック
        if self.total_cost >= self.max_cost:
            raise Exception(f"コスト上限（${self.max_cost}）を超過しました。")
        
        try:
            start_time = time.time()
            
            # 既検出の問題を文字列化
            detected_issues_str = "なし"
            if already_detected:
                issues = [f"- {elem.title}" for elem in already_detected[:10]]
                detected_issues_str = "\n".join(issues)
            
            # ユーザープロンプトの作成
            user_prompt = self.USER_PROMPT_TEMPLATE.format(
                requirement_text=requirement_text,
                already_detected_issues=detected_issues_str
            )
            
            print(f"\n🤖 LLM（{self.model}）で文脈依存の曖昧さを検出中...")
            
            # API呼び出し
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=2000
            )
            
            elapsed_time = time.time() - start_time
            
            # レスポンスの取得
            content = response.choices[0].message.content
            
            # トークン数の記録
            usage = response.usage
            input_tokens = usage.prompt_tokens
            output_tokens = usage.completion_tokens
            
            # コストの計算
            cost = (input_tokens / 1000 * self.price_per_1k_input +
                   output_tokens / 1000 * self.price_per_1k_output)
            self.total_cost += cost
            self.call_count += 1
            
            print(f"✓ 完了（{elapsed_time:.1f}秒）")
            print(f"  入力トークン: {input_tokens}, 出力トークン: {output_tokens}")
            print(f"  コスト: ${cost:.4f} (累計: ${self.total_cost:.4f})")
            
            # JSONのパース
            try:
                result = json.loads(content)
            except json.JSONDecodeError as e:
                print(f"⚠️  JSON parse失敗: {e}")
                return []
            
            # UndefinedElementに変換
            elements = []
            for amb_data in result.get("contextual_ambiguities", []):
                element = self._convert_to_undefined_element(
                    amb_data,
                    requirement_text
                )
                elements.append(element)
            
            print(f"✓ {len(elements)}個の曖昧さを検出")
            
            return elements
        
        except Exception as e:
            print(f"❌ LLM検出エラー: {e}")
            raise
    
    def _convert_to_undefined_element(
        self,
        amb_data: Dict[str, Any],
        requirement_text: str
    ) -> UndefinedElement:
        """
        LLM検出結果をUndefinedElementに変換
        """
        category_map = {
            "振る舞いの曖昧さ": "振る舞いの曖昧さ",
            "状況説明の不足": "非機能要件の曖昧さ",
            "解決策の具体性欠如": "振る舞いの曖昧さ",
            "境界条件・環境依存": "境界条件の未定義",
            "エラー処理": "エラーハンドリングの欠落"
        }
        
        category_raw = amb_data.get("category", "振る舞いの曖昧さ")
        category = category_map.get(category_raw, "非機能要件の曖昧さ")
        issue = amb_data.get("issue", "要件の曖昧さ")
        quoted_text = amb_data.get("quoted_text", "")
        explanation = amb_data.get("explanation", "")
        missing_info = amb_data.get("missing_information", [])
        questions_raw = amb_data.get("clarification_questions", [])
        risks = amb_data.get("potential_risks", [])
        severity_str = amb_data.get("severity", "medium")
        
        # 重要度の変換
        severity_map = {
            "critical": Priority.CRITICAL,
            "high": Priority.HIGH,
            "medium": Priority.MEDIUM,
            "low": Priority.LOW
        }
        priority = severity_map.get(severity_str, Priority.MEDIUM)
        
        # Questionオブジェクトに変換
        questions = []
        for q_text in questions_raw:
            questions.append(
                Question(
                    text=q_text,
                    type="specification"
                )
            )
        
        # Contextの作成
        context = Context(
            source_text=quoted_text if quoted_text else issue,
            surrounding_text=quoted_text if quoted_text else requirement_text[:100],
            line_number=1
        )
        
        # 説明文の生成
        description = explanation
        if missing_info:
            description += f"\n不足情報: {', '.join(missing_info[:3])}"
        if risks:
            description += f"\nリスク: {risks[0]}"
        
        return UndefinedElement(
            id=f"LLM-AMB-{uuid.uuid4().hex[:8].upper()}",
            category=category,
            subcategory=category_raw,
            title=issue,
            description=description,
            questions=questions,
            detection=DetectionInfo(
                method="llm",
                confidence=0.8,
                reasoning=f"LLM（{self.model}）による文脈分析"
            ),
            context=context,
            estimated_severity=priority
        )


class LLMQuestionGenerator:
    """実践的な質問を生成するLLMクラス"""
    
    # プロンプト3: 実践的な質問生成用
    SYSTEM_PROMPT = """あなたはプロジェクトマネージャーです。未定義要素を解消するために、ステークホルダーに確認すべき質問を作成してください。

質問作成ガイドライン:
1. 具体的で答えやすい質問にする
2. Yes/Noで答えられるものと、具体値を求めるものを混在させる
3. 可能な限り選択肢を提示する
4. 誰に聞くべきかを明示する（ビジネス側 or 技術側）
5. 優先度を付ける（critical=今すぐ, high=早めに, medium=余裕があれば）

出力形式: JSON
{
  "questions": [
    {
      "id": "Q001",
      "question": "質問文（具体的で答えやすい形式）",
      "question_type": "yes_no | choice | numeric | text",
      "choices": ["選択肢1", "選択肢2", "選択肢3"],
      "who_to_ask": "プロダクトオーナー | エンジニアリーダー | デザイナー | ビジネス担当者 | セキュリティ担当者",
      "priority": "critical | high | medium | low",
      "reason": "なぜこの質問が重要か（50文字程度）",
      "impact_if_not_answered": "答えられなかった場合のリスク（50文字程度）"
    }
  ],
  "follow_up_scenarios": [
    {
      "condition": "もし〜を選んだ場合",
      "additional_questions": [
        "追加で確認すべき質問1",
        "質問2"
      ]
    }
  ]
}"""
    
    USER_PROMPT_TEMPLATE = """未定義要素:
- カテゴリ: {category}
- タイトル: {title}
- 説明: {description}
- 文脈: {context}

この未定義要素を解消するための質問を生成してください。"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        max_cost: float = 1.00,
        timeout: int = 30
    ):
        """初期化"""
        if not OPENAI_AVAILABLE:
            raise ImportError("openai パッケージがインストールされていません。")
        
        self.client = OpenAI(api_key=api_key, timeout=timeout)
        self.model = model
        self.max_cost = max_cost
        self.timeout = timeout
        self.total_cost = 0.0
        self.call_count = 0
        
        self.price_per_1k_input = 0.005
        self.price_per_1k_output = 0.015
    
    def generate_questions(
        self,
        undefined_element: UndefinedElement
    ) -> List[Question]:
        """
        未定義要素に対する実践的な質問を生成
        
        Args:
            undefined_element: 未定義要素
        
        Returns:
            質問のリスト
        """
        # コスト上限チェック
        if self.total_cost >= self.max_cost:
            print(f"⚠️  コスト上限（${self.max_cost}）に達したため、質問生成をスキップします。")
            return []
        
        try:
            start_time = time.time()
            
            # ユーザープロンプトの作成
            user_prompt = self.USER_PROMPT_TEMPLATE.format(
                category=undefined_element.category,
                title=undefined_element.title,
                description=undefined_element.description,
                context=undefined_element.context.surrounding_text
            )
            
            print(f"\n🤖 LLM（{self.model}）で実践的な質問を生成中...")
            
            # API呼び出し
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.5,
                max_tokens=1500
            )
            
            elapsed_time = time.time() - start_time
            
            # レスポンスの取得
            content = response.choices[0].message.content
            
            # トークン数の記録
            usage = response.usage
            input_tokens = usage.prompt_tokens
            output_tokens = usage.completion_tokens
            
            # コストの計算
            cost = (input_tokens / 1000 * self.price_per_1k_input +
                   output_tokens / 1000 * self.price_per_1k_output)
            self.total_cost += cost
            self.call_count += 1
            
            print(f"✓ 完了（{elapsed_time:.1f}秒）")
            print(f"  コスト: ${cost:.4f} (累計: ${self.total_cost:.4f})")
            
            # JSONのパース
            try:
                result = json.loads(content)
            except json.JSONDecodeError as e:
                print(f"⚠️  JSON parse失敗: {e}")
                return []
            
            # Questionオブジェクトに変換
            questions = []
            for q_data in result.get("questions", []):
                question = Question(
                    text=q_data.get("question", ""),
                    type="specification",
                    suggested_answers=q_data.get("choices", [])
                )
                questions.append(question)
            
            print(f"✓ {len(questions)}個の質問を生成")
            
            return questions
        
        except Exception as e:
            print(f"❌ LLM質問生成エラー: {e}")
            return []
