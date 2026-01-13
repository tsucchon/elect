# 詳細セットアップガイド

このガイドでは、開発環境のセットアップから初回起動までの手順を詳しく説明します。

## 📋 目次

1. [前提条件](#前提条件)
2. [環境構築](#環境構築)
3. [データ準備](#データ準備)
4. [モデル学習](#モデル学習)
5. [アプリケーション起動](#アプリケーション起動)
6. [動作確認](#動作確認)
7. [トラブルシューティング](#トラブルシューティング)

## 前提条件

### 必須

- **Node.js**: 18.0.0 以上
- **Python**: 3.9 以上（3.14 対応済み）
- **npm**: Node.jsに同梱
- **Git**: バージョン管理用

### 推奨

- **VS Code**: 開発エディタ
- **Postman**: API テスト用（オプション）
- **SQLite Browser**: データベース確認用（オプション）

### バージョン確認

```bash
node --version   # v18.0.0 以上
python3 --version # 3.9 以上
npm --version
git --version
```

## 環境構築

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd elect
```

### 2. プロジェクト構造の確認

```
elect/
├── frontend/           # React フロントエンド
├── backend/           # FastAPI バックエンド
├── ml/                # 機械学習
├── DATA_GUIDE.md      # データ取得ガイド
├── README.md          # メインドキュメント
└── SETUP.md           # このファイル
```

## データ準備

### オプション A: 実データを使用（推奨）

実際の東京電力とJEPXのデータを使用します。

#### 1. 発電量データ（東京電力エリア需給実績）

**手動ダウンロード:**
1. https://www.tepco.co.jp/forecast/html/area_jukyu-j.html にアクセス
2. 最新月のCSVをダウンロード
3. `ml/data/seed/generation_tokyo_tepco.csv` として保存

**コマンドラインでダウンロード:**
```bash
cd ml

# 2026年1月のデータをダウンロード
curl -o data/seed/generation_tokyo_tepco.csv \
  "https://www.tepco.co.jp/forecast/html/images/eria_jukyu_202601_03.csv"
```

#### 2. 価格データ（JEPXスポット市場）

**自動取得（推奨）:**
```bash
cd ml

# Python仮想環境を作成・起動
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存パッケージをインストール
pip install -r requirements.txt

# JEPX価格データを自動取得
# 発電量データと同じ期間のデータを自動抽出
python scripts/fetch_jepx_price.py
```

このスクリプトは以下を自動実行します：
- `generation_tokyo_tepco.csv` の期間を検出
- JEPXの年度CSVをダウンロード
- 同じ期間の東京エリア価格を抽出
- `data/seed/price_tokyo_sample.csv` に保存

**手動ダウンロード:**
1. https://www.jepx.jp/electricpower/market-data/spot/ にアクセス
2. 「データダウンロード」から年度を選択
3. Shift-JISからUTF-8に変換して保存

詳細は [DATA_GUIDE.md](./DATA_GUIDE.md) を参照してください。

### オプション B: サンプルデータを使用

テスト用のサンプルデータを生成します。

```bash
cd ml
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# サンプルデータ生成
python scripts/generate_sample_data.py
```

生成されるファイル：
- `data/seed/generation_tokyo_sample.csv` - 90日分の発電量データ
- `data/seed/price_tokyo_sample.csv` - 90日分の価格データ

## モデル学習

### 1. ML環境のセットアップ

```bash
cd ml

# 仮想環境作成（未作成の場合）
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存パッケージインストール
pip install -r requirements.txt
```

### 2. モデル学習の実行

```bash
# モデル学習（5-10分程度）
python scripts/train.py
```

**出力例:**
```
Training Generation Model (Renewable Energy)
============================================================
Loaded 4321 records
After dropping NaN: 4225 records
Train: 3380, Test: 845

Test Metrics:
  RMSE: 117.29 MW
  MAE: 94.19 MW
  MAPE: 27.90%

✓ Model saved to models/generation_tokyo.pkl

Training Price Model
============================================================
Loaded 4368 records
After dropping NaN: 4272 records
Train: 3417, Test: 855

Test Metrics:
  RMSE: 1.05 円/kWh
  MAE: 0.57 円/kWh
  MAPE: 5.17%

✓ Model saved to models/price_tokyo.pkl
```

### 3. 生成されるファイル

```
ml/models/
├── generation_tokyo.pkl          # 発電量予測モデル
├── generation_tokyo.metadata.pkl # メタデータ
├── price_tokyo.pkl               # 価格予測モデル
└── price_tokyo.metadata.pkl      # メタデータ
```

## アプリケーション起動

### 1. バックエンド（FastAPI）

**新しいターミナルを開いて:**

```bash
cd backend

# 仮想環境作成（mlと別）
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存パッケージインストール
pip install -r requirements.txt

# データベース初期化とデータインポート
python scripts/import_tepco_data.py ../ml/data/seed/generation_tokyo_tepco.csv tokyo
python scripts/import_price_data.py ../ml/data/seed/price_tokyo_sample.csv tokyo

# サーバー起動
uvicorn api.main:app --reload
```

**起動確認:**
- バックエンド: http://localhost:8000
- API ドキュメント: http://localhost:8000/docs
- ヘルスチェック: http://localhost:8000/api/health

### 2. フロントエンド（React + Vite）

**新しいターミナルを開いて:**

```bash
cd frontend

# 依存パッケージインストール
npm install

# 開発サーバー起動
npm run dev
```

**起動確認:**
- フロントエンド: http://localhost:3000

## 動作確認

### 1. ブラウザでアクセス

http://localhost:3000 にアクセスして、以下を確認：

- ✅ ダッシュボードが表示される
- ✅ API ステータスが "ok" と表示される
- ✅ 48時間予測グラフが表示される
- ✅ MAPE（精度指標）が表示される

### 2. APIの動作確認

```bash
# ヘルスチェック
curl http://localhost:8000/api/health

# データ状態確認
curl http://localhost:8000/api/data/status

# 予測取得
curl http://localhost:8000/api/predict/latest?area=tokyo&hours=48
```

### 3. CSVアップロードのテスト

1. ブラウザで http://localhost:3000 にアクセス
2. 「CSVデータアップロード」セクションを見つける
3. 発電量データ: `ml/data/seed/generation_tokyo_tepco.csv` を選択
4. 価格データ: `ml/data/seed/price_tokyo_sample.csv` を選択
5. 「アップロード」ボタンをクリック
6. 予測グラフとMAPEが更新されることを確認

## トラブルシューティング

### Python仮想環境の問題

**症状:** `ModuleNotFoundError`

**解決策:**
```bash
# 仮想環境が有効化されているか確認
which python  # venv内のpythonを指しているべき

# 依存パッケージを再インストール
pip install -r requirements.txt
```

### ポート競合

**症状:** `Address already in use`

**解決策:**
```bash
# 使用中のポートを確認
lsof -i :8000  # バックエンド
lsof -i :3000  # フロントエンド

# プロセスを終了
kill -9 <PID>
```

### モデルファイルが見つからない

**症状:** `Generation model not found`

**解決策:**
```bash
cd ml
source venv/bin/activate
python scripts/train.py

# モデルファイルの存在確認
ls -la models/*.pkl
```

### データベースが空

**症状:** データが表示されない、レコード数が0

**解決策:**
```bash
cd backend
source venv/bin/activate

# データを再インポート
python scripts/import_tepco_data.py ../ml/data/seed/generation_tokyo_tepco.csv tokyo
python scripts/import_price_data.py ../ml/data/seed/price_tokyo_sample.csv tokyo

# 確認
sqlite3 /tmp/elect.db "SELECT COUNT(*) FROM generation_actual;"
```

### CORSエラー

**症状:** `Access to fetch has been blocked by CORS policy`

**原因:** バックエンドが起動していない、または異なるポートで起動している

**解決策:**
1. バックエンドが http://localhost:8000 で起動していることを確認
2. `backend/api/main.py` のCORS設定を確認
3. ブラウザのキャッシュをクリア

## 次のステップ

セットアップが完了したら：

1. **開発**: コードを修正して機能追加
2. **テスト**: 異なるデータセットでテスト
3. **デプロイ**: Vercelへのデプロイ（[DEPLOYMENT.md](./DEPLOYMENT.md) 参照）

## 参考資料

- [README.md](./README.md) - プロジェクト概要
- [DATA_GUIDE.md](./DATA_GUIDE.md) - データ取得詳細
- [ml/README.md](./ml/README.md) - モデル学習詳細
- [API Documentation](http://localhost:8000/docs) - FastAPI Swagger UI
