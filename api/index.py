from fastapi import FastAPI
from mangum import Mangum

# 最小限のFastAPIアプリを作成
app = FastAPI()

@app.get("/")
async def root():
    return {"message": "API is working"}

@app.get("/api/health")
async def health():
    return {"status": "ok", "message": "API is running"}

# Vercel Serverless Functionのエントリーポイント
handler = Mangum(app, lifespan="off")
