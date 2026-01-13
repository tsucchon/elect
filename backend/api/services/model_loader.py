import joblib
import onnxruntime as ort
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
            # 発電量予測モデル（ONNX形式）
            gen_model_path = self.model_dir / "generation_tokyo.onnx"
            gen_metadata_path = self.model_dir / "generation_tokyo.metadata.pkl"

            if gen_model_path.exists() and gen_metadata_path.exists():
                # ONNXモデルをロード
                ort_session = ort.InferenceSession(str(gen_model_path))
                metadata = joblib.load(gen_metadata_path)

                self.models["generation"] = {
                    "model": ort_session,
                    "feature_cols": metadata["feature_cols"],
                    "metrics": metadata["metrics"]
                }
                logger.info(f"Loaded generation ONNX model (MAPE: {metadata['metrics']['mape']:.2f}%)")
            else:
                logger.warning(f"Generation ONNX model not found at {gen_model_path}")

            # 価格予測モデル（ONNX形式）
            price_model_path = self.model_dir / "price_tokyo.onnx"
            price_metadata_path = self.model_dir / "price_tokyo.metadata.pkl"

            if price_model_path.exists() and price_metadata_path.exists():
                # ONNXモデルをロード
                ort_session = ort.InferenceSession(str(price_model_path))
                metadata = joblib.load(price_metadata_path)

                self.models["price"] = {
                    "model": ort_session,
                    "feature_cols": metadata["feature_cols"],
                    "metrics": metadata["metrics"]
                }
                logger.info(f"Loaded price ONNX model (MAPE: {metadata['metrics']['mape']:.2f}%)")
            else:
                logger.warning(f"Price ONNX model not found at {price_model_path}")

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
