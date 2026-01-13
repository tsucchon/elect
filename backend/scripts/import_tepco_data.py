"""
東京電力形式のCSVデータをデータベースにインポート
"""

import pandas as pd
import sys
from pathlib import Path

# バックエンドのパスを追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.services.db import init_database, get_db, save_generation_data, clear_generation_data

def import_tepco_csv(csv_path: str, area: str = "tokyo"):
    """
    東京電力形式のCSVをインポート

    Args:
        csv_path: CSVファイルのパス
        area: エリア名
    """
    # CSVを読み込み
    df = pd.read_csv(csv_path, skiprows=1)  # ヘッダー行をスキップ

    # DATEとTIMEを結合してtimestampを作成
    df['timestamp'] = pd.to_datetime(df['DATE'] + ' ' + df['TIME'], format='%Y/%m/%d %H:%M')

    print(f"Loaded {len(df)} records from {csv_path}")
    print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"Solar range: {df['太陽光発電実績'].min()} - {df['太陽光発電実績'].max()} MW")
    print(f"Wind range: {df['風力発電実績'].min()} - {df['風力発電実績'].max()} MW")

    # データベースに保存
    init_database()
    conn = get_db()

    try:
        # 既存データをクリア
        clear_generation_data(conn, area)

        # 新しいデータを保存
        save_generation_data(conn, df, area)

        print(f"\n✓ Successfully imported {len(df)} records to database for area: {area}")

    finally:
        conn.close()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python import_tepco_data.py <csv_file> [area]")
        print("\nExample:")
        print("  python import_tepco_data.py ../ml/data/seed/generation_tokyo_tepco.csv tokyo")
        sys.exit(1)

    csv_file = sys.argv[1]
    area = sys.argv[2] if len(sys.argv) > 2 else "tokyo"

    if not Path(csv_file).exists():
        print(f"Error: File not found: {csv_file}")
        sys.exit(1)

    import_tepco_csv(csv_file, area)
