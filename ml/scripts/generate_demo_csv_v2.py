"""
アップロードテスト用のデモCSV v2を生成（14日分、冬季パターン）

既存のデモCSVとは異なるパターン：
- 期間: 14日分
- 季節: 冬季（太陽光発電量が少なめ）
- 風力: やや強め
- 価格: 高め（暖房需要期）
"""

import csv
import math
import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(123)  # 異なるシードで異なるパターン生成

def generate_demo_csv_v2(days: int = 14):
    """
    テスト用の別パターンデモCSVを生成

    Args:
        days: 生成する日数（デフォルト14日）
    """
    # 30分単位のタイムスタンプを生成
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    timestamps = []
    current = start_date
    while current <= end_date:
        timestamps.append(current)
        current += timedelta(minutes=30)

    print(f"Generating {len(timestamps)} records ({days} days) - Winter pattern")

    # 発電量データ生成（冬季パターン）
    generation_data = []

    for ts in timestamps:
        hour = ts.hour
        day_of_year = ts.timetuple().tm_yday

        # 太陽光発電量（冬季なので少なめ、昼間にピーク）
        if 7 <= hour <= 17:  # 日照時間が短い
            solar_base = 600 + 300 * math.sin((day_of_year / 365) * 2 * math.pi)
            solar_curve = math.sin((hour - 7) / 10 * math.pi)
            pv_mw = max(0, solar_base * solar_curve + random.gauss(0, 80))
        else:
            pv_mw = 0

        # 風力発電量（冬季なので強め）
        wind_base = 450 + 300 * math.sin((day_of_year / 365) * 2 * math.pi + math.pi)
        wind_variation = random.gauss(1.2, 0.4)  # より変動が大きい
        wind_mw = max(0, wind_base * wind_variation)

        total_mw = pv_mw + wind_mw

        generation_data.append({
            'timestamp': ts.strftime('%Y-%m-%d %H:%M:%S'),
            'pv_mw': round(pv_mw, 2),
            'wind_mw': round(wind_mw, 2),
            'total_mw': round(total_mw, 2)
        })

    # 価格データ生成（冬季は暖房需要で高め）
    price_data = []

    for i, ts in enumerate(timestamps):
        hour = ts.hour

        base_price = 12.0  # 冬季は基本価格が高め

        # 時間帯による変動（朝夕ピークがより顕著）
        if 7 <= hour <= 9:
            time_factor = 1.8  # 朝のピークが強い
        elif 17 <= hour <= 21:
            time_factor = 2.0  # 夕方のピークがさらに強い
        elif 0 <= hour <= 5:
            time_factor = 0.8
        else:
            time_factor = 1.1

        # 再エネ発電量が多いと価格が下がる
        generation = generation_data[i]['total_mw']
        generation_factor = 1 - (generation / 2000) * 0.25

        # ランダムノイズ（より大きめ）
        noise = random.gauss(1, 0.15)

        price_yen = base_price * time_factor * generation_factor * noise
        price_yen = max(0.5, min(35, price_yen))  # 0.5〜35円の範囲

        price_data.append({
            'timestamp': ts.strftime('%Y-%m-%d %H:%M:%S'),
            'price_yen': round(price_yen, 2)
        })

    # プロジェクトルートに保存
    output_dir = Path(__file__).parent.parent.parent

    generation_file = output_dir / 'generation_tokyo_demo2.csv'
    price_file = output_dir / 'price_tokyo_demo2.csv'

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

    print(f"✓ Generated: {generation_file}")
    print(f"  - Records: {len(generation_data)}")
    print(f"  - Pattern: Winter (less solar, more wind)")

    print(f"\n✓ Generated: {price_file}")
    print(f"  - Records: {len(price_data)}")
    print(f"  - Pattern: Higher prices (heating demand)")

    # 統計情報を表示
    avg_pv = sum(d['pv_mw'] for d in generation_data) / len(generation_data)
    avg_wind = sum(d['wind_mw'] for d in generation_data) / len(generation_data)
    avg_total = sum(d['total_mw'] for d in generation_data) / len(generation_data)
    avg_price = sum(d['price_yen'] for d in price_data) / len(price_data)

    print(f"\n統計情報:")
    print(f"  - 平均PV発電量: {avg_pv:.2f} MW")
    print(f"  - 平均風力発電量: {avg_wind:.2f} MW")
    print(f"  - 平均総発電量: {avg_total:.2f} MW")
    print(f"  - 平均価格: {avg_price:.2f} 円/kWh")


if __name__ == '__main__':
    generate_demo_csv_v2(days=14)
    print("\n✓ Alternative demo CSV files created!")
    print("\n特徴:")
    print("- 14日分のデータ（v1は7日分）")
    print("- 冬季パターン（太陽光少なめ、風力強め）")
    print("- 価格高め（暖房需要期）")
    print("- 価格変動が大きい")
    print("\nこのファイルをアップロードすると、異なるMAPE値が表示されます。")
