import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging
from .model_loader import ModelLoader
from .weather import WeatherService
from .db import get_db, get_generation_data, get_price_data

logger = logging.getLogger(__name__)


class Predictor:
    """予測実行サービス"""

    def __init__(self, model_loader: ModelLoader):
        self.model_loader = model_loader
        self.weather_service = WeatherService()

    async def predict(self, area: str = "tokyo", hours: int = 48):
        """
        48時間予測を実行

        Args:
            area: 対象エリア
            hours: 予測時間数

        Returns:
            予測結果の辞書
        """
        try:
            # 気象予報取得
            weather_df = await self.weather_service.fetch_forecast(area, hours)

            # 過去データ取得（Lag特徴量用）
            db = get_db()
            historical_generation = get_generation_data(db, area, limit=200)
            historical_price = get_price_data(db, area, limit=200)
            db.close()

            # 発電量予測
            generation_pred = await self._predict_generation(
                weather_df,
                historical_generation
            )

            # 価格予測
            price_pred = await self._predict_price(
                weather_df,
                historical_price
            )

            return {
                "generation": generation_pred,
                "price": price_pred
            }

        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            raise

    async def _predict_generation(self, weather_df: pd.DataFrame, historical_data: list):
        """発電量を予測（再エネ合計）"""
        if not self.model_loader.is_loaded("generation"):
            raise ValueError("Generation model not loaded")

        model_data = self.model_loader.get_model("generation")
        ort_session = model_data['model']
        feature_cols = model_data['feature_cols']

        # 特徴量生成（renewable_total_mwを予測）
        features = self._create_features(weather_df, historical_data, 'renewable_total_mw')

        # 特徴量の列名をメタデータと一致させる（total_mw_* に変換）
        features = self._rename_features_for_onnx(features, 'renewable_total_mw', 'total_mw')

        # 予測実行（ONNX）
        input_name = ort_session.get_inputs()[0].name
        predictions = ort_session.run(None, {input_name: features[feature_cols].astype('float32').values})[0]

        # 結果をフォーマット
        timestamps = [
            (datetime.now() + timedelta(minutes=30 * i)).isoformat()
            for i in range(len(predictions))
        ]

        return [
            {"timestamp": ts, "value": max(0, float(val))}
            for ts, val in zip(timestamps, predictions)
        ]

    async def _predict_price(self, weather_df: pd.DataFrame, historical_data: list):
        """価格を予測"""
        if not self.model_loader.is_loaded("price"):
            raise ValueError("Price model not loaded")

        model_data = self.model_loader.get_model("price")
        ort_session = model_data['model']
        feature_cols = model_data['feature_cols']

        # 特徴量生成
        features = self._create_features(weather_df, historical_data, 'price_yen')

        # 特徴量の列名をメタデータと一致させる（price_* に変換）
        features = self._rename_features_for_onnx(features, 'price_yen', 'price')

        # 予測実行（ONNX）
        input_name = ort_session.get_inputs()[0].name
        predictions = ort_session.run(None, {input_name: features[feature_cols].astype('float32').values})[0]

        # 結果をフォーマット
        timestamps = [
            (datetime.now() + timedelta(minutes=30 * i)).isoformat()
            for i in range(len(predictions))
        ]

        return [
            {"timestamp": ts, "value": max(0, float(val))}
            for ts, val in zip(timestamps, predictions)
        ]

    def _rename_features_for_onnx(self, features: pd.DataFrame, old_prefix: str, new_prefix: str) -> pd.DataFrame:
        """
        ONNX モデル用に特徴量の列名を変換

        Args:
            features: 特徴量DataFrame
            old_prefix: 現在の列名プレフィックス（例: 'renewable_total_mw', 'price_yen'）
            new_prefix: ONNXモデルが期待する列名プレフィックス（例: 'total_mw', 'price'）

        Returns:
            列名を変換したDataFrame
        """
        rename_dict = {}
        for col in features.columns:
            if old_prefix in col:
                # renewable_total_mw_lag_1 -> total_mw_lag_1
                # price_yen_lag_1 -> price_lag_1
                new_col = col.replace(old_prefix, new_prefix)
                rename_dict[col] = new_col

        return features.rename(columns=rename_dict)

    def _create_features(self, weather_df: pd.DataFrame, historical_data: list, target_col: str) -> pd.DataFrame:
        """
        予測用の特徴量を生成

        Args:
            weather_df: 気象予報データ
            historical_data: 過去データ（Lag特徴量用）
            target_col: ターゲット列名

        Returns:
            特徴量DataFrame
        """
        features = pd.DataFrame()

        # timestampを日時型に変換
        if 'timestamp' not in weather_df.columns:
            # 現在時刻から30分刻みでタイムスタンプを生成
            start_time = datetime.now()
            timestamps = [start_time + timedelta(minutes=30 * i) for i in range(len(weather_df))]
            weather_df['timestamp'] = timestamps
        else:
            weather_df['timestamp'] = pd.to_datetime(weather_df['timestamp'])

        # 時刻特徴
        features['hour'] = weather_df['timestamp'].dt.hour
        features['hour_sin'] = np.sin(2 * np.pi * features['hour'] / 24)
        features['hour_cos'] = np.cos(2 * np.pi * features['hour'] / 24)

        # 曜日特徴
        features['day_of_week'] = weather_df['timestamp'].dt.dayofweek
        features['is_weekend'] = (features['day_of_week'] >= 5).astype(int)

        # 月特徴
        features['month'] = weather_df['timestamp'].dt.month
        features['month_sin'] = np.sin(2 * np.pi * features['month'] / 12)
        features['month_cos'] = np.cos(2 * np.pi * features['month'] / 12)

        # Lag特徴量（過去データから計算）
        if historical_data:
            # 最新の値を使用
            if target_col == 'renewable_total_mw':
                # renewable_total_mwカラムを使用（DBのエイリアス）
                recent_values = [row['renewable_total_mw'] for row in historical_data[:100]]
            else:
                recent_values = [row['price_yen'] for row in historical_data[:100]]

            # Lag特徴量を計算
            features[f'{target_col}_lag_1'] = recent_values[0] if len(recent_values) > 0 else 0
            features[f'{target_col}_lag_2'] = recent_values[1] if len(recent_values) > 1 else 0
            features[f'{target_col}_lag_48'] = recent_values[47] if len(recent_values) > 47 else recent_values[0] if recent_values else 0
            features[f'{target_col}_lag_96'] = recent_values[95] if len(recent_values) > 95 else recent_values[0] if recent_values else 0

            # 移動平均
            features[f'{target_col}_rolling_mean_24'] = np.mean(recent_values[:24]) if len(recent_values) >= 24 else np.mean(recent_values) if recent_values else 0
            features[f'{target_col}_rolling_std_24'] = np.std(recent_values[:24]) if len(recent_values) >= 24 else 0

            features[f'{target_col}_rolling_mean_48'] = np.mean(recent_values[:48]) if len(recent_values) >= 48 else np.mean(recent_values) if recent_values else 0
            features[f'{target_col}_rolling_std_48'] = np.std(recent_values[:48]) if len(recent_values) >= 48 else 0
        else:
            # 過去データがない場合はデフォルト値
            for lag in [1, 2, 48, 96]:
                features[f'{target_col}_lag_{lag}'] = 0

            for window in [24, 48]:
                features[f'{target_col}_rolling_mean_{window}'] = 0
                features[f'{target_col}_rolling_std_{window}'] = 0

        return features
