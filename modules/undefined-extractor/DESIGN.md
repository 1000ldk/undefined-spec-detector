# Undefined Extractor モジュール設計仕様

## 概要

構造化された要件から未定義要素を検出し、分類するモジュールです。

## 責務

- 分類テンプレートに基づく未定義要素の検出
- パターンマッチングによる曖昧表現の検出
- 質問の自動生成
- 未定義要素のグループ化

## 技術スタック（想定）

```yaml
primary_language: Python 3.10+

libraries:
  - pydantic: データバリデーション
  - pyyaml: 分類テンプレート読み込み
  - jinja2: 質問テンプレートの生成
  - scikit-learn: 類似度計算（オプション）

testing:
  - pytest
  - pytest-cov: カバレッジ測定
```

## モジュール構成

```
modules/undefined-extractor/
├── __init__.py
├── extractor.py           # メインのExtractorクラス
├── pattern_matcher.py     # パターンマッチング
├── semantic_analyzer.py   # 意味解析
├── question_generator.py  # 質問生成
├── grouper.py             # 未定義要素のグループ化
├── schema.py              # データスキーマ
└── tests/
    ├── test_extractor.py
    └── test_pattern_matcher.py
```

## 主要クラス設計

### UndefinedExtractor

```python
class UndefinedExtractor:
    """未定義要素を抽出するメインクラス"""
    
    def __init__(
        self, 
        classification_template: ClassificationTemplate,
        domain_knowledge: Optional[DomainKnowledge] = None
    ):
        self.template = classification_template
        self.domain_knowledge = domain_knowledge or {}
        
        self.pattern_matcher = PatternMatcher(self.template)
        self.semantic_analyzer = SemanticAnalyzer()
        self.question_generator = QuestionGenerator(self.template)
        self.grouper = UndefinedElementGrouper()
    
    def extract(
        self, 
        parsed_requirements: ParsedRequirement,
        options: ExtractorOptions = None
    ) -> UndefinedElements:
        """
        未定義要素を抽出する
        
        Args:
            parsed_requirements: 構造化された要件（Module 1の出力）
            options: 抽出オプション
        
        Returns:
            未定義要素のリスト
        """
        options = options or ExtractorOptions()
        undefined_elements = []
        
        # 1. エンティティの未定義要素を検出
        for entity in parsed_requirements.entities:
            elements = self._extract_from_entity(entity)
            undefined_elements.extend(elements)
        
        # 2. アクションの未定義要素を検出
        for action in parsed_requirements.actions:
            elements = self._extract_from_action(action)
            undefined_elements.extend(elements)
        
        # 3. 要件レベルの未定義要素を検出
        for requirement in parsed_requirements.requirements:
            elements = self._extract_from_requirement(requirement)
            undefined_elements.extend(elements)
        
        # 4. フィルタリング（信頼度閾値）
        undefined_elements = [
            e for e in undefined_elements 
            if e.detection.confidence >= options.confidence_threshold
        ]
        
        # 5. 質問生成
        for element in undefined_elements:
            element.questions = self.question_generator.generate(element)
        
        # 6. グループ化
        groups = self.grouper.group(undefined_elements)
        
        # 7. 統計情報とメタ分析
        statistics = self._calculate_statistics(undefined_elements)
        meta_analysis = self._perform_meta_analysis(
            parsed_requirements, undefined_elements
        )
        
        return UndefinedElements(
            document_id=parsed_requirements.document_id,
            analyzed_at=datetime.now(timezone.utc),
            undefined_elements=undefined_elements,
            groups=groups,
            statistics=statistics,
            meta_analysis=meta_analysis
        )
    
    def _extract_from_entity(self, entity: Entity) -> List[UndefinedElement]:
        """エンティティから未定義要素を抽出"""
        elements = []
        
        # 属性の型が未定義
        for attr in entity.attributes:
            if attr.mentioned and not attr.defined:
                element = UndefinedElement(
                    id=self._generate_id(),
                    category="データ定義の欠落",
                    subcategory="型定義",
                    related_entity=entity.id,
                    title=f"{attr.name}の型が定義されていない",
                    description=f"{entity.name}の属性「{attr.name}」のデータ型が明示されていません",
                    detection=DetectionInfo(
                        method="rule_based",
                        confidence=0.9,
                        reasoning="属性が言及されているが型定義がない"
                    ),
                    context=self._extract_context(entity),
                    estimated_severity="medium"
                )
                elements.append(element)
        
        # エンティティ自体が未定義
        if entity.definition_status == "undefined":
            element = self._create_undefined_entity_element(entity)
            elements.append(element)
        
        return elements
    
    def _extract_from_action(self, action: Action) -> List[UndefinedElement]:
        """アクションから未定義要素を抽出"""
        elements = []
        
        # 前提条件が曖昧
        for condition in action.preconditions:
            if condition.ambiguous:
                element = UndefinedElement(
                    id=self._generate_id(),
                    category="振る舞いの曖昧さ",
                    subcategory="実行条件",
                    related_action=action.id,
                    title=f"{action.verb}の条件が曖昧",
                    description=f"「{condition.description}」の具体的な判定方法が不明",
                    detection=DetectionInfo(
                        method="semantic_analysis",
                        confidence=0.85,
                        reasoning="条件文が存在するが具体的な定義がない"
                    ),
                    context=self._extract_context(action),
                    estimated_severity="high"
                )
                elements.append(element)
        
        # エラーハンドリングが欠落
        if action.error_handling and not action.error_handling.defined:
            element = self._create_missing_error_handling_element(action)
            elements.append(element)
        
        return elements
```

### PatternMatcher

```python
class PatternMatcher:
    """パターンベースで未定義要素を検出"""
    
    def __init__(self, template: ClassificationTemplate):
        self.detection_rules = template.detection_rules
        self._compile_patterns()
    
    def _compile_patterns(self):
        """正規表現パターンをコンパイル"""
        self.compiled_patterns = {}
        for rule in self.detection_rules:
            self.compiled_patterns[rule.id] = re.compile(
                rule.pattern, 
                re.IGNORECASE
            )
    
    def match(self, text: str) -> List[PatternMatch]:
        """テキストからパターンにマッチする箇所を検出"""
        matches = []
        
        for rule_id, pattern in self.compiled_patterns.items():
            rule = self._get_rule(rule_id)
            
            for match in pattern.finditer(text):
                matches.append(PatternMatch(
                    rule_id=rule_id,
                    category=rule.category,
                    matched_text=match.group(),
                    start=match.start(),
                    end=match.end(),
                    confidence=rule.confidence
                ))
        
        return matches
```

### QuestionGenerator

```python
class QuestionGenerator:
    """未定義要素に対する質問を生成"""
    
    def __init__(self, template: ClassificationTemplate):
        self.question_templates = template.question_templates
        self.jinja_env = jinja2.Environment()
    
    def generate(self, element: UndefinedElement) -> List[Question]:
        """
        未定義要素に対する質問を生成
        
        1. テンプレートベースの質問
        2. コンテキストに応じた質問
        3. 過去の類似ケースからの質問
        """
        questions = []
        
        # カテゴリに対応するテンプレートを取得
        templates = self._get_templates_for_category(
            element.category, 
            element.subcategory
        )
        
        for template_text in templates:
            # テンプレートに変数を埋め込み
            question_text = self._render_template(
                template_text, 
                element
            )
            
            questions.append(Question(
                text=question_text,
                type=self._infer_question_type(template_text),
                suggested_answers=self._suggest_answers(element)
            ))
        
        # カスタム質問の追加
        custom_questions = self._generate_custom_questions(element)
        questions.extend(custom_questions)
        
        return questions[:5]  # 最大5つまで
    
    def _render_template(
        self, 
        template: str, 
        element: UndefinedElement
    ) -> str:
        """Jinjaテンプレートをレンダリング"""
        template_obj = self.jinja_env.from_string(template)
        return template_obj.render(
            entity=element.related_entity,
            action=element.related_action,
            # その他のコンテキスト変数
        )
```

## 検出ルールの例

```yaml
# templates/detection_rules.yaml

rules:
  - id: "ambiguous_timing"
    name: "曖昧な時間表現"
    pattern: "すぐに|速やかに|適宜|随時|定期的に|後で"
    category: "behavior_ambiguity"
    subcategory: "timing"
    confidence: 0.7
    questions:
      - "具体的にいつ実行されますか？"
      - "実行間隔または遅延時間は？"
  
  - id: "vague_quantifier"
    name: "曖昧な数量表現"
    pattern: "多数|少数|複数|大量|適切|十分"
    category: "boundary_condition_gap"
    subcategory: "limits"
    confidence: 0.8
    questions:
      - "具体的な数値は？"
      - "上限・下限は？"
  
  - id: "missing_error_case"
    name: "エラーケースの欠落"
    pattern: "できる|可能"
    check: "negative_case_mentioned"
    category: "error_handling_gap"
    confidence: 0.6
    questions:
      - "できない場合の挙動は？"
      - "エラー時のユーザーフィードバックは？"
```

## テスト戦略

```python
def test_detect_ambiguous_adjectives():
    """曖昧な形容詞を検出"""
    parsed = ParsedRequirement(
        requirements=[
            Requirement(
                text="システムは高速に動作する",
                type="non_functional"
            )
        ]
    )
    
    extractor = UndefinedExtractor(default_template)
    result = extractor.extract(parsed)
    
    # "高速に"という曖昧表現が検出されるべき
    assert any(
        e.category == "非機能要件の曖昧さ" 
        for e in result.undefined_elements
    )
    assert any(
        "具体的" in q.text 
        for e in result.undefined_elements 
        for q in e.questions
    )

def test_detect_missing_error_handling():
    """エラーハンドリングの欠落を検出"""
    parsed = ParsedRequirement(
        actions=[
            Action(
                verb="追加する",
                subject="ユーザー",
                object="商品",
                error_handling=ErrorHandling(
                    mentioned=False,
                    defined=False
                )
            )
        ]
    )
    
    extractor = UndefinedExtractor(default_template)
    result = extractor.extract(parsed)
    
    assert any(
        e.category == "エラーハンドリングの欠落"
        for e in result.undefined_elements
    )

def test_group_related_elements():
    """関連する未定義要素をグループ化"""
    # 在庫関連の未定義要素が複数ある場合
    result = extractor.extract(parsed_with_inventory_issues)
    
    # "在庫管理"関連のグループが作成されるべき
    inventory_group = next(
        g for g in result.groups 
        if "在庫" in g.title
    )
    assert len(inventory_group.element_ids) >= 2
    assert inventory_group.should_resolve_together == True
```

## パフォーマンス

```yaml
performance:
  - 100個のエンティティ: < 1秒
  - 1000個のエンティティ: < 10秒
  
memory:
  - 効率的なパターンマッチング
  - 不要な中間データの削除
```

## まとめ

このモジュールは：
- ✅ ルールベース + 意味解析のハイブリッド
- ✅ カスタマイズ可能な検出ルール
- ✅ 自動質問生成
- ✅ 関連要素のグループ化




