"""
統合レイヤー: Analysis Coordinator v2.0
各モジュールを統合してエンドツーエンドの分析を実行（コンテキスト駆動型）
"""
from typing import Optional, Dict, Any
from datetime import datetime

from usd.schema import InputDocument, ParsedRequirement, UndefinedElements
from usd.modules.requirement_parser import RequirementParser
from usd.modules.undefined_extractor import UndefinedExtractor
from usd.modules.action_classifier import ActionTypeClassifier


class AnalysisCoordinator:
    """分析ワークフローを統合・調整するクラス（v2.1 - LLM統合）"""
    
    def __init__(self, use_llm: bool = False, api_key: Optional[str] = None):
        """
        初期化
        
        Args:
            use_llm: LLMを使用するかどうか（デフォルト: False）
            api_key: OpenAI API Key（use_llm=Trueの場合に必要）
        """
        self.parser = RequirementParser()
        self.extractor = UndefinedExtractor(use_llm=use_llm, api_key=api_key)
        self.classifier = ActionTypeClassifier()
        # Risk Analyzer と Remediation Advisor は将来実装
        self.use_llm = use_llm
    
    def analyze(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        要件文書を分析する（フルワークフロー v2.0）
        
        Args:
            content: 要件文書のテキスト
            metadata: メタデータ（オプション）
            options: 分析オプション
        
        Returns:
            統合レポート
        """
        # 1. 入力ドキュメントの作成
        input_doc = InputDocument(
            content=content,
            metadata=metadata,
            options=options
        )
        
        # 【新機能】1.5. 処理タイプを分類
        print("🎯 処理タイプを分類中...")
        classification = self.classifier.classify(content)
        print(f"✓ 処理タイプ: {classification.action_type.value}")
        print(f"✓ 信頼度: {classification.confidence:.0%}")
        print(f"✓ 基本危険度: {classification.base_severity}")
        if classification.detected_entities:
            print(f"✓ 検出エンティティ: {', '.join(classification.detected_entities)}")
        
        # 2. Module 1: 要件解析
        print("\n📝 要件を解析中...")
        parsed_req = self.parser.parse(input_doc)
        print(f"✓ {parsed_req.statistics.total_sentences}文を解析")
        print(f"✓ {parsed_req.statistics.total_entities}個のエンティティを検出")
        print(f"✓ {parsed_req.statistics.total_actions}個のアクションを検出")
        
        # 3. Module 2: 未定義要素の抽出（v2.1 - LLM統合型）
        print("\n🔍 未定義要素を検出中...")
        if self.use_llm:
            print("   （LLMモード有効）")
        undefined_elements = self.extractor.extract(parsed_req)
        print(f"✓ {undefined_elements.statistics['total_undefined']}個の未定義要素を検出")
        
        # 統計情報の表示（致命度別）
        if undefined_elements.undefined_elements:
            print("\n📊 致命度別:")
            critical_count = sum(1 for e in undefined_elements.undefined_elements 
                               if e.criticality_info and "🔴" in e.criticality_info.get("level", ""))
            warning_count = sum(1 for e in undefined_elements.undefined_elements 
                              if e.criticality_info and "🟡" in e.criticality_info.get("level", ""))
            ok_count = sum(1 for e in undefined_elements.undefined_elements 
                          if e.criticality_info and "🟢" in e.criticality_info.get("level", ""))
            
            if critical_count > 0:
                print(f"  🔴 着手不可: {critical_count}件")
            if warning_count > 0:
                print(f"  🟡 要確認: {warning_count}件")
            if ok_count > 0:
                print(f"  🟢 後決めOK: {ok_count}件")
            
            # 🆕 検出方法別の表示
            if "by_method" in undefined_elements.statistics:
                print("\n検出方法別:")
                for method, count in undefined_elements.statistics["by_method"].items():
                    method_name = {
                        "rule_based": "ルールベース",
                        "template_driven": "テンプレート",
                        "llm": "LLM",
                        "semantic_analysis": "意味解析",
                        "pattern_matching": "パターンマッチ"
                    }.get(method, method)
                    print(f"  - {method_name}: {count}件")
        
        # カテゴリ別の表示
        if undefined_elements.statistics.get('by_category'):
            print("\nカテゴリ別:")
            for category, count in undefined_elements.statistics['by_category'].items():
                print(f"  - {category}: {count}件")
        
        # 4. 統合レポートの生成
        report = self._create_comprehensive_report(
            input_doc,
            parsed_req,
            undefined_elements,
            classification
        )
        
        return report
    
    def analyze_quick(self, content: str) -> UndefinedElements:
        """
        クイック分析（未定義要素のみ）
        
        Args:
            content: 要件文書のテキスト
        
        Returns:
            未定義要素リスト
        """
        input_doc = InputDocument(content=content)
        parsed_req = self.parser.parse(input_doc)
        undefined_elements = self.extractor.extract(parsed_req)
        return undefined_elements
    
    def _create_comprehensive_report(
        self,
        input_doc: InputDocument,
        parsed_req: ParsedRequirement,
        undefined_elements: UndefinedElements,
        classification=None
    ) -> Dict[str, Any]:
        """統合レポートを作成（v2.0）"""
        # 致命度別の集計
        criticality_stats = {
            "must_define": 0,
            "should_confirm": 0,
            "can_decide_later": 0
        }
        
        for elem in undefined_elements.undefined_elements:
            if elem.criticality_info:
                level = elem.criticality_info.get("level", "")
                if "🔴" in level:
                    criticality_stats["must_define"] += 1
                elif "🟡" in level:
                    criticality_stats["should_confirm"] += 1
                elif "🟢" in level:
                    criticality_stats["can_decide_later"] += 1
        
        return {
            "report_id": f"REPORT-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "generated_at": datetime.now().isoformat(),
            "system_version": "2.1.0-hybrid",  # 🆕 バージョン更新
            
            "input_document": {
                "content": input_doc.content,
                "length": len(input_doc.content),
            },
            
            # 【新機能】処理タイプ情報
            "action_classification": {
                "action_type": classification.action_type.value if classification else "UNKNOWN",
                "confidence": classification.confidence if classification else 0.0,
                "base_severity": classification.base_severity if classification else "UNKNOWN",
                "detected_entities": classification.detected_entities if classification else [],
                "matched_keywords": classification.matched_keywords if classification else []
            } if classification else None,
            
            "parsing_result": {
                "document_id": parsed_req.document_id,
                "sentences": len(parsed_req.sentences),
                "entities": len(parsed_req.entities),
                "actions": len(parsed_req.actions),
                "requirements": len(parsed_req.requirements),
                "statistics": {
                    "avg_completeness": parsed_req.statistics.avg_completeness_score,
                    "avg_ambiguity": parsed_req.statistics.avg_ambiguity_score,
                },
            },
            
            "undefined_elements": {
                "total": undefined_elements.statistics["total_undefined"],
                "by_category": undefined_elements.statistics.get("by_category", {}),
                "by_severity": undefined_elements.statistics.get("by_severity", {}),
                # 【新機能】致命度別の集計
                "by_criticality": criticality_stats,
                "elements": [
                    {
                        "id": elem.id,
                        "title": elem.title,
                        "category": elem.category,
                        "subcategory": elem.subcategory,
                        "description": elem.description,
                        "severity": elem.estimated_severity.value,
                        "questions": [q.text for q in elem.questions],
                        "confidence": elem.detection.confidence,
                        # 【新機能】致命度情報
                        "criticality": elem.criticality_info if elem.criticality_info else None
                    }
                    for elem in undefined_elements.undefined_elements
                ],
            },
            
            "executive_summary": self._generate_executive_summary(
                parsed_req,
                undefined_elements,
                criticality_stats
            ),
            
            "meta_analysis": {
                "overall_completeness": undefined_elements.meta_analysis.overall_completeness if undefined_elements.meta_analysis else 0.0,
                "critical_gaps": undefined_elements.meta_analysis.critical_gaps if undefined_elements.meta_analysis else [],
                "recommendations": undefined_elements.meta_analysis.recommendations if undefined_elements.meta_analysis else [],
            }
        }
    
    def _generate_executive_summary(
        self,
        parsed_req: ParsedRequirement,
        undefined_elements: UndefinedElements,
        criticality_stats: Dict[str, int] = None
    ) -> Dict[str, Any]:
        """エグゼクティブサマリーを生成（v2.0）"""
        total_undefined = undefined_elements.statistics["total_undefined"]
        high_risk_count = undefined_elements.statistics.get("by_severity", {}).get("high", 0)
        
        # 致命度に基づく評価
        if criticality_stats:
            must_define_count = criticality_stats.get("must_define", 0)
            should_confirm_count = criticality_stats.get("should_confirm", 0)
        else:
            must_define_count = 0
            should_confirm_count = 0
        
        # 全体的な評価
        if must_define_count > 0:
            overall_assessment = "着手不可（未定義解決が必須）"
            assessment_level = "CRITICAL"
        elif should_confirm_count > 5:
            overall_assessment = "要確認事項が多い"
            assessment_level = "HIGH"
        elif parsed_req.statistics.avg_completeness_score >= 0.7:
            overall_assessment = "良好"
            assessment_level = "GOOD"
        elif parsed_req.statistics.avg_completeness_score >= 0.5:
            overall_assessment = "要改善"
            assessment_level = "MEDIUM"
        else:
            overall_assessment = "不十分"
            assessment_level = "LOW"
        
        # キーファインディング
        key_findings = []
        if must_define_count > 0:
            key_findings.append(f"🔴 着手不可項目が{must_define_count}個あります。実装開始前に必ず解決してください")
        if should_confirm_count > 0:
            key_findings.append(f"🟡 確認推奨項目が{should_confirm_count}個あります")
        if total_undefined > 10:
            key_findings.append(f"{total_undefined}個の未定義要素が検出されました")
        if high_risk_count > 0:
            key_findings.append(f"うち{high_risk_count}個は高リスクです")
        if parsed_req.statistics.avg_ambiguity_score > 0.6:
            key_findings.append("曖昧な表現が多く含まれています")
        
        return {
            "overall_assessment": overall_assessment,
            "assessment_level": assessment_level,
            "key_findings": key_findings,
            "total_undefined": total_undefined,
            "high_risk_count": high_risk_count,
            "must_define_count": must_define_count,
            "should_confirm_count": should_confirm_count,
        }



