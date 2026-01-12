import httpx
import pandas as pd
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class WeatherService:
    """Open-Meteo API連携サービス"""

    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    # 日本の主要地点座標
    LOCATIONS = {
        "tokyo": {"lat": 35.6762, "lon": 139.6503, "name": "東京"},
        "osaka": {"lat": 34.6937, "lon": 135.5023, "name": "大阪"},
        "nagoya": {"lat": 35.1815, "lon": 136.9066, "name": "名古屋"},
    }

    async def fetch_forecast(self, area: str = "tokyo", hours: int = 48) -> pd.DataFrame:
        """
        気象予報を取得

        Args:
            area: 対象エリア（tokyo, osaka, nagoya）
            hours: 予報時間数（デフォルト48時間）

        Returns:
            気象予報データのDataFrame
        """
        location = self.LOCATIONS.get(area)

        if not location:
            raise ValueError(f"Unknown area: {area}")

        params = {
            "latitude": location["lat"],
            "longitude": location["lon"],
            "hourly": "temperature_2m,wind_speed_10m,shortwave_radiation",
            "forecast_days": 3,  # 3日分（72時間）
            "timezone": "Asia/Tokyo"
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()

            logger.info(f"Fetched weather forecast for {area}")

            # DataFrameに変換
            hourly = data["hourly"]
            df = pd.DataFrame({
                "timestamp": pd.to_datetime(hourly["time"]),
                "temperature": hourly["temperature_2m"],
                "wind_speed": hourly["wind_speed_10m"],
                "solar_radiation": hourly.get("shortwave_radiation", [0] * len(hourly["time"]))
            })

            # 指定時間数分のみ返す
            df = df.head(hours)

            # 30分単位に変換（時間単位のデータを補間）
            df_30min = self._resample_to_30min(df)

            return df_30min

        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch weather data: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in weather fetch: {e}")
            raise

    def _resample_to_30min(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        時間単位のデータを30分単位に補間

        Args:
            df: 時間単位のDataFrame

        Returns:
            30分単位のDataFrame
        """
        df = df.set_index('timestamp')

        # 30分間隔にリサンプリング（線形補間）
        df_resampled = df.resample('30T').interpolate(method='linear')

        # インデックスをリセット
        df_resampled = df_resampled.reset_index()

        return df_resampled

    async def fetch_historical(self, area: str = "tokyo", days: int = 90) -> pd.DataFrame:
        """
        過去の気象データを取得（学習用）

        Args:
            area: 対象エリア
            days: 過去何日分

        Returns:
            過去気象データのDataFrame
        """
        location = self.LOCATIONS.get(area)

        if not location:
            raise ValueError(f"Unknown area: {area}")

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        params = {
            "latitude": location["lat"],
            "longitude": location["lon"],
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "hourly": "temperature_2m,wind_speed_10m,shortwave_radiation",
            "timezone": "Asia/Tokyo"
        }

        # Open-Meteo Historical API（別のエンドポイント）
        historical_url = "https://archive-api.open-meteo.com/v1/archive"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(historical_url, params=params)
                response.raise_for_status()
                data = response.json()

            logger.info(f"Fetched {days} days of historical weather data for {area}")

            hourly = data["hourly"]
            df = pd.DataFrame({
                "timestamp": pd.to_datetime(hourly["time"]),
                "temperature": hourly["temperature_2m"],
                "wind_speed": hourly["wind_speed_10m"],
                "solar_radiation": hourly.get("shortwave_radiation", [0] * len(hourly["time"]))
            })

            # 30分単位に変換
            df_30min = self._resample_to_30min(df)

            return df_30min

        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch historical weather data: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in historical weather fetch: {e}")
            raise
