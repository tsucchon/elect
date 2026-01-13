from fastapi import APIRouter, UploadFile, File, HTTPException
import pandas as pd
import numpy as np
import io
import logging
from ..services.db import (
    get_db,
    save_generation_data,
    save_price_data,
    save_predictions,
    clear_generation_data,
    clear_price_data,
    clear_predictions
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/data", tags=["data"])


@router.post("/upload")
async def upload_csv(
    generation_file: UploadFile = File(None),
    price_file: UploadFile = File(None)
):
    """
    CSV一括アップロード

    Args:
        generation_file: 発電量CSVファイル
        price_file: 価格CSVファイル

    Returns:
        アップロード結果
    """
    try:
        db = get_db()
        uploaded_files = []

        # 古いデータをクリア
        if generation_file:
            clear_generation_data(db, area="tokyo")
            clear_predictions(db, area="tokyo", target_type="generation")

        if price_file:
            clear_price_data(db, area="tokyo")
            clear_predictions(db, area="tokyo", target_type="price")

        if generation_file:
            # CSVファイルを読み込み
            content = await generation_file.read()

            # まず最初の行を確認してTEPCO形式かどうか判定
            first_line = content.decode('utf-8').split('\n')[0]
            is_tepco_format = '単位[MW平均]' in first_line or 'DATE' in first_line

            if is_tepco_format and '単位[MW平均]' in first_line:
                # TEPCO形式で1行目がヘッダー行の場合、スキップして読み込み
                df = pd.read_csv(io.BytesIO(content), skiprows=1)
                logger.info(f"Detected TEPCO format CSV with header row (skiprows=1)")
            elif is_tepco_format:
                # TEPCO形式だがヘッダー行がない場合
                df = pd.read_csv(io.BytesIO(content))
                logger.info(f"Detected TEPCO format CSV without header row")
            else:
                # 旧形式
                df = pd.read_csv(io.BytesIO(content))
                logger.info(f"Detected old format CSV")

            # TEPCO形式かどうかを再判定
            is_tepco_format = 'DATE' in df.columns and 'TIME' in df.columns

            if is_tepco_format:

                # timestampを作成
                df['timestamp'] = pd.to_datetime(df['DATE'] + ' ' + df['TIME'], format='%Y/%m/%d %H:%M')

                # 再エネ合計を計算
                df['total_mw'] = df['太陽光発電実績'].astype(float) + df['風力発電実績'].astype(float)
                df['pv_mw'] = df['太陽光発電実績'].astype(float)
                df['wind_mw'] = df['風力発電実績'].astype(float)

                logger.info(f"Detected TEPCO format CSV")
            else:
                # 旧形式の場合
                # データ検証
                required_columns = ['timestamp']
                for col in required_columns:
                    if col not in df.columns:
                        raise ValueError(f"Required column '{col}' not found in generation file")

                # timestampを日時型に変換
                df['timestamp'] = pd.to_datetime(df['timestamp'])

                # 必要なカラムがない場合はデフォルト値を設定
                if 'total_mw' not in df.columns:
                    df['total_mw'] = df.get('pv_mw', 0) + df.get('wind_mw', 0)

            # DBに保存
            save_generation_data(db, df, area="tokyo")
            uploaded_files.append({
                "type": "generation",
                "filename": generation_file.filename,
                "rows": len(df)
            })

            # デモ用: 仮想的な予測データを生成してMAPE計算を可能にする
            # 実績値に5-10%のランダムノイズを加えたものを予測値として保存
            virtual_predictions = []
            for _, row in df.iterrows():
                noise_factor = np.random.uniform(0.9, 1.1)  # ±10%のノイズ
                predicted_value = row['total_mw'] * noise_factor

                virtual_predictions.append({
                    'timestamp': row['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                    'value': float(predicted_value),
                    'actual': float(row['total_mw'])
                })

            # 予測データを保存（actual_valueも同時に保存）
            save_predictions(db, "tokyo", "generation", virtual_predictions)

            logger.info(f"Uploaded generation file: {generation_file.filename} ({len(df)} rows)")
            logger.info(f"Generated {len(virtual_predictions)} virtual predictions for MAPE calculation")

        if price_file:
            # CSVファイルを読み込み
            content = await price_file.read()
            df = pd.read_csv(io.BytesIO(content))

            # データ検証
            required_columns = ['timestamp', 'price_yen']
            for col in required_columns:
                if col not in df.columns:
                    raise ValueError(f"Required column '{col}' not found in price file")

            # timestampを日時型に変換
            df['timestamp'] = pd.to_datetime(df['timestamp'])

            # DBに保存
            save_price_data(db, df, area="tokyo")
            uploaded_files.append({
                "type": "price",
                "filename": price_file.filename,
                "rows": len(df)
            })

            # デモ用: 仮想的な予測データを生成してMAPE計算を可能にする
            virtual_predictions = []
            for _, row in df.iterrows():
                noise_factor = np.random.uniform(0.9, 1.1)  # ±10%のノイズ
                predicted_value = row['price_yen'] * noise_factor

                virtual_predictions.append({
                    'timestamp': row['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                    'value': float(predicted_value),
                    'actual': float(row['price_yen'])
                })

            # 予測データを保存（actual_valueも同時に保存）
            save_predictions(db, "tokyo", "price", virtual_predictions)

            logger.info(f"Uploaded price file: {price_file.filename} ({len(df)} rows)")
            logger.info(f"Generated {len(virtual_predictions)} virtual predictions for MAPE calculation")

        db.close()

        if not uploaded_files:
            raise HTTPException(status_code=400, detail="No files uploaded")

        return {
            "status": "success",
            "message": "データをアップロードしました",
            "uploaded": uploaded_files
        }

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"アップロードに失敗しました: {str(e)}")


@router.get("/status")
async def get_data_status():
    """
    データ更新状態を確認

    Returns:
        データ統計情報
    """
    try:
        db = get_db()
        cursor = db.cursor()

        # 発電量データの件数
        cursor.execute("SELECT COUNT(*) as count FROM generation_actual")
        generation_count = cursor.fetchone()['count']

        # 価格データの件数
        cursor.execute("SELECT COUNT(*) as count FROM price_actual")
        price_count = cursor.fetchone()['count']

        # 最新のタイムスタンプ
        cursor.execute("""
            SELECT MAX(timestamp) as latest
            FROM generation_actual
        """)
        latest_generation = cursor.fetchone()['latest']

        cursor.execute("""
            SELECT MAX(timestamp) as latest
            FROM price_actual
        """)
        latest_price = cursor.fetchone()['latest']

        db.close()

        return {
            "generation": {
                "count": generation_count,
                "latest_timestamp": latest_generation
            },
            "price": {
                "count": price_count,
                "latest_timestamp": latest_price
            }
        }

    except Exception as e:
        logger.error(f"Failed to get data status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
