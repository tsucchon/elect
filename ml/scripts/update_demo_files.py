"""
デモファイルを実際のJEPXデータに置き換え
"""

import pandas as pd
from pathlib import Path
import shutil

def update_demo_files():
    """
    デモファイルを実際のJEPXデータで更新
    """
    # ソースファイル
    data_dir = Path(__file__).parent.parent / 'data' / 'seed'
    price_source = data_dir / 'price_tokyo_sample.csv'

    # デモファイルの場所
    root_dir = Path(__file__).parent.parent.parent
    demo_files = [
        root_dir / 'price_tokyo_demo.csv',
        root_dir / 'price_tokyo_demo2.csv'
    ]

    if not price_source.exists():
        print(f"Error: Source file not found: {price_source}")
        print("Please run 'python scripts/fetch_jepx_price.py' first")
        return

    # ソースデータを読み込み
    df_source = pd.read_csv(price_source)
    print(f"Loaded {len(df_source)} records from {price_source.name}")
    print(f"Date range: {df_source['timestamp'].min()} to {df_source['timestamp'].max()}")

    # デモファイルごとに異なる期間を抽出
    for i, demo_file in enumerate(demo_files):
        # バックアップ
        if demo_file.exists():
            backup_file = demo_file.with_suffix('.csv.bak')
            shutil.copy(demo_file, backup_file)
            print(f"\nBackup created: {backup_file}")

        # 期間を分割（デモ1: 前半、デモ2: 後半）
        if i == 0:
            # 前半のデータ
            df_demo = df_source.iloc[:len(df_source)//2].copy()
        else:
            # 後半のデータ
            df_demo = df_source.iloc[len(df_source)//2:].copy()

        # 保存
        df_demo.to_csv(demo_file, index=False)

        print(f"\n✓ Updated: {demo_file}")
        print(f"  Records: {len(df_demo)}")
        print(f"  Date range: {df_demo['timestamp'].min()} to {df_demo['timestamp'].max()}")
        print(f"  Price range: {df_demo['price_yen'].min():.2f} - {df_demo['price_yen'].max():.2f} 円/kWh")
        print(f"  Average: {df_demo['price_yen'].mean():.2f} 円/kWh")


if __name__ == '__main__':
    print("Updating demo files with real JEPX data...")
    print("=" * 60)
    update_demo_files()
    print("\n" + "=" * 60)
    print("✓ Demo files updated successfully!")
    print("\nNote: Original files backed up with .bak extension")
