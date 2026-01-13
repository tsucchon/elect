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

実際のOCCTO（電力広域的運営推進機関）のデータを使用する場合は、**東京電力のエリア需給実績データ形式**でCSVを配置してください。

#### データの入手方法

1. **東京電力エリア需給実績データ**
   - URL: https://www.tepco.co.jp/forecast/html/area_jukyu-j.html
   - 各月のCSVファイルをダウンロード可能（例：`eria_jukyu_202601_03.csv`）

2. **他のエリア**
   - OCCTOの系統情報サービス: https://occtonet3.occto.or.jp/public/dfw/RP11/OCCTO/SD/LOGIN_login
   - メニュー → 需給関連情報 → 供給区域別の供給実績 から各電力会社のページにアクセス

**発電量データ形式（東京電力エリア需給実績）:**
```csv
単位[MW平均],,,供給力
DATE,TIME,エリア需要,原子力,火力(LNG),火力(石炭),火力(石油),火力(その他),水力,地熱,バイオマス,太陽光発電実績,太陽光出力制御量,風力発電実績,風力出力制御量,揚水,蓄電池,連系線,その他,合計
2026/1/1,0:00,27195,0,11426,6861,415,1729,753,0,449,0,0,98,0,140,0,5190,134,27195
2026/1/1,0:30,26147,0,10177,6861,416,1766,755,0,452,0,0,115,0,120,0,5300,186,26148
...
```

**注意事項:**
- 1行目は単位を示すヘッダー行（読み込み時にスキップされます）
- 2行目以降が実際のデータ
- 30分間隔のデータ
- 本システムは主に「太陽光発電実績」と「風力発電実績」を使用して再エネ発電量を予測します

**価格データ（price_tokyo_sample.csv）:**

JEPX（日本卸電力取引所）のスポット市場エリアプライスデータを使用します。

データ取得方法：
```bash
# 発電量データと同じ期間のJEPX価格データを自動取得
python scripts/fetch_jepx_price.py
```

このスクリプトは以下を自動的に実行します：
1. `generation_tokyo_tepco.csv`の期間を確認
2. JEPXの年度CSVをダウンロード（例：`https://www.jepx.jp/market/excel/spot_2025.csv`）
3. 同じ期間の東京エリア価格を抽出して`price_tokyo_sample.csv`に保存

**手動でダウンロードする場合：**
1. https://www.jepx.jp/electricpower/market-data/spot/ にアクセス
2. 「データダウンロード」から年度を選択してダウンロード
3. または直接URL: `https://www.jepx.jp/market/excel/spot_YYYY.csv`（YYYYは年度）

**CSVフォーマット（JEPX）:**
```csv
年月日,時刻コード,売り入札量(kWh),買い入札量(kWh),約定総量(kWh),システムプライス(円/kWh),エリアプライス北海道(円/kWh),エリアプライス東北(円/kWh),エリアプライス東京(円/kWh),...
2025/10/14,1,15558150,15358850,11414250,13.50,15.41,15.41,15.41,...
```
- **時刻コード:** 1～48（30分単位、1=0:00-0:30、2=0:30-1:00、...、48=23:30-24:00）
- **文字コード:** Shift-JIS（スクリプトが自動でUTF-8に変換）
- **エリア別価格:** 北海道、東北、東京、中部、北陸、関西、中国、四国、九州の各エリアプライスが含まれる

**抽出後のフォーマット（price_tokyo_sample.csv）:**
```csv
timestamp,price_yen
2025-10-14 00:00:00,11.27
2025-10-14 00:30:00,11.27
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
