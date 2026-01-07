# Webアプリケーション起動スクリプト (Windows用)

Write-Host "🚀 未定義要素検出器 Webアプリを起動します..." -ForegroundColor Cyan
Write-Host ""

# 依存パッケージのチェック
try {
    python -c "import fastapi" 2>$null
} catch {
    Write-Host "📦 FastAPIがインストールされていません。インストール中..." -ForegroundColor Yellow
    pip install fastapi uvicorn[standard] python-multipart
}

# Webサーバーの起動
Write-Host "🌐 Webサーバーを起動しています..." -ForegroundColor Green
Write-Host ""
Write-Host "✅ 準備完了！以下のURLでアクセスできます:" -ForegroundColor Green
Write-Host ""
Write-Host "   📱 Webアプリ: " -NoNewline
Write-Host "http://localhost:8000/app" -ForegroundColor Yellow
Write-Host "   📚 API ドキュメント: " -NoNewline
Write-Host "http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "   🏥 ヘルスチェック: " -NoNewline
Write-Host "http://localhost:8000/health" -ForegroundColor Yellow
Write-Host ""
Write-Host "終了するには Ctrl+C を押してください" -ForegroundColor Gray
Write-Host ""

python -m uvicorn usd.web_api:app --host 0.0.0.0 --port 8000 --reload


