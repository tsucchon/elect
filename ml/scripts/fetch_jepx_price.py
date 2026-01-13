"""
JEPXスポット価格CSVから指定期間・エリアのデータを抽出
"""

import pandas as pd
import subprocess
from pathlib import Path
from datetime import datetime
import sys

def fetch_jepx_spot_data(year: int, output_dir: Path):
    """
    JEPXスポット価格CSVをダウンロード（curlを使用）

    Args:
        year: 年度（例: 2025）
        output_dir: 出力ディレクトリ
    """
    url = f"https://www.jepx.jp/market/excel/spot_{year}.csv"
    output_file = output_dir / f"jepx_spot_{year}.csv"

    print(f"Downloading JEPX spot data for {year}...")
    print(f"URL: {url}")

    try:
        # curlでダウンロード
        result = subprocess.run(
            ['curl', '-o', str(output_file), url],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(f"✓ Downloaded to {output_file}")
            return output_file
        else:
            print(f"Error: {result.stderr}")
            return None

    except Exception as e:
        print(f"Error downloading: {e}")
        return None


def extract_area_price(
    jepx_file: Path,
    area: str = "tokyo",
    start_date: str = None,
    end_date: str = None,
    output_file: Path = None
):
    """
    JEPXデータから指定エリア・期間の価格を抽出

    Args:
        jepx_file: JEPXのCSVファイル
        area: エリア名（tokyo, hokkaido, tohoku, chubu, hokuriku, kansai, chugoku, shikoku, kyushu）
        start_date: 開始日（YYYY-MM-DD）
        end_date: 終了日（YYYY-MM-DD）
        output_file: 出力ファイルパス
    """
    # エリア名のマッピング
    area_columns = {
        'hokkaido': 'エリアプライス北海道(円/kWh)',
        'tohoku': 'エリアプライス東北(円/kWh)',
        'tokyo': 'エリアプライス東京(円/kWh)',
        'chubu': 'エリアプライス中部(円/kWh)',
        'hokuriku': 'エリアプライス北陸(円/kWh)',
        'kansai': 'エリアプライス関西(円/kWh)',
        'chugoku': 'エリアプライス中国(円/kWh)',
        'shikoku': 'エリアプライス四国(円/kWh)',
        'kyushu': 'エリアプライス九州(円/kWh)'
    }

    if area not in area_columns:
        print(f"Error: Invalid area '{area}'. Valid areas: {list(area_columns.keys())}")
        return None

    price_column = area_columns[area]

    print(f"\nExtracting {area} area price data...")
    print(f"Input file: {jepx_file}")

    # CSVを読み込み（Shift-JIS）
    df = pd.read_csv(jepx_file, encoding='shift-jis')

    print(f"Loaded {len(df)} records")
    print(f"Date range: {df['年月日'].min()} to {df['年月日'].max()}")

    # 日付をパース
    df['date'] = pd.to_datetime(df['年月日'], format='%Y/%m/%d')

    # 期間でフィルタリング
    if start_date:
        start = pd.to_datetime(start_date)
        df = df[df['date'] >= start]
        print(f"Filtered from {start_date}: {len(df)} records")

    if end_date:
        end = pd.to_datetime(end_date)
        df = df[df['date'] <= end]
        print(f"Filtered to {end_date}: {len(df)} records")

    # 時刻コードを時刻に変換（1=0:00, 2=0:30, ..., 48=23:30）
    def time_code_to_time(code):
        hour = (code - 1) // 2
        minute = 0 if code % 2 == 1 else 30
        return f"{hour:02d}:{minute:02d}"

    df['time'] = df['時刻コード'].apply(time_code_to_time)

    # timestampを作成
    df['timestamp'] = pd.to_datetime(
        df['年月日'].astype(str) + ' ' + df['time'],
        format='%Y/%m/%d %H:%M'
    )

    # 必要な列だけ抽出
    result = pd.DataFrame({
        'timestamp': df['timestamp'],
        'price_yen': df[price_column]
    })

    print(f"\nExtracted data:")
    print(f"  Records: {len(result)}")
    print(f"  Date range: {result['timestamp'].min()} to {result['timestamp'].max()}")
    print(f"  Price range: {result['price_yen'].min():.2f} - {result['price_yen'].max():.2f} 円/kWh")
    print(f"  Average price: {result['price_yen'].mean():.2f} 円/kWh")

    # 保存
    if output_file is None:
        output_file = jepx_file.parent / f'price_{area}_sample.csv'

    result.to_csv(output_file, index=False)
    print(f"\n✓ Saved to {output_file}")

    return result


if __name__ == '__main__':
    # データディレクトリ
    data_dir = Path(__file__).parent.parent / 'data' / 'seed'
    data_dir.mkdir(parents=True, exist_ok=True)

    # サンプルデータの期間を確認
    generation_file = data_dir / 'generation_tokyo_tepco.csv'

    if generation_file.exists():
        print("Checking sample data period...")
        df_gen = pd.read_csv(generation_file, skiprows=1)
        df_gen['timestamp'] = pd.to_datetime(df_gen['DATE'] + ' ' + df_gen['TIME'], format='%Y/%m/%d %H:%M')

        start_date = df_gen['timestamp'].min().strftime('%Y-%m-%d')
        end_date = df_gen['timestamp'].max().strftime('%Y-%m-%d')

        print(f"Sample data period: {start_date} to {end_date}")
    else:
        # デフォルト値
        start_date = '2025-10-14'
        end_date = '2026-01-12'
        print(f"Using default period: {start_date} to {end_date}")

    # JEPXデータをダウンロード
    jepx_file = data_dir / 'jepx_spot_2025.csv'

    if not jepx_file.exists():
        jepx_file = fetch_jepx_spot_data(2025, data_dir)
        if jepx_file is None:
            print("Failed to download JEPX data")
            sys.exit(1)
    else:
        print(f"Using existing file: {jepx_file}")

    # 東京エリアの価格を抽出
    output_file = data_dir / 'price_tokyo_sample.csv'

    extract_area_price(
        jepx_file=jepx_file,
        area='tokyo',
        start_date=start_date,
        end_date=end_date,
        output_file=output_file
    )

    print("\n✓ JEPX price data extraction completed!")
