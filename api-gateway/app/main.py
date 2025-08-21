from fastapi import FastAPI, Request, HTTPException, Depends
import httpx, os

app = FastAPI(title="Stock Alert API Gateway")

ANALYZER_URL = os.getenv("ANALYZER_URL", "http://analyzer-service:8002")
NOTIFIER_URL = os.getenv("NOTIFIER_URL", "http://notifier-service:8001")
AUTH_URL = os.getenv("AUTH_URL", "http://auth-service:8003")
USER_URL = os.getenv("USER_URL", "http://user-service:8004")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "api-gateway"}

@app.post("/auth/register")
async def register(payload: dict):
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{AUTH_URL}/register", json=payload, timeout=15)
        return r.json()

@app.post("/auth/login")
async def login(payload: dict):
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{AUTH_URL}/login", json=payload, timeout=15)
        return r.json()

@app.get("/portfolio")
async def get_portfolio(user_id: int):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{USER_URL}/portfolio/{user_id}", timeout=15)
        return r.json()

@app.post("/portfolio")
async def set_portfolio(payload: dict):
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{USER_URL}/portfolio", json=payload, timeout=15)
        return r.json()

@app.get("/analyze")
async def analyze(symbol: str = "RELIANCE.NS"):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{ANALYZER_URL}/analyze", params={"symbol": symbol}, timeout=30)
        return r.json()

@app.post("/notify")
async def notify(payload: dict):
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{NOTIFIER_URL}/notify", json=payload, timeout=15)
        return r.json()
