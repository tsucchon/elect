from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from .services.db import init_database
from .routers import data, predict

# ロガー設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="再エネ予測API", version="0.1.0")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では制限する
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """起動時初期化（Vercel Serverless Functions用に最小化）"""
    try:
        # データベース初期化のみ実行
        init_database()
        logger.info("Database initialized")

        # モデルロードは遅延初期化（predict.get_predictor()で実行）
        logger.info("ML models will be loaded on first prediction request (lazy loading)")

    except Exception as e:
        logger.error(f"Startup failed: {e}")
        logger.warning("Continuing with limited functionality")


# ルーター登録
app.include_router(data.router)
app.include_router(predict.router)


@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {"message": "再エネ発電量＋電力価格予測API"}


@app.get("/api/health")
async def health_check():
    """ヘルスチェック"""
    return {"status": "ok", "message": "API is running"}

# Vercel Python Functionsは、appオブジェクトを自動的に認識します
