"""
TEPCOエリア需給実績CSVを自動取得
"""

import pandas as pd
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
import sys
import time
import hashlib


def get_target_year_month():
    """
    現在日時から対象年月（YYYYMM）を取得

    Returns:
        list[str]: 対象年月のリスト（月初3日間は前月も含む）
    """
    now = datetime.now()
    year_months = [now.strftime('%Y%m')]

    # 月初3日間は前月も試行（更新遅延対応）
    if now.day <= 3:
        prev_month = (now - timedelta(days=5)).strftime('%Y%m')
        year_months.append(prev_month)

    return year_months


def fetch_tepco_data(year_month: str, output_file: Path, max_retries=3):
    """
    TEPCOエリア需給実績CSVをダウンロード

    Args:
        year_month: 年月（YYYYMM形式）
        output_file: 出力ファイルパス
        max_retries: 最大リトライ回数

    Returns:
        bool: 成功したらTrue、失敗したらFalse
    """
    base_url = "https://www.tepco.co.jp/forecast/html/images/"
    filename = f"eria_jukyu_{year_month}_03.csv"
    url = f"{base_url}{filename}"

    print(f"Fetching TEPCO data for {year_month}...")
    print(f"URL: {url}")

    for attempt in range(max_retries):
        try:
            # curlでダウンロード（-f: HTTPエラーで失敗, -s: サイレント, -S: エラーは表示）
            result = subprocess.run(
                ['curl', '-f', '-s', '-S', '--connect-timeout', '30', '-o', str(output_file), url],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                # データ検証
                if validate_tepco_csv(output_file):
                    print(f"✓ Successfully downloaded to {output_file}")
                    return True
                else:
                    print(f"⚠ Downloaded file is invalid")
                    return False
            elif result.returncode == 22:  # HTTP 404
                print(f"✗ File not found (404): {url}")
                return False
            else:
                print(f"⚠ Attempt {attempt + 1}/{max_retries} failed (exit code {result.returncode})")
                if result.stderr:
                    print(f"   Error: {result.stderr}")
                time.sleep(2 ** attempt)  # 指数バックオフ: 1秒, 2秒, 4秒

        except subprocess.TimeoutExpired:
            print(f"⚠ Timeout on attempt {attempt + 1}/{max_retries}")
            time.sleep(2 ** attempt)
        except Exception as e:
            print(f"⚠ Error on attempt {attempt + 1}/{max_retries}: {e}")
            time.sleep(2 ** attempt)

    return False


def validate_tepco_csv(file_path: Path):
    """
    TEPCOデータの妥当性を検証

    Args:
        file_path: CSVファイルパス

    Returns:
        bool: 妥当ならTrue、不正ならFalse
    """
    try:
        # ファイルサイズチェック（最低1KB）
        if file_path.stat().st_size < 1024:
            print("✗ File is too small")
            return False

        # 1行目のヘッダーチェック
        with open(file_path, 'r', encoding='utf-8') as f:
            first_line = f.readline()
            if '単位[MW平均]' not in first_line:
                print("✗ Invalid header: '単位[MW平均]' not found")
                return False

        # データ読み込みテスト
        df = pd.read_csv(file_path, skiprows=1)

        # 必須カラムの存在確認
        required_columns = ['DATE', 'TIME', '太陽光発電実績', '風力発電実績']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"✗ Missing required columns: {missing_columns}")
            return False

        # レコード数チェック（最低10レコード）
        if len(df) < 10:
            print(f"✗ Too few records: {len(df)}")
            return False

        print(f"✓ Validation passed: {len(df)} records")
        return True

    except Exception as e:
        print(f"✗ Validation error: {e}")
        return False


def get_file_hash(file_path: Path):
    """
    ファイルのMD5ハッシュを取得

    Args:
        file_path: ファイルパス

    Returns:
        str: MD5ハッシュ（ファイルが存在しない場合はNone）
    """
    if not file_path.exists():
        return None

    md5_hash = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5_hash.update(chunk)

    return md5_hash.hexdigest()


def main():
    """メイン処理"""
    # データディレクトリ
    data_dir = Path(__file__).parent.parent / 'data' / 'seed'
    data_dir.mkdir(parents=True, exist_ok=True)
    output_file = data_dir / 'generation_tokyo_tepco.csv'

    # 既存ファイルのハッシュを保存
    old_hash = get_file_hash(output_file)
    print(f"Old file hash: {old_hash or 'N/A (file does not exist)'}")

    # 対象年月リストを取得
    year_months = get_target_year_month()
    print(f"Target year-months: {year_months}")

    # ダウンロード試行
    success = False
    for ym in year_months:
        if fetch_tepco_data(ym, output_file):
            success = True
            break

    if not success:
        print("\n✗ Failed to fetch TEPCO data")
        sys.exit(1)

    # ハッシュ比較
    new_hash = get_file_hash(output_file)
    print(f"New file hash: {new_hash}")

    if old_hash == new_hash:
        print("\nℹ No changes detected in TEPCO data")
    else:
        print("\n✓ TEPCO data updated successfully")

    # データ統計を表示
    try:
        df = pd.read_csv(output_file, skiprows=1)
        df['timestamp'] = pd.to_datetime(df['DATE'] + ' ' + df['TIME'], format='%Y/%m/%d %H:%M')

        print(f"\nData statistics:")
        print(f"  Records: {len(df)}")
        print(f"  Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        print(f"  Solar range: {df['太陽光発電実績'].min():.0f} - {df['太陽光発電実績'].max():.0f} MW")
        print(f"  Wind range: {df['風力発電実績'].min():.0f} - {df['風力発電実績'].max():.0f} MW")
    except Exception as e:
        print(f"⚠ Could not display statistics: {e}")

    print(f"\n✓ TEPCO data fetch completed!")


if __name__ == '__main__':
    main()
