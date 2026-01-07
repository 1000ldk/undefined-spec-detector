# モジュール入出力仕様

このドキュメントは、各モジュールの詳細な入出力定義、データスキーマ、バリデーションルールを定義します。

---

## 共通データ型定義

### 基本型

```typescript
// タイムスタンプ
type Timestamp = string; // ISO 8601 format: "2026-01-07T10:00:00Z"

// 識別子
type ID = string; // 例: "DOC-001", "UE-123", "RISK-456"

// 信頼度スコア
type ConfidenceScore = number; // 0.0 〜 1.0

// 優先度レベル
type Priority = "low" | "medium" | "high" | "critical";

// 工程
type Phase = "requirement_definition" | "design" | "implementation" | "testing" | "operation";

// リスクレベル
type RiskLevel = "low" | "medium" | "high" | "critical";
```

### メタデータ

```typescript
interface Metadata {
  created_at: Timestamp;
  created_by?: string;
  version: string;
  source?: string;
  tags?: string[];
}
```

---

## Module 1: Requirement Parser

### 入力仕様

#### InputDocument

```typescript
interface InputDocument {
  // 必須フィールド
  content: string;              // 解析対象のテキスト
  
  // オプションフィールド
  metadata?: {
    source?: string;            // 出典: "要件定義書", "メール", "チケット"
    author?: string;            // 作成者
    created_at?: Timestamp;     // 作成日時
    document_type?: string;     // "requirement" | "specification" | "design"
    version?: string;           // ドキュメントバージョン
  };
  
  // コンテキスト情報
  context?: {
    project_name?: string;
    domain?: string;            // "ecommerce", "finance", "healthcare"
    phase?: Phase;
    related_documents?: string[]; // 関連ドキュメントのID
  };
  
  // 解析オプション
  options?: {
    language?: string;          // "ja", "en" (デフォルト: 自動検出)
    sentence_split?: boolean;   // 文単位に分割するか (デフォルト: true)
    extract_entities?: boolean; // エンティティ抽出を行うか (デフォルト: true)
    extract_relations?: boolean;// 関係抽出を行うか (デフォルト: true)
  };
}
```

#### 入力例

```json
{
  "content": "ユーザーは商品をカートに追加できる。在庫がある場合のみ追加可能。",
  "metadata": {
    "source": "要件定義書 v1.2",
    "author": "山田太郎",
    "created_at": "2026-01-05T14:30:00Z",
    "document_type": "requirement"
  },
  "context": {
    "project_name": "ECサイトリニューアル",
    "domain": "ecommerce",
    "phase": "requirement_definition"
  },
  "options": {
    "language": "ja",
    "sentence_split": true,
    "extract_entities": true,
    "extract_relations": true
  }
}
```

### 出力仕様

#### ParsedRequirement

```typescript
interface ParsedRequirement {
  // メタ情報
  document_id: ID;
  parsed_at: Timestamp;
  parser_version: string;
  
  // 元文書情報
  original_content: string;
  metadata: Metadata;
  
  // 解析結果
  sentences: Sentence[];
  entities: Entity[];
  relationships: Relationship[];
  actions: Action[];
  constraints: Constraint[];
  requirements: Requirement[];
  
  // 統計情報
  statistics: {
    total_sentences: number;
    total_entities: number;
    total_relationships: number;
    total_actions: number;
    avg_completeness_score: number;
    avg_ambiguity_score: number;
  };
}

interface Sentence {
  id: ID;
  text: string;
  line_number: number;
  start_char: number;
  end_char: number;
  type: "requirement" | "constraint" | "explanation" | "example";
  importance: Priority;
}

interface Entity {
  id: ID;
  name: string;
  type: "actor" | "object" | "system" | "data" | "event";
  
  attributes: Attribute[];
  
  mentions: {
    sentence_id: ID;
    text: string;
    position: number;
  }[];
  
  definition_status: "defined" | "partially_defined" | "undefined";
  ambiguity_score: ConfidenceScore;
}

interface Attribute {
  name: string;
  mentioned: boolean;
  defined: boolean;
  definition?: {
    type?: string;
    constraints?: string[];
    default_value?: string;
  };
}

interface Relationship {
  id: ID;
  from_entity: ID;
  to_entity: ID;
  type: "owns" | "uses" | "depends_on" | "references" | "contains";
  description: string;
  
  cardinality?: {
    min?: number;
    max?: number | "unlimited";
  };
  
  bidirectional: boolean;
  strength: "weak" | "medium" | "strong";
}

interface Action {
  id: ID;
  verb: string;
  subject: ID;          // Entity ID
  object?: ID;          // Entity ID
  
  preconditions: Condition[];
  postconditions: Condition[];
  
  timing?: {
    trigger?: string;   // "on_click", "periodic", "on_event"
    duration?: string;
  };
  
  error_handling?: {
    mentioned: boolean;
    defined: boolean;
  };
}

interface Condition {
  description: string;
  type: "precondition" | "postcondition" | "invariant";
  defined: boolean;
  ambiguous: boolean;
  entities: ID[];       // 関連するEntity ID
}

interface Constraint {
  id: ID;
  description: string;
  type: "business_rule" | "technical" | "legal" | "performance";
  entities: ID[];
  scope: "global" | "local";
  priority: Priority;
}

interface Requirement {
  id: ID;
  text: string;
  type: "functional" | "non_functional";
  category?: string;
  
  priority?: Priority;
  
  completeness_score: ConfidenceScore;  // 0: 不完全, 1: 完全
  ambiguity_score: ConfidenceScore;     // 0: 明確, 1: 曖昧
  
  related_entities: ID[];
  related_actions: ID[];
  
  missing_elements: string[];  // 欠けている要素のリスト
}
```

#### 出力例

```json
{
  "document_id": "DOC-001",
  "parsed_at": "2026-01-07T10:00:00Z",
  "parser_version": "1.0.0",
  
  "original_content": "ユーザーは商品をカートに追加できる。在庫がある場合のみ追加可能。",
  
  "sentences": [
    {
      "id": "S-001",
      "text": "ユーザーは商品をカートに追加できる。",
      "line_number": 1,
      "start_char": 0,
      "end_char": 21,
      "type": "requirement",
      "importance": "high"
    }
  ],
  
  "entities": [
    {
      "id": "E-001",
      "name": "ユーザー",
      "type": "actor",
      "attributes": [],
      "mentions": [
        {
          "sentence_id": "S-001",
          "text": "ユーザー",
          "position": 0
        }
      ],
      "definition_status": "undefined",
      "ambiguity_score": 0.8
    },
    {
      "id": "E-002",
      "name": "商品",
      "type": "object",
      "attributes": [
        {
          "name": "在庫数",
          "mentioned": true,
          "defined": false
        }
      ],
      "mentions": [
        {
          "sentence_id": "S-001",
          "text": "商品",
          "position": 5
        }
      ],
      "definition_status": "partially_defined",
      "ambiguity_score": 0.6
    }
  ],
  
  "actions": [
    {
      "id": "A-001",
      "verb": "追加する",
      "subject": "E-001",
      "object": "E-002",
      "preconditions": [
        {
          "description": "在庫がある場合",
          "type": "precondition",
          "defined": false,
          "ambiguous": true,
          "entities": ["E-002"]
        }
      ],
      "postconditions": [],
      "error_handling": {
        "mentioned": false,
        "defined": false
      }
    }
  ],
  
  "requirements": [
    {
      "id": "REQ-001",
      "text": "ユーザーは商品をカートに追加できる",
      "type": "functional",
      "completeness_score": 0.3,
      "ambiguity_score": 0.7,
      "related_entities": ["E-001", "E-002"],
      "related_actions": ["A-001"],
      "missing_elements": [
        "カートの定義",
        "在庫確認の方法",
        "エラー時の挙動"
      ]
    }
  ],
  
  "statistics": {
    "total_sentences": 2,
    "total_entities": 3,
    "total_relationships": 1,
    "total_actions": 1,
    "avg_completeness_score": 0.3,
    "avg_ambiguity_score": 0.7
  }
}
```

---

## Module 2: Undefined Extractor

### 入力仕様

```typescript
interface ExtractorInput {
  // 必須: Module 1の出力
  parsed_requirements: ParsedRequirement;
  
  // オプション: 分類ルール
  classification_template?: ClassificationTemplate;
  
  // オプション: ドメイン知識
  domain_knowledge?: DomainKnowledge;
  
  // 抽出オプション
  options?: {
    confidence_threshold?: number;     // 最小信頼度 (デフォルト: 0.5)
    categories?: string[];             // 抽出対象カテゴリ (デフォルト: 全て)
    max_questions_per_element?: number; // 質問の最大数 (デフォルト: 5)
    include_low_confidence?: boolean;  // 低信頼度も含めるか (デフォルト: false)
  };
}

interface ClassificationTemplate {
  version: string;
  categories: Category[];
  detection_rules: DetectionRule[];
  question_templates: QuestionTemplate[];
}

interface DomainKnowledge {
  domain: string;
  common_entities: string[];
  typical_constraints: string[];
  domain_specific_risks: string[];
}
```

### 出力仕様

```typescript
interface UndefinedElements {
  // メタ情報
  document_id: ID;
  analyzed_at: Timestamp;
  extractor_version: string;
  
  // 入力の参照
  source_document: ID;
  
  // 未定義要素リスト
  undefined_elements: UndefinedElement[];
  
  // グループ化
  groups: UndefinedElementGroup[];
  
  // 統計情報
  statistics: {
    total_undefined: number;
    by_category: Record<string, number>;
    by_confidence: {
      high: number;
      medium: number;
      low: number;
    };
    by_severity: Record<string, number>;
  };
  
  // メタ分析
  meta_analysis: {
    overall_completeness: ConfidenceScore;
    critical_gaps: string[];
    recommendations: string[];
  };
}

interface UndefinedElement {
  id: ID;
  
  // 分類
  category: string;        // "データ定義の欠落" など
  subcategory: string;     // "制約条件" など
  
  // 関連要素
  related_entity?: ID;
  related_action?: ID;
  related_requirement?: ID;
  
  // 説明
  title: string;
  description: string;
  
  // 質問
  questions: Question[];
  
  // 検出情報
  detection: {
    method: "pattern_matching" | "semantic_analysis" | "rule_based" | "ml_model";
    confidence: ConfidenceScore;
    reasoning: string;
  };
  
  // コンテキスト
  context: {
    source_text: string;
    surrounding_text: string;
    sentence_id: ID;
    line_number: number;
  };
  
  // 関連性
  cross_references: ID[];  // 関連する他の未定義要素
  
  // 優先度（初期推定）
  estimated_severity: Priority;
}

interface Question {
  text: string;
  type: "clarification" | "specification" | "constraint" | "exception";
  suggested_answers?: string[];
  reference?: string;      // 確認先の参考情報
}

interface UndefinedElementGroup {
  id: ID;
  title: string;
  description: string;
  element_ids: ID[];
  relationship: "related" | "dependent" | "mutually_exclusive";
  should_resolve_together: boolean;
}
```

#### 出力例

```json
{
  "document_id": "DOC-001",
  "analyzed_at": "2026-01-07T10:05:00Z",
  "extractor_version": "1.0.0",
  "source_document": "DOC-001",
  
  "undefined_elements": [
    {
      "id": "UE-001",
      "category": "振る舞いの曖昧さ",
      "subcategory": "実行条件",
      "related_action": "A-001",
      
      "title": "在庫確認のタイミングが不明",
      "description": "「在庫がある場合」の確認タイミングと方法が定義されていない",
      
      "questions": [
        {
          "text": "在庫確認はリアルタイムで行うか、キャッシュを使用するか？",
          "type": "specification",
          "suggested_answers": ["リアルタイム確認", "キャッシュ（1分更新）", "キャッシュ（5分更新）"]
        },
        {
          "text": "複数ユーザーが同時に同じ商品をカートに追加した場合の挙動は？",
          "type": "exception",
          "reference": "同時実行制御の設計が必要"
        },
        {
          "text": "在庫予約の仕組みは必要か？（カートに入れた時点で在庫を確保するか）",
          "type": "clarification"
        }
      ],
      
      "detection": {
        "method": "semantic_analysis",
        "confidence": 0.85,
        "reasoning": "条件文「在庫がある場合」に対する具体的な判定方法の記述がない"
      },
      
      "context": {
        "source_text": "在庫がある場合のみ追加可能",
        "surrounding_text": "ユーザーは商品をカートに追加できる。在庫がある場合のみ追加可能。",
        "sentence_id": "S-002",
        "line_number": 1
      },
      
      "cross_references": ["UE-004", "UE-007"],
      "estimated_severity": "high"
    }
  ],
  
  "groups": [
    {
      "id": "G-001",
      "title": "在庫管理関連",
      "description": "在庫確認、予約、ロック処理に関する未定義要素",
      "element_ids": ["UE-001", "UE-004", "UE-007"],
      "relationship": "dependent",
      "should_resolve_together": true
    }
  ],
  
  "statistics": {
    "total_undefined": 15,
    "by_category": {
      "データ定義の欠落": 5,
      "振る舞いの曖昧さ": 4,
      "責任分担の不明確さ": 2,
      "境界条件の未定義": 2,
      "エラーハンドリングの欠落": 1,
      "非機能要件の曖昧さ": 1
    },
    "by_confidence": {
      "high": 8,
      "medium": 5,
      "low": 2
    },
    "by_severity": {
      "critical": 2,
      "high": 5,
      "medium": 6,
      "low": 2
    }
  },
  
  "meta_analysis": {
    "overall_completeness": 0.35,
    "critical_gaps": [
      "在庫管理の同時実行制御が未定義",
      "エラーハンドリングがほぼ全て欠落"
    ],
    "recommendations": [
      "在庫管理に関する技術的仕様を優先的に定義すべき",
      "異常系のシナリオを網羅的に洗い出すべき"
    ]
  }
}
```

---

## Module 3: Risk Analyzer

### 入力仕様

```typescript
interface RiskAnalyzerInput {
  // 必須: Module 2の出力
  undefined_elements: UndefinedElements;
  
  // オプション: 地雷パターンDB
  risk_knowledge_base?: RiskKnowledgeBase;
  
  // プロジェクトコンテキスト
  project_context?: {
    phase: Phase;
    team_size?: number;
    deadline?: Timestamp;
    budget?: "tight" | "moderate" | "flexible";
    domain: string;
    criticality?: "low" | "medium" | "high" | "mission_critical";
  };
  
  // 分析オプション
  options?: {
    include_historical_cases?: boolean;
    calculate_financial_impact?: boolean;
    min_risk_level?: RiskLevel;
  };
}

interface RiskKnowledgeBase {
  patterns: RiskPattern[];
  historical_incidents: HistoricalIncident[];
  domain_specific_risks: DomainRisk[];
}
```

### 出力仕様

```typescript
interface RiskAnalysisResult {
  // メタ情報
  document_id: ID;
  analyzed_at: Timestamp;
  analyzer_version: string;
  
  // リスク評価
  risks: Risk[];
  
  // 統計とサマリー
  summary: RiskSummary;
  
  // プロジェクトへの影響予測
  project_impact: ProjectImpact;
}

interface Risk {
  id: ID;
  undefined_element: ID;
  
  // タイトルと説明
  title: string;
  description: string;
  
  // 発生シナリオ
  scenario: string;
  trigger_conditions: string[];
  
  // 影響
  consequences: Consequence[];
  
  // リスク評価
  risk_assessment: RiskAssessment;
  
  // 参考情報
  similar_incidents: HistoricalIncident[];
  
  // 予防コスト
  prevention_cost: PreventionCost;
  
  // メタ情報
  confidence: ConfidenceScore;
  last_updated: Timestamp;
}

interface Consequence {
  type: "business" | "technical" | "legal" | "reputation" | "security";
  description: string;
  severity: Priority;
  affected_stakeholders: string[];
  estimated_cost?: {
    min: number;
    max: number;
    currency: string;
  };
}

interface RiskAssessment {
  // 4軸評価
  probability: {
    level: Priority;
    score: number;        // 1-5
    reasoning: string;
  };
  
  impact: {
    level: Priority;
    score: number;        // 1-5
    reasoning: string;
  };
  
  detectability: {
    level: Priority;
    score: number;        // 1-5
    reasoning: string;
    detection_phase: Phase;
  };
  
  remediation_cost: {
    level: Priority;
    score: number;        // 1-5
    reasoning: string;
  };
  
  // 総合評価
  total_score: number;
  risk_level: RiskLevel;
  priority_rank: number;
}

interface PreventionCost {
  if_found_in_requirement: string;
  if_found_in_design: string;
  if_found_in_implementation: string;
  if_found_in_testing: string;
  if_found_in_production: string;
  
  cost_multiplier: {
    requirement_to_design: number;
    design_to_implementation: number;
    implementation_to_testing: number;
    testing_to_production: number;
  };
}

interface RiskSummary {
  total_risks: number;
  by_level: Record<RiskLevel, number>;
  by_type: Record<string, number>;
  
  top_risks: ID[];       // Top 5のリスクID
  
  estimated_total_impact: {
    min_cost: number;
    max_cost: number;
    currency: string;
    time_delay: string;
  };
  
  estimated_prevention_cost: {
    effort: string;
    cost: number;
    currency: string;
  };
  
  roi: number;           // Return on Investment (予防のROI)
}

interface ProjectImpact {
  schedule_risk: {
    probability_of_delay: ConfidenceScore;
    estimated_delay: string;
    critical_path_impact: boolean;
  };
  
  quality_risk: {
    defect_probability: ConfidenceScore;
    severity_distribution: Record<Priority, number>;
  };
  
  cost_risk: {
    budget_overrun_probability: ConfidenceScore;
    estimated_additional_cost: number;
  };
  
  recommendations: string[];
}
```

---

## Module 4: Remediation Advisor

### 入力仕様

```typescript
interface RemediationAdvisorInput {
  // 必須: Module 3の出力
  risks: RiskAnalysisResult;
  
  // プロジェクト状況
  project_status: {
    current_phase: Phase;
    team_members: TeamMember[];
    constraints: {
      budget: "tight" | "moderate" | "flexible";
      deadline: "immediate" | "tight" | "moderate" | "flexible";
      quality_priority: "speed" | "balanced" | "quality";
    };
  };
  
  // オプション
  options?: {
    max_recommendations?: number;
    focus_on_quick_wins?: boolean;
    include_alternatives?: boolean;
  };
}

interface TeamMember {
  role: string;          // "PM", "architect", "developer", "QA"
  name?: string;
  availability?: "full" | "partial" | "limited";
}
```

### 出力仕様

```typescript
interface RemediationPlan {
  // メタ情報
  document_id: ID;
  generated_at: Timestamp;
  advisor_version: string;
  
  // 推奨アクション
  recommendations: Recommendation[];
  
  // サマリー
  summary: RemediationSummary;
  
  // トラッキング
  tracking: DecisionTracking;
}

interface Recommendation {
  id: ID;
  undefined_element: ID;
  risk: ID;
  
  // 優先度
  priority: number;      // 1が最高優先
  urgency: "immediate" | "high" | "medium" | "low";
  
  // 工程判定
  recommended_phase: Phase;
  current_phase: Phase;
  phase_gap: number;     // マイナスなら戻る必要あり
  warning?: string;      // 工程を戻る場合の警告
  
  // アクション
  action: Action;
  
  // 代替案
  alternatives: Alternative[];
  
  // 影響
  impact_on_schedule: string;
  impact_on_cost: string;
  impact_on_quality: string;
}

interface Action {
  type: "clarify" | "design" | "implement" | "test" | "rollback_and_clarify";
  title: string;
  description: string;
  
  steps: ActionStep[];
  deliverables: string[];
  acceptance_criteria: string[];
  
  estimated_effort: {
    total: string;
    by_role: Record<string, string>;
  };
}

interface ActionStep {
  step: number;
  description: string;
  assignee: string;      // role
  estimated_time: string;
  
  dependencies?: number[];  // 依存する他のステップ番号
  
  questions?: string[];
  decision_criteria?: string[];
  stakeholders?: string[];
  
  artifacts?: string[];  // 成果物
}

interface Alternative {
  option: string;
  description: string;
  conditions: string;
  pros: string[];
  cons: string[];
  residual_risk: RiskLevel;
  effort: string;
}

interface RemediationSummary {
  total_recommendations: number;
  
  by_phase: Record<Phase, number>;
  by_urgency: Record<string, number>;
  
  estimated_total_effort: string;
  estimated_total_cost: number;
  
  quick_wins: QuickWin[];
  
  critical_blockers: ID[];  // 即座に対応が必要な項目
}

interface QuickWin {
  recommendation_id: ID;
  description: string;
  effort: string;
  risk_reduction: RiskLevel;
  roi_score: number;
}

interface DecisionTracking {
  decisions: Decision[];
  
  accepted_risks: AcceptedRisk[];
  deferred_items: DeferredItem[];
}

interface Decision {
  undefined_element: ID;
  decision: "resolve" | "accept" | "defer" | "need_more_info";
  reason: string;
  decided_by: string;
  decided_at: Timestamp;
  
  resolution?: {
    how: string;
    when: Phase;
    assigned_to: string;
  };
}

interface AcceptedRisk {
  risk_id: ID;
  reason: string;
  mitigation_plan?: string;
  review_date?: Timestamp;
  approved_by: string;
  approved_at: Timestamp;
}

interface DeferredItem {
  recommendation_id: ID;
  deferred_to: Phase;
  reason: string;
  reminder_conditions: string[];
}
```

---

## 統合出力フォーマット

### 最終レポート

```typescript
interface ComprehensiveReport {
  // メタ情報
  report_id: ID;
  generated_at: Timestamp;
  system_version: string;
  
  // 入力文書
  input_document: {
    content: string;
    metadata: Metadata;
  };
  
  // 各モジュールの結果
  parsing_result: ParsedRequirement;
  undefined_elements: UndefinedElements;
  risk_analysis: RiskAnalysisResult;
  remediation_plan: RemediationPlan;
  
  // エグゼクティブサマリー
  executive_summary: {
    overall_assessment: string;
    key_findings: string[];
    critical_issues: string[];
    recommended_actions: string[];
    estimated_impact_if_ignored: string;
    estimated_effort_to_resolve: string;
  };
  
  // 出力形式オプション
  format_options: {
    include_full_details: boolean;
    language: string;
    style: "technical" | "business" | "mixed";
  };
}
```

### マークダウン出力テンプレート

```markdown
# 未定義要素検出レポート

## プロジェクト情報
- ドキュメント: {document_name}
- 分析日時: {analyzed_at}
- 分析対象工程: {phase}

## エグゼクティブサマリー

### 総合評価
{overall_assessment}

### 主要な発見
{key_findings}

### 重大な問題
{critical_issues}

## 未定義要素

### カテゴリ別サマリー
| カテゴリ | 件数 | 高リスク | 中リスク | 低リスク |
|---------|------|---------|---------|---------|
| ... | ... | ... | ... | ... |

### 詳細

#### 1. {undefined_element_title}
- **カテゴリ**: {category}
- **説明**: {description}
- **質問**:
  - {question_1}
  - {question_2}
- **リスク**: {risk_level}
- **推奨工程**: {recommended_phase}

## リスク分析

### Top 5 リスク
1. {risk_1_title} - {risk_level}
2. ...

### 影響予測
- スケジュール: {schedule_impact}
- コスト: {cost_impact}
- 品質: {quality_impact}

## 推奨アクション

### 即座に対応が必要
1. {immediate_action_1}
   - 担当: {assignee}
   - 工数: {effort}
   - 期日: {deadline}

### クイックウィン（短時間で効果大）
1. {quick_win_1}
   - 工数: {effort}
   - リスク削減: {risk_reduction}

## 付録
- 詳細データ
- 参考資料
```

---

## データフロー検証

### 型の整合性

```typescript
// Module 1 → Module 2
function validateModule1To2(output: ParsedRequirement): boolean {
  return (
    output.document_id !== undefined &&
    output.entities.length >= 0 &&
    output.actions.length >= 0
  );
}

// Module 2 → Module 3
function validateModule2To3(output: UndefinedElements): boolean {
  return (
    output.undefined_elements.length >= 0 &&
    output.statistics !== undefined
  );
}

// Module 3 → Module 4
function validateModule3To4(output: RiskAnalysisResult): boolean {
  return (
    output.risks.length >= 0 &&
    output.summary !== undefined
  );
}
```

### エラーハンドリング

```typescript
interface ModuleError {
  module: string;
  error_type: "validation" | "processing" | "dependency";
  message: string;
  recoverable: boolean;
  suggestion?: string;
}
```

---

## まとめ

このモジュール入出力仕様により以下が保証されます：

1. **型安全性**: TypeScriptで型定義されたデータ構造
2. **モジュール独立性**: 各モジュールは明確なインターフェースで分離
3. **拡張性**: 新しいフィールドの追加が容易
4. **検証可能性**: 入出力のバリデーションルールが明確
5. **実装の指針**: 実装者が参照すべき具体的な仕様



