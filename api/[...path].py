import sys
import os

# バックエンドモジュールのパスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.api.main import handler

# Vercel Serverless Functionのエントリーポイント
# このhandlerがすべての /api/* リクエストを処理します
