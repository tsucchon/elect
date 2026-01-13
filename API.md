# API仕様書

再エネ発電量＋電力価格予測ダッシュボードのAPI仕様書です。

## 📋 目次

1. [ベース情報](#ベース情報)
2. [認証](#認証)
3. [エンドポイント一覧](#エンドポイント一覧)
4. [データ管理API](#データ管理api)
5. [予測API](#予測api)
6. [ヘルスチェックAPI](#ヘルスチェックapi)
7. [エラーレスポンス](#エラーレスポンス)
8. [データ型定義](#データ型定義)

## ベース情報

### ベースURL

- **開発環境**: `http://localhost:8000`
- **本番環境**: `https://your-app.vercel.app`

### API ドキュメント

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### レスポンス形式

すべてのレスポンスはJSON形式です。

## 認証

現在、認証は実装されていません（デモ用途）。

## エンドポイント一覧

| メソッド | エンドポイント | 説明 |
|---------|--------------|------|
| GET | `/` | API情報取得 |
| GET | `/api/health` | ヘルスチェック |
| POST | `/api/data/upload` | CSVデータアップロード |
| GET | `/api/data/status` | データ状態確認 |
| GET | `/api/predict/latest` | 最新予測取得 |
| GET | `/api/predict/accuracy` | 予測精度取得 |
| GET | `/api/predict/history` | 予測履歴取得 |

---

## データ管理API

### POST /api/data/upload

CSV形式のデータをアップロードして、データベースを更新します。

#### リクエスト

**Content-Type**: `multipart/form-data`

**Form Data**:
- `generation_file` (File, optional): 発電量データCSV（TEPCO形式）
- `price_file` (File, optional): 価格データCSV（JEPX形式）

**発電量CSVフォーマット（TEPCO形式）**:
```csv
単位[MW平均],,,供給力
DATE,TIME,エリア需要,原子力,火力(LNG),火力(石炭),火力(石油),火力(その他),水力,地熱,バイオマス,太陽光発電実績,太陽光出力制御量,風力発電実績,風力出力制御量,揚水,蓄電池,連系線,その他,合計
2026/1/1,0:00,27195,0,11426,6861,415,1729,753,0,449,0,0,98,0,140,0,5190,134,27195
```

**価格CSVフォーマット（JEPX形式）**:
```csv
timestamp,price_yen
2025-10-14 00:00:00,11.27
```

#### レスポンス

**Success (200 OK)**:
```json
{
  "status": "success",
  "message": "データをアップロードしました",
  "uploaded": [
    {
      "type": "generation",
      "filename": "generation_tokyo_demo.csv",
      "rows": 337
    },
    {
      "type": "price",
      "filename": "price_tokyo_demo.csv",
      "rows": 2184
    }
  ]
}
```

**Error (400 Bad Request)**:
```json
{
  "detail": "Required column 'timestamp' not found in generation file"
}
```

#### cURLサンプル

```bash
curl -X POST "http://localhost:8000/api/data/upload" \
  -F "generation_file=@generation_tokyo_demo.csv" \
  -F "price_file=@price_tokyo_demo.csv"
```

---

### GET /api/data/status

データベース内のデータ状態を確認します。

#### リクエスト

パラメータなし

#### レスポンス

**Success (200 OK)**:
```json
{
  "generation": {
    "count": 4321,
    "latest_timestamp": "2026-01-12 08:53:00"
  },
  "price": {
    "count": 4368,
    "latest_timestamp": "2026-01-12 23:30:00"
  }
}
```

#### cURLサンプル

```bash
curl http://localhost:8000/api/data/status
```

---

## 予測API

### GET /api/predict/latest

次のN時間の発電量と価格の予測を取得します。

#### リクエスト

**Query Parameters**:
- `area` (string, optional): 対象エリア（デフォルト: `tokyo`）
- `hours` (integer, optional): 予測時間数（デフォルト: `48`）

#### レスポンス

**Success (200 OK)**:
```json
{
  "area": "tokyo",
  "predictions": {
    "generation": [
      {
        "timestamp": "2026-01-13T10:48:09",
        "value": 366.74
      },
      ...
    ],
    "price": [
      {
        "timestamp": "2026-01-13T10:48:09",
        "value": 11.41
      },
      ...
    ]
  },
  "generated_at": "2026-01-13T10:48:09"
}
```

**フィールド説明**:
- `area`: 対象エリア
- `predictions.generation[].value`: 発電量予測値（MW）
- `predictions.price[].value`: 価格予測値（円/kWh）
- `generated_at`: 予測生成時刻（ISO 8601形式）

#### cURLサンプル

```bash
# デフォルト（tokyo、48時間）
curl "http://localhost:8000/api/predict/latest"

# パラメータ指定
curl "http://localhost:8000/api/predict/latest?area=tokyo&hours=24"
```

---

### GET /api/predict/accuracy

過去N日間の予測精度（MAPE）を取得します。

#### リクエスト

**Query Parameters**:
- `area` (string, optional): 対象エリア（デフォルト: `tokyo`）
- `days` (integer, optional): 過去日数（デフォルト: `7`）

#### レスポンス

**Success (200 OK)**:
```json
{
  "area": "tokyo",
  "period_days": 7,
  "generation": {
    "mape": 4.92,
    "rating": "優秀",
    "sample_count": 337
  },
  "price": {
    "mape": 5.08,
    "rating": "良好",
    "sample_count": 337
  },
  "calculated_at": "2026-01-13T10:48:09"
}
```

**フィールド説明**:
- `mape`: 平均絶対パーセント誤差（%）
- `rating`: 評価
  - `< 5%`: "優秀"
  - `< 10%`: "良好"
  - `< 20%`: "普通"
  - `≥ 20%`: "改善が必要"
- `sample_count`: 評価に使用したサンプル数

#### cURLサンプル

```bash
curl "http://localhost:8000/api/predict/accuracy?area=tokyo&days=7"
```

---

### GET /api/predict/history

過去の予測履歴を取得します。

#### リクエスト

**Query Parameters**:
- `area` (string, optional): 対象エリア（デフォルト: `tokyo`）
- `days` (integer, optional): 過去日数（デフォルト: `7`）

#### レスポンス

**Success (200 OK)**:
```json
{
  "area": "tokyo",
  "period_days": 7,
  "generation_history": [
    {
      "timestamp": "2026-01-06T10:00:00",
      "predicted": 450.5,
      "actual": 445.2,
      "error_percentage": 1.19
    },
    ...
  ],
  "price_history": [
    {
      "timestamp": "2026-01-06T10:00:00",
      "predicted": 11.5,
      "actual": 11.2,
      "error_percentage": 2.68
    },
    ...
  ]
}
```

#### cURLサンプル

```bash
curl "http://localhost:8000/api/predict/history?area=tokyo&days=7"
```

---

## ヘルスチェックAPI

### GET /

API情報を取得します。

#### レスポンス

```json
{
  "message": "再エネ発電量＋電力価格予測API"
}
```

---

### GET /api/health

APIのヘルスチェックを行います。

#### レスポンス

**Success (200 OK)**:
```json
{
  "status": "ok",
  "message": "API is running"
}
```

#### cURLサンプル

```bash
curl http://localhost:8000/api/health
```

---

## エラーレスポンス

### 一般的なエラー形式

```json
{
  "detail": "エラーメッセージ"
}
```

### HTTPステータスコード

| コード | 意味 | 説明 |
|-------|------|------|
| 200 | OK | リクエスト成功 |
| 400 | Bad Request | リクエストパラメータが不正 |
| 404 | Not Found | リソースが見つからない |
| 500 | Internal Server Error | サーバー内部エラー |

### エラー例

**400 Bad Request**:
```json
{
  "detail": "Required column 'timestamp' not found in generation file"
}
```

**404 Not Found**:
```json
{
  "detail": "Not Found"
}
```

**500 Internal Server Error**:
```json
{
  "detail": "アップロードに失敗しました: Database is locked"
}
```

---

## データ型定義

### Timestamp

ISO 8601形式の日時文字列

```
2026-01-13T10:48:09
```

### TEPCO CSV形式

東京電力エリア需給実績データの形式

**必須カラム**:
- `DATE`: 日付（YYYY/M/D）
- `TIME`: 時刻（H:MM）
- `太陽光発電実績`: 太陽光発電量（MW）
- `風力発電実績`: 風力発電量（MW）

**1行目**: ヘッダー行（`単位[MW平均],,,供給力`）

### JEPX CSV形式

JEPX スポット市場価格データの形式

**必須カラム**:
- `timestamp`: 日時（YYYY-MM-DD HH:MM:SS）
- `price_yen`: 価格（円/kWh）

---

## レート制限

現在、レート制限は実装されていません。

## CORS設定

開発環境では全オリジンを許可しています。

```python
allow_origins=["*"]
```

本番環境では適切に制限してください。

## 参考リンク

- [Swagger UI](http://localhost:8000/docs) - 対話的なAPI仕様
- [ReDoc](http://localhost:8000/redoc) - きれいなAPI仕様
- [README.md](./README.md) - プロジェクト概要
- [SETUP.md](./SETUP.md) - セットアップガイド
