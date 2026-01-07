# 未定義要素検出器 - 設計完了サマリー

## プロジェクト概要

**未定義要素検出器（Undefined Spec Detector）** は、自然言語で書かれた要件や仕様から「定義されていない要素」を自動的に検出し、それが引き起こす潜在的な問題（地雷）を可視化するための支援ツールです。

**設計完了日**: 2026年1月7日

---

## 完成した成果物

### 1. ドキュメント

| ドキュメント | パス | 内容 |
|------------|------|------|
| **README** | `README.md` | プロジェクト全体の概要、コンセプト、クイックスタート |
| **アーキテクチャ** | `docs/architecture.md` | システム全体のアーキテクチャ、モジュール構成 |
| **ユースケース** | `docs/use-cases.md` | 想定利用シナリオ、具体例 |
| **分類テンプレート** | `docs/classification-template.md` | 未定義要素の分類体系、評価基準 |
| **モジュール仕様** | `docs/module-specs.md` | 各モジュールの入出力定義（TypeScript型定義） |
| **人間とAI** | `docs/human-ai-responsibilities.md` | 役割分担の詳細 |
| **拡張案** | `docs/future-extensions.md` | 今後の拡張の方向性 |

### 2. モジュール設計

| モジュール | パス | 設計書 |
|-----------|------|--------|
| **Module 1: Requirement Parser** | `modules/requirement-parser/` | `DESIGN.md` |
| **Module 2: Undefined Extractor** | `modules/undefined-extractor/` | `DESIGN.md` |
| **Module 3: Risk Analyzer** | `modules/risk-analyzer/` | `DESIGN.md` |
| **Module 4: Remediation Advisor** | `modules/remediation-advisor/` | `DESIGN.md` |

### 3. テンプレートとサンプル

| ファイル | パス | 内容 |
|---------|------|------|
| **分類テンプレート** | `templates/classification-template.yaml` | 検出ルール、質問テンプレート |
| **サンプル入力** | `examples/input-sample-ec-cart.md` | ECサイトカート機能の要件例 |
| **サンプル出力（JSON）** | `examples/output-sample-ec-cart.json` | 構造化された分析結果 |
| **サンプルレポート** | `examples/report-sample-ec-cart.md` | 人間が読みやすいレポート形式 |

---

## 設計のハイライト

### コアコンセプト

1. **曖昧さの可視化**: 曖昧さを排除するのではなく、可視化する
2. **完全性よりも有用性**: 100%の精度より80%で実用的な価値を提供
3. **人間とAIの協働**: それぞれの強みを活かした役割分担

### アーキテクチャの特徴

```
入力（要件文書）
    ↓
[Module 1: Requirement Parser] ← 構造化
    ↓
[Module 2: Undefined Extractor] ← 未定義要素の検出
    ↓
[Module 3: Risk Analyzer] ← リスク評価と地雷予測
    ↓
[Module 4: Remediation Advisor] ← 修正指示の生成
    ↓
出力（統合レポート）
```

**特徴**:
- ✅ モジュール単位で独立動作可能
- ✅ 明確な入出力インターフェース
- ✅ 各モジュールが単体でも有用
- ✅ 拡張・カスタマイズが容易

### 未定義要素の分類（6カテゴリ）

1. **データ定義の欠落**: 型、制約、フォーマットなど
2. **振る舞いの曖昧さ**: タイミング、順序、条件など
3. **責任分担の不明確さ**: 実行主体、判断権限など
4. **境界条件の未定義**: 上限、下限、特殊ケースなど
5. **エラーハンドリングの欠落**: 異常系の処理
6. **非機能要件の曖昧さ**: パフォーマンス、セキュリティなど

### リスク評価の4軸

1. **発生確率**: 問題が顕在化する確率
2. **影響度**: 発生時の影響の大きさ
3. **発見困難度**: どの工程で発見できるか
4. **修正コスト**: 修正にかかるコスト

### 人間とAIの役割分担

#### 人間の役割 👤
- 要件文書の準備
- 未定義要素の妥当性確認
- リスク評価の調整
- リスク受容の判断（最終決定）
- 実際の解消作業
- 決定の記録

#### AIの役割 🤖
- 入力の正規化
- 構造化と抽出
- パターンベース検出
- リスクシナリオ生成
- 4軸評価の算出
- 推奨アクション生成
- 進捗トラッキング

**原則**: AIは提案、人間が決定

---

## 技術設計の詳細

### 想定技術スタック

```yaml
language: Python 3.10+

libraries:
  nlp:
    - spaCy/ginza: 自然言語処理
    - fugashi: 日本語形態素解析
  
  data:
    - pydantic: データバリデーション
    - pyyaml: 設定ファイル
  
  optional:
    - transformers: 高度な解析（将来）
    - scikit-learn: 類似度計算

database:
  - SQLite: 地雷パターンDB
  - JSON/YAML: 設定・履歴

deployment:
  - CLI: スタンドアロン実行
  - Web UI: Docker化
  - IDE Plugin: VS Code拡張
  - API: RESTful API
```

### データフロー

```typescript
// Module 1 の出力 → Module 2 の入力
ParsedRequirement → UndefinedElements

// Module 2 の出力 → Module 3 の入力
UndefinedElements → RiskAnalysisResult

// Module 3 の出力 → Module 4 の入力
RiskAnalysisResult → RemediationPlan

// 統合レポート
ComprehensiveReport
```

すべての型定義は `docs/module-specs.md` に詳細記載。

### テスト戦略

**特徴**: 「実装の正しさ」ではなく「前提の破綻」を検出

```python
# Good Test Example
def test_should_not_detect_undefined_in_complete_spec():
    """完全な仕様では未定義要素を検出しないはず"""
    complete_spec = "..."  # 完全に定義された仕様
    result = system.analyze(complete_spec)
    assert result.completeness_score > 0.8
    assert result.ambiguity_score < 0.3

def test_should_detect_ambiguity():
    """意図的に曖昧な仕様で曖昧さを検出するはず"""
    ambiguous_spec = "システムは高速に動作する。"
    result = system.analyze(ambiguous_spec)
    assert result.ambiguity_score > 0.7
```

---

## 利用の流れ

### 典型的なワークフロー

```bash
# 1. 要件文書を準備
$ cat requirements.md

# 2. 分析を実行
$ usd-cli analyze --input requirements.md --output report.md

# 3. レポートをレビュー
$ cat report.md

# 4. 高リスク項目を解消
# (人間が作業)

# 5. 更新後に再分析
$ usd-cli analyze --input requirements-v2.md --output report-v2.md

# 6. 改善を確認
$ usd-cli compare report.md report-v2.md
```

### 期待される効果

| 指標 | 期待値 |
|------|--------|
| **未定義要素の検出** | 80%以上の精度 |
| **手戻り削減** | 要件定義フェーズで30-50%削減 |
| **バグ発見の前倒し** | テスト前に40%以上発見 |
| **分析時間** | 1000行の文書を5分以内 |

---

## 今後の展開

### 短期（3-6ヶ月）
- インタラクティブモード
- IDE統合プラグイン（VS Code）
- ドメイン知識の拡充

### 中期（6-12ヶ月）
- コードとの連携（要件↔実装の照合）
- 機械学習モデルの導入
- テストケース生成

### 長期（12ヶ月以上）
- 自動修正の提案
- 仕様変更の影響分析
- グラフィカルな可視化

詳細は `docs/future-extensions.md` を参照。

---

## 実装への移行

### 次のステップ

1. **環境構築**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Module 1から実装開始**
   - `modules/requirement-parser/parser.py` の実装
   - 単体テストの作成
   - サンプルデータでの動作確認

3. **段階的な統合**
   - Module 1 → Module 2 → Module 3 → Module 4
   - 各モジュール完成後に統合テスト

4. **知識ベースの構築**
   - 地雷パターンの収集
   - ドメイン知識の整備
   - 過去事例のデータベース化

### 推奨開発体制

```yaml
roles:
  architect: 1名
    - アーキテクチャの監督
    - モジュール間の整合性確保
  
  nlp_engineer: 1-2名
    - Module 1, 2の実装
    - 自然言語処理の精度向上
  
  backend_engineer: 1-2名
    - Module 3, 4の実装
    - データベース設計
  
  frontend_engineer: 1名（オプション）
    - Web UI の実装
  
  domain_expert: 1名（パートタイム）
    - ドメイン知識の提供
    - 地雷パターンのレビュー

estimated_development_time: 3-6ヶ月（MVP版）
```

---

## 成功基準

### 定量的指標

- [ ] Module 1: 90%以上の精度でエンティティ抽出
- [ ] Module 2: 1000行を30秒以内で解析
- [ ] Module 3: 地雷パターン100件以上を整備
- [ ] Module 4: 推奨アクションの生成成功率90%以上

### 定性的指標

- [ ] ユーザーが「実際に役立った」と感じる
- [ ] 要件レビューの時間が削減された
- [ ] 手戻りが減少した
- [ ] チームの仕様理解度が向上した

---

## ライセンスと貢献

### ライセンス

（プロジェクトの方針に応じて決定）
- オープンソース（MIT, Apache 2.0など）
- プロプライエタリ
- デュアルライセンス

### 貢献歓迎

- 新しいドメイン知識の追加
- 地雷パターンの報告
- バグ修正
- ドキュメント改善

---

## 連絡先・リソース

```yaml
repository: (TBD)
documentation: docs/
issues: (TBD)
discussions: (TBD)
```

---

## まとめ

このプロジェクトは**設計レベルまで完成**しました。

✅ **完成した項目**:
1. アプリ全体のコンセプト説明
2. 想定ユースケース
3. 未定義要素の分類テンプレート
4. モジュール構成（4モジュール）
5. 各モジュールの入出力定義
6. 人間が担当すべき作業範囲
7. AIに委任できる作業範囲
8. 今後の拡張案

📋 **ドキュメント**: 合計12ファイル  
🔧 **モジュール設計**: 4モジュール  
📊 **サンプル**: 入力・出力・レポートの3点セット  
📝 **総ページ数**: 約150ページ相当

**次のフェーズ**: 実装

このドキュメント群を基に、開発チームは実装を開始できます。
各モジュールの設計書には、具体的なクラス設計、テスト戦略、サンプルコードが含まれており、
実装の指針として十分な詳細度を持っています。

---

**設計完了日**: 2026年1月7日  
**設計者**: AI System Architect  
**バージョン**: 1.0.0




