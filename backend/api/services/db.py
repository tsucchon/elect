import sqlite3
import shutil
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

DB_PATH = "/tmp/elect.db"
SCHEMA_PATH = Path(__file__).parent.parent.parent / "db" / "schema.sql"

def init_database():
    """起動時にDBを初期化"""
    db_file = Path(DB_PATH)

    if not db_file.exists():
        logger.info("Initializing database at /tmp/elect.db")

        # スキーマから作成
        conn = sqlite3.connect(DB_PATH)
        try:
            with open(SCHEMA_PATH) as f:
                conn.executescript(f.read())
            logger.info("Database schema created successfully")
        except Exception as e:
            logger.error(f"Failed to create database: {e}")
            raise
        finally:
            conn.close()
    else:
        logger.info("Database already exists at /tmp/elect.db")

def get_db():
    """DB接続取得"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 辞書形式でアクセス可能に
    return conn


# CRUD操作

def clear_generation_data(conn, area: str = "tokyo"):
    """発電量データを削除"""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM generation_actual WHERE area = ?", (area,))
    conn.commit()
    logger.info(f"Cleared generation data for area: {area}")


def save_generation_data(conn, df, area: str = "tokyo"):
    """発電量データをDBに保存（東京電力形式対応）"""
    cursor = conn.cursor()

    for _, row in df.iterrows():
        # pandasのTimestamp型を文字列に変換
        timestamp_str = row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')

        # 東京電力形式の場合
        if '太陽光発電実績' in row:
            pv_mw = row.get('太陽光発電実績', 0)
            wind_mw = row.get('風力発電実績', 0)
            total_mw = pv_mw + wind_mw
        else:
            # 旧形式の場合
            pv_mw = row.get('pv_mw', 0)
            wind_mw = row.get('wind_mw', 0)
            total_mw = row.get('total_mw', row.get('renewable_total_mw', pv_mw + wind_mw))

        cursor.execute("""
            INSERT INTO generation_actual (area, timestamp, pv_mw, wind_mw, total_mw)
            VALUES (?, ?, ?, ?, ?)
        """, (
            area,
            timestamp_str,
            pv_mw,
            wind_mw,
            total_mw
        ))

    conn.commit()
    logger.info(f"Saved {len(df)} generation records for area: {area}")


def clear_price_data(conn, area: str = "tokyo"):
    """価格データを削除"""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM price_actual WHERE area = ?", (area,))
    conn.commit()
    logger.info(f"Cleared price data for area: {area}")


def save_price_data(conn, df, area: str = "tokyo"):
    """価格データをDBに保存"""
    cursor = conn.cursor()

    for _, row in df.iterrows():
        # pandasのTimestamp型を文字列に変換
        timestamp_str = row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute("""
            INSERT INTO price_actual (area, timestamp, price_yen)
            VALUES (?, ?, ?)
        """, (
            area,
            timestamp_str,
            row.get('price_yen', 0)
        ))

    conn.commit()
    logger.info(f"Saved {len(df)} price records for area: {area}")


def get_generation_data(conn, area: str = "tokyo", limit: int = 1000):
    """発電量データを取得"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT area, timestamp, pv_mw, wind_mw, total_mw,
               pv_mw as '太陽光発電実績',
               wind_mw as '風力発電実績',
               total_mw as renewable_total_mw
        FROM generation_actual
        WHERE area = ?
        ORDER BY timestamp DESC
        LIMIT ?
    """, (area, limit))

    return cursor.fetchall()


def get_price_data(conn, area: str = "tokyo", limit: int = 1000):
    """価格データを取得"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT area, timestamp, price_yen
        FROM price_actual
        WHERE area = ?
        ORDER BY timestamp DESC
        LIMIT ?
    """, (area, limit))

    return cursor.fetchall()


def clear_predictions(conn, area: str = "tokyo", target_type: str = None):
    """予測データを削除"""
    cursor = conn.cursor()
    if target_type:
        cursor.execute("DELETE FROM predictions WHERE area = ? AND target_type = ?", (area, target_type))
        logger.info(f"Cleared {target_type} predictions for area: {area}")
    else:
        cursor.execute("DELETE FROM predictions WHERE area = ?", (area,))
        logger.info(f"Cleared all predictions for area: {area}")
    conn.commit()


def save_predictions(conn, area: str, target_type: str, predictions: list):
    """予測結果を保存"""
    cursor = conn.cursor()

    for pred in predictions:
        # actual_value がある場合は一緒に保存
        actual_value = pred.get('actual', None)

        cursor.execute("""
            INSERT INTO predictions (area, target_type, forecast_timestamp, predicted_value, actual_value)
            VALUES (?, ?, ?, ?, ?)
        """, (
            area,
            target_type,
            pred['timestamp'],
            pred['value'],
            actual_value
        ))

    conn.commit()
    logger.info(f"Saved {len(predictions)} {target_type} predictions for area: {area}")


def get_predictions(conn, area: str = "tokyo", days: int = 7):
    """予測データを取得"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT area, target_type, forecast_timestamp, predicted_value, actual_value, created_at
        FROM predictions
        WHERE area = ?
        AND created_at >= datetime('now', '-' || ? || ' days')
        ORDER BY forecast_timestamp DESC
    """, (area, days))

    return cursor.fetchall()


def calculate_mape(conn, target_type: str, area: str = "tokyo", days: int = 7):
    """MAPE（平均絶対パーセント誤差）を計算"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT predicted_value, actual_value
        FROM predictions
        WHERE area = ?
        AND target_type = ?
        AND actual_value IS NOT NULL
        AND created_at >= datetime('now', '-' || ? || ' days')
    """, (area, target_type, days))

    rows = cursor.fetchall()

    if not rows:
        return None

    total_error = 0
    count = 0

    for row in rows:
        predicted = row['predicted_value']
        actual = row['actual_value']

        if actual != 0:
            error = abs((actual - predicted) / actual)
            total_error += error
            count += 1

    if count == 0:
        return None

    mape = (total_error / count) * 100
    return round(mape, 2)
