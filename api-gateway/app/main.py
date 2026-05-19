import os
import logging
import httpx
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from .deps import get_current_user, CurrentUser
from .middleware import RequestLoggingMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("gateway")

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
# Rate limiter — keyed by client IP
# Used only on public endpoints to prevent abuse.
# Authenticated endpoints rely on JWT for identity; per-user limiting comes in Phase 4.
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Stock Alert — API Gateway",
    version="1.1.0",
    description="BFF gateway with JWT validation and upstream proxying.",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — tighten origins in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)

# ---------------------------------------------------------------------------
# Upstream URLs
# ---------------------------------------------------------------------------
ANALYZER_URL = os.getenv("ANALYZER_URL", "http://analyzer-service:8002")
NOTIFIER_URL = os.getenv("NOTIFIER_URL", "http://notifier-service:8001")
AUTH_URL     = os.getenv("AUTH_URL",     "http://auth-service:8003")
USER_URL     = os.getenv("USER_URL",     "http://user-service:8004")
SCANNER_URL  = os.getenv("SCANNER_URL",  "http://scanner-service:8005")


def _auth_headers(user: CurrentUser) -> dict:
    """
    Build headers that downstream services use to identify the caller.
    Services must NEVER accept these headers from untrusted external callers —
    they are only injected by the gateway after token validation.
    """
    return {
        "X-User-Id":    str(user.user_id),
        "X-User-Email": user.email,
    }


# ---------------------------------------------------------------------------
# Public routes  (no auth required)
# ---------------------------------------------------------------------------

@app.get("/health", tags=["ops"])
async def health():
    return {"status": "ok", "service": "api-gateway"}


@app.post("/auth/register", tags=["auth"])
@limiter.limit("5/minute")
async def register(request: Request, payload: dict):
    """Proxy registration to auth-service. No token required."""
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{AUTH_URL}/register", json=payload, timeout=15)
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.json().get("detail"))
    return r.json()


@app.post("/auth/login", tags=["auth"])
@limiter.limit("10/minute")
async def login(request: Request, payload: dict):
    """Proxy login to auth-service. Returns JWT on success."""
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{AUTH_URL}/login", json=payload, timeout=15)
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.json().get("detail"))
    return r.json()


# ---------------------------------------------------------------------------
# Protected routes  (valid JWT required)
# ---------------------------------------------------------------------------

# --- Portfolio ----------------------------------------------------------

@app.get("/portfolio", tags=["portfolio"])
async def get_portfolio(user: CurrentUser = Depends(get_current_user)):
    """Fetch the portfolio for the authenticated user."""
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{USER_URL}/portfolio/{user.user_id}",
            headers=_auth_headers(user),
            timeout=15,
        )
    return r.json()


@app.post("/portfolio", tags=["portfolio"])
async def set_portfolio(payload: dict, user: CurrentUser = Depends(get_current_user)):
    """
    Set portfolio symbols for the authenticated user.
    user_id is taken from the JWT — the client cannot spoof it.
    """
    payload["user_id"] = user.user_id
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{USER_URL}/portfolio",
            json=payload,
            headers=_auth_headers(user),
            timeout=15,
        )
    return r.json()


# --- Analyzer -----------------------------------------------------------

@app.get("/analyse", tags=["analysis"])
async def analyse(symbol: str = "RELIANCE.NS", user: CurrentUser = Depends(get_current_user)):
    """
    Run full technical analysis on a stock symbol.
    Requires authentication so we can rate-limit per user later.
    """
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{ANALYZER_URL}/analyse",
            params={"symbol": symbol},
            headers=_auth_headers(user),
            timeout=30,
        )
    if r.status_code != 200:
        logger.error(f"Analyzer error {r.status_code}: {r.text}")
        raise HTTPException(
            status_code=r.status_code,
            detail=f"Analyzer service error: {r.status_code}",
        )
    try:
        return r.json()
    except Exception:
        logger.error("Analyzer returned non-JSON response")
        raise HTTPException(status_code=502, detail="Analyzer returned invalid response")


# --- Notifier -----------------------------------------------------------

@app.post("/notify", tags=["notifications"])
async def notify(payload: dict, user: CurrentUser = Depends(get_current_user)):
    """Send a notification on behalf of the authenticated user."""
    payload["user_id"] = user.user_id
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{NOTIFIER_URL}/notify",
            json=payload,
            headers=_auth_headers(user),
            timeout=15,
        )
    return r.json()


# ---------------------------------------------------------------------------
# Watchlists  (proxied to user-service, user_id injected from JWT)
# ---------------------------------------------------------------------------

@app.get("/watchlists", tags=["watchlists"])
async def list_watchlists(user: CurrentUser = Depends(get_current_user)):
    """List all watchlists for the authenticated user."""
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{USER_URL}/watchlists",
            headers=_auth_headers(user),
            timeout=15,
        )
    return r.json()


@app.post("/watchlists", tags=["watchlists"], status_code=201)
async def create_watchlist(payload: dict, user: CurrentUser = Depends(get_current_user)):
    """Create a new named watchlist."""
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{USER_URL}/watchlists",
            json=payload,
            headers=_auth_headers(user),
            timeout=15,
        )
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.json().get("detail"))
    return r.json()


@app.get("/watchlists/{watchlist_id}", tags=["watchlists"])
async def get_watchlist(watchlist_id: int, user: CurrentUser = Depends(get_current_user)):
    """Get a watchlist with all its items."""
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{USER_URL}/watchlists/{watchlist_id}",
            headers=_auth_headers(user),
            timeout=15,
        )
    if r.status_code == 404:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return r.json()


@app.delete("/watchlists/{watchlist_id}", tags=["watchlists"], status_code=204)
async def delete_watchlist(watchlist_id: int, user: CurrentUser = Depends(get_current_user)):
    """Delete a watchlist and all its items."""
    async with httpx.AsyncClient() as client:
        r = await client.delete(
            f"{USER_URL}/watchlists/{watchlist_id}",
            headers=_auth_headers(user),
            timeout=15,
        )
    if r.status_code == 404:
        raise HTTPException(status_code=404, detail="Watchlist not found")


@app.post("/watchlists/{watchlist_id}/items", tags=["watchlists"], status_code=201)
async def add_watchlist_item(
    watchlist_id: int,
    payload: dict,
    user: CurrentUser = Depends(get_current_user),
):
    """Add a symbol to a watchlist."""
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{USER_URL}/watchlists/{watchlist_id}/items",
            json=payload,
            headers=_auth_headers(user),
            timeout=15,
        )
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.json().get("detail"))
    return r.json()


@app.delete("/watchlists/{watchlist_id}/items/{symbol}", tags=["watchlists"], status_code=204)
async def remove_watchlist_item(
    watchlist_id: int,
    symbol: str,
    user: CurrentUser = Depends(get_current_user),
):
    """Remove a symbol from a watchlist."""
    async with httpx.AsyncClient() as client:
        r = await client.delete(
            f"{USER_URL}/watchlists/{watchlist_id}/items/{symbol}",
            headers=_auth_headers(user),
            timeout=15,
        )
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.json().get("detail"))


# ---------------------------------------------------------------------------
# Public market snapshot — no JWT, used by login page
# ---------------------------------------------------------------------------

@app.get("/market/snapshot", tags=["market"])
@limiter.limit("10/minute")
async def market_snapshot(request: Request, symbol: str = "^NSEI", period: str = "1y"):
    """
    Proxy to analyzer /history. Public — no auth required.
    Returns daily closing prices for the requested symbol and period.
    """
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{ANALYZER_URL}/history",
            params={"symbol": symbol, "period": period},
            timeout=30,
        )
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail="Market data unavailable")
    return r.json()

@app.get("/scan/stream", tags=["scanner"])
async def proxy_scan_stream(
    scope: str = "nifty50",
    user: CurrentUser = Depends(get_current_user),
):
    """
    Proxy SSE scan stream from scanner-service.
    Passes X-User-Id so scanner can decorate results with watchlist badges.
    Uses httpx streaming to forward SSE events as they arrive.
    """
    url = f"{SCANNER_URL}/scan/stream?scope={scope}"
    headers = _auth_headers(user)

    async def stream():
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("GET", url, headers=headers) as response:
                async for chunk in response.aiter_text():
                    yield chunk

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":     "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/scan/results", tags=["scanner"])
async def proxy_scan_results(user: CurrentUser = Depends(get_current_user)):
    """Return latest persisted scan results for the authenticated user."""
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{SCANNER_URL}/scan/results",
            headers=_auth_headers(user),
            timeout=15,
        )
    return r.json()