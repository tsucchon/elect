# 再エネ発電量＋電力価格 短期予測ダッシュボード

東京電力エリアの発電量データ（TEPCO形式）とJEPX価格データ、Open-Meteo気象予報を使用して、次の48時間の再エネ発電量とスポット価格を予測するダッシュボードアプリケーション。

## 特徴

- 📈 **48時間予測**: 再エネ発電量（太陽光+風力）と電力価格の短期予測
- 🎯 **高精度**: MAPE 5%以下の優秀な予測精度
- 📊 **インタラクティブグラフ**: Rechartsによる見やすい2軸グラフ表示
- 📁 **実データ対応**: 東京電力エリア需給実績（TEPCO形式）とJEPXスポット価格に対応
- 🔄 **自動データ更新**: CSVアップロード時に予測とMAPEを自動再計算
- 🌍 **拡張性**: 複数エリア対応可能な設計（現在は東京専用）
- 🚀 **Vercel デプロイ**: SQLiteのみでシンプルなデプロイ

## アーキテクチャ

- **フロントエンド**: React + Vite + TypeScript + Recharts
- **バックエンド**: FastAPI (Python 3.9+ / 3.14対応)
- **データベース**: SQLite (Vercel /tmp - ephemeral)
- **機械学習**: LightGBM (時系列特徴量 + Lag特徴量)
- **気象API**: Open-Meteo (無料)
- **デプロイ**: Vercel

## セットアップ

### 前提条件

- Node.js 18+
- Python 3.9+ (Python 3.14対応済み)
- npm または yarn

### 1. リポジトリをクローン

```bash
git clone <repository-url>
cd elect
```

### 2. データ準備

**実データを使用する場合（推奨）:**

データ取得方法の詳細は [DATA_GUIDE.md](./DATA_GUIDE.md) を参照してください。

```bash
cd ml

# 1. 東京電力エリア需給実績データを取得
curl -o data/seed/generation_tokyo_tepco.csv \
  "https://www.tepco.co.jp/forecast/html/images/eria_jukyu_202601_03.csv"

# 2. JEPX価格データを自動取得
python scripts/fetch_jepx_price.py
```

**サンプルデータを使用する場合:**

```bash
cd ml
python scripts/generate_sample_data.py
```

### 3. 機械学習モデルの学習（最初に必須）

```bash
cd ml

# 仮想環境作成
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存パッケージインストール
pip install -r requirements.txt

# モデル学習（5-10分程度）
python scripts/train.py
```

学習が完了すると、`ml/models/` に以下のファイルが生成されます：
- `generation_tokyo.pkl` - 発電量予測モデル（RMSE: ~117 MW, MAPE: ~28%）
- `price_tokyo.pkl` - 価格予測モデル（RMSE: ~1.05 円/kWh, MAPE: ~5%）

### 4. バックエンド起動

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

→ バックエンドが http://localhost:8000 で起動
→ API ドキュメント: http://localhost:8000/docs

### 5. フロントエンド起動

別のターミナルで：

```bash
cd frontend

# 依存パッケージインストール
npm install

# 開発サーバー起動
npm run dev
```

→ フロントエンドが http://localhost:3000 で起動

### 6. ブラウザでアクセス

http://localhost:3000 にアクセスして、ダッシュボードを確認

## 使い方

### 1. 初期状態での予測

アプリを起動すると、サンプルデータに基づいた初期予測が表示されます。

### 2. CSVデータのアップロード

実際の東京電力エリア需給実績データとJEPXスポット価格データをアップロードして予測を更新できます。

**発電量データ（TEPCO形式）:**
```csv
単位[MW平均],,,供給力
DATE,TIME,エリア需要,原子力,火力(LNG),火力(石炭),火力(石油),火力(その他),水力,地熱,バイオマス,太陽光発電実績,太陽光出力制御量,風力発電実績,風力出力制御量,揚水,蓄電池,連系線,その他,合計
2026/1/1,0:00,27195,0,11426,6861,415,1729,753,0,449,0,0,98,0,140,0,5190,134,27195
2026/1/1,0:30,26147,0,10177,6861,416,1766,755,0,452,0,0,115,0,120,0,5300,186,26148
```

- データソース: [東京電力エリア需給実績](https://www.tepco.co.jp/forecast/html/area_jukyu-j.html)
- 詳細: [DATA_GUIDE.md](./DATA_GUIDE.md)

**価格データ（JEPX形式）:**
```csv
timestamp,price_yen
2025-10-14 00:00:00,11.27
2025-10-14 00:30:00,11.27
```

- データソース: [JEPX スポット市場](https://www.jepx.jp/electricpower/market-data/spot/)
- 自動取得: `python ml/scripts/fetch_jepx_price.py`

### 3. 予測の更新

CSVをアップロードすると、自動的に：
1. データベースが更新される
2. 予測が再計算される
3. MAPE（精度指標）が再計算される

## プロジェクト構造

```
elect/
├── frontend/                    # React アプリケーション
│   ├── src/
│   │   ├── components/          # UIコンポーネント
│   │   │   ├── Dashboard.tsx    # メインダッシュボード
│   │   │   ├── ForecastChart.tsx # 予測グラフ
│   │   │   ├── AccuracyChart.tsx # 精度表示
│   │   │   └── UploadPanel.tsx   # CSVアップロード
│   │   ├── hooks/               # カスタムフック
│   │   ├── services/            # API通信
│   │   └── types/               # TypeScript型定義
│   └── package.json
│
├── backend/                     # FastAPI アプリケーション
│   ├── api/
│   │   ├── main.py              # エントリーポイント
│   │   ├── routers/             # エンドポイント
│   │   │   ├── data.py          # データ管理API
│   │   │   └── predict.py       # 予測API
│   │   └── services/            # ビジネスロジック
│   │       ├── db.py            # SQLite操作
│   │       ├── model_loader.py  # モデルロード
│   │       ├── predictor.py     # 予測実行
│   │       └── weather.py       # Open-Meteo API
│   ├── db/
│   │   └── schema.sql           # DBスキーマ
│   └── requirements.txt
│
├── ml/                          # 機械学習
│   ├── scripts/
│   │   ├── generate_sample_data.py # サンプルデータ生成
│   │   └── train.py             # モデル学習
│   ├── data/seed/               # 学習データ
│   ├── models/                  # 学習済みモデル
│   └── README.md                # ML詳細ドキュメント
│
├── shared/                      # 共通定義
├── vercel.json                  # Vercel設定
└── README.md
```

## API エンドポイント

詳細は http://localhost:8000/docs (Swagger UI) を参照してください。

### データ管理

- `POST /api/data/upload` - CSV一括アップロード（TEPCO/JEPX形式対応）
  - Form Data: `generation_file`, `price_file`
  - 自動でデータベース更新＋MAPE計算

- `GET /api/data/status` - データ状態確認
  - レスポンス: レコード数、最新タイムスタンプ

### 予測

- `GET /api/predict/latest?area=tokyo&hours=48` - 次のN時間予測取得
  - 発電量予測（MW）と価格予測（円/kWh）を返す

- `GET /api/predict/accuracy?area=tokyo&days=7` - 過去N日間の精度（MAPE）
  - 発電量予測精度と価格予測精度を返す

- `GET /api/predict/history?area=tokyo&days=7` - 予測履歴取得

### ヘルスチェック

- `GET /api/health` - APIヘルスチェック
- `GET /` - API情報

## Vercel デプロイ

### デプロイ前の準備

1. モデルを学習（ローカルで実行）
2. 学習済みモデルをコミット

```bash
cd ml
python scripts/train.py
git add models/*.pkl
git commit -m "Add trained models"
```

### Vercelにデプロイ

```bash
# Vercel CLIインストール（初回のみ）
npm install -g vercel

# デプロイ
vercel deploy
```

### 注意事項

- Vercel Functionsは **ephemeral filesystem** を使用するため、アップロードされたデータは永続化されません
- デモ用途に最適、本番環境では Vercel Blob や外部DBの使用を推奨

## トラブルシューティング

### モデルが見つからないエラー

```
WARNING: Generation model not found
```

**原因**: モデルが学習されていない

**解決策**:
```bash
cd ml
source venv/bin/activate
python scripts/train.py
```

### 予測APIがエラー

```
Failed to fetch prediction
```

**原因**: バックエンドが起動していない、またはモデルがロードされていない

**解決策**:
1. バックエンドが http://localhost:8000 で起動しているか確認
2. http://localhost:8000/docs でAPI状態を確認
3. バックエンドログを確認

### CSVアップロードが失敗

```
Required column 'timestamp' not found in generation file
```

**原因**: CSV形式が正しくない

**解決策**:
- 発電量データ: TEPCO形式（19カラム、1行目に「単位[MW平均]」）を使用
- 価格データ: JEPX形式（timestamp, price_yen）を使用
- サンプルファイル: `ml/data/seed/` を参照

### データベースエラー

```
Database is locked
```

**原因**: 複数のプロセスが同時にDBにアクセスしている

**解決策**:
```bash
# DBを削除して再作成
rm /tmp/elect.db
cd backend
python scripts/import_tepco_data.py ../ml/data/seed/generation_tokyo_tepco.csv tokyo
python scripts/import_price_data.py ../ml/data/seed/price_tokyo_sample.csv tokyo
```

### フロントエンドが表示されない

**原因**: ポート3000が使用中

**解決策**:
1. `lsof -i :3000` で使用中のプロセスを確認
2. 別のポートを使用: `vite.config.ts` の `port` を変更

## ライセンス

MIT

## 今後の拡張

- [ ] 複数エリア対応（現在は東京のみ）
- [ ] リアルタイム予測更新
- [ ] 予測精度の可視化強化
- [ ] ユーザー認証
- [ ] Vercel Blob統合（データ永続化）
- [ ] GitHub Actions による自動学習

## サポート

問題が発生した場合は、Issueを作成してください。
