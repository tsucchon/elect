import joblib
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ModelLoader:
    """学習済みモデルをロードするクラス"""

    def __init__(self):
        self.models = {}
        self.model_dir = Path(__file__).parent.parent.parent.parent / "ml" / "models"

    def load_models(self):
        """学習済みモデルをロード（同期関数）"""
        try:
            # 発電量予測モデル
            gen_model_path = self.model_dir / "generation_tokyo.pkl"
            if gen_model_path.exists():
                model_data = joblib.load(gen_model_path)
                self.models["generation"] = model_data
                logger.info(f"Loaded generation model (MAPE: {model_data['metrics']['mape']:.2f}%)")
            else:
                logger.warning(f"Generation model not found at {gen_model_path}")

            # 価格予測モデル
            price_model_path = self.model_dir / "price_tokyo.pkl"
            if price_model_path.exists():
                model_data = joblib.load(price_model_path)
                self.models["price"] = model_data
                logger.info(f"Loaded price model (MAPE: {model_data['metrics']['mape']:.2f}%)")
            else:
                logger.warning(f"Price model not found at {price_model_path}")

            if not self.models:
                logger.error("No models loaded. Please run ml/scripts/train.py first.")

        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            raise

    def get_model(self, model_type: str):
        """
        モデルを取得

        Args:
            model_type: "generation" or "price"

        Returns:
            モデルデータ辞書
        """
        if model_type not in self.models:
            raise ValueError(f"Model type '{model_type}' not loaded")

        return self.models[model_type]

    def is_loaded(self, model_type: str) -> bool:
        """モデルがロードされているか確認"""
        return model_type in self.models
