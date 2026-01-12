import sys
import os

# バックエンドモジュールのパスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.api.main import app
from mangum import Mangum

# Vercel Serverless Functionのエントリーポイント
# MangumでFastAPIアプリをラップ（lifespanイベントは無効化）
handler = Mangum(app, lifespan="off")
