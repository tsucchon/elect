"""
既存のサンプルCSVを東京電力の形式に変換するスクリプト
"""

import pandas as pd
import numpy as np
from pathlib import Path

def convert_to_tepco_format():
    """
    既存のサンプルCSVを東京電力のエリア需給実績データ形式に変換
    """
    # 既存のサンプルCSVを読み込み
    data_dir = Path(__file__).parent.parent / 'data' / 'seed'
    generation_file = data_dir / 'generation_tokyo_sample.csv'

    if not generation_file.exists():
        print(f"Error: {generation_file} not found")
        print("Run 'python scripts/generate_sample_data.py' first")
        return

    df = pd.read_csv(generation_file)
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    print(f"Converting {len(df)} records to TEPCO format...")

    # 東京電力形式のデータを作成
    tepco_data = []

    for _, row in df.iterrows():
        ts = row['timestamp']
        pv_mw = row['pv_mw']
        wind_mw = row['wind_mw']
        total_mw = row['total_mw']

        # エリア需要を計算（再エネ以外の電源も含めた総需要）
        # 実際の東京エリアの需要は約25,000〜50,000 MW程度
        hour = ts.hour
        day_of_week = ts.dayofweek

        # ベース需要（時間帯により変動）
        if 0 <= hour <= 5:
            base_demand = 25000
        elif 6 <= hour <= 9:
            base_demand = 35000
        elif 10 <= hour <= 17:
            base_demand = 40000
        elif 18 <= hour <= 22:
            base_demand = 38000
        else:
            base_demand = 30000

        # 曜日による変動（平日は需要が高い）
        if day_of_week < 5:  # 平日
            weekday_factor = 1.0
        else:  # 週末
            weekday_factor = 0.85

        # 季節変動
        month = ts.month
        if month in [7, 8]:  # 夏
            season_factor = 1.15
        elif month in [1, 2, 12]:  # 冬
            season_factor = 1.10
        else:
            season_factor = 1.0

        area_demand = int(base_demand * weekday_factor * season_factor + np.random.normal(0, 500))

        # 各電源の発電量を推定（エリア需要を満たすように配分）
        remaining_demand = area_demand - pv_mw - wind_mw

        # 原子力（ベースロード、現在はほぼゼロ）
        nuclear = 0

        # 火力発電（LNG、石炭、石油、その他）
        thermal_total = max(0, remaining_demand * 0.65)
        fire_lng = int(thermal_total * 0.45)
        fire_coal = int(thermal_total * 0.30)
        fire_oil = int(thermal_total * 0.15)
        fire_other = int(thermal_total * 0.10)

        # 水力（ベースロード + 調整力）
        hydro = int(max(0, remaining_demand * 0.08 + np.random.normal(0, 50)))

        # 地熱（ベースロード、少量）
        geothermal = 0

        # バイオマス
        biomass = int(max(0, remaining_demand * 0.02 + np.random.normal(0, 20)))

        # 太陽光・風力（既存データを使用）
        solar_actual = int(pv_mw)
        solar_curtailment = 0  # 出力制御量
        wind_actual = int(wind_mw)
        wind_curtailment = 0  # 出力制御量

        # 揚水発電（ピーク時に放電、深夜に充電）
        if 9 <= hour <= 20:
            pumped_storage = int(np.random.uniform(0, 500))
        elif 0 <= hour <= 5:
            pumped_storage = -int(np.random.uniform(0, 300))  # 負は揚水（充電）
        else:
            pumped_storage = 0

        # 蓄電池
        battery = 0

        # 連系線（他エリアとの融通）
        interconnection = int(np.random.normal(0, 200))

        # その他
        other = int(max(0, np.random.uniform(100, 300)))

        # 合計を計算
        supply_total = (nuclear + fire_lng + fire_coal + fire_oil + fire_other +
                       hydro + geothermal + biomass + solar_actual + wind_actual +
                       pumped_storage + battery + interconnection + other)

        # エリア需要と合計を一致させる（誤差調整）
        adjustment = area_demand - supply_total
        if adjustment != 0:
            # 火力LNGで調整
            fire_lng += adjustment
            supply_total = area_demand

        tepco_data.append({
            'DATE': ts.strftime('%Y/%-m/%-d'),
            'TIME': ts.strftime('%-H:%M'),
            'エリア需要': area_demand,
            '原子力': nuclear,
            '火力(LNG)': fire_lng,
            '火力(石炭)': fire_coal,
            '火力(石油)': fire_oil,
            '火力(その他)': fire_other,
            '水力': hydro,
            '地熱': geothermal,
            'バイオマス': biomass,
            '太陽光発電実績': solar_actual,
            '太陽光出力制御量': solar_curtailment,
            '風力発電実績': wind_actual,
            '風力出力制御量': wind_curtailment,
            '揚水': pumped_storage,
            '蓄電池': battery,
            '連系線': interconnection,
            'その他': other,
            '合計': supply_total
        })

    df_tepco = pd.DataFrame(tepco_data)

    # CSVファイルとして保存
    output_file = data_dir / 'generation_tokyo_tepco.csv'

    # ヘッダー行を手動で書き込む
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('単位[MW平均],,,供給力\n')
        df_tepco.to_csv(f, index=False)

    print(f"✓ Converted to TEPCO format: {output_file}")
    print(f"  - Records: {len(df_tepco)}")
    print(f"  - Area demand range: {df_tepco['エリア需要'].min()} - {df_tepco['エリア需要'].max()} MW")
    print(f"  - Solar range: {df_tepco['太陽光発電実績'].min()} - {df_tepco['太陽光発電実績'].max()} MW")
    print(f"  - Wind range: {df_tepco['風力発電実績'].min()} - {df_tepco['風力発電実績'].max()} MW")

if __name__ == '__main__':
    convert_to_tepco_format()
    print("\n✓ Conversion completed!")
