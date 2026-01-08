"""
致命度判定エンジン
未定義要素の致命度を判定する
"""
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional
import yaml
from pathlib import Path


class Criticality(Enum):
    """致命度レベル"""
    MUST_DEFINE = "🔴 着手不可"           # 未定義のまま実装開始は危険
    SHOULD_CONFIRM = "🟡 要確認"          # 仮置きで進めるが確認必要
    CAN_DECIDE_LATER = "🟢 後決めOK"      # 実装中に決めても間に合う
    
    def get_color(self) -> str:
        """色を取得"""
        if self == Criticality.MUST_DEFINE:
            return "red"
        elif self == Criticality.SHOULD_CONFIRM:
            return "yellow"
        else:
            return "green"
    
    def get_priority(self) -> int:
        """優先度を取得（数値が大きいほど優先）"""
        if self == Criticality.MUST_DEFINE:
            return 3
        elif self == Criticality.SHOULD_CONFIRM:
            return 2
        else:
            return 1


@dataclass
class CriticalityResult:
    """致命度判定結果"""
    element_id: str
    question: str
    criticality: Criticality
    reason: str
    change_cost_if_later: str
    recommended_decision_timing: str
    default_assumption: Optional[str]
    score: float
    affects: Dict[str, bool]


class CriticalityJudge:
    """致命度判定エンジン"""
    
    def __init__(self, templates_dir: str = "templates/action_checklists"):
        """
        初期化
        
        Args:
            templates_dir: チェックリストテンプレートのディレクトリ
        """
        self.templates_dir = Path(templates_dir)
        self.templates_cache = {}
    
    def load_template(self, action_type: str) -> Dict[str, Any]:
        """
        処理タイプのテンプレートを読み込み
        
        Args:
            action_type: 処理タイプ（例: "DELETE", "EXTERNAL_API"）
            
        Returns:
            テンプレートデータ
        """
        if action_type in self.templates_cache:
            return self.templates_cache[action_type]
        
        # ファイル名の変換（DELETE -> delete.yaml）
        filename = action_type.lower().replace("_", "_") + ".yaml"
        template_path = self.templates_dir / filename
        
        if not template_path.exists():
            return {"checklist": []}
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template = yaml.safe_load(f)
        
        self.templates_cache[action_type] = template
        return template
    
    def judge(
        self,
        element: Dict[str, Any],
        action_type: str,
        context: Optional[Dict[str, Any]] = None
    ) -> CriticalityResult:
        """
        未定義要素の致命度を判定
        
        Args:
            element: 未定義要素の情報
            action_type: 処理タイプ
            context: コンテキスト情報
            
        Returns:
            CriticalityResult: 致命度判定結果
        """
        # スコアを計算
        score = self._calculate_score(element, action_type, context)
        
        # 致命度を判定
        criticality = self._determine_criticality(score, element)
        
        # 推奨決定タイミング
        timing = self._determine_timing(criticality)
        
        return CriticalityResult(
            element_id=element.get("id", "unknown"),
            question=element.get("question", ""),
            criticality=criticality,
            reason=element.get("why_critical", ""),
            change_cost_if_later=element.get("change_cost_if_later", "不明"),
            recommended_decision_timing=timing,
            default_assumption=element.get("default_assumption"),
            score=score,
            affects=element.get("affects", {})
        )
    
    def _calculate_score(
        self,
        element: Dict[str, Any],
        action_type: str,
        context: Optional[Dict[str, Any]]
    ) -> float:
        """
        致命度スコアを計算
        
        Returns:
            スコア（0.0-10.0）
        """
        score = 0.0
        
        # 1. 影響範囲による加算
        affects = element.get("affects", {})
        if affects.get("data_model"):
            score += 3.0  # DB設計に影響
        if affects.get("external_system"):
            score += 2.0  # 外部システムに影響
        if affects.get("security"):
            score += 3.0  # セキュリティに影響
        
        # 2. 変更コストによる加算
        change_cost = element.get("change_cost_if_later", "")
        if "200" in change_cost or "300" in change_cost:
            score += 3.0  # 超高コスト
        elif "100" in change_cost:
            score += 2.5  # 高コスト
        elif "50" in change_cost or "40" in change_cost:
            score += 2.0  # 中コスト
        elif "20" in change_cost or "30" in change_cost:
            score += 1.5  # やや高コスト
        elif "10" in change_cost:
            score += 1.0  # 普通
        else:
            score += 0.5  # 低コスト
        
        # 3. 検出フェーズによる加算
        detection_phase = element.get("detection_phase", "implementation")
        if detection_phase == "production":
            score += 2.0  # 本番で発覚すると致命的
        elif detection_phase == "testing":
            score += 1.5  # テストで発覚
        elif detection_phase == "design":
            score += 1.0  # 設計フェーズ
        
        # 4. テンプレートで明示的に指定されている場合
        criticality_str = element.get("criticality", "")
        if criticality_str == "MUST_DEFINE":
            score = max(score, 5.0)  # 最低でも5.0
        elif criticality_str == "SHOULD_CONFIRM":
            score = max(score, 3.0)  # 最低でも3.0
        
        return min(score, 10.0)  # 最大10.0
    
    def _determine_criticality(
        self,
        score: float,
        element: Dict[str, Any]
    ) -> Criticality:
        """
        スコアから致命度を判定
        
        Args:
            score: 計算されたスコア
            element: 要素情報
            
        Returns:
            Criticality: 致命度レベル
        """
        # テンプレートで明示的に指定されている場合はそれを優先
        criticality_str = element.get("criticality", "")
        if criticality_str == "MUST_DEFINE":
            return Criticality.MUST_DEFINE
        elif criticality_str == "SHOULD_CONFIRM":
            return Criticality.SHOULD_CONFIRM
        elif criticality_str == "CAN_DECIDE_LATER":
            return Criticality.CAN_DECIDE_LATER
        
        # スコアベースの判定
        if score >= 5.0:
            return Criticality.MUST_DEFINE
        elif score >= 3.0:
            return Criticality.SHOULD_CONFIRM
        else:
            return Criticality.CAN_DECIDE_LATER
    
    def _determine_timing(self, criticality: Criticality) -> str:
        """
        推奨決定タイミングを判定
        
        Args:
            criticality: 致命度
            
        Returns:
            推奨タイミング
        """
        if criticality == Criticality.MUST_DEFINE:
            return "実装開始前"
        elif criticality == Criticality.SHOULD_CONFIRM:
            return "設計完了前"
        else:
            return "実装中"
    
    def get_checklist_for_action_type(self, action_type: str) -> list:
        """
        処理タイプのチェックリストを取得
        
        Args:
            action_type: 処理タイプ
            
        Returns:
            チェックリスト
        """
        template = self.load_template(action_type)
        return template.get("checklist", [])
    
    def judge_all_for_action_type(
        self,
        action_type: str,
        context: Optional[Dict[str, Any]] = None
    ) -> list[CriticalityResult]:
        """
        処理タイプの全チェック項目を判定
        
        Args:
            action_type: 処理タイプ
            context: コンテキスト
            
        Returns:
            判定結果のリスト
        """
        checklist = self.get_checklist_for_action_type(action_type)
        results = []
        
        for item in checklist:
            result = self.judge(item, action_type, context)
            results.append(result)
        
        # 優先度でソート
        results.sort(key=lambda x: x.criticality.get_priority(), reverse=True)
        
        return results



