# Risk Analyzer モジュール設計仕様

## 概要

未定義要素が引き起こす潜在的なリスクを評価し、地雷を予測するモジュールです。

## 責務

- 地雷パターンとのマッチング
- リスクの4軸評価（発生確率、影響度、発見困難度、修正コスト）
- 具体的な問題シナリオの生成
- プロジェクトへの影響予測

## 技術スタック（想定）

```yaml
primary_language: Python 3.10+

libraries:
  - pydantic: データバリデーション
  - sqlalchemy: 地雷パターンDBアクセス（オプション）
  - numpy: 数値計算
  
database:
  - SQLite: 地雷パターンDB（軽量）
  - または JSON/YAML ファイルベース

testing:
  - pytest
  - factory_boy: テストデータ生成
```

## モジュール構成

```
modules/risk-analyzer/
├── __init__.py
├── analyzer.py             # メインのAnalyzerクラス
├── risk_evaluator.py       # リスク評価
├── scenario_generator.py   # シナリオ生成
├── pattern_matcher.py      # 地雷パターンマッチング
├── cost_estimator.py       # コスト見積もり
├── schema.py               # データスキーマ
├── knowledge_base/
│   ├── risk_patterns.yaml  # 地雷パターン定義
│   └── historical_cases.yaml  # 過去の失敗事例
└── tests/
    ├── test_analyzer.py
    └── test_risk_evaluator.py
```

## 主要クラス設計

### RiskAnalyzer

```python
class RiskAnalyzer:
    """リスク分析を行うメインクラス"""
    
    def __init__(
        self,
        risk_knowledge_base: RiskKnowledgeBase,
        project_context: Optional[ProjectContext] = None
    ):
        self.knowledge_base = risk_knowledge_base
        self.project_context = project_context or ProjectContext()
        
        self.pattern_matcher = RiskPatternMatcher(self.knowledge_base)
        self.risk_evaluator = RiskEvaluator(self.project_context)
        self.scenario_generator = ScenarioGenerator(self.knowledge_base)
        self.cost_estimator = CostEstimator()
    
    def analyze(
        self,
        undefined_elements: UndefinedElements,
        options: AnalyzerOptions = None
    ) -> RiskAnalysisResult:
        """
        未定義要素のリスク分析を行う
        
        Args:
            undefined_elements: 未定義要素リスト（Module 2の出力）
            options: 分析オプション
        
        Returns:
            リスク分析結果
        """
        options = options or AnalyzerOptions()
        risks = []
        
        for element in undefined_elements.undefined_elements:
            # 1. 地雷パターンとマッチング
            matched_patterns = self.pattern_matcher.match(element)
            
            # 2. リスク評価
            risk_assessment = self.risk_evaluator.evaluate(
                element, 
                matched_patterns
            )
            
            # 3. シナリオ生成
            scenario = self.scenario_generator.generate(
                element, 
                matched_patterns
            )
            
            # 4. 影響分析
            consequences = self._analyze_consequences(
                element, 
                risk_assessment
            )
            
            # 5. 類似事例の検索
            similar_incidents = self._find_similar_incidents(element)
            
            # 6. 予防コストの見積もり
            prevention_cost = self.cost_estimator.estimate(
                element,
                risk_assessment
            )
            
            # 7. リスクオブジェクトの作成
            risk = Risk(
                id=self._generate_id(),
                undefined_element=element.id,
                title=self._generate_title(element, matched_patterns),
                description=self._generate_description(element),
                scenario=scenario,
                consequences=consequences,
                risk_assessment=risk_assessment,
                similar_incidents=similar_incidents,
                prevention_cost=prevention_cost,
                confidence=self._calculate_confidence(
                    element, matched_patterns
                )
            )
            risks.append(risk)
        
        # 8. 優先順位付け
        risks = self._prioritize_risks(risks)
        
        # 9. サマリーの生成
        summary = self._create_summary(risks)
        
        # 10. プロジェクト影響の予測
        project_impact = self._predict_project_impact(
            risks, 
            self.project_context
        )
        
        return RiskAnalysisResult(
            document_id=undefined_elements.document_id,
            analyzed_at=datetime.now(timezone.utc),
            risks=risks,
            summary=summary,
            project_impact=project_impact
        )
```

### RiskEvaluator

```python
class RiskEvaluator:
    """リスクの4軸評価を行う"""
    
    def __init__(self, project_context: ProjectContext):
        self.project_context = project_context
    
    def evaluate(
        self,
        element: UndefinedElement,
        matched_patterns: List[RiskPattern]
    ) -> RiskAssessment:
        """
        未定義要素のリスクを4軸で評価
        
        1. 発生確率（Probability）
        2. 影響度（Impact）
        3. 発見困難度（Detectability）
        4. 修正コスト（Remediation Cost）
        """
        
        # 1. 発生確率の評価
        probability = self._evaluate_probability(element, matched_patterns)
        
        # 2. 影響度の評価
        impact = self._evaluate_impact(element, matched_patterns)
        
        # 3. 発見困難度の評価
        detectability = self._evaluate_detectability(element)
        
        # 4. 修正コストの評価
        remediation_cost = self._evaluate_remediation_cost(element)
        
        # 5. 総合スコアの計算
        total_score = self._calculate_total_score(
            probability, impact, detectability, remediation_cost
        )
        
        # 6. リスクレベルの判定
        risk_level = self._determine_risk_level(total_score)
        
        return RiskAssessment(
            probability=probability,
            impact=impact,
            detectability=detectability,
            remediation_cost=remediation_cost,
            total_score=total_score,
            risk_level=risk_level
        )
    
    def _evaluate_probability(
        self,
        element: UndefinedElement,
        matched_patterns: List[RiskPattern]
    ) -> DimensionScore:
        """発生確率を評価"""
        
        # ベーススコア（カテゴリごとの統計値）
        base_score = self._get_base_probability(element.category)
        
        # パターンマッチによる調整
        pattern_adjustment = sum(
            p.probability_multiplier 
            for p in matched_patterns
        ) / len(matched_patterns) if matched_patterns else 1.0
        
        # プロジェクトコンテキストによる調整
        context_multiplier = self._get_context_multiplier(
            element, 
            "probability"
        )
        
        # 最終スコア
        score = base_score * pattern_adjustment * context_multiplier
        score = min(max(score, 1), 5)  # 1-5の範囲に正規化
        
        # レベルとreasoningの生成
        level = self._score_to_level(score)
        reasoning = self._generate_probability_reasoning(
            element, matched_patterns, score
        )
        
        return DimensionScore(
            level=level,
            score=score,
            reasoning=reasoning
        )
    
    def _evaluate_impact(
        self,
        element: UndefinedElement,
        matched_patterns: List[RiskPattern]
    ) -> DimensionScore:
        """影響度を評価"""
        
        # カテゴリごとの影響度
        category_impact = {
            "データ定義の欠落": 3.0,
            "振る舞いの曖昧さ": 3.5,
            "責任分担の不明確さ": 3.0,
            "境界条件の未定義": 3.5,
            "エラーハンドリングの欠落": 4.0,
            "非機能要件の曖昧さ": 3.5
        }
        
        base_score = category_impact.get(element.category, 3.0)
        
        # サブカテゴリによる調整
        if element.subcategory in ["セキュリティ", "トランザクション"]:
            base_score += 1.0
        
        # パターンマッチによる調整
        if matched_patterns:
            max_severity = max(
                p.severity_score 
                for p in matched_patterns
            )
            base_score = (base_score + max_severity) / 2
        
        # プロジェクトの重要度による調整
        if self.project_context.criticality == "mission_critical":
            base_score *= 1.2
        
        score = min(max(base_score, 1), 5)
        level = self._score_to_level(score)
        reasoning = self._generate_impact_reasoning(element, score)
        
        return DimensionScore(
            level=level,
            score=score,
            reasoning=reasoning
        )
    
    def _calculate_total_score(
        self,
        probability: DimensionScore,
        impact: DimensionScore,
        detectability: DimensionScore,
        remediation_cost: DimensionScore
    ) -> float:
        """総合スコアを計算（重み付き平均）"""
        weights = {
            "probability": 0.3,
            "impact": 0.4,
            "detectability": 0.2,
            "remediation_cost": 0.1
        }
        
        total = (
            probability.score * weights["probability"] +
            impact.score * weights["impact"] +
            detectability.score * weights["detectability"] +
            remediation_cost.score * weights["remediation_cost"]
        )
        
        return round(total, 2)
    
    def _determine_risk_level(self, total_score: float) -> RiskLevel:
        """総合スコアからリスクレベルを判定"""
        if total_score >= 3.5:
            return "critical"
        elif total_score >= 2.5:
            return "high"
        elif total_score >= 1.5:
            return "medium"
        else:
            return "low"
```

### ScenarioGenerator

```python
class ScenarioGenerator:
    """具体的な問題発生シナリオを生成"""
    
    def __init__(self, knowledge_base: RiskKnowledgeBase):
        self.knowledge_base = knowledge_base
        self.templates = self._load_scenario_templates()
    
    def generate(
        self,
        element: UndefinedElement,
        matched_patterns: List[RiskPattern]
    ) -> str:
        """
        未定義要素から具体的な問題シナリオを生成
        
        1. パターンに基づくテンプレート選択
        2. コンテキスト情報の埋め込み
        3. 具体的なステップの記述
        """
        
        if matched_patterns:
            # マッチしたパターンのシナリオを使用
            pattern = matched_patterns[0]  # 最も関連性の高いパターン
            template = pattern.scenario_template
        else:
            # デフォルトテンプレート
            template = self._get_default_template(element.category)
        
        # テンプレートに変数を埋め込み
        scenario = self._render_scenario(template, element)
        
        return scenario
    
    def _render_scenario(
        self,
        template: str,
        element: UndefinedElement
    ) -> str:
        """シナリオテンプレートをレンダリング"""
        # 実装省略
        pass
```

## 地雷パターンの定義

```yaml
# knowledge_base/risk_patterns.yaml

patterns:
  - id: "inventory_race_condition"
    name: "在庫の同時実行制御不備"
    
    triggers:
      categories: ["振る舞いの曖昧さ"]
      keywords: ["在庫", "同時", "確認"]
    
    scenario_template: |
      1. ユーザーAとユーザーBが同時に在庫1の商品を{action}
      2. 両方とも在庫チェックを通過
      3. 両方が処理を確定
      4. 在庫が-1になる
      5. {consequence}
    
    consequences:
      - type: "business"
        description: "出荷不可能な注文の発生"
        severity_score: 4
      - type: "reputation"
        description: "顧客満足度の低下"
        severity_score: 3
    
    probability_multiplier: 1.5  # 発生確率が高い
    
    historical_incidents:
      - case_id: "CASE-001"
        project: "某ECサイト"
        loss: "500万円"
    
    detection_phase: "testing"
    remediation_cost_multiplier: 10

  - id: "price_manipulation"
    name: "価格改ざんの脆弱性"
    
    triggers:
      categories: ["非機能要件の曖昧さ", "責任分担の不明確さ"]
      keywords: ["価格", "金額", "セキュリティ"]
    
    scenario_template: |
      1. 攻撃者がHTTPリクエストを傍受
      2. 価格パラメータを改ざん（例: 10000円 → 1円）
      3. サーバー側で価格検証がない
      4. 改ざんされた価格で購入が完了
      5. {consequence}
    
    consequences:
      - type: "security"
        description: "不正購入による金銭的損失"
        severity_score: 5
      - type: "legal"
        description: "監査での指摘"
        severity_score: 4
    
    probability_multiplier: 1.3
    detection_phase: "production"
    remediation_cost_multiplier: 50
```

## テスト戦略

```python
def test_evaluate_high_risk_element():
    """高リスクの未定義要素を正しく評価"""
    element = UndefinedElement(
        category="振る舞いの曖昧さ",
        subcategory="同時実行制御",
        title="在庫確認のタイミングが不明",
        # ...
    )
    
    analyzer = RiskAnalyzer(knowledge_base, project_context)
    result = analyzer.analyze(UndefinedElements(
        undefined_elements=[element]
    ))
    
    risk = result.risks[0]
    assert risk.risk_assessment.risk_level in ["high", "critical"]
    assert risk.risk_assessment.probability.score >= 3
    assert len(risk.consequences) > 0

def test_match_risk_pattern():
    """地雷パターンとのマッチング"""
    element = create_inventory_related_element()
    
    matched = pattern_matcher.match(element)
    
    assert any(p.id == "inventory_race_condition" for p in matched)

def test_scenario_generation():
    """具体的なシナリオが生成される"""
    element = create_test_element()
    
    scenario = scenario_generator.generate(element, [])
    
    # シナリオは複数のステップを含む
    assert scenario.count('\n') >= 3
    # 具体的な記述を含む
    assert len(scenario) > 100

def test_cost_estimation():
    """予防コストの見積もり"""
    element = create_test_element()
    
    cost = cost_estimator.estimate(element, risk_assessment)
    
    # フェーズが後になるほどコストが増加
    assert cost.if_found_in_production > cost.if_found_in_testing
    assert cost.if_found_in_testing > cost.if_found_in_design
```

## パフォーマンス

```yaml
performance:
  - 100個の未定義要素: < 5秒
  - 1000個の未定義要素: < 1分

caching:
  - 地雷パターンはメモリにキャッシュ
  - 類似事例の検索は最適化

scalability:
  - 並列処理可能
```

## まとめ

このモジュールは：
- ✅ 過去の失敗事例を活用
- ✅ 4軸の定量的評価
- ✅ 具体的なシナリオ生成
- ✅ プロジェクトコンテキストを考慮






