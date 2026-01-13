# Vercel デプロイガイド

このガイドでは、再エネ発電量＋電力価格予測ダッシュボードをVercelにデプロイする手順を説明します。

## 📋 目次

1. [デプロイ前の準備](#デプロイ前の準備)
2. [Vercel CLIによるデプロイ](#vercel-cliによるデプロイ)
3. [Vercel Dashboardによるデプロイ](#vercel-dashboardによるデプロイ)
4. [環境変数の設定](#環境変数の設定)
5. [デプロイ後の確認](#デプロイ後の確認)
6. [トラブルシューティング](#トラブルシューティング)
7. [制限事項と注意点](#制限事項と注意点)

## デプロイ前の準備

### 1. 必要なアカウント

- **Vercel アカウント**: https://vercel.com/signup
- **GitHub アカウント**: リポジトリ連携用

### 2. モデルの学習

デプロイ前に、ローカル環境でモデルを学習してコミットします。

```bash
# ML環境で実行
cd ml
source venv/bin/activate
python scripts/train.py

# モデルファイルの確認
ls -la models/*.pkl
# → generation_tokyo.pkl
# → generation_tokyo.metadata.pkl
# → price_tokyo.pkl
# → price_tokyo.metadata.pkl

# Gitにコミット
git add models/*.pkl models/*.metadata.pkl
git commit -m "Add trained models for deployment"
```

**重要**: Vercelはビルド時にモデルを学習しません。学習済みモデルを含める必要があります。

### 3. .gitignoreの確認

`.gitignore`でモデルファイルが除外されていないことを確認：

```bash
# models/*.pklが含まれていないことを確認
cat .gitignore | grep -v "^#" | grep models
```

もし除外されている場合は、`.gitignore`を編集：

```gitignore
# モデルファイルはデプロイに必要なので除外しない
# ml/models/*.pkl  # この行をコメントアウトまたは削除
```

### 4. リポジトリのプッシュ

```bash
git push origin main
```

## Vercel CLIによるデプロイ

### 1. Vercel CLIのインストール

```bash
npm install -g vercel
```

### 2. ログイン

```bash
vercel login
```

ブラウザが開いてログイン画面が表示されます。

### 3. プロジェクトのリンク

```bash
# プロジェクトルートで実行
vercel link
```

質問に答えていきます：

```
? Set up and deploy "~/elect"? [Y/n] y
? Which scope do you want to deploy to? <your-username>
? Link to existing project? [y/N] n
? What's your project's name? elect
? In which directory is your code located? ./
```

### 4. デプロイ

**プレビューデプロイ（テスト用）:**

```bash
vercel
```

**本番デプロイ:**

```bash
vercel --prod
```

デプロイが完了すると、URLが表示されます：

```
✅ Production: https://elect-xxxxx.vercel.app
```

## Vercel Dashboardによるデプロイ

### 1. Vercel Dashboardにアクセス

https://vercel.com/dashboard にアクセスします。

### 2. 新規プロジェクトの作成

1. 「Add New...」→「Project」をクリック
2. GitHubリポジトリを選択
3. 「Import」をクリック

### 3. プロジェクト設定

**Configure Project画面で以下を設定：**

- **Framework Preset**: `Other`
- **Root Directory**: `./`（デフォルト）
- **Build Command**: `cd frontend && npm run build`
- **Output Directory**: `frontend/dist`
- **Install Command**: `cd frontend && npm install`

これらは `vercel.json` で定義されているため、自動設定されます。

### 4. デプロイ実行

「Deploy」ボタンをクリックしてデプロイを開始します。

## 環境変数の設定

### 現在の実装

このプロジェクトは環境変数を使用していません（すべてデフォルト値）。

### 将来的な拡張

環境変数を追加する場合：

1. Vercel Dashboard → Project → Settings → Environment Variables
2. 変数を追加：
   - `DATABASE_URL`: データベースURL（外部DB使用時）
   - `OPENMETEO_API_KEY`: Open-Meteo API キー（有料プラン使用時）
   - `ALLOWED_ORIGINS`: CORS設定

3. `backend/api/main.py` で環境変数を読み込む：

```python
import os

DATABASE_URL = os.getenv("DATABASE_URL", "/tmp/elect.db")
```

## デプロイ後の確認

### 1. デプロイステータスの確認

Vercel Dashboardで：
- **Deployments** タブを開く
- ビルドログを確認
- エラーがないことを確認

### 2. アプリケーションの動作確認

デプロイされたURLにアクセス（例: https://elect-xxxxx.vercel.app）

**確認項目：**
- ✅ ダッシュボードが表示される
- ✅ API ステータスが "ok" と表示される
- ✅ 予測グラフが表示される
- ✅ MAPE（精度指標）が表示される

### 3. APIエンドポイントの確認

```bash
# ヘルスチェック
curl https://elect-xxxxx.vercel.app/api/health

# データ状態（初回は空）
curl https://elect-xxxxx.vercel.app/api/data/status

# API ドキュメント
open https://elect-xxxxx.vercel.app/api/docs
```

### 4. CSVアップロードのテスト

1. デプロイされたURLにアクセス
2. CSVデータをアップロード
3. 予測が更新されることを確認

**注意**: Vercelの `/tmp` は一時的なストレージです。再デプロイやコールドスタート時にデータは消去されます。

## トラブルシューティング

### ビルドエラー

**症状**: `Build failed`

**原因と解決策**:

1. **モデルファイルが見つからない**
   ```
   ERROR: Model file not found
   ```
   → モデルファイルをGitにコミット＆プッシュ

2. **依存パッケージのエラー**
   ```
   ERROR: Could not find a version that satisfies the requirement
   ```
   → `requirements.txt` と `package.json` を確認

3. **Pythonバージョンの問題**
   ```
   ERROR: Python version mismatch
   ```
   → `vercel.json` または `runtime.txt` でPythonバージョンを指定

### ランタイムエラー

**症状**: デプロイ成功したがアプリが動作しない

**解決策**:

1. **ログの確認**
   - Vercel Dashboard → Deployments → Functions → Logs

2. **Function Timeout**
   ```
   Task timed out after 10.00 seconds
   ```
   → Vercel の Serverless Functions は10秒制限があります
   → モデルの遅延読み込み（Lazy Loading）を実装済み

3. **メモリ不足**
   ```
   Process exited with code 137
   ```
   → Vercel Pro プランにアップグレード（メモリ制限緩和）

### APIが404エラー

**症状**: `/api/*` にアクセスすると404

**原因**: `vercel.json` の rewrites 設定が正しくない

**解決策**:

```json
{
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "/api/index"
    }
  ]
}
```

### CORSエラー

**症状**: フロントエンドからAPIにアクセスできない

**解決策**:

`backend/api/main.py` のCORS設定を確認：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番では適切に制限
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 制限事項と注意点

### Vercel Serverless Functions の制限

| 項目 | 無料プラン | Pro プラン |
|------|----------|-----------|
| 実行時間 | 10秒 | 60秒 |
| メモリ | 1024 MB | 3008 MB |
| ペイロードサイズ | 4.5 MB | 4.5 MB |
| 同時実行数 | 1,000 | 10,000 |

### Ephemeral File System

Vercel の `/tmp` は **一時的** です：

- デプロイごとにリセット
- コールドスタート時にクリア
- 最大 512 MB

**影響**:
- アップロードしたデータは永続化されない
- SQLite データベースは揮発性

**解決策（本番環境）**:
- Vercel Blob（ファイルストレージ）
- Vercel Postgres（データベース）
- 外部DB（Supabase、PlanetScale など）

### モデルサイズ

LightGBMモデルは比較的小さい（各 ~1MB）ですが、大きなモデルを使用する場合：

- Vercel の 50MB デプロイサイズ制限に注意
- モデル圧縮を検討
- 外部ストレージからロードを検討

### コールドスタート

Serverless Functions は使用されていないとスリープします。

- 初回アクセス時に数秒の遅延
- モデルロードに時間がかかる可能性

**対策**:
- 遅延ロード（Lazy Loading）実装済み
- ウォームアップリクエストの定期実行

## 継続的デプロイ（CI/CD）

### 自動デプロイの設定

GitHubリポジトリと連携すると、自動デプロイが有効になります：

1. **main ブランチ** → 本番デプロイ
2. **その他のブランチ** → プレビューデプロイ

### プレビューデプロイの確認

プルリクエストを作成すると、自動的にプレビューURLが生成されます。

## カスタムドメインの設定

### 1. Vercel Dashboardでドメイン追加

1. Project Settings → Domains
2. 「Add」をクリック
3. ドメイン名を入力（例: `elect.example.com`）
4. DNSレコードを設定

### 2. DNS設定

ドメインレジストラで以下のレコードを追加：

**A レコード**:
```
76.76.21.21
```

または

**CNAME レコード**:
```
cname.vercel-dns.com
```

## モニタリング

### Vercel Analytics

Vercel Dashboard → Analytics でアクセス解析を確認できます。

### カスタムモニタリング

外部サービスとの連携：
- Sentry（エラー追跡）
- LogRocket（セッション録画）
- Datadog（APM）

## 次のステップ

デプロイが完了したら：

1. **カスタムドメイン設定**
2. **Vercel Blob 統合**（データ永続化）
3. **認証の実装**（NextAuth.js など）
4. **モニタリング設定**
5. **パフォーマンス最適化**

## 参考リンク

- [Vercel Documentation](https://vercel.com/docs)
- [Vercel Serverless Functions](https://vercel.com/docs/functions/serverless-functions)
- [Vercel Blob](https://vercel.com/docs/storage/vercel-blob)
- [README.md](./README.md) - プロジェクト概要
- [SETUP.md](./SETUP.md) - セットアップガイド
