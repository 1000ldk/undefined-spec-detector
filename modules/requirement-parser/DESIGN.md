# Requirement Parser モジュール設計仕様

## 概要

自然言語で書かれた要件文書を構造化し、エンティティ、アクション、関係性を抽出するモジュールです。

## 責務

- テキストの前処理と正規化
- 文章の分割（センテンス単位）
- エンティティ（名詞）の抽出
- アクション（動詞）の抽出
- 関係性の推論
- 構造化されたデータとしての出力

## 技術スタック（想定）

```yaml
primary_language: Python 3.10+

libraries:
  nlp:
    - spaCy: 自然言語処理の基盤
    - fugashi: 日本語形態素解析（MeCab互換）
    - ginza: spaCy用日本語モデル
  
  data_processing:
    - pydantic: データバリデーション
    - pyyaml: YAML設定ファイル読み込み
  
  optional:
    - langdetect: 言語自動検出
    - transformers: より高度な解析（将来的に）

testing:
  - pytest
  - hypothesis: プロパティベーステスト
```

## モジュール構成

```
modules/requirement-parser/
├── __init__.py
├── parser.py              # メインのParserクラス
├── preprocessor.py        # テキスト前処理
├── entity_extractor.py    # エンティティ抽出
├── action_extractor.py    # アクション抽出
├── relation_extractor.py  # 関係性抽出
├── schema.py              # データスキーマ（Pydantic）
├── config.py              # 設定管理
└── tests/
    ├── test_parser.py
    ├── test_entity_extractor.py
    └── fixtures/          # テスト用サンプルデータ
```

## 主要クラス設計

### RequirementParser

```python
class RequirementParser:
    """要件文書の解析を行うメインクラス"""
    
    def __init__(self, config: ParserConfig):
        self.config = config
        self.nlp_model = self._load_nlp_model()
        self.preprocessor = Preprocessor()
        self.entity_extractor = EntityExtractor(self.nlp_model)
        self.action_extractor = ActionExtractor(self.nlp_model)
        self.relation_extractor = RelationExtractor(self.nlp_model)
    
    def parse(self, input_doc: InputDocument) -> ParsedRequirement:
        """
        要件文書を解析する
        
        Args:
            input_doc: 入力文書
        
        Returns:
            解析結果（構造化データ）
        """
        # 1. 前処理
        cleaned_text = self.preprocessor.clean(input_doc.content)
        
        # 2. NLP処理
        doc = self.nlp_model(cleaned_text)
        
        # 3. 文章分割
        sentences = self._extract_sentences(doc)
        
        # 4. エンティティ抽出
        entities = self.entity_extractor.extract(doc, sentences)
        
        # 5. アクション抽出
        actions = self.action_extractor.extract(doc, sentences, entities)
        
        # 6. 関係性抽出
        relationships = self.relation_extractor.extract(entities, actions)
        
        # 7. 要件の評価
        requirements = self._evaluate_requirements(
            sentences, entities, actions
        )
        
        # 8. 統計情報の計算
        statistics = self._calculate_statistics(
            sentences, entities, actions, requirements
        )
        
        return ParsedRequirement(
            document_id=self._generate_document_id(),
            parsed_at=datetime.now(timezone.utc),
            original_content=input_doc.content,
            sentences=sentences,
            entities=entities,
            actions=actions,
            relationships=relationships,
            requirements=requirements,
            statistics=statistics
        )
```

### Preprocessor

```python
class Preprocessor:
    """テキストの前処理を行う"""
    
    def clean(self, text: str) -> str:
        """
        テキストをクリーニングする
        
        - 不要な空白の削除
        - 改行の正規化
        - 全角英数字の半角化
        - 制御文字の除去
        """
        # 改行の統一
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # 連続する空白を1つに
        text = re.sub(r'[ \t]+', ' ', text)
        
        # 全角英数字を半角に
        text = self._normalize_alnum(text)
        
        # 制御文字の除去
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        return text.strip()
    
    def _normalize_alnum(self, text: str) -> str:
        """全角英数字を半角に変換"""
        # 実装省略
        pass
```

### EntityExtractor

```python
class EntityExtractor:
    """エンティティ（名詞）を抽出する"""
    
    def __init__(self, nlp_model):
        self.nlp_model = nlp_model
        # ドメイン固有の辞書を読み込み
        self.domain_dict = self._load_domain_dictionary()
    
    def extract(
        self, 
        doc, 
        sentences: List[Sentence]
    ) -> List[Entity]:
        """
        文書からエンティティを抽出
        
        1. 固有表現抽出（NER）
        2. 名詞句の抽出
        3. ドメイン辞書とのマッチング
        4. 重複の統合
        """
        entities = []
        entity_map = {}  # 表記ゆれを統合
        
        for token in doc:
            if self._is_entity_candidate(token):
                entity = self._create_entity(token, sentences)
                
                # 重複チェックと統合
                normalized_name = self._normalize_entity_name(entity.name)
                if normalized_name in entity_map:
                    # 既存のエンティティにメンションを追加
                    entity_map[normalized_name].mentions.append(...)
                else:
                    entity_map[normalized_name] = entity
                    entities.append(entity)
        
        # 属性の推論
        for entity in entities:
            entity.attributes = self._infer_attributes(entity, doc)
            entity.definition_status = self._evaluate_definition_status(entity)
            entity.ambiguity_score = self._calculate_ambiguity(entity)
        
        return entities
    
    def _is_entity_candidate(self, token) -> bool:
        """トークンがエンティティの候補かどうか"""
        return (
            token.pos_ in ['NOUN', 'PROPN'] or
            token.ent_type_ != '' or
            token.text in self.domain_dict
        )
```

## 設定ファイル

```yaml
# config/parser_config.yaml

nlp:
  model: "ja_ginza"  # 日本語モデル
  batch_size: 100
  max_length: 10000000  # 最大文字数

entity_extraction:
  min_frequency: 1  # 最低出現回数
  merge_similar: true  # 類似エンティティの統合
  similarity_threshold: 0.85

action_extraction:
  verb_patterns:
    - "できる"
    - "可能"
    - "する"
  extract_conditions: true  # 条件の抽出

scoring:
  completeness_weights:
    has_type_definition: 0.3
    has_constraints: 0.3
    has_error_handling: 0.2
    has_examples: 0.2
  
  ambiguity_penalties:
    vague_adjective: 0.2  # "速い"など
    undefined_condition: 0.3
    missing_subject: 0.2
```

## テスト戦略

### 単体テスト

```python
# tests/test_entity_extractor.py

def test_extract_entities_from_simple_sentence():
    """シンプルな文からエンティティを抽出"""
    text = "ユーザーは商品を購入する。"
    parser = RequirementParser(default_config)
    result = parser.parse(InputDocument(content=text))
    
    assert len(result.entities) == 2
    assert any(e.name == "ユーザー" for e in result.entities)
    assert any(e.name == "商品" for e in result.entities)

def test_merge_similar_entities():
    """表記ゆれのあるエンティティを統合"""
    text = "ユーザーは情報を入力する。利用者は情報を確認する。"
    parser = RequirementParser(default_config)
    result = parser.parse(InputDocument(content=text))
    
    # "ユーザー"と"利用者"は統合されるべき
    user_entities = [e for e in result.entities if "ユーザー" in e.name]
    assert len(user_entities) == 1
    assert len(user_entities[0].mentions) == 2

def test_attribute_inference():
    """属性の推論"""
    text = "ユーザー名は文字列型で、最大50文字とする。"
    parser = RequirementParser(default_config)
    result = parser.parse(InputDocument(content=text))
    
    user_entity = next(e for e in result.entities if e.name == "ユーザー")
    name_attr = next(a for a in user_entity.attributes if a.name == "ユーザー名")
    
    assert name_attr.defined == True
    assert name_attr.definition.type == "文字列"
    assert "最大50文字" in name_attr.definition.constraints
```

### 前提の破綻を検出するテスト

```python
def test_should_not_detect_undefined_in_complete_spec():
    """完全な仕様では未定義要素を検出しないはず"""
    complete_spec = """
    ユーザーは商品をカートに追加できる。
    ユーザーはUser型で、IDはUUID型とする。
    商品はProduct型で、在庫数はinteger型（0以上）とする。
    カートへの追加は、在庫数が1以上の場合のみ可能とする。
    在庫確認はリアルタイムで行い、楽観的ロックを使用する。
    在庫がない場合は「在庫切れ」エラーメッセージを表示する。
    """
    
    parser = RequirementParser(default_config)
    result = parser.parse(InputDocument(content=complete_spec))
    
    # 完全度スコアが高いはず
    assert result.statistics.avg_completeness_score > 0.8
    # 曖昧さスコアが低いはず
    assert result.statistics.avg_ambiguity_score < 0.3

def test_should_detect_ambiguity():
    """意図的に曖昧な仕様で曖昧さを検出するはず"""
    ambiguous_spec = "システムは高速に動作する。"
    
    parser = RequirementParser(default_config)
    result = parser.parse(InputDocument(content=ambiguous_spec))
    
    # 曖昧さスコアが高いはず
    assert result.requirements[0].ambiguity_score > 0.7
```

## パフォーマンス目標

```yaml
performance_targets:
  small_document:
    size: "< 100行"
    time: "< 3秒"
  
  medium_document:
    size: "100-1000行"
    time: "< 30秒"
  
  large_document:
    size: "1000-10000行"
    time: "< 5分"

memory:
  max_usage: "2GB"
  
concurrency:
  thread_safe: true
  max_parallel: 4
```

## エラーハンドリング

```python
class ParserError(Exception):
    """Parser固有のエラー基底クラス"""
    pass

class InvalidInputError(ParserError):
    """入力が不正な場合"""
    pass

class NLPModelError(ParserError):
    """NLPモデルの読み込みエラー"""
    pass

# 使用例
try:
    result = parser.parse(input_doc)
except InvalidInputError as e:
    logger.error(f"Invalid input: {e}")
    # ユーザーに分かりやすいエラーメッセージを返す
except NLPModelError as e:
    logger.critical(f"NLP model error: {e}")
    # システム管理者に通知
```

## 拡張ポイント

### カスタムエンティティ辞書

```python
# ユーザーがドメイン固有の用語を追加可能
custom_entities = {
    "カート": {
        "type": "object",
        "aliases": ["買い物カゴ", "ショッピングカート"],
        "typical_attributes": ["商品リスト", "合計金額"]
    }
}

parser = RequirementParser(
    config=default_config,
    custom_entities=custom_entities
)
```

### プラグイン機構

```python
class EntityExtractorPlugin(ABC):
    @abstractmethod
    def extract(self, doc) -> List[Entity]:
        pass

# ユーザー定義プラグインの登録
parser.register_plugin(MyCustomEntityExtractor())
```

## ログ出力

```python
import logging

logger = logging.getLogger(__name__)

# 詳細度レベル
logger.debug("Parsing sentence: {sentence}")
logger.info("Extracted {count} entities")
logger.warning("Low confidence entity: {entity}")
logger.error("Failed to parse: {error}")
```

## まとめ

このモジュールは：
- ✅ 単体でも利用可能
- ✅ テストが容易
- ✅ 拡張可能
- ✅ パフォーマンス目標が明確
- ✅ エラーハンドリングが適切






