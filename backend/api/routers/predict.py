from fastapi import APIRouter, HTTPException
from datetime import datetime
import logging
from ..services.db import get_db, calculate_mape
from ..services.model_loader import ModelLoader
from ..services.predictor import Predictor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/predict", tags=["predict"])

# グローバルキャッシュ（Vercel Serverless Functions用）
_model_loader = None
_predictor = None


def get_predictor():
    """
    予測サービスを取得（遅延初期化）
    Vercel Serverless Functions用に、初回アクセス時にモデルをロード
    """
    global _model_loader, _predictor

    if _predictor is None:
        try:
            logger.info("Initializing predictor (lazy loading)...")
            _model_loader = ModelLoader()
            # 同期的にモデルをロード
            _model_loader.load_models()

            _predictor = Predictor(_model_loader)
            logger.info("Predictor initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize predictor: {e}")
            raise

    return _predictor


def set_predictor(p):
    """予測サービスを設定（後方互換性のため残す）"""
    global _predictor
    _predictor = p


@router.get("/latest")
async def get_latest_prediction(area: str = "tokyo", hours: int = 48):
    """
    次のN時間の予測を取得

    Args:
        area: 対象エリア（デフォルト: tokyo）
        hours: 予測時間数（デフォルト: 48）

    Returns:
        予測結果
    """
    try:
        # 予測サービスを取得（初回時にロード）
        predictor = get_predictor()

        logger.info(f"Generating {hours}h prediction for {area}")

        # 予測実行
        predictions = await predictor.predict(area=area, hours=hours)

        return {
            "area": area,
            "predictions": predictions,
            "generated_at": datetime.now().isoformat()
        }

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=f"予測に失敗しました: {str(e)}")


@router.get("/accuracy")
async def get_accuracy(area: str = "tokyo", days: int = 7):
    """
    過去N日間の予測精度（MAPE）を取得

    Args:
        area: 対象エリア
        days: 過去何日分

    Returns:
        精度メトリクス
    """
    try:
        db = get_db()

        # 発電量のMAPE
        generation_mape = calculate_mape(db, "generation", area, days)

        # 価格のMAPE
        price_mape = calculate_mape(db, "price", area, days)

        db.close()

        return {
            "area": area,
            "period_days": days,
            "generation_mape": generation_mape,
            "price_mape": price_mape,
            "note": "MAPEが小さいほど精度が高い"
        }

    except Exception as e:
        logger.error(f"Failed to calculate accuracy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_prediction_history(area: str = "tokyo", days: int = 7):
    """
    過去の予測履歴を取得

    Args:
        area: 対象エリア
        days: 過去何日分

    Returns:
        予測履歴
    """
    try:
        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
            SELECT area, target_type, forecast_timestamp, predicted_value, actual_value, created_at
            FROM predictions
            WHERE area = ?
            AND created_at >= datetime('now', '-' || ? || ' days')
            ORDER BY forecast_timestamp DESC
            LIMIT 1000
        """, (area, days))

        rows = cursor.fetchall()
        db.close()

        history = []
        for row in rows:
            history.append({
                "area": row['area'],
                "target_type": row['target_type'],
                "forecast_timestamp": row['forecast_timestamp'],
                "predicted_value": row['predicted_value'],
                "actual_value": row['actual_value'],
                "created_at": row['created_at']
            })

        return {
            "area": area,
            "period_days": days,
            "history": history
        }

    except Exception as e:
        logger.error(f"Failed to get prediction history: {e}")
        raise HTTPException(status_code=500, detail=str(e))
