"""
Module 2: Undefined Extractor v2.0
未定義要素を抽出する（コンテキスト駆動型）
"""
import re
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

from usd.schema import (
    ParsedRequirement,
    UndefinedElements,
    UndefinedElement,
    Question,
    DetectionInfo,
    Context,
    Priority,
    MetaAnalysis,
)

# 新しいモジュールをインポート
from usd.modules.action_classifier import ActionTypeClassifier, ActionType
from usd.modules.criticality_judge import CriticalityJudge, Criticality
from usd.modules.question_generator import QuestionGenerator


class UndefinedExtractor:
    """未定義要素を抽出するメインクラス（v2.1 - LLM統合型）"""
    
    def __init__(self, use_llm: bool = False, api_key: Optional[str] = None):
        """
        初期化
        
        Args:
            use_llm: LLMを使用するかどうか（デフォルト: False）
            api_key: OpenAI API Key（use_llm=Trueの場合に必要）
        """
        self.version = "2.1.0-hybrid"
        self._load_detection_rules()
        
        # 新しいモジュールの初期化
        self.action_classifier = ActionTypeClassifier()
        self.criticality_judge = CriticalityJudge()
        self.question_generator = QuestionGenerator()
        
        # 🆕 LLMモジュール（オプション）
        self.use_llm = use_llm
        self.llm_unknown_detector = None
        self.llm_ambiguity_detector = None
        self.llm_question_generator = None
        
        if use_llm:
            if not api_key:
                print("⚠️  use_llm=True ですが api_key が指定されていません。LLM機能はスキップされます。")
            else:
                try:
                    from usd.llm.llm_detector import (
                        LLMUnknownTermDetector,
                        LLMContextualAmbiguityDetector,
                        LLMQuestionGenerator,
                    )
                    
                    print("✓ LLMモジュールを初期化中...")
                    self.llm_unknown_detector = LLMUnknownTermDetector(api_key)
                    self.llm_ambiguity_detector = LLMContextualAmbiguityDetector(api_key)
                    self.llm_question_generator = LLMQuestionGenerator(api_key)
                    print("✓ LLMモジュール初期化完了")
                
                except ImportError as e:
                    print(f"⚠️  LLMモジュールのインポートに失敗しました: {e}")
                    print("   openai パッケージがインストールされているか確認してください。")
                    self.use_llm = False
                except Exception as e:
                    print(f"⚠️  LLMモジュールの初期化に失敗しました: {e}")
                    self.use_llm = False
    
    def _load_detection_rules(self):
        """検出ルールを読み込み"""
        # 曖昧な形容詞・副詞のパターン
        self.vague_patterns = {
            '非機能要件の曖昧さ': [
                ('速い|遅い|高速|低速', 'パフォーマンス'),
                ('大きい|小さい|多い|少ない|適切|十分', '境界条件'),
                ('安全|セキュア', 'セキュリティ'),
            ],
            '振る舞いの曖昧さ': [
                ('すぐに|速やかに|適宜|随時|定期的', 'タイミング'),
                ('場合|とき|際', '実行条件'),
            ],
        }
    
    def extract(self, parsed_req: ParsedRequirement) -> UndefinedElements:
        """
        未定義要素を抽出する（v2.0 - コンテキスト駆動型）
        
        Args:
            parsed_req: 構造化された要件（Module 1の出力）
        
        Returns:
            未定義要素のリスト
        """
        undefined_elements = []
        
        # 【新機能】1. 処理タイプを分類
        content = parsed_req.original_content
        classification = self.action_classifier.classify(content)
        
        # 【新機能】2. 処理タイプ別のチェックリストを取得
        if classification.action_type != ActionType.UNKNOWN:
            elements = self._extract_from_checklist(
                classification,
                parsed_req
            )
            undefined_elements.extend(elements)
        
        # 3. 従来の方法でも抽出（エンティティから）
        for entity in parsed_req.entities:
            elements = self._extract_from_entity(entity, parsed_req)
            undefined_elements.extend(elements)
        
        # 4. アクションから抽出（ただし重複を避ける）
        for action in parsed_req.actions:
            elements = self._extract_from_action(action, parsed_req, classification)
            undefined_elements.extend(elements)
        
        # 5. 要件から抽出
        for requirement in parsed_req.requirements:
            elements = self._extract_from_requirement(requirement)
            undefined_elements.extend(elements)
        
        # 🆕 6. LLMによる検出（オプション）
        if self.use_llm and self.llm_unknown_detector:
            try:
                print("\n🤖 LLMで追加の未定義要素を検出中...")
                
                # 6-1. 未知の用語を検出
                llm_unknown_elements = self.llm_unknown_detector.detect_unknown_terms(
                    parsed_req.original_content
                )
                undefined_elements.extend(llm_unknown_elements)
                
                # 6-2. 文脈依存の曖昧さを検出（既検出要素を除外）
                if self.llm_ambiguity_detector:
                    llm_ambiguity_elements = self.llm_ambiguity_detector.detect_ambiguities(
                        parsed_req.original_content,
                        already_detected=undefined_elements
                    )
                    undefined_elements.extend(llm_ambiguity_elements)
                
                print(f"✓ LLMで合計 {len(llm_unknown_elements) + len(llm_ambiguity_elements)} 個検出")
                
            except Exception as e:
                # LLM失敗時もアプリ全体を止めない
                print(f"⚠️  LLM検出に失敗しましたが、処理を続行します: {e}")
        
        # 7. 重複排除（同じtitleが複数検出された場合は1つにまとめる）
        undefined_elements = self._deduplicate(undefined_elements)
        
        # 8. 統計情報の計算
        statistics = self._calculate_statistics(undefined_elements)
        
        # 9. メタ分析
        meta_analysis = self._perform_meta_analysis(parsed_req, undefined_elements)
        
        return UndefinedElements(
            document_id=parsed_req.document_id,
            analyzed_at=datetime.now(),
            extractor_version=self.version,
            source_document=parsed_req.document_id,
            undefined_elements=undefined_elements,
            statistics=statistics,
            meta_analysis=meta_analysis
        )
    
    def _extract_from_checklist(
        self,
        classification,
        parsed_req: ParsedRequirement
    ) -> List[UndefinedElement]:
        """
        処理タイプ別のチェックリストから未定義要素を抽出
        
        Args:
            classification: 処理タイプの分類結果
            parsed_req: 構造化された要件
            
        Returns:
            未定義要素のリスト
        """
        elements = []
        
        # 処理タイプに応じたチェックリストを取得
        action_type_str = classification.action_type.name
        checklist_items = self.criticality_judge.get_checklist_for_action_type(action_type_str)
        
        # コンテキスト情報の準備
        context = {
            "entity": classification.detected_entities[0] if classification.detected_entities else "対象",
            "action_type": classification.action_type.value,
            "original_text": classification.context
        }
        
        # 各チェック項目を未定義要素として抽出
        for item in checklist_items:
            # 致命度を判定
            criticality_result = self.criticality_judge.judge(
                item,
                action_type_str,
                context
            )
            
            # 質問を生成
            practical_question = self.question_generator.generate(item, context)
            
            # UndefinedElementに変換
            element = self._convert_to_undefined_element(
                item,
                criticality_result,
                practical_question,
                parsed_req
            )
            
            elements.append(element)
        
        return elements
    
    def _convert_to_undefined_element(
        self,
        checklist_item: Dict[str, Any],
        criticality_result,
        practical_question,
        parsed_req: ParsedRequirement
    ) -> UndefinedElement:
        """
        チェックリスト項目をUndefinedElementに変換
        
        Args:
            checklist_item: チェックリスト項目
            criticality_result: 致命度判定結果
            practical_question: 実践的な質問
            parsed_req: 構造化要件
            
        Returns:
            UndefinedElement
        """
        # 致命度をPriorityに変換
        if criticality_result.criticality == Criticality.MUST_DEFINE:
            priority = Priority.CRITICAL
        elif criticality_result.criticality == Criticality.SHOULD_CONFIRM:
            priority = Priority.HIGH
        else:
            priority = Priority.MEDIUM
        
        # 質問をQuestionオブジェクトに変換
        questions = [
            Question(
                text=practical_question.question,
                type="specification",
                suggested_answers=[opt["label"] for opt in practical_question.options] if practical_question.options else None
            )
        ]
        
        # 例も質問として追加
        for example in practical_question.examples:
            questions.append(
                Question(
                    text=example,
                    type="clarification"
                )
            )
        
        # カテゴリの決定
        category = checklist_item.get("category", "処理タイプ固有の確認事項")
        
        # コンテキストの作成
        context = Context(
            source_text=parsed_req.original_content[:100],
            surrounding_text=parsed_req.original_content,
            line_number=1
        )
        
        return UndefinedElement(
            id=checklist_item.get("id", self._generate_id()),
            category=category,
            subcategory=checklist_item.get("title", ""),
            title=practical_question.title,
            description=practical_question.explanation,
            questions=questions,
            detection=DetectionInfo(
                method="template_driven",
                confidence=criticality_result.score / 10.0,
                reasoning=f"処理タイプ別チェックリストによる検出。{criticality_result.reason}"
            ),
            context=context,
            estimated_severity=priority,
            criticality_info={
                "level": criticality_result.criticality.value,
                "change_cost": criticality_result.change_cost_if_later,
                "timing": criticality_result.recommended_decision_timing,
                "who_to_ask": practical_question.who_to_ask,
                "default": criticality_result.default_assumption
            }
        )
    
    def _extract_from_entity(self, entity, parsed_req: ParsedRequirement) -> List[UndefinedElement]:
        """エンティティから未定義要素を抽出"""
        elements = []
        
        # エンティティ自体が未定義
        if entity.definition_status == "undefined":
            element_id = self._generate_id()
            
            # コンテキストの抽出
            context = self._get_entity_context(entity, parsed_req)
            
            element = UndefinedElement(
                id=element_id,
                category="データ定義の欠落",
                subcategory="型定義",
                related_entity=entity.id,
                title=f"{entity.name}の定義が不明確",
                description=f"{entity.name}の具体的なデータ型や属性が定義されていません",
                questions=self._generate_questions_for_entity(entity),
                detection=DetectionInfo(
                    method="rule_based",
                    confidence=0.85,
                    reasoning="エンティティが言及されているが、具体的な定義がない"
                ),
                context=context,
                estimated_severity=Priority.MEDIUM
            )
            elements.append(element)
        
        # 属性が未定義
        for attr in entity.attributes:
            if attr.mentioned and not attr.defined:
                element_id = self._generate_id()
                context = self._get_entity_context(entity, parsed_req)
                
                element = UndefinedElement(
                    id=element_id,
                    category="データ定義の欠落",
                    subcategory="制約条件",
                    related_entity=entity.id,
                    title=f"{entity.name}の{attr.name}の仕様が不明",
                    description=f"{attr.name}のデータ型、制約条件が定義されていません",
                    questions=self._generate_questions_for_attribute(entity, attr),
                    detection=DetectionInfo(
                        method="rule_based",
                        confidence=0.9,
                        reasoning="属性が言及されているが型定義がない"
                    ),
                    context=context,
                    estimated_severity=Priority.MEDIUM
                )
                elements.append(element)
        
        return elements
    
    def _extract_from_action(self, action, parsed_req: ParsedRequirement, classification=None) -> List[UndefinedElement]:
        """
        アクションから未定義要素を抽出
        
        Args:
            action: アクション
            parsed_req: 構造化要件
            classification: 処理タイプの分類結果（重複回避用）
        """
        elements = []
        
        # 前提条件が曖昧
        for condition in action.preconditions:
            if condition.ambiguous:
                element_id = self._generate_id()
                context = self._get_action_context(action, parsed_req)
                
                element = UndefinedElement(
                    id=element_id,
                    category="振る舞いの曖昧さ",
                    subcategory="実行条件",
                    related_action=action.id,
                    title=f"{action.verb}の実行条件が曖昧",
                    description=f"「{condition.description}」の具体的な判定方法が不明",
                    questions=self._generate_questions_for_condition(action, condition),
                    detection=DetectionInfo(
                        method="semantic_analysis",
                        confidence=0.85,
                        reasoning="条件文が存在するが具体的な定義がない"
                    ),
                    context=context,
                    estimated_severity=Priority.HIGH
                )
                elements.append(element)
        
        # エラーハンドリングの欠落
        # ※ チェックリストベースで既に検出されている場合はスキップ
        if action.error_handling and not action.error_handling.defined:
            # 処理タイプ別のチェックリストで既にカバーされている場合はスキップ
            if classification and classification.action_type != ActionType.UNKNOWN:
                # チェックリストで対応済みなのでスキップ
                pass
            else:
                # 処理タイプが不明な場合は従来通り検出
                element_id = self._generate_id()
                context = self._get_action_context(action, parsed_req)
                
                # 動詞が「処理」の場合はアクションIDを含める
                if action.verb == "処理":
                    title = f"アクション {action.id} のエラー処理が未定義"
                else:
                    title = f"{action.verb}のエラー処理が未定義"
                
                element = UndefinedElement(
                    id=element_id,
                    category="エラーハンドリングの欠落",
                    subcategory="ユーザーフィードバック",
                    related_action=action.id,
                    title=title,
                    description="エラー発生時の挙動やユーザーへのフィードバックが定義されていません",
                    questions=self._generate_questions_for_error_handling(action),
                    detection=DetectionInfo(
                        method="rule_based",
                        confidence=0.8,
                        reasoning="正常系の記述のみでエラー処理の言及がない"
                    ),
                    context=context,
                    estimated_severity=Priority.MEDIUM
                )
                elements.append(element)
        
        return elements
    
    def _extract_from_requirement(self, requirement) -> List[UndefinedElement]:
        """要件から未定義要素を抽出"""
        elements = []
        
        # 曖昧さが高い要件
        if requirement.ambiguity_score > 0.6:
            element_id = self._generate_id()
            
            # パターンマッチで具体的な問題を特定
            category, subcategory = self._identify_ambiguity_type(requirement.text)
            
            context = Context(
                source_text=requirement.text,
                surrounding_text=requirement.text,
                line_number=1  # 簡易実装
            )
            
            element = UndefinedElement(
                id=element_id,
                category=category,
                subcategory=subcategory,
                related_requirement=requirement.id,
                title=self._generate_ambiguity_title(requirement.text, category),
                description=f"「{requirement.text}」に曖昧な表現が含まれています",
                questions=self._generate_questions_for_ambiguity(requirement.text, category),
                detection=DetectionInfo(
                    method="pattern_matching",
                    confidence=0.75,
                    reasoning=f"曖昧さスコア: {requirement.ambiguity_score}"
                ),
                context=context,
                estimated_severity=Priority.MEDIUM
            )
            elements.append(element)
        
        return elements
    
    def _identify_ambiguity_type(self, text: str) -> tuple:
        """曖昧さのタイプを特定"""
        for category, patterns in self.vague_patterns.items():
            for pattern, subcategory in patterns:
                if re.search(pattern, text):
                    return category, subcategory
        
        return "非機能要件の曖昧さ", "パフォーマンス"
    
    def _generate_ambiguity_title(self, text: str, category: str) -> str:
        """曖昧性のタイトルを生成"""
        if '速い' in text or '高速' in text:
            return "「高速」の具体的基準が不明"
        elif '安全' in text or 'セキュア' in text:
            return "「安全」の具体的対策が不明"
        elif '場合' in text or 'とき' in text:
            return "実行条件の判定方法が不明"
        else:
            return "要件の定義が曖昧"
    
    def _generate_questions_for_entity(self, entity) -> List[Question]:
        """エンティティに対する質問を生成"""
        return [
            Question(
                text=f"{entity.name}のデータ型は何ですか？",
                type="specification",
                suggested_answers=["String", "Integer", "UUID", "Object"]
            ),
            Question(
                text=f"{entity.name}の制約条件はありますか？",
                type="constraint",
                suggested_answers=["最大長", "必須/任意", "一意性"]
            ),
        ]
    
    def _generate_questions_for_attribute(self, entity, attr) -> List[Question]:
        """属性に対する質問を生成"""
        return [
            Question(
                text=f"{attr.name}のデータ型は？",
                type="specification"
            ),
            Question(
                text=f"{attr.name}の最大値・最小値は？",
                type="constraint"
            ),
        ]
    
    def _generate_questions_for_condition(self, action, condition) -> List[Question]:
        """条件に対する質問を生成"""
        return [
            Question(
                text=f"「{condition.description}」の具体的な判定方法は？",
                type="clarification"
            ),
            Question(
                text="判定はリアルタイムで行うか、キャッシュを使用するか？",
                type="specification",
                suggested_answers=["リアルタイム", "キャッシュ（1分更新）", "キャッシュ（5分更新）"]
            ),
        ]
    
    def _generate_questions_for_error_handling(self, action) -> List[Question]:
        """エラーハンドリングに対する質問を生成"""
        return [
            Question(
                text=f"{action.verb}が失敗した場合の挙動は？",
                type="exception"
            ),
            Question(
                text="エラー時のユーザーへのフィードバックは？",
                type="clarification",
                suggested_answers=["エラーメッセージ表示", "ログ記録のみ", "通知"]
            ),
        ]
    
    def _generate_questions_for_ambiguity(self, text: str, category: str) -> List[Question]:
        """曖昧性に対する質問を生成"""
        if '速い' in text or '高速' in text:
            return [
                Question(
                    text="応答時間の目標値は？（例: 500ms以内）",
                    type="specification"
                ),
                Question(
                    text="想定する同時アクセス数は？",
                    type="specification"
                ),
            ]
        elif '安全' in text or 'セキュア' in text:
            return [
                Question(
                    text="具体的なセキュリティ対策は？（CSRF、XSS、SQL injection等）",
                    type="specification"
                ),
                Question(
                    text="認証・認可の方式は？",
                    type="specification"
                ),
            ]
        else:
            return [
                Question(
                    text="具体的な基準や数値を定義してください",
                    type="clarification"
                ),
            ]
    
    def _get_entity_context(self, entity, parsed_req: ParsedRequirement) -> Context:
        """エンティティのコンテキストを取得"""
        if entity.mentions:
            mention = entity.mentions[0]
            # センテンスを探す
            for sent in parsed_req.sentences:
                if sent.id == mention.sentence_id:
                    return Context(
                        source_text=entity.name,
                        surrounding_text=sent.text,
                        sentence_id=sent.id,
                        line_number=sent.line_number
                    )
        
        return Context(
            source_text=entity.name,
            surrounding_text="",
            line_number=1
        )
    
    def _get_action_context(self, action, parsed_req: ParsedRequirement) -> Context:
        """アクションのコンテキストを取得"""
        # アクションを含む文を探す
        for sent in parsed_req.sentences:
            if action.verb in sent.text:
                return Context(
                    source_text=action.verb,
                    surrounding_text=sent.text,
                    sentence_id=sent.id,
                    line_number=sent.line_number
                )
        
        return Context(
            source_text=action.verb,
            surrounding_text="",
            line_number=1
        )
    
    def _calculate_statistics(self, elements: List[UndefinedElement]) -> Dict[str, Any]:
        """統計情報を計算"""
        stats = {
            "total_undefined": len(elements),
            "by_category": {},
            "by_confidence": {"high": 0, "medium": 0, "low": 0},
            "by_severity": {},
            "by_method": {}  # 🆕 検出方法別の統計
        }
        
        for element in elements:
            # カテゴリ別
            category = element.category
            stats["by_category"][category] = stats["by_category"].get(category, 0) + 1
            
            # 信頼度別
            if element.detection.confidence >= 0.8:
                stats["by_confidence"]["high"] += 1
            elif element.detection.confidence >= 0.6:
                stats["by_confidence"]["medium"] += 1
            else:
                stats["by_confidence"]["low"] += 1
            
            # 重要度別
            severity = element.estimated_severity.value
            stats["by_severity"][severity] = stats["by_severity"].get(severity, 0) + 1
            
            # 🆕 検出方法別
            method = element.detection.method
            stats["by_method"][method] = stats["by_method"].get(method, 0) + 1
        
        return stats
    
    def _deduplicate(self, elements: List[UndefinedElement]) -> List[UndefinedElement]:
        """
        重複する未定義要素を除去
        
        同じtitleを持つ要素がある場合、信頼度の高い方を残す
        
        Args:
            elements: 未定義要素のリスト
        
        Returns:
            重複を除去したリスト
        """
        if not elements:
            return []
        
        # titleをキーとした辞書
        unique_map = {}
        
        for elem in elements:
            title = elem.title
            
            if title not in unique_map:
                unique_map[title] = elem
            else:
                # 既存要素と比較し、信頼度の高い方を保持
                existing = unique_map[title]
                if elem.detection.confidence > existing.detection.confidence:
                    unique_map[title] = elem
        
        return list(unique_map.values())
    
    def _perform_meta_analysis(
        self,
        parsed_req: ParsedRequirement,
        elements: List[UndefinedElement]
    ) -> MetaAnalysis:
        """メタ分析を実行"""
        overall_completeness = parsed_req.statistics.avg_completeness_score
        
        # クリティカルなギャップ
        critical_gaps = []
        for element in elements:
            if element.estimated_severity == Priority.HIGH or element.estimated_severity == Priority.CRITICAL:
                critical_gaps.append(element.title)
        
        # 推奨事項
        recommendations = []
        if parsed_req.statistics.avg_ambiguity_score > 0.6:
            recommendations.append("非機能要件を具体的な数値で定義してください")
        
        error_handling_count = sum(1 for e in elements if e.category == "エラーハンドリングの欠落")
        if error_handling_count > 0:
            recommendations.append(f"エラーハンドリングが{error_handling_count}箇所で欠落しています。異常系シナリオを網羅的に検討してください")
        
        if overall_completeness < 0.5:
            recommendations.append("全体的に仕様の詳細度が低いです。エンティティの定義、処理フロー、制約条件を明確化してください")
        
        return MetaAnalysis(
            overall_completeness=overall_completeness,
            critical_gaps=critical_gaps[:5],  # 上位5つ
            recommendations=recommendations
        )
    
    def _generate_id(self) -> str:
        """ID生成"""
        return f"UE-{uuid.uuid4().hex[:8].upper()}"



