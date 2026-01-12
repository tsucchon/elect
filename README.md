# 再エネ発電量＋電力価格 短期予測ダッシュボード

OCCTO発電量データとJEPX価格データ、Open-Meteo気象予報を使用して、次の48時間の再エネ発電量とスポット価格を予測するダッシュボードアプリケーション。

## 特徴

- 📈 **48時間予測**: 再エネ発電量と電力価格の短期予測
- 🎯 **精度表示**: 過去7日間のMAPE（平均絶対パーセント誤差）をリアルタイム表示
- 📊 **インタラクティブグラフ**: Rechartsによる見やすい2軸グラフ表示
- 📁 **CSV アップロード**: OCCTO/JEPXデータの簡単アップロード（自動更新対応）
- 🔄 **自動データ更新**: CSVアップロード時に予測とMAPEを自動再計算
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

### 2. 機械学習モデルの学習（最初に必須）

```bash
cd ml

# 仮想環境作成
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存パッケージインストール
pip install -r requirements.txt

# サンプルデータ生成
python scripts/generate_sample_data.py

# モデル学習（5-10分程度）
python scripts/train.py
```

学習が完了すると、`ml/models/` に以下のファイルが生成されます：
- `generation_tokyo.pkl` - 発電量予測モデル
- `price_tokyo.pkl` - 価格予測モデル

### 3. バックエンド起動

```bash
cd backend

# 仮想環境作成（mlと別）
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存パッケージインストール
pip install -r requirements.txt

# サーバー起動
uvicorn api.main:app --reload
```

→ バックエンドが http://localhost:8000 で起動

### 4. フロントエンド起動

別のターミナルで：

```bash
cd frontend

# 依存パッケージインストール
npm install

# 開発サーバー起動
npm run dev
```

→ フロントエンドが http://localhost:5173 で起動(Viteデフォルト)

### 5. ブラウザでアクセス

http://localhost:5173 にアクセスして、ダッシュボードを確認

## 使い方

### 1. 初期状態での予測

アプリを起動すると、サンプルデータに基づいた初期予測が表示されます。

### 2. CSVデータのアップロード

実際のOCCTO/JEPXデータをアップロードして予測を更新できます。

**発電量データ（generation_tokyo_sample.csv）の形式:**
```csv
timestamp,pv_mw,wind_mw,total_mw
2024-01-01 00:00:00,0,250.5,250.5
2024-01-01 00:30:00,0,245.2,245.2
```

**価格データ（price_tokyo_sample.csv）の形式:**
```csv
timestamp,price_yen
2024-01-01 00:00:00,8.5
2024-01-01 00:30:00,8.2
```

### 3. 予測の更新

CSVをアップロードすると、自動的に予測が再計算されます。

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

### データ管理

- `POST /api/data/upload` - CSV一括アップロード
- `GET /api/data/status` - データ状態確認

### 予測

- `GET /api/predict/latest?hours=48` - 次のN時間予測取得
- `GET /api/predict/accuracy?days=7` - 過去N日間の精度（MAPE）
- `GET /api/predict/history?days=7` - 予測履歴取得

### ヘルスチェック

- `GET /api/health` - APIヘルスチェック

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

→ `ml/scripts/train.py` を実行してモデルを生成してください

### 予測APIが503エラー

→ バックエンド起動時にモデルがロードされているか確認してください

### CSVアップロードが失敗

→ CSV形式が正しいか確認してください（`ml/data/seed/` のサンプルを参照）

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
