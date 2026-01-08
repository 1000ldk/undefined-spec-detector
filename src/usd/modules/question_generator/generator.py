"""
実践的質問文生成器
若手SEがそのまま使える質問文を生成する
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class PracticalQuestion:
    """実践的な質問"""
    element_id: str
    title: str
    question: str
    options: List[Dict[str, Any]]
    explanation: str
    urgency: str
    who_to_ask: str
    examples: List[str]
    default_assumption: Optional[str]


class QuestionGenerator:
    """質問文生成器"""
    
    def __init__(self):
        """初期化"""
        self.question_templates = self._load_question_templates()
    
    def _load_question_templates(self) -> Dict[str, str]:
        """質問テンプレートを読み込み"""
        return {
            "delete_method": """
【削除機能について】
{entity}の削除は、以下のどちらの方式で実装しますか？

A) 論理削除（deleted_atフラグを立てる）
   - メリット: 復元可能、履歴が残る、データ分析に使える
   - デメリット: データ容量増加、クエリが複雑化（WHERE deleted_at IS NULL）
   
B) 物理削除（レコードを完全に削除）
   - メリット: シンプル、容量節約、GDPR対応しやすい
   - デメリット: 復元不可、履歴が残らない

👉 この決定は後から変更困難です（DB全体の再設計が必要）
""",
            "cascade_delete": """
【関連データの扱いについて】
{entity}を削除する際、以下の関連データはどうしますか？

{related_entities}

選択肢:
A) 全て一緒に削除（カスケード削除）
B) 削除せず残す（孤立データとして）
C) 残すが参照を無効化（匿名化など）
D) ユーザーに選択させる

参考事例:
- SNS: ユーザー削除時、投稿は「残す（匿名化）」が一般的
- プロジェクト管理ツール: プロジェクト削除時、タスクは「一緒に削除」が一般的
- ECサイト: カート削除時、カート内商品は「一緒に削除」

👉 一度削除したデータは復元できません
""",
            "api_timeout": """
【外部API連携について】
{api_name}の呼び出しは何秒でタイムアウトとしますか？

選択肢:
A) 5秒（短め・リアルタイム系向け）
B) 10秒（一般的）
C) 30秒（重い処理向け）
D) 60秒（バッチ処理など）

👉 タイムアウト設定なしだとシステム全体が停止する可能性があります
""",
            "api_fallback": """
【外部API障害時の対応】
{api_name}が障害で応答しない場合、どうしますか？

選択肢:
A) キャッシュデータを返す
B) デフォルト値を使う
C) エラー画面を表示
D) キューに入れて後で再実行

👉 外部システムは必ず障害が起きます。フォールバックがないとユーザーに影響します
""",
            "authentication_method": """
【認証方式の選択】
認証方式は何を採用しますか？

A) JWT（JSON Web Token）
   - メリット: ステートレス、スケールしやすい
   - デメリット: 無効化が難しい
   
B) セッションベース
   - メリット: 管理しやすい、即座に無効化可能
   - デメリット: サーバー側でセッション管理が必要

C) OAuth 2.0
   - メリット: 標準的、外部サービス連携が容易
   - デメリット: 実装が複雑

👉 この決定はアーキテクチャの根幹です。後から変更は全面的な作り直しになります
""",
            "token_storage": """
【トークン保存場所】
クライアント側で認証トークンをどこに保存しますか？

A) Cookie（HttpOnly, Secure属性付き）
   - メリット: XSS攻撃に強い
   - デメリット: CSRF対策が必要

B) LocalStorage
   - メリット: 実装が簡単、容量が大きい
   - デメリット: XSS攻撃に弱い

C) SessionStorage
   - メリット: タブを閉じると消える（セキュリティ◯）
   - デメリット: 永続化されない

👉 セキュリティに直結する重要な決定です
""",
        }
    
    def generate(
        self,
        element: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> PracticalQuestion:
        """
        実践的な質問を生成
        
        Args:
            element: チェックリスト要素
            context: コンテキスト情報（エンティティ名など）
            
        Returns:
            PracticalQuestion: 生成された質問
        """
        element_id = element.get("id", "")
        title = element.get("title", "")
        question_text = element.get("question", "")
        
        # テンプレートがあれば使用
        template_text = element.get("question_template")
        if template_text:
            question_text = self._format_template(template_text, context)
        elif "question_template_key" in element:
            template_key = element["question_template_key"]
            if template_key in self.question_templates:
                template = self.question_templates[template_key]
                question_text = self._format_template(template, context)
        
        # オプションの整形
        options = self._format_options(element.get("options", []))
        
        # 説明文の生成
        explanation = self._generate_explanation(element)
        
        # 誰に聞くべきかを判定
        who_to_ask = self._suggest_stakeholder(element)
        
        # 例の取得
        examples = element.get("examples", [])
        
        return PracticalQuestion(
            element_id=element_id,
            title=title,
            question=question_text,
            options=options,
            explanation=explanation,
            urgency=element.get("criticality", "SHOULD_CONFIRM"),
            who_to_ask=who_to_ask,
            examples=examples,
            default_assumption=element.get("default_assumption")
        )
    
    def _format_template(
        self,
        template: str,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """
        テンプレートに値を埋め込む
        
        Args:
            template: テンプレート文字列
            context: コンテキスト
            
        Returns:
            フォーマットされた文字列
        """
        if not context:
            return template
        
        # プレースホルダーを置換
        formatted = template
        if "entity" in context:
            formatted = formatted.replace("{entity}", context["entity"])
        if "api_name" in context:
            formatted = formatted.replace("{api_name}", context["api_name"])
        if "related_entities" in context:
            entities_list = "\n".join([f"  - {e}" for e in context["related_entities"]])
            formatted = formatted.replace("{related_entities}", entities_list)
        
        return formatted
    
    def _format_options(self, options: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        選択肢をフォーマット
        
        Args:
            options: 選択肢のリスト
            
        Returns:
            フォーマットされた選択肢
        """
        formatted = []
        for opt in options:
            formatted_opt = {
                "value": opt.get("value", ""),
                "label": opt.get("label", ""),
            }
            
            if "pros" in opt:
                formatted_opt["pros"] = opt["pros"]
            if "cons" in opt:
                formatted_opt["cons"] = opt["cons"]
            if "implementation" in opt:
                formatted_opt["implementation"] = opt["implementation"]
            if "warning" in opt:
                formatted_opt["warning"] = opt["warning"]
            
            formatted.append(formatted_opt)
        
        return formatted
    
    def _generate_explanation(self, element: Dict[str, Any]) -> str:
        """
        説明文を生成
        
        Args:
            element: チェックリスト要素
            
        Returns:
            説明文
        """
        parts = []
        
        # なぜ重要か
        if "why_critical" in element:
            parts.append(f"【重要な理由】\n{element['why_critical']}")
        
        # 後から変更するコスト
        if "change_cost_if_later" in element:
            parts.append(f"【後から変更する場合のコスト】\n{element['change_cost_if_later']}")
        
        # オプションの説明文
        if "why_optional" in element:
            parts.append(f"【備考】\n{element['why_optional']}")
        
        return "\n\n".join(parts)
    
    def _suggest_stakeholder(self, element: Dict[str, Any]) -> str:
        """
        誰に確認すべきかを提案
        
        Args:
            element: チェックリスト要素
            
        Returns:
            確認先の提案
        """
        affects = element.get("affects", {})
        
        if affects.get("security"):
            return "セキュリティチーム、上長"
        
        if affects.get("data_model"):
            return "プロダクトオーナー、アーキテクト"
        
        if affects.get("external_system"):
            return "外部連携担当、インフラチーム"
        
        criticality = element.get("criticality", "")
        if criticality == "MUST_DEFINE":
            return "プロダクトオーナー、上長"
        elif criticality == "SHOULD_CONFIRM":
            return "プロダクトオーナー"
        else:
            return "チーム内で決定可能"
    
    def generate_all(
        self,
        elements: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> List[PracticalQuestion]:
        """
        複数要素の質問を一括生成
        
        Args:
            elements: チェックリスト要素のリスト
            context: コンテキスト
            
        Returns:
            生成された質問のリスト
        """
        questions = []
        for element in elements:
            question = self.generate(element, context)
            questions.append(question)
        
        return questions



