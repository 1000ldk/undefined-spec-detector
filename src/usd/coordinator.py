"""
統合レイヤー: Analysis Coordinator
各モジュールを統合してエンドツーエンドの分析を実行
"""
from typing import Optional, Dict, Any
from datetime import datetime

from usd.schema import InputDocument, ParsedRequirement, UndefinedElements
from usd.modules.requirement_parser import RequirementParser
from usd.modules.undefined_extractor import UndefinedExtractor


class AnalysisCoordinator:
    """分析ワークフローを統合・調整するクラス"""
    
    def __init__(self):
        """初期化"""
        self.parser = RequirementParser()
        self.extractor = UndefinedExtractor()
        # Risk Analyzer と Remediation Advisor は将来実装
    
    def analyze(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        要件文書を分析する（フルワークフロー）
        
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
        
        # 2. Module 1: 要件解析
        print("📝 要件を解析中...")
        parsed_req = self.parser.parse(input_doc)
        print(f"✓ {parsed_req.statistics.total_sentences}文を解析")
        print(f"✓ {parsed_req.statistics.total_entities}個のエンティティを検出")
        print(f"✓ {parsed_req.statistics.total_actions}個のアクションを検出")
        
        # 3. Module 2: 未定義要素の抽出
        print("\n🔍 未定義要素を検出中...")
        undefined_elements = self.extractor.extract(parsed_req)
        print(f"✓ {undefined_elements.statistics['total_undefined']}個の未定義要素を検出")
        
        # 統計情報の表示
        if undefined_elements.statistics.get('by_category'):
            print("\nカテゴリ別:")
            for category, count in undefined_elements.statistics['by_category'].items():
                print(f"  - {category}: {count}件")
        
        # 4. 統合レポートの生成
        report = self._create_comprehensive_report(
            input_doc,
            parsed_req,
            undefined_elements
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
        undefined_elements: UndefinedElements
    ) -> Dict[str, Any]:
        """統合レポートを作成"""
        return {
            "report_id": f"REPORT-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "generated_at": datetime.now().isoformat(),
            "system_version": "0.1.0",
            
            "input_document": {
                "content": input_doc.content,
                "length": len(input_doc.content),
            },
            
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
                    }
                    for elem in undefined_elements.undefined_elements
                ],
            },
            
            "executive_summary": self._generate_executive_summary(
                parsed_req,
                undefined_elements
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
        undefined_elements: UndefinedElements
    ) -> Dict[str, Any]:
        """エグゼクティブサマリーを生成"""
        total_undefined = undefined_elements.statistics["total_undefined"]
        high_risk_count = undefined_elements.statistics.get("by_severity", {}).get("high", 0)
        
        # 全体的な評価
        if parsed_req.statistics.avg_completeness_score >= 0.7:
            overall_assessment = "良好"
        elif parsed_req.statistics.avg_completeness_score >= 0.5:
            overall_assessment = "要改善"
        else:
            overall_assessment = "不十分"
        
        # キーファインディング
        key_findings = []
        if total_undefined > 10:
            key_findings.append(f"{total_undefined}個の未定義要素が検出されました")
        if high_risk_count > 0:
            key_findings.append(f"うち{high_risk_count}個は高リスクです")
        if parsed_req.statistics.avg_ambiguity_score > 0.6:
            key_findings.append("曖昧な表現が多く含まれています")
        
        return {
            "overall_assessment": overall_assessment,
            "key_findings": key_findings,
            "total_undefined": total_undefined,
            "high_risk_count": high_risk_count,
        }



