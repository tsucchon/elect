import sys
import os

# バックエンドモジュールのパスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# バックエンドのFastAPIアプリをインポート
from backend.api.main import app

# Vercel Python Functionsは、appオブジェクトを自動的に認識します
# Mangumは不要です
