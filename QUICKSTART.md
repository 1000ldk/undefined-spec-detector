# クイックスタートガイド

## 🚀 最速で始める（推奨）

### Webアプリケーション

```bash
# 1. 起動スクリプトを実行（Windows）
.\start_web.ps1

# または Mac/Linux
./start_web.sh

# 2. ブラウザで開く
# http://localhost:8000/app
```

**これだけ！** ブラウザで要件を入力して、分析開始ボタンを押すだけです。

---

## 📱 Webアプリの使い方

### ステップ1: 起動

Windows:
```powershell
.\start_web.ps1
```

Mac/Linux:
```bash
chmod +x start_web.sh
./start_web.sh
```

### ステップ2: アクセス

ブラウザで以下にアクセス：
- **Webアプリ**: http://localhost:8000/app
- **API ドキュメント**: http://localhost:8000/docs

### ステップ3: 分析

1. 左側のテキストエリアに要件を入力
2. または「サンプル要件」ボタンでサンプルを読み込み
3. 「分析開始」ボタンをクリック
4. 右側に結果が表示されます！

---

## 🐳 Dockerで起動（最も簡単）

```bash
# 起動
docker-compose up

# ブラウザで http://localhost:8000/app にアクセス

# 停止
docker-compose down
```

---

## 💻 コマンドライン（CLI）

```bash
# インストール
pip install -r requirements.txt
pip install -e .

# 分析実行
usd-cli analyze --input examples/input-sample-ec-cart.md

# 結果をファイルに保存
usd-cli analyze --input my_requirements.txt --output report.md --format markdown
```

---

## 🐍 Python API

```python
from usd.coordinator import AnalysisCoordinator

# 要件文書
content = """
ユーザーは商品をカートに追加できる。
在庫がある場合のみ追加可能。
システムは高速に動作すること。
"""

# 分析実行
coordinator = AnalysisCoordinator()
report = coordinator.analyze(content)

# 結果を表示
print(f"未定義要素: {report['undefined_elements']['total']}個")
for elem in report['undefined_elements']['elements']:
    print(f"- {elem['title']}")
```

---

## 📋 サンプルで試す

### Webアプリで

1. http://localhost:8000/app を開く
2. 「サンプル要件」から選択：
   - 🛒 ECサイト カート機能
   - 🔐 ユーザー認証
   - 📡 API仕様
3. 「分析開始」をクリック

### CLIで

```bash
# サンプルを分析
usd-cli analyze --input examples/input-sample-ec-cart.md

# 出力例:
# ✓ 未定義要素: 12個検出
# ✓ エンティティ: 6個抽出
# ✓ アクション: 3個抽出
```

---

## 🔧 トラブルシューティング

### ポートが使用中の場合

```bash
# 別のポートで起動
uvicorn usd.web_api:app --port 8001
```

### 依存パッケージがない

```bash
# 必要なパッケージをインストール
pip install fastapi uvicorn[standard] python-multipart pydantic click rich pyyaml
```

### Dockerが動かない

```bash
# Dockerがインストールされているか確認
docker --version

# Docker Composeがインストールされているか確認
docker-compose --version
```

---

## ⚡ 各方法の比較

| 方法 | 起動速度 | 簡単さ | 用途 |
|------|---------|--------|------|
| **Webアプリ** | ⚡⚡⚡ | ★★★★★ | ブラウザで試したい |
| **Docker** | ⚡⚡ | ★★★★★ | 環境を汚したくない |
| **CLI** | ⚡⚡⚡ | ★★★ | バッチ処理したい |
| **Python API** | ⚡⚡⚡ | ★★★ | プログラムから使いたい |

---

## 📊 動作確認

### 正常に動作しているか確認

```bash
# ヘルスチェック
curl http://localhost:8000/health

# 期待される結果:
# {"status":"healthy"}
```

### APIテスト

```bash
curl -X POST "http://localhost:8000/api/analyze" \
  -H "Content-Type: application/json" \
  -d '{"content":"ユーザーはログインできる。"}'
```

---

## 🎓 次のステップ

1. ✅ Webアプリで要件を分析してみる
2. ✅ 自分のプロジェクトの要件で試す
3. ✅ API経由で自動化する
4. ✅ ドキュメントを読んで深く理解する

---

## 📚 参考資料

- [README.md](README.md) - 詳細な使用方法
- [WEB_APP_COMPLETE.md](WEB_APP_COMPLETE.md) - Webアプリの詳細
- [docs/](docs/) - 設計ドキュメント

---

## 💡 よくある質問

### Q: インターネット接続は必要？

A: 不要です。完全にローカルで動作します。

### Q: データは外部に送信される？

A: いいえ。すべてローカルで処理されます。

### Q: どんな要件文書でも分析できる？

A: 日本語の自然言語で書かれた要件であれば分析可能です。

### Q: 商用利用できる？

A: ライセンスは未定です。プロジェクトオーナーに確認してください。

---

**バージョン**: 0.2.0 (Web対応版)  
**最終更新**: 2026年1月7日

すぐに始めるには、`.\start_web.ps1` を実行してください！
