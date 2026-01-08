"""
Web API: FastAPIを使ったREST API
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import traceback

from usd.coordinator import AnalysisCoordinator

# FastAPIアプリケーションの作成
app = FastAPI(
    title="未定義要素検出器 API",
    description="要件や仕様から未定義要素を自動検出するAPI",
    version="0.1.0"
)

# CORS設定（フロントエンドからのアクセスを許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では具体的なドメインを指定
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 分析コーディネーターのインスタンス（グローバル変数は削除）
# coordinator = AnalysisCoordinator()  # 削除: リクエストごとに生成する


# リクエストモデル
class AnalysisRequest(BaseModel):
    """分析リクエスト"""
    content: str
    metadata: Optional[Dict[str, Any]] = None
    options: Optional[Dict[str, Any]] = None
    use_llm: bool = False  # 🆕 LLMを使用するかどうか
    api_key: Optional[str] = None  # 🆕 OpenAI API Key


class AnalysisResponse(BaseModel):
    """分析レスポンス"""
    success: bool
    report: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# エンドポイント
@app.get("/")
async def root():
    """ルート"""
    return {
        "message": "未定義要素検出器 API",
        "version": "0.1.0",
        "endpoints": {
            "docs": "/docs",
            "analyze": "/api/analyze",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {"status": "healthy"}


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze(request: AnalysisRequest):
    """
    要件文書を分析する
    
    Args:
        request: 分析リクエスト
    
    Returns:
        分析結果
    """
    try:
        # 入力の検証
        if not request.content or not request.content.strip():
            raise HTTPException(status_code=400, detail="content is required")
        
        # LLM使用時のAPIキーチェック
        if request.use_llm and not request.api_key:
            raise HTTPException(
                status_code=400, 
                detail="api_key is required when use_llm=true"
            )
        
        # 分析実行
        coordinator = AnalysisCoordinator(
            use_llm=request.use_llm,
            api_key=request.api_key
        )
        
        report = coordinator.analyze(
            content=request.content,
            metadata=request.metadata,
            options=request.options
        )
        
        return AnalysisResponse(
            success=True,
            report=report
        )
    
    except Exception as e:
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        print(f"Error during analysis: {error_msg}")
        
        return AnalysisResponse(
            success=False,
            error=str(e)
        )


@app.get("/api/examples")
async def get_examples():
    """サンプル要件を取得"""
    examples = [
        {
            "id": "ec-cart",
            "title": "ECサイト カート機能",
            "content": """ユーザーは商品をカートに追加できる。
在庫がある場合のみ追加可能。

ユーザーはカート内の商品一覧を確認できる。
商品名、価格、数量を表示する。

ユーザーはカート内の商品を購入できる。
決済完了後、在庫から減算する。

システムは高速に動作すること。
安全に処理すること。"""
        },
        {
            "id": "user-auth",
            "title": "ユーザー認証",
            "content": """ユーザーはログインできる。
パスワードは8文字以上とする。

ログインに失敗した場合は適切に処理する。
セキュアに認証を行うこと。"""
        },
        {
            "id": "api-spec",
            "title": "API仕様",
            "content": """GET /api/users/:id
ユーザー情報を取得する

レスポンス:
{
  "name": "文字列",
  "email": "文字列",
  "createdAt": "日付"
}

高速に応答すること。"""
        }
    ]
    
    return {"examples": examples}


# 静的ファイルの配信（HTML, CSS, JS）
try:
    app.mount("/static", StaticFiles(directory="web/static"), name="static")
except Exception:
    pass  # 静的ファイルディレクトリがない場合は無視


@app.get("/app", response_class=HTMLResponse)
async def web_app():
    """Webアプリケーションのページ"""
    try:
        with open("web/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Web UI is not available</h1><p>Please check web/index.html</p>",
            status_code=404
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)





