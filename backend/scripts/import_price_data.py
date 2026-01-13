"""
JEPX価格データをデータベースにインポート
"""

import pandas as pd
import sys
from pathlib import Path

# バックエンドのパスを追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.services.db import init_database, get_db, save_price_data, clear_price_data

def import_price_csv(csv_path: str, area: str = "tokyo"):
    """
    価格CSVをインポート

    Args:
        csv_path: CSVファイルのパス
        area: エリア名
    """
    # CSVを読み込み
    df = pd.read_csv(csv_path)

    # timestampを日時型に変換
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    print(f"Loaded {len(df)} records from {csv_path}")
    print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"Price range: {df['price_yen'].min():.2f} - {df['price_yen'].max():.2f} 円/kWh")
    print(f"Average price: {df['price_yen'].mean():.2f} 円/kWh")

    # データベースに保存
    init_database()
    conn = get_db()

    try:
        # 既存データをクリア
        clear_price_data(conn, area)

        # 新しいデータを保存
        save_price_data(conn, df, area)

        print(f"\n✓ Successfully imported {len(df)} records to database for area: {area}")

    finally:
        conn.close()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python import_price_data.py <csv_file> [area]")
        print("\nExample:")
        print("  python import_price_data.py ../ml/data/seed/price_tokyo_sample.csv tokyo")
        sys.exit(1)

    csv_file = sys.argv[1]
    area = sys.argv[2] if len(sys.argv) > 2 else "tokyo"

    if not Path(csv_file).exists():
        print(f"Error: File not found: {csv_file}")
        sys.exit(1)

    import_price_csv(csv_file, area)
