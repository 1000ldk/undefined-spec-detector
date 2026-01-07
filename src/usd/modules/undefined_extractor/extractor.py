"""
Module 2: Undefined Extractor
未定義要素を抽出する
"""
import re
import uuid
from typing import List, Dict, Any
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


class UndefinedExtractor:
    """未定義要素を抽出するメインクラス"""
    
    def __init__(self):
        """初期化"""
        self.version = "1.0.0"
        self._load_detection_rules()
    
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
        未定義要素を抽出する
        
        Args:
            parsed_req: 構造化された要件（Module 1の出力）
        
        Returns:
            未定義要素のリスト
        """
        undefined_elements = []
        
        # 1. エンティティから抽出
        for entity in parsed_req.entities:
            elements = self._extract_from_entity(entity, parsed_req)
            undefined_elements.extend(elements)
        
        # 2. アクションから抽出
        for action in parsed_req.actions:
            elements = self._extract_from_action(action, parsed_req)
            undefined_elements.extend(elements)
        
        # 3. 要件から抽出
        for requirement in parsed_req.requirements:
            elements = self._extract_from_requirement(requirement)
            undefined_elements.extend(elements)
        
        # 4. 統計情報の計算
        statistics = self._calculate_statistics(undefined_elements)
        
        # 5. メタ分析
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
    
    def _extract_from_action(self, action, parsed_req: ParsedRequirement) -> List[UndefinedElement]:
        """アクションから未定義要素を抽出"""
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
        if action.error_handling and not action.error_handling.defined:
            element_id = self._generate_id()
            context = self._get_action_context(action, parsed_req)
            
            element = UndefinedElement(
                id=element_id,
                category="エラーハンドリングの欠落",
                subcategory="ユーザーフィードバック",
                related_action=action.id,
                title=f"{action.verb}のエラー処理が未定義",
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
            "by_severity": {}
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
        
        return stats
    
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


