"""
サンプルデータ生成スクリプト

OCCTO/JEPX形式の3ヶ月分のダミーデータを生成します。
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# シード固定
np.random.seed(42)

def generate_sample_data(days: int = 90):
    """
    サンプルデータを生成

    Args:
        days: 生成する日数（デフォルト90日 = 約3ヶ月）
    """
    # 30分単位のタイムスタンプを生成
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    timestamps = pd.date_range(
        start=start_date,
        end=end_date,
        freq='30T'  # 30分単位
    )

    print(f"Generating {len(timestamps)} records ({days} days)")

    # 発電量データ生成
    generation_data = []

    for ts in timestamps:
        hour = ts.hour
        day_of_year = ts.dayofyear

        # 太陽光発電量（昼間にピーク、季節変動あり）
        # 日の出から日没まで発電
        if 6 <= hour <= 18:
            solar_base = 1000 + 500 * np.sin((day_of_year / 365) * 2 * np.pi)
            solar_curve = np.sin((hour - 6) / 12 * np.pi)
            pv_mw = max(0, solar_base * solar_curve + np.random.normal(0, 100))
        else:
            pv_mw = 0

        # 風力発電量（時間帯や季節で変動）
        wind_base = 300 + 200 * np.sin((day_of_year / 365) * 2 * np.pi + np.pi)
        wind_variation = np.random.normal(1, 0.3)
        wind_mw = max(0, wind_base * wind_variation)

        total_mw = pv_mw + wind_mw

        generation_data.append({
            'timestamp': ts,
            'pv_mw': round(pv_mw, 2),
            'wind_mw': round(wind_mw, 2),
            'total_mw': round(total_mw, 2)
        })

    df_generation = pd.DataFrame(generation_data)

    # 価格データ生成（発電量と負の相関）
    price_data = []

    for i, ts in enumerate(timestamps):
        hour = ts.hour

        # ベース価格
        base_price = 10.0  # 円/kWh

        # 時間帯による変動（朝夕にピーク）
        if 7 <= hour <= 9 or 17 <= hour <= 20:
            time_factor = 1.5
        elif 0 <= hour <= 5:
            time_factor = 0.7
        else:
            time_factor = 1.0

        # 再エネ発電量が多いと価格が下がる
        generation = generation_data[i]['total_mw']
        generation_factor = 1 - (generation / 2000) * 0.3

        # ランダムノイズ
        noise = np.random.normal(1, 0.1)

        price_yen = base_price * time_factor * generation_factor * noise
        price_yen = max(0.5, min(30, price_yen))  # 0.5〜30円の範囲に制限

        price_data.append({
            'timestamp': ts,
            'price_yen': round(price_yen, 2)
        })

    df_price = pd.DataFrame(price_data)

    # ファイル保存
    output_dir = Path(__file__).parent.parent / 'data' / 'seed'
    output_dir.mkdir(parents=True, exist_ok=True)

    generation_file = output_dir / 'generation_tokyo_sample.csv'
    price_file = output_dir / 'price_tokyo_sample.csv'

    df_generation.to_csv(generation_file, index=False)
    df_price.to_csv(price_file, index=False)

    print(f"✓ Generated generation data: {generation_file}")
    print(f"  - Records: {len(df_generation)}")
    print(f"  - PV range: {df_generation['pv_mw'].min():.2f} - {df_generation['pv_mw'].max():.2f} MW")
    print(f"  - Wind range: {df_generation['wind_mw'].min():.2f} - {df_generation['wind_mw'].max():.2f} MW")

    print(f"\n✓ Generated price data: {price_file}")
    print(f"  - Records: {len(df_price)}")
    print(f"  - Price range: {df_price['price_yen'].min():.2f} - {df_price['price_yen'].max():.2f} 円/kWh")


if __name__ == '__main__':
    generate_sample_data(days=90)
    print("\n✓ Sample data generation completed!")
