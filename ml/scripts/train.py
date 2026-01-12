"""
機械学習モデル学習スクリプト

LightGBMを使用して発電量と価格を予測するモデルを学習します。
"""

import pandas as pd
import numpy as np
import lightgbm as lgb
import joblib
from pathlib import Path
from datetime import datetime
import json


def create_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    特徴量を生成

    Args:
        df: 入力DataFrame（timestamp列が必要）

    Returns:
        特徴量が追加されたDataFrame
    """
    df = df.copy()

    # timestampを日時型に変換
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # 時刻特徴（周期性を考慮）
    df['hour'] = df['timestamp'].dt.hour
    df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)

    # 曜日特徴
    df['day_of_week'] = df['timestamp'].dt.dayofweek
    df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)

    # 月特徴（季節性）
    df['month'] = df['timestamp'].dt.month
    df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
    df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)

    # 年間通算日
    df['day_of_year'] = df['timestamp'].dt.dayofyear

    return df


def create_lag_features(df: pd.DataFrame, target_col: str, lags: list = [1, 2, 48, 96]) -> pd.DataFrame:
    """
    Lag特徴量を生成

    Args:
        df: 入力DataFrame
        target_col: ターゲット列名
        lags: ラグのリスト（30分単位）

    Returns:
        Lag特徴量が追加されたDataFrame
    """
    df = df.copy()

    for lag in lags:
        df[f'{target_col}_lag_{lag}'] = df[target_col].shift(lag)

    # 移動平均
    for window in [24, 48]:
        df[f'{target_col}_rolling_mean_{window}'] = df[target_col].rolling(window=window).mean()
        df[f'{target_col}_rolling_std_{window}'] = df[target_col].rolling(window=window).std()

    return df


def train_generation_model():
    """発電量予測モデルを学習"""
    print("=" * 60)
    print("Training Generation Model")
    print("=" * 60)

    # データロード
    data_dir = Path(__file__).parent.parent / 'data' / 'seed'
    df = pd.read_csv(data_dir / 'generation_tokyo_sample.csv')

    print(f"Loaded {len(df)} records")

    # 特徴量生成
    df = create_features(df)
    df = create_lag_features(df, 'total_mw')

    # 欠損値削除
    df = df.dropna()
    print(f"After dropping NaN: {len(df)} records")

    # 学習データ準備
    feature_cols = [
        'hour_sin', 'hour_cos',
        'day_of_week', 'is_weekend',
        'month_sin', 'month_cos',
        'total_mw_lag_1', 'total_mw_lag_2', 'total_mw_lag_48', 'total_mw_lag_96',
        'total_mw_rolling_mean_24', 'total_mw_rolling_std_24',
        'total_mw_rolling_mean_48', 'total_mw_rolling_std_48'
    ]

    X = df[feature_cols]
    y = df['total_mw']

    # 学習データとテストデータに分割（時系列なので単純分割）
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    print(f"Train: {len(X_train)}, Test: {len(X_test)}")

    # LightGBM学習
    params = {
        'objective': 'regression',
        'metric': 'rmse',
        'num_leaves': 31,
        'learning_rate': 0.05,
        'feature_fraction': 0.9,
        'bagging_fraction': 0.8,
        'bagging_freq': 5,
        'verbose': -1
    }

    train_data = lgb.Dataset(X_train, label=y_train)
    test_data = lgb.Dataset(X_test, label=y_test, reference=train_data)

    model = lgb.train(
        params,
        train_data,
        num_boost_round=200,
        valid_sets=[test_data],
        callbacks=[lgb.early_stopping(stopping_rounds=20), lgb.log_evaluation(period=50)]
    )

    # 評価
    y_pred = model.predict(X_test, num_iteration=model.best_iteration)
    rmse = np.sqrt(np.mean((y_test - y_pred) ** 2))
    mae = np.mean(np.abs(y_test - y_pred))
    mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100

    print(f"\nTest Metrics:")
    print(f"  RMSE: {rmse:.2f} MW")
    print(f"  MAE: {mae:.2f} MW")
    print(f"  MAPE: {mape:.2f}%")

    # モデル保存
    model_dir = Path(__file__).parent.parent / 'models'
    model_dir.mkdir(parents=True, exist_ok=True)

    model_path = model_dir / 'generation_tokyo.pkl'
    joblib.dump({
        'model': model,
        'feature_cols': feature_cols,
        'metrics': {'rmse': rmse, 'mae': mae, 'mape': mape},
        'trained_at': datetime.now().isoformat()
    }, model_path)

    print(f"\n✓ Model saved to {model_path}")

    return model, feature_cols


def train_price_model():
    """価格予測モデルを学習"""
    print("\n" + "=" * 60)
    print("Training Price Model")
    print("=" * 60)

    # データロード
    data_dir = Path(__file__).parent.parent / 'data' / 'seed'
    df = pd.read_csv(data_dir / 'price_tokyo_sample.csv')

    print(f"Loaded {len(df)} records")

    # 特徴量生成
    df = create_features(df)
    df = create_lag_features(df, 'price_yen')

    # 欠損値削除
    df = df.dropna()
    print(f"After dropping NaN: {len(df)} records")

    # 学習データ準備
    feature_cols = [
        'hour_sin', 'hour_cos',
        'day_of_week', 'is_weekend',
        'month_sin', 'month_cos',
        'price_yen_lag_1', 'price_yen_lag_2', 'price_yen_lag_48', 'price_yen_lag_96',
        'price_yen_rolling_mean_24', 'price_yen_rolling_std_24',
        'price_yen_rolling_mean_48', 'price_yen_rolling_std_48'
    ]

    X = df[feature_cols]
    y = df['price_yen']

    # 学習データとテストデータに分割
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    print(f"Train: {len(X_train)}, Test: {len(X_test)}")

    # LightGBM学習
    params = {
        'objective': 'regression',
        'metric': 'rmse',
        'num_leaves': 31,
        'learning_rate': 0.05,
        'feature_fraction': 0.9,
        'bagging_fraction': 0.8,
        'bagging_freq': 5,
        'verbose': -1
    }

    train_data = lgb.Dataset(X_train, label=y_train)
    test_data = lgb.Dataset(X_test, label=y_test, reference=train_data)

    model = lgb.train(
        params,
        train_data,
        num_boost_round=200,
        valid_sets=[test_data],
        callbacks=[lgb.early_stopping(stopping_rounds=20), lgb.log_evaluation(period=50)]
    )

    # 評価
    y_pred = model.predict(X_test, num_iteration=model.best_iteration)
    rmse = np.sqrt(np.mean((y_test - y_pred) ** 2))
    mae = np.mean(np.abs(y_test - y_pred))
    mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100

    print(f"\nTest Metrics:")
    print(f"  RMSE: {rmse:.2f} 円/kWh")
    print(f"  MAE: {mae:.2f} 円/kWh")
    print(f"  MAPE: {mape:.2f}%")

    # モデル保存
    model_dir = Path(__file__).parent.parent / 'models'
    model_dir.mkdir(parents=True, exist_ok=True)

    model_path = model_dir / 'price_tokyo.pkl'
    joblib.dump({
        'model': model,
        'feature_cols': feature_cols,
        'metrics': {'rmse': rmse, 'mae': mae, 'mape': mape},
        'trained_at': datetime.now().isoformat()
    }, model_path)

    print(f"\n✓ Model saved to {model_path}")

    return model, feature_cols


if __name__ == '__main__':
    print("Starting model training...")
    print(f"Timestamp: {datetime.now().isoformat()}\n")

    # 発電量モデル学習
    gen_model, gen_features = train_generation_model()

    # 価格モデル学習
    price_model, price_features = train_price_model()

    print("\n" + "=" * 60)
    print("✓ All models trained successfully!")
    print("=" * 60)
