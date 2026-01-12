from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
import logging
from .services.db import init_database
from .services.model_loader import ModelLoader
from .services.predictor import Predictor
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
    """起動時初期化"""
    try:
        # データベース初期化
        init_database()

        # モデルロード
        model_loader = ModelLoader()
        await model_loader.load_models()

        # 予測サービス初期化
        predictor = Predictor(model_loader)
        predict.set_predictor(predictor)

        logger.info("Application started successfully")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        logger.warning("Continuing without ML models. Run ml/scripts/train.py to generate models.")


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


# Vercel用ハンドラー
handler = Mangum(app)
