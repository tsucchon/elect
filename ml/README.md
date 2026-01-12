# 機械学習モデル学習ガイド

このディレクトリには、再エネ発電量と電力価格を予測するLightGBMモデルの学習スクリプトが含まれています。

## セットアップ

### 1. Python仮想環境の作成

```bash
cd ml
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

## データ準備

### サンプルデータ生成

```bash
python scripts/generate_sample_data.py
```

これにより、以下のファイルが生成されます：
- `data/seed/generation_tokyo_sample.csv` - 発電量データ（90日分、4,321レコード）
- `data/seed/price_tokyo_sample.csv` - 価格データ（90日分、4,321レコード）

### 実データの配置

実際のOCCTO/JEPXデータを使用する場合は、以下の形式でCSVを配置してください：

**発電量データ（generation_tokyo_sample.csv）:**
```csv
timestamp,pv_mw,wind_mw,total_mw
2024-01-01 00:00:00,0,250.5,250.5
2024-01-01 00:30:00,0,245.2,245.2
...
```

**価格データ（price_tokyo_sample.csv）:**
```csv
timestamp,price_yen
2024-01-01 00:00:00,8.5
2024-01-01 00:30:00,8.2
...
```

## モデル学習

### 学習実行

```bash
python scripts/train.py
```

学習が完了すると、以下のモデルが生成されます：
- `models/generation_tokyo.pkl` - 発電量予測モデル
- `models/price_tokyo.pkl` - 価格予測モデル

### 学習結果

学習スクリプトは以下のメトリクスを出力します：
- **RMSE** (Root Mean Square Error): 二乗平均平方根誤差
- **MAE** (Mean Absolute Error): 平均絶対誤差
- **MAPE** (Mean Absolute Percentage Error): 平均絶対パーセント誤差

例：
```
Training Generation Model
============================================================
Loaded 4321 records
After dropping NaN: 4225 records
Train: 3380, Test: 845

[LightGBM] [Info] ...
[LightGBM] [Info] ...

Test Metrics:
  RMSE: 85.42 MW
  MAE: 62.15 MW
  MAPE: 8.23%

✓ Model saved to models/generation_tokyo.pkl
```

## モデル構造

### 特徴量

学習に使用される特徴量：

**時刻特徴:**
- `hour_sin`, `hour_cos` - 時刻の周期性（24時間）
- `day_of_week` - 曜日（0=月曜、6=日曜）
- `is_weekend` - 週末フラグ
- `month_sin`, `month_cos` - 月の周期性（季節性）

**Lag特徴（過去の値）:**
- `{target}_lag_1` - 30分前
- `{target}_lag_2` - 1時間前
- `{target}_lag_48` - 24時間前
- `{target}_lag_96` - 48時間前

**移動統計量:**
- `{target}_rolling_mean_24` - 過去12時間の平均
- `{target}_rolling_std_24` - 過去12時間の標準偏差
- `{target}_rolling_mean_48` - 過去24時間の平均
- `{target}_rolling_std_48` - 過去24時間の標準偏差

### ハイパーパラメータ

```python
params = {
    'objective': 'regression',
    'metric': 'rmse',
    'num_leaves': 31,
    'learning_rate': 0.05,
    'feature_fraction': 0.9,
    'bagging_fraction': 0.8,
    'bagging_freq': 5
}
```

## トラブルシューティング

### モジュールが見つからないエラー

```
ModuleNotFoundError: No module named 'pandas'
```

→ 仮想環境がアクティブか確認し、`pip install -r requirements.txt`を実行

### データが少なすぎるエラー

```
ValueError: Not enough data for lag features
```

→ 少なくとも100レコード（約2日分）のデータが必要です

### モデルが読み込めないエラー

バックエンド起動時：
```
WARNING: Generation model not found
```

→ `python scripts/train.py`を実行してモデルを生成してください

## 次のステップ

モデル学習が完了したら、バックエンドを起動して予測APIを使用できます：

```bash
cd ../backend
uvicorn api.main:app --reload
```

予測エンドポイント：
- `GET /api/predict/latest` - 次の48時間の予測
- `GET /api/predict/accuracy` - 過去7日間の精度
- `GET /api/predict/history` - 予測履歴
