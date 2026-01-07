#!/bin/bash
# Webアプリケーション起動スクリプト (Unix/Mac用)

echo "🚀 未定義要素検出器 Webアプリを起動します..."
echo ""

# 依存パッケージのチェック
if ! python -c "import fastapi" 2>/dev/null; then
    echo "📦 FastAPIがインストールされていません。インストール中..."
    pip install fastapi uvicorn[standard] python-multipart
fi

# Webサーバーの起動
echo "🌐 Webサーバーを起動しています..."
echo ""
echo "✅ 準備完了！以下のURLでアクセスできます:"
echo ""
echo "   📱 Webアプリ: http://localhost:8000/app"
echo "   📚 API ドキュメント: http://localhost:8000/docs"
echo "   🏥 ヘルスチェック: http://localhost:8000/health"
echo ""
echo "終了するには Ctrl+C を押してください"
echo ""

python -m uvicorn usd.web_api:app --host 0.0.0.0 --port 8000 --reload


