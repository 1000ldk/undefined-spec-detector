# 未定義要素検出器 (Undefined Spec Detector)

## プロジェクト概要

**未定義要素検出器**は、自然言語で書かれた要件や仕様から「定義されていない要素」を自動的に検出し、それが引き起こす潜在的な問題（地雷）を可視化するための支援ツールです。

**現在のステータス**: ✅ **Webアプリケーションが利用可能です！**

## 🎉 完成した機能

- ✅ Module 1: Requirement Parser（要件解析）
- ✅ Module 2: Undefined Extractor（未定義要素抽出）
- ✅ 統合レイヤー（AnalysisCoordinator）
- ✅ CLI（コマンドラインインターフェース）
- ✅ **Web API（FastAPI）**
- ✅ **Webアプリケーション（HTML/CSS/JS）**
- ⏳ Module 3 & 4は将来実装予定

## 🚀 クイックスタート

### Web アプリケーション（推奨）

```bash
# 1. 依存パッケージをインストール
pip install -r requirements.txt

# 2. Webサーバーを起動
python -m uvicorn usd.web_api:app --reload

# または、スクリプトを使用（Windows）
.\start_web.ps1

# または、スクリプトを使用（Mac/Linux）
./start_web.sh
```

ブラウザで以下にアクセス：
- **Webアプリ**: http://localhost:8000/app
- **API ドキュメント**: http://localhost:8000/docs
- **ヘルスチェック**: http://localhost:8000/health

### Docker を使用（簡単！）

```bash
# Docker Composeで起動
docker-compose up

# ブラウザで http://localhost:8000/app にアクセス
```

### コマンドライン（CLI）

```bash
# CLIで分析
usd-cli analyze --input examples/input-sample-ec-cart.md

# 結果をファイルに保存
usd-cli analyze --input requirements.txt --output report.md --format markdown
```

### Python API

```python
from usd.coordinator import AnalysisCoordinator

content = """
ユーザーは商品をカートに追加できる。
在庫がある場合のみ追加可能。
システムは高速に動作すること。
"""

coordinator = AnalysisCoordinator()
report = coordinator.analyze(content)
print(f"未定義要素: {report['undefined_elements']['total']}個")
```

## 📱 Webアプリの使い方

1. **要件を入力**: 左側のテキストエリアに要件や仕様を入力
2. **サンプルを試す**: 「サンプル要件」ボタンでサンプルを読み込み
3. **分析開始**: 「分析開始」ボタンをクリック
4. **結果を確認**: 右側に未定義要素が表示されます

### スクリーンショット機能

- ✅ リアルタイム分析
- ✅ 美しいUI（グラデーション、カード型デザイン）
- ✅ カテゴリ別の統計表示
- ✅ 重要度別の色分け（🔴高 🟡中 🟢低）
- ✅ 質問の自動生成
- ✅ サンプル要件のプリセット

## 🌐 Web API エンドポイント

### `POST /api/analyze`
要件文書を分析します。

**リクエスト:**
```json
{
  "content": "ユーザーは商品をカートに追加できる。",
  "metadata": {},
  "options": {}
}
```

**レスポンス:**
```json
{
  "success": true,
  "report": {
    "executive_summary": {...},
    "undefined_elements": {...},
    ...
  }
}
```

### `GET /api/examples`
サンプル要件を取得します。

### `GET /docs`
FastAPIの自動生成APIドキュメント（Swagger UI）

## インストール

### 必要な環境
- Python 3.10+
- pip

### 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### パッケージのインストール（開発モード）

```bash
pip install -e .
```

## プロジェクト構成

```
undefined-spec-detector/
├── README.md                          # 本ファイル
├── requirements.txt                   # 依存パッケージ
├── setup.py                          # パッケージ設定
├── Dockerfile                        # Docker設定
├── docker-compose.yml                # Docker Compose設定
├── start_web.sh                      # 起動スクリプト（Unix/Mac）
├── start_web.ps1                     # 起動スクリプト（Windows）
├── test_run.py                       # 簡易テストスクリプト
├── src/
│   └── usd/                          # メインパッケージ
│       ├── __init__.py
│       ├── schema.py                  # データスキーマ定義
│       ├── coordinator.py             # 統合レイヤー
│       ├── cli.py                     # CLI実装
│       ├── web_api.py                # Web API実装 ⭐NEW
│       └── modules/                   # 各モジュール
│           ├── requirement_parser/    # Module 1
│           └── undefined_extractor/   # Module 2
├── web/                              # Webアプリケーション ⭐NEW
│   ├── index.html                    # メインページ
│   └── static/                       # 静的ファイル
├── docs/                             # 設計ドキュメント
├── examples/                         # サンプル
└── templates/                        # テンプレート
```

## 主要機能

### 1. 未定義要素の自動抽出

以下のカテゴリで未定義要素を検出します：

- **データ定義の欠落**: 型、制約、フォーマットなど
- **振る舞いの曖昧さ**: タイミング、順序、条件など
- **責任分担の不明確さ**: 実行主体、判断権限など
- **境界条件の未定義**: 上限、下限、特殊ケースなど
- **エラーハンドリングの欠落**: 異常系の処理
- **非機能要件の曖昧さ**: パフォーマンス、セキュリティなど

### 2. 質問の自動生成

各未定義要素に対して、解消のための質問を自動生成します。

### 3. 統計情報とメタ分析

- 完全度スコア
- 曖昧さスコア
- カテゴリ別の集計
- 推奨事項の提示

## 技術スタック

- **Python 3.10+**
- **FastAPI**: Web API フレームワーク
- **Uvicorn**: ASGI サーバー
- **Pydantic**: データバリデーション
- **Click**: CLIフレームワーク
- **Rich**: 美しいCLI出力
- **HTML/CSS/JavaScript**: フロントエンド
- **Docker**: コンテナ化

## 使用例

### Webアプリでの使用

1. ブラウザで http://localhost:8000/app を開く
2. サンプル要件（「ECサイト カート機能」など）を選択
3. 「分析開始」ボタンをクリック
4. 右側に結果が表示されます

### curlでAPIを呼び出し

```bash
curl -X POST "http://localhost:8000/api/analyze" \
  -H "Content-Type: application/json" \
  -d '{"content":"ユーザーは商品をカートに追加できる。在庫がある場合のみ追加可能。"}'
```

## 設計ドキュメント

詳細な設計ドキュメントは `docs/` ディレクトリにあります：

- [アーキテクチャ設計](docs/architecture.md)
- [ユースケース集](docs/use-cases.md)
- [分類テンプレート](docs/classification-template.md)
- [モジュール仕様](docs/module-specs.md)
- [人間とAIの役割分担](docs/human-ai-responsibilities.md)
- [今後の拡張案](docs/future-extensions.md)
- [設計完了サマリー](DESIGN_SUMMARY.md)
- [実装完了レポート](IMPLEMENTATION_COMPLETE.md)

## 開発状況

### 完成済み ✅

- [x] プロジェクト構造
- [x] データスキーマ定義
- [x] Module 1: Requirement Parser
- [x] Module 2: Undefined Extractor
- [x] 統合レイヤー
- [x] CLI実装
- [x] **Web API（FastAPI）**
- [x] **Webアプリケーション**
- [x] **Docker化**
- [x] サンプルデータでの動作確認

### 今後の実装予定 ⏳

- [ ] Module 3: Risk Analyzer（リスク評価）
- [ ] Module 4: Remediation Advisor（修正指示生成）
- [ ] spaCy/ginzaによる高度なNLP
- [ ] 認証・認可機能
- [ ] 分析履歴の保存
- [ ] IDEプラグイン
- [ ] テストカバレッジの向上

## トラブルシューティング

### ポート8000が使用中の場合

```bash
# 別のポートで起動
uvicorn usd.web_api:app --port 8001
```

### FastAPIがインストールされていない

```bash
pip install fastapi uvicorn[standard] python-multipart
```

## ライセンス

（未定）

## 貢献

プルリクエスト、バグ報告、機能提案を歓迎します！

## 作者

AI System Architect

---

**バージョン**: 0.2.0 (Web対応版)  
**最終更新**: 2026年1月7日
