"""
共通データスキーマ定義
"""
from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from enum import Enum


# 基本型
class Phase(str, Enum):
    """開発工程"""
    REQUIREMENT_DEFINITION = "requirement_definition"
    DESIGN = "design"
    IMPLEMENTATION = "implementation"
    TESTING = "testing"
    OPERATION = "operation"


class Priority(str, Enum):
    """優先度レベル"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskLevel(str, Enum):
    """リスクレベル"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# メタデータ
class Metadata(BaseModel):
    """メタデータ"""
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[str] = None
    version: str = "1.0.0"
    source: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


# Module 1: Requirement Parser の出力
class Attribute(BaseModel):
    """エンティティの属性"""
    name: str
    mentioned: bool
    defined: bool
    definition: Optional[Dict[str, Any]] = None


class Mention(BaseModel):
    """エンティティの言及箇所"""
    sentence_id: str
    text: str
    position: int


class Entity(BaseModel):
    """エンティティ（名詞）"""
    id: str
    name: str
    type: Literal["actor", "object", "system", "data", "event"]
    attributes: List[Attribute] = Field(default_factory=list)
    mentions: List[Mention] = Field(default_factory=list)
    definition_status: Literal["defined", "partially_defined", "undefined"] = "undefined"
    ambiguity_score: float = 0.0


class Condition(BaseModel):
    """条件"""
    description: str
    type: Literal["precondition", "postcondition", "invariant"]
    defined: bool
    ambiguous: bool
    entities: List[str] = Field(default_factory=list)


class ErrorHandling(BaseModel):
    """エラーハンドリング情報"""
    mentioned: bool
    defined: bool


class Action(BaseModel):
    """アクション（動詞）"""
    id: str
    verb: str
    subject: str  # Entity ID
    object: Optional[str] = None  # Entity ID
    preconditions: List[Condition] = Field(default_factory=list)
    postconditions: List[Condition] = Field(default_factory=list)
    timing: Optional[Dict[str, str]] = None
    error_handling: Optional[ErrorHandling] = None


class Relationship(BaseModel):
    """エンティティ間の関係"""
    id: str
    from_entity: str
    to_entity: str
    type: Literal["owns", "uses", "depends_on", "references", "contains"]
    description: str
    cardinality: Optional[Dict[str, Any]] = None
    bidirectional: bool = False
    strength: Literal["weak", "medium", "strong"] = "medium"


class Constraint(BaseModel):
    """制約"""
    id: str
    description: str
    type: Literal["business_rule", "technical", "legal", "performance"]
    entities: List[str] = Field(default_factory=list)
    scope: Literal["global", "local"] = "local"
    priority: Priority = Priority.MEDIUM


class Sentence(BaseModel):
    """文章"""
    id: str
    text: str
    line_number: int
    start_char: int
    end_char: int
    type: Literal["requirement", "constraint", "explanation", "example"]
    importance: Priority = Priority.MEDIUM


class Requirement(BaseModel):
    """要件"""
    id: str
    text: str
    type: Literal["functional", "non_functional"]
    category: Optional[str] = None
    priority: Optional[Priority] = None
    completeness_score: float = 0.0
    ambiguity_score: float = 0.0
    related_entities: List[str] = Field(default_factory=list)
    related_actions: List[str] = Field(default_factory=list)
    missing_elements: List[str] = Field(default_factory=list)


class Statistics(BaseModel):
    """統計情報"""
    total_sentences: int = 0
    total_entities: int = 0
    total_relationships: int = 0
    total_actions: int = 0
    avg_completeness_score: float = 0.0
    avg_ambiguity_score: float = 0.0


class ParsedRequirement(BaseModel):
    """解析済み要件（Module 1の出力）"""
    document_id: str
    parsed_at: datetime = Field(default_factory=datetime.now)
    parser_version: str = "1.0.0"
    original_content: str
    metadata: Optional[Metadata] = None
    sentences: List[Sentence] = Field(default_factory=list)
    entities: List[Entity] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)
    actions: List[Action] = Field(default_factory=list)
    constraints: List[Constraint] = Field(default_factory=list)
    requirements: List[Requirement] = Field(default_factory=list)
    statistics: Statistics = Field(default_factory=Statistics)


# Module 2: Undefined Extractor の出力
class Question(BaseModel):
    """質問"""
    text: str
    type: Literal["clarification", "specification", "constraint", "exception"]
    suggested_answers: List[str] = Field(default_factory=list)
    reference: Optional[str] = None


class DetectionInfo(BaseModel):
    """検出情報"""
    method: Literal["pattern_matching", "semantic_analysis", "rule_based", "ml_model", "template_driven"]
    confidence: float
    reasoning: str


class Context(BaseModel):
    """コンテキスト情報"""
    source_text: str
    surrounding_text: str
    sentence_id: Optional[str] = None
    line_number: int


class UndefinedElement(BaseModel):
    """未定義要素"""
    id: str
    category: str
    subcategory: str
    related_entity: Optional[str] = None
    related_action: Optional[str] = None
    related_requirement: Optional[str] = None
    title: str
    description: str
    questions: List[Question] = Field(default_factory=list)
    detection: DetectionInfo
    context: Context
    cross_references: List[str] = Field(default_factory=list)
    estimated_severity: Priority = Priority.MEDIUM
    criticality_info: Optional[Dict[str, Any]] = None  # 新規追加: 致命度情報


class UndefinedElementGroup(BaseModel):
    """未定義要素のグループ"""
    id: str
    title: str
    description: str
    element_ids: List[str]
    relationship: Literal["related", "dependent", "mutually_exclusive"]
    should_resolve_together: bool


class MetaAnalysis(BaseModel):
    """メタ分析"""
    overall_completeness: float
    critical_gaps: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class UndefinedElements(BaseModel):
    """未定義要素リスト（Module 2の出力）"""
    document_id: str
    analyzed_at: datetime = Field(default_factory=datetime.now)
    extractor_version: str = "1.0.0"
    source_document: str
    undefined_elements: List[UndefinedElement] = Field(default_factory=list)
    groups: List[UndefinedElementGroup] = Field(default_factory=list)
    statistics: Dict[str, Any] = Field(default_factory=dict)
    meta_analysis: Optional[MetaAnalysis] = None


# Input/Output
class InputDocument(BaseModel):
    """入力ドキュメント"""
    content: str
    metadata: Optional[Metadata] = None
    context: Optional[Dict[str, Any]] = None
    options: Optional[Dict[str, Any]] = None



