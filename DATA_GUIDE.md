# データ取得ガイド

このプロジェクトで使用する実データの取得方法をまとめています。

## 概要

本システムは以下の2種類のデータを使用します：

1. **発電量データ** - 東京電力のエリア需給実績データ（OCCTO経由）
2. **価格データ** - JEPXのスポット市場エリアプライス

## 1. 発電量データ（東京電力エリア需給実績）

### データソース

**東京エリア:**
- URL: https://www.tepco.co.jp/forecast/html/area_jukyu-j.html
- 各月のCSVファイルをダウンロード可能

**他のエリア:**
- OCCTO系統情報サービス: https://occtonet3.occto.or.jp/public/dfw/RP11/OCCTO/SD/LOGIN_login
- メニュー → 需給関連情報 → 供給区域別の供給実績

### ダウンロード方法

#### 手動ダウンロード

1. 東京電力のエリア需給実績データページにアクセス
2. 必要な月のCSVファイルをダウンロード（例：`eria_jukyu_202601_03.csv`）
3. `ml/data/seed/generation_tokyo_tepco.csv` として保存

#### 直接URL（コマンドライン）

```bash
# 2026年1月のデータをダウンロード
curl -o ml/data/seed/generation_tokyo_tepco.csv \
  "https://www.tepco.co.jp/forecast/html/images/eria_jukyu_202601_03.csv"
```

**URLパターン:**
```
https://www.tepco.co.jp/forecast/html/images/eria_jukyu_YYYYMM_03.csv
```
- `YYYYMM`: 年月（例: 202601 = 2026年1月）

### CSVフォーマット

```csv
単位[MW平均],,,供給力
DATE,TIME,エリア需要,原子力,火力(LNG),火力(石炭),火力(石油),火力(その他),水力,地熱,バイオマス,太陽光発電実績,太陽光出力制御量,風力発電実績,風力出力制御量,揚水,蓄電池,連系線,その他,合計
2026/1/1,0:00,27195,0,11426,6861,415,1729,753,0,449,0,0,98,0,140,0,5190,134,27195
2026/1/1,0:30,26147,0,10177,6861,416,1766,755,0,452,0,0,115,0,120,0,5300,186,26148
```

**主要カラム:**
- `DATE`: 日付（YYYY/M/D形式）
- `TIME`: 時刻（H:MM形式、30分間隔）
- `太陽光発電実績`: 太陽光発電量 [MW]
- `風力発電実績`: 風力発電量 [MW]
- その他の電源別発電量も含まれる

### データインポート

```bash
cd backend
python scripts/import_tepco_data.py ../ml/data/seed/generation_tokyo_tepco.csv tokyo
```

---

## 2. 価格データ（JEPXスポット市場）

### データソース

**JEPX公式サイト:**
- URL: https://www.jepx.jp/electricpower/market-data/spot/
- 「データダウンロード」ボタンから年度を選択

**直接URL:**
```
https://www.jepx.jp/market/excel/spot_YYYY.csv
```
- `YYYY`: 年度（例: 2025 = 2025年度 = 2025/04/01～2026/03/31）

### ダウンロード方法

#### 自動取得（推奨）

発電量データと同じ期間のJEPX価格データを自動取得：

```bash
cd ml
python scripts/fetch_jepx_price.py
```

このスクリプトは：
1. `generation_tokyo_tepco.csv`の期間を自動検出
2. 該当年度のJEPX CSVをダウンロード
3. 同じ期間の東京エリア価格を抽出
4. `price_tokyo_sample.csv`に保存

#### 手動ダウンロード

```bash
# 2025年度のデータをダウンロード
curl -o ml/data/seed/jepx_spot_2025.csv \
  "https://www.jepx.jp/market/excel/spot_2025.csv"

# Shift-JISからUTF-8に変換
iconv -f SHIFT-JIS -t UTF-8 ml/data/seed/jepx_spot_2025.csv \
  > ml/data/seed/jepx_spot_2025_utf8.csv
```

### CSVフォーマット

**元データ（JEPX）:**
```csv
年月日,時刻コード,売り入札量(kWh),買い入札量(kWh),約定総量(kWh),システムプライス(円/kWh),エリアプライス北海道(円/kWh),エリアプライス東北(円/kWh),エリアプライス東京(円/kWh),エリアプライス中部(円/kWh),エリアプライス北陸(円/kWh),エリアプライス関西(円/kWh),エリアプライス中国(円/kWh),エリアプライス四国(円/kWh),エリアプライス九州(円/kWh),...
2025/10/14,1,15558150,15358850,11414250,13.50,15.41,15.41,15.41,11.00,11.00,11.00,11.00,7.81,11.00,...
```

- **時刻コード:** 1～48（30分単位）
  - 1 = 0:00-0:30
  - 2 = 0:30-1:00
  - ...
  - 48 = 23:30-24:00
- **文字コード:** Shift-JIS
- **エリア別価格:** 北海道、東北、東京、中部、北陸、関西、中国、四国、九州

**抽出後（price_tokyo_sample.csv）:**
```csv
timestamp,price_yen
2025-10-14 00:00:00,11.27
2025-10-14 00:30:00,11.27
...
```

### カスタム期間での抽出

`fetch_jepx_price.py`を編集して期間を指定：

```python
# スクリプト内で期間を指定
start_date = '2025-10-01'
end_date = '2025-12-31'
```

または、`extract_area_price()`関数を直接呼び出し：

```python
from scripts.fetch_jepx_price import extract_area_price
from pathlib import Path

extract_area_price(
    jepx_file=Path('data/seed/jepx_spot_2025.csv'),
    area='tokyo',
    start_date='2025-10-01',
    end_date='2025-12-31',
    output_file=Path('data/seed/price_tokyo_custom.csv')
)
```

### データインポート

```bash
cd backend
python scripts/import_price_data.py ../ml/data/seed/price_tokyo_sample.csv tokyo
```

---

## 3. データの確認

### サンプルデータの統計情報

```bash
cd ml
python scripts/fetch_jepx_price.py
```

出力例：
```
Sample data period: 2025-10-14 to 2026-01-12
Loaded 4368 records
Date range: 2025-10-14 00:00:00 to 2026-01-12 23:30:00
Price range: 1.00 - 35.83 円/kWh
Average price: 11.84 円/kWh
```

### データベースの確認

```bash
cd backend
sqlite3 /tmp/elect.db "SELECT COUNT(*) FROM generation_actual;"
sqlite3 /tmp/elect.db "SELECT COUNT(*) FROM price_actual;"
```

---

## 4. データ更新フロー

### 定期的なデータ更新手順

1. **最新の発電量データをダウンロード**
   ```bash
   # 現在の月のデータを取得（例: 2026年1月）
   curl -o ml/data/seed/generation_tokyo_latest.csv \
     "https://www.tepco.co.jp/forecast/html/images/eria_jukyu_202601_03.csv"
   ```

2. **対応する価格データを取得**
   ```bash
   cd ml
   python scripts/fetch_jepx_price.py
   ```

3. **データベースにインポート**
   ```bash
   cd backend
   python scripts/import_tepco_data.py ../ml/data/seed/generation_tokyo_latest.csv tokyo
   python scripts/import_price_data.py ../ml/data/seed/price_tokyo_sample.csv tokyo
   ```

4. **モデル再学習**
   ```bash
   cd ml
   python scripts/train.py
   ```

---

## 5. 他のエリアのデータ取得

### 北海道エリアの例

```bash
# 1. 発電量データ（北海道電力ネットワーク経由）
# OCCTOの系統情報サービスからアクセス

# 2. 価格データ（JEPX）
cd ml
python scripts/fetch_jepx_price.py --area hokkaido

# 3. インポート
cd backend
python scripts/import_tepco_data.py ../ml/data/seed/generation_hokkaido.csv hokkaido
python scripts/import_price_data.py ../ml/data/seed/price_hokkaido_sample.csv hokkaido
```

**対応エリア:**
- `tokyo` - 東京
- `hokkaido` - 北海道
- `tohoku` - 東北
- `chubu` - 中部
- `hokuriku` - 北陸
- `kansai` - 関西
- `chugoku` - 中国
- `shikoku` - 四国
- `kyushu` - 九州

---

## トラブルシューティング

### JEPXデータのダウンロードエラー

**エラー:** `curl: (22) The requested URL returned error: 404`

**原因:** 指定年度のデータがまだ公開されていない

**解決策:** 前年度のデータを使用するか、公開を待つ

### 文字コードエラー

**エラー:** `UnicodeDecodeError: 'utf-8' codec can't decode`

**原因:** JEPXのCSVはShift-JISエンコーディング

**解決策:** スクリプトは自動で変換しますが、手動の場合は：
```bash
iconv -f SHIFT-JIS -t UTF-8 input.csv > output.csv
```

### 期間の不一致

**エラー:** 発電量データと価格データの期間が合わない

**解決策:** `fetch_jepx_price.py`は自動で期間を合わせますが、手動の場合は開始日・終了日を確認

---

## 参考リンク

### 発電量データ
- [東京電力エリア需給実績データ](https://www.tepco.co.jp/forecast/html/area_jukyu-j.html)
- [OCCTO系統情報サービス](https://occtonet3.occto.or.jp/public/dfw/RP11/OCCTO/SD/LOGIN_login)

### 価格データ
- [JEPXスポット市場](https://www.jepx.jp/electricpower/market-data/spot/)
- [JEPX取引概要](https://www.jepx.jp/electricpower/outline/)

### 技術記事
- [JEPXが公開する電力市場価格のCSVをLambdaで整形してみた](https://dev.classmethod.jp/articles/jepx-spot-csv-etl-lambda/)
- [日本卸電力取引所の電力市場価格CSVを整形してGoogle Cloud Firestoreにアップロードした話](https://qiita.com/darshu/items/71f98eed279c1ca0c8dd)
