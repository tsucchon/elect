"""
サンプルデータ生成スクリプト（標準ライブラリのみ）

OCCTO/JEPX形式の3ヶ月分のダミーデータを生成します。
"""

import csv
import math
import random
from datetime import datetime, timedelta
from pathlib import Path

# シード固定
random.seed(42)

def generate_sample_data(days: int = 90):
    """
    サンプルデータを生成

    Args:
        days: 生成する日数（デフォルト90日 = 約3ヶ月）
    """
    # 30分単位のタイムスタンプを生成
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    timestamps = []
    current = start_date
    while current <= end_date:
        timestamps.append(current)
        current += timedelta(minutes=30)

    print(f"Generating {len(timestamps)} records ({days} days)")

    # 発電量データ生成
    generation_data = []

    for ts in timestamps:
        hour = ts.hour
        day_of_year = ts.timetuple().tm_yday

        # 太陽光発電量（昼間にピーク、季節変動あり）
        if 6 <= hour <= 18:
            solar_base = 1000 + 500 * math.sin((day_of_year / 365) * 2 * math.pi)
            solar_curve = math.sin((hour - 6) / 12 * math.pi)
            pv_mw = max(0, solar_base * solar_curve + random.gauss(0, 100))
        else:
            pv_mw = 0

        # 風力発電量（時間帯や季節で変動）
        wind_base = 300 + 200 * math.sin((day_of_year / 365) * 2 * math.pi + math.pi)
        wind_variation = random.gauss(1, 0.3)
        wind_mw = max(0, wind_base * wind_variation)

        total_mw = pv_mw + wind_mw

        generation_data.append({
            'timestamp': ts.strftime('%Y-%m-%d %H:%M:%S'),
            'pv_mw': round(pv_mw, 2),
            'wind_mw': round(wind_mw, 2),
            'total_mw': round(total_mw, 2)
        })

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
        noise = random.gauss(1, 0.1)

        price_yen = base_price * time_factor * generation_factor * noise
        price_yen = max(0.5, min(30, price_yen))  # 0.5〜30円の範囲に制限

        price_data.append({
            'timestamp': ts.strftime('%Y-%m-%d %H:%M:%S'),
            'price_yen': round(price_yen, 2)
        })

    # ファイル保存
    output_dir = Path(__file__).parent.parent / 'data' / 'seed'
    output_dir.mkdir(parents=True, exist_ok=True)

    generation_file = output_dir / 'generation_tokyo_sample.csv'
    price_file = output_dir / 'price_tokyo_sample.csv'

    # 発電量CSVを書き込み
    with open(generation_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['timestamp', 'pv_mw', 'wind_mw', 'total_mw'])
        writer.writeheader()
        writer.writerows(generation_data)

    # 価格CSVを書き込み
    with open(price_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['timestamp', 'price_yen'])
        writer.writeheader()
        writer.writerows(price_data)

    print(f"✓ Generated generation data: {generation_file}")
    print(f"  - Records: {len(generation_data)}")

    print(f"\n✓ Generated price data: {price_file}")
    print(f"  - Records: {len(price_data)}")


if __name__ == '__main__':
    generate_sample_data(days=90)
    print("\n✓ Sample data generation completed!")
