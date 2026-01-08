"""
意思決定記録システム
要件定義時の意思決定を記録・追跡する
"""
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
import json
from pathlib import Path


class DecisionType(Enum):
    """意思決定のタイプ"""
    SELF_DECIDED = "自己判断"           # 自分で決めた仮定
    CONFIRMED = "確認済み"              # 相手に確認して得た回答
    DEFERRED = "保留"                   # 未解決のまま保留
    ASSUMED_DEFAULT = "デフォルト採用"  # 仮置きのデフォルト値を採用


@dataclass
class DecisionRecord:
    """意思決定の記録"""
    element_id: str
    question: str
    decision: str
    decision_type: DecisionType
    decided_by: str
    decided_at: datetime
    confidence: float  # 0.0-1.0
    rationale: str
    impact: str = ""
    related_decisions: List[str] = None
    
    def __post_init__(self):
        if self.related_decisions is None:
            self.related_decisions = []
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        d = asdict(self)
        d["decided_at"] = self.decided_at.isoformat()
        d["decision_type"] = self.decision_type.value
        return d
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DecisionRecord':
        """辞書から復元"""
        data["decided_at"] = datetime.fromisoformat(data["decided_at"])
        data["decision_type"] = DecisionType(data["decision_type"])
        return cls(**data)


class DecisionTracker:
    """意思決定追跡システム"""
    
    def __init__(self, storage_path: str = "decisions"):
        """
        初期化
        
        Args:
            storage_path: 記録ファイルの保存先
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.decisions: List[DecisionRecord] = []
    
    def record_decision(
        self,
        element_id: str,
        question: str,
        decision: str,
        decision_type: DecisionType,
        decided_by: str,
        rationale: str,
        confidence: float = 1.0,
        impact: str = ""
    ) -> DecisionRecord:
        """
        意思決定を記録
        
        Args:
            element_id: 要素ID
            question: 質問
            decision: 決定内容
            decision_type: 決定タイプ
            decided_by: 決定者
            rationale: 根拠・理由
            confidence: 確信度
            impact: 影響範囲
            
        Returns:
            DecisionRecord: 記録された意思決定
        """
        record = DecisionRecord(
            element_id=element_id,
            question=question,
            decision=decision,
            decision_type=decision_type,
            decided_by=decided_by,
            decided_at=datetime.now(),
            confidence=confidence,
            rationale=rationale,
            impact=impact
        )
        
        self.decisions.append(record)
        return record
    
    def get_decision(self, element_id: str) -> Optional[DecisionRecord]:
        """
        要素IDで意思決定を取得
        
        Args:
            element_id: 要素ID
            
        Returns:
            DecisionRecord または None
        """
        for decision in self.decisions:
            if decision.element_id == element_id:
                return decision
        return None
    
    def get_decisions_by_type(self, decision_type: DecisionType) -> List[DecisionRecord]:
        """
        タイプで意思決定を絞り込み
        
        Args:
            decision_type: 決定タイプ
            
        Returns:
            該当する意思決定のリスト
        """
        return [d for d in self.decisions if d.decision_type == decision_type]
    
    def save(self, project_name: str):
        """
        意思決定をファイルに保存
        
        Args:
            project_name: プロジェクト名
        """
        filename = f"{project_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.storage_path / filename
        
        data = {
            "project": project_name,
            "created_at": datetime.now().isoformat(),
            "decisions": [d.to_dict() for d in self.decisions]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load(self, filepath: str):
        """
        ファイルから意思決定を読み込み
        
        Args:
            filepath: ファイルパス
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.decisions = [
            DecisionRecord.from_dict(d) for d in data["decisions"]
        ]
    
    def generate_report(self, project_name: str) -> str:
        """
        意思決定記録のレポートを生成
        
        Args:
            project_name: プロジェクト名
            
        Returns:
            Markdown形式のレポート
        """
        report = f"""# 要件定義 意思決定記録

## プロジェクト: {project_name}
## 作成日: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}

---

"""
        
        # 確認済み事項
        confirmed = self.get_decisions_by_type(DecisionType.CONFIRMED)
        if confirmed:
            report += "### 🟢 必須事項（確認済み）\n\n"
            report += "| 項目 | 決定内容 | 決定者 | 日時 | 根拠 |\n"
            report += "|------|---------|-------|------|------|\n"
            for d in confirmed:
                report += f"| {d.question} | {d.decision} | {d.decided_by} | {d.decided_at.strftime('%m/%d %H:%M')} | {d.rationale} |\n"
            report += "\n"
        
        # 仮置き事項
        assumed = self.get_decisions_by_type(DecisionType.ASSUMED_DEFAULT)
        if assumed:
            report += "### 🟡 仮置き事項（後で確認予定）\n\n"
            report += "| 項目 | 仮置き内容 | 理由 | 確認先 |\n"
            report += "|------|-----------|------|--------|\n"
            for d in assumed:
                report += f"| {d.question} | {d.decision} | {d.rationale} | {d.decided_by} |\n"
            report += "\n"
        
        # 自己判断事項
        self_decided = self.get_decisions_by_type(DecisionType.SELF_DECIDED)
        if self_decided:
            report += "### 💡 自己判断事項\n\n"
            report += "| 項目 | 決定内容 | 理由 |\n"
            report += "|------|---------|------|\n"
            for d in self_decided:
                report += f"| {d.question} | {d.decision} | {d.rationale} |\n"
            report += "\n"
        
        # 未解決事項
        deferred = self.get_decisions_by_type(DecisionType.DEFERRED)
        if deferred:
            report += "### ⚠️ 未解決事項\n\n"
            report += "| 項目 | 現状 | リスク | 対応予定 |\n"
            report += "|------|------|--------|----------|\n"
            for d in deferred:
                report += f"| {d.question} | 保留中 | {d.impact} | {d.rationale} |\n"
            report += "\n"
        
        # サマリー
        report += "---\n\n"
        report += "### 📊 サマリー\n\n"
        report += f"- 確認済み: {len(confirmed)}件\n"
        report += f"- 仮置き: {len(assumed)}件\n"
        report += f"- 自己判断: {len(self_decided)}件\n"
        report += f"- 未解決: {len(deferred)}件\n"
        report += f"- 合計: {len(self.decisions)}件\n"
        
        return report
    
    def get_unresolved_count(self) -> int:
        """未解決事項の数を取得"""
        return len(self.get_decisions_by_type(DecisionType.DEFERRED))
    
    def get_high_risk_items(self) -> List[DecisionRecord]:
        """
        高リスクな未解決事項を取得
        
        Returns:
            高リスクな意思決定のリスト
        """
        return [
            d for d in self.decisions
            if d.decision_type == DecisionType.DEFERRED and d.confidence < 0.5
        ]



