# Remediation Advisor モジュール設計仕様

## 概要

検出されたリスクに対して、具体的な解消アクションを提案するモジュールです。

## 責務

- 工程判定（どのフェーズで解消すべきか）
- 具体的なアクションステップの生成
- 代替案の提示
- 優先順位付け
- 決定のトラッキング

## 技術スタック（想定）

```yaml
primary_language: Python 3.10+

libraries:
  - pydantic: データバリデーション
  - jinja2: レポートテンプレート
  - pyyaml: 設定ファイル
  
storage:
  - JSON/SQLite: 決定履歴の記録

testing:
  - pytest
```

## モジュール構成

```
modules/remediation-advisor/
├── __init__.py
├── advisor.py              # メインのAdvisorクラス
├── phase_detector.py       # 工程判定
├── action_generator.py     # アクション生成
├── alternative_generator.py # 代替案生成
├── prioritizer.py          # 優先順位付け
├── tracker.py              # 決定のトラッキング
├── schema.py               # データスキーマ
├── templates/
│   ├── action_templates.yaml
│   └── report_template.md.jinja2
└── tests/
    ├── test_advisor.py
    └── test_phase_detector.py
```

## 主要クラス設計

### RemediationAdvisor

```python
class RemediationAdvisor:
    """修正指示を生成するメインクラス"""
    
    def __init__(self, project_status: ProjectStatus):
        self.project_status = project_status
        
        self.phase_detector = PhaseDetector()
        self.action_generator = ActionGenerator()
        self.alternative_generator = AlternativeGenerator()
        self.prioritizer = Prioritizer(project_status)
        self.tracker = DecisionTracker()
    
    def generate(
        self,
        risks: RiskAnalysisResult,
        options: AdvisorOptions = None
    ) -> RemediationPlan:
        """
        リスクに対する修正指示を生成
        
        Args:
            risks: リスク分析結果（Module 3の出力）
            options: 生成オプション
        
        Returns:
            修正計画
        """
        options = options or AdvisorOptions()
        recommendations = []
        
        for risk in risks.risks:
            # 1. 工程判定
            recommended_phase = self.phase_detector.detect(risk)
            
            # 2. アクション生成
            action = self.action_generator.generate(
                risk,
                recommended_phase,
                self.project_status
            )
            
            # 3. 代替案生成
            alternatives = self.alternative_generator.generate(
                risk,
                action
            )
            
            # 4. 影響分析
            impact = self._analyze_impact(
                risk,
                recommended_phase,
                self.project_status.current_phase
            )
            
            # 5. 推奨事項の作成
            recommendation = Recommendation(
                id=self._generate_id(),
                undefined_element=risk.undefined_element,
                risk=risk.id,
                priority=0,  # 後で設定
                urgency=self._determine_urgency(risk, recommended_phase),
                recommended_phase=recommended_phase,
                current_phase=self.project_status.current_phase,
                phase_gap=self._calculate_phase_gap(
                    recommended_phase, 
                    self.project_status.current_phase
                ),
                warning=self._generate_warning(
                    recommended_phase, 
                    self.project_status.current_phase
                ),
                action=action,
                alternatives=alternatives,
                impact_on_schedule=impact.schedule,
                impact_on_cost=impact.cost,
                impact_on_quality=impact.quality
            )
            recommendations.append(recommendation)
        
        # 6. 優先順位付け
        recommendations = self.prioritizer.prioritize(
            recommendations,
            options
        )
        
        # 7. サマリーの生成
        summary = self._create_summary(recommendations)
        
        # 8. トラッキング情報の取得
        tracking = self.tracker.get_tracking_info(risks.document_id)
        
        return RemediationPlan(
            document_id=risks.document_id,
            generated_at=datetime.now(timezone.utc),
            recommendations=recommendations,
            summary=summary,
            tracking=tracking
        )
```

### PhaseDetector

```python
class PhaseDetector:
    """どの工程で解消すべきかを判定"""
    
    # フェーズの順序定義
    PHASE_ORDER = [
        "requirement_definition",
        "design", 
        "implementation",
        "testing",
        "operation"
    ]
    
    def detect(self, risk: Risk) -> Phase:
        """
        リスクを解消すべき工程を判定
        
        判定基準:
        1. 未定義要素のカテゴリ
        2. リスクレベル
        3. 影響範囲
        """
        element = risk.undefined_element
        
        # カテゴリベースの判定
        phase_rules = {
            "データ定義の欠落": self._judge_data_definition,
            "振る舞いの曖昧さ": self._judge_behavior,
            "責任分担の不明確さ": self._judge_responsibility,
            "境界条件の未定義": self._judge_boundary,
            "エラーハンドリングの欠落": self._judge_error_handling,
            "非機能要件の曖昧さ": self._judge_non_functional
        }
        
        judge_func = phase_rules.get(
            element.category,
            self._default_judge
        )
        
        return judge_func(risk)
    
    def _judge_data_definition(self, risk: Risk) -> Phase:
        """データ定義の欠落の判定"""
        element = risk.undefined_element
        
        # 基本的なデータ型や制約 → 要件定義
        if element.subcategory in ["型定義", "制約条件"]:
            return "requirement_definition"
        
        # フォーマットや詳細仕様 → 設計
        elif element.subcategory in ["フォーマット", "リレーション"]:
            return "design"
        
        # 初期値やデフォルト → 実装
        else:
            return "implementation"
    
    def _judge_behavior(self, risk: Risk) -> Phase:
        """振る舞いの曖昧さの判定"""
        # ビジネスロジック、トランザクション → 設計
        # アルゴリズムの詳細 → 実装
        
        if risk.risk_assessment.risk_level in ["critical", "high"]:
            return "design"
        else:
            return "implementation"
    
    def _judge_error_handling(self, risk: Risk) -> Phase:
        """エラーハンドリングの判定"""
        element = risk.undefined_element
        
        # エラー時のビジネスルール → 要件定義/設計
        if "業務" in element.description or "ユーザー" in element.description:
            return "design"
        
        # エラーメッセージの文言 → 実装
        else:
            return "implementation"
```

### ActionGenerator

```python
class ActionGenerator:
    """具体的なアクションステップを生成"""
    
    def __init__(self):
        self.templates = self._load_action_templates()
    
    def generate(
        self,
        risk: Risk,
        recommended_phase: Phase,
        project_status: ProjectStatus
    ) -> Action:
        """
        リスクに対する具体的なアクションを生成
        
        1. テンプレートベースの生成
        2. プロジェクト状況に応じたカスタマイズ
        3. 成果物と受入基準の定義
        """
        
        # テンプレートの選択
        template = self._select_template(
            risk.undefined_element.category,
            recommended_phase
        )
        
        # ステップの生成
        steps = self._generate_steps(
            risk,
            template,
            project_status
        )
        
        # 成果物の定義
        deliverables = self._define_deliverables(risk, recommended_phase)
        
        # 受入基準の定義
        acceptance_criteria = self._define_acceptance_criteria(risk)
        
        # 工数見積もり
        estimated_effort = self._estimate_effort(steps, project_status)
        
        return Action(
            type=self._determine_action_type(
                recommended_phase,
                project_status.current_phase
            ),
            title=self._generate_title(risk),
            description=self._generate_description(risk),
            steps=steps,
            deliverables=deliverables,
            acceptance_criteria=acceptance_criteria,
            estimated_effort=estimated_effort
        )
    
    def _generate_steps(
        self,
        risk: Risk,
        template: ActionTemplate,
        project_status: ProjectStatus
    ) -> List[ActionStep]:
        """アクションステップを生成"""
        steps = []
        
        for step_template in template.steps:
            # テンプレートをレンダリング
            description = self._render_template(
                step_template.description,
                risk=risk,
                project=project_status
            )
            
            # 担当者の割り当て
            assignee = self._assign_role(
                step_template.required_role,
                project_status.team_members
            )
            
            # 工数見積もり
            estimated_time = self._estimate_step_time(
                step_template,
                project_status
            )
            
            step = ActionStep(
                step=len(steps) + 1,
                description=description,
                assignee=assignee,
                estimated_time=estimated_time,
                questions=step_template.questions,
                decision_criteria=step_template.decision_criteria,
                stakeholders=step_template.stakeholders
            )
            steps.append(step)
        
        return steps
```

### Prioritizer

```python
class Prioritizer:
    """推奨事項の優先順位付け"""
    
    def __init__(self, project_status: ProjectStatus):
        self.project_status = project_status
    
    def prioritize(
        self,
        recommendations: List[Recommendation],
        options: AdvisorOptions
    ) -> List[Recommendation]:
        """
        推奨事項に優先順位を付ける
        
        考慮要素:
        1. リスクレベル
        2. 緊急度
        3. 工数
        4. 依存関係
        5. クイックウィン
        """
        
        # スコアリング
        for rec in recommendations:
            rec.priority_score = self._calculate_priority_score(rec)
        
        # ソート
        recommendations.sort(
            key=lambda r: r.priority_score,
            reverse=True
        )
        
        # 優先順位番号を付与
        for i, rec in enumerate(recommendations, 1):
            rec.priority = i
        
        return recommendations
    
    def _calculate_priority_score(
        self,
        recommendation: Recommendation
    ) -> float:
        """優先度スコアを計算"""
        
        # リスクレベルのスコア
        risk_score = {
            "critical": 10,
            "high": 7,
            "medium": 4,
            "low": 2
        }[recommendation.risk.risk_assessment.risk_level]
        
        # 緊急度のスコア
        urgency_score = {
            "immediate": 10,
            "high": 7,
            "medium": 4,
            "low": 2
        }[recommendation.urgency]
        
        # 工数の逆数（短時間で解決できるものを優先）
        effort_hours = self._parse_effort(
            recommendation.action.estimated_effort.total
        )
        effort_score = 10 / (effort_hours + 1)
        
        # 重み付き合計
        score = (
            risk_score * 0.5 +
            urgency_score * 0.3 +
            effort_score * 0.2
        )
        
        return score
```

## アクションテンプレート

```yaml
# templates/action_templates.yaml

templates:
  - category: "データ定義の欠落"
    phase: "requirement_definition"
    type: "clarify"
    
    steps:
      - required_role: "PM"
        description: "ステークホルダーと{entity}の定義を確認"
        estimated_base_time: "1時間"
        stakeholders: ["プロダクトオーナー"]
        questions:
          - "{entity}の具体的な型は？"
          - "制約条件は？"
      
      - required_role: "PM"
        description: "要件定義書に{entity}の定義を追記"
        estimated_base_time: "30分"
        artifacts: ["要件定義書 v{version+1}"]
    
    deliverables:
      - "更新された要件定義書"
    
    acceptance_criteria:
      - "{entity}のデータ型が明記されている"
      - "制約条件が列挙されている"

  - category: "振る舞いの曖昧さ"
    phase: "design"
    type: "design"
    
    steps:
      - required_role: "architect"
        description: "{action}の詳細フローを設計"
        estimated_base_time: "3時間"
      
      - required_role: "architect"
        description: "シーケンス図を作成"
        estimated_base_time: "2時間"
        artifacts: ["シーケンス図"]
      
      - required_role: "PM"
        description: "設計をレビュー"
        estimated_base_time: "1時間"
    
    deliverables:
      - "詳細設計書"
      - "シーケンス図"
    
    acceptance_criteria:
      - "処理の順序が明確"
      - "エラーケースが網羅されている"
```

## テスト戦略

```python
def test_phase_detection():
    """工程判定のテスト"""
    # データ定義の欠落 → 要件定義
    risk_data = create_data_definition_risk()
    phase = phase_detector.detect(risk_data)
    assert phase == "requirement_definition"
    
    # 振る舞いの曖昧さ（高リスク） → 設計
    risk_behavior = create_high_risk_behavior()
    phase = phase_detector.detect(risk_behavior)
    assert phase == "design"
    
    # エラーメッセージの文言 → 実装
    risk_error_msg = create_error_message_risk()
    phase = phase_detector.detect(risk_error_msg)
    assert phase == "implementation"

def test_action_generation():
    """アクション生成のテスト"""
    risk = create_test_risk()
    action = action_generator.generate(
        risk, 
        "design", 
        project_status
    )
    
    # ステップが存在
    assert len(action.steps) > 0
    # 担当者が割り当てられている
    assert all(s.assignee for s in action.steps)
    # 工数見積もりがある
    assert action.estimated_effort.total
    # 成果物が定義されている
    assert len(action.deliverables) > 0

def test_prioritization():
    """優先順位付けのテスト"""
    recs = [
        create_low_risk_recommendation(),
        create_high_risk_recommendation(),
        create_quick_win_recommendation()
    ]
    
    prioritized = prioritizer.prioritize(recs, options)
    
    # 高リスクが優先される
    assert prioritized[0].risk.risk_assessment.risk_level == "high"
    # クイックウィンも上位にくる
    assert any(
        r.action.estimated_effort.total == "30分" 
        for r in prioritized[:3]
    )
```

## まとめ

このモジュールは：
- ✅ 工程を自動判定
- ✅ 具体的なアクションを生成
- ✅ 複数の代替案を提示
- ✅ 優先順位を自動計算
- ✅ 決定をトラッキング


