"""
Ghostfolio API skeleton — Python translation target.

All endpoints return structurally correct responses so that the integration
test suite can run without crashing.  Portfolio calculations are stubbed out
(values will be wrong); implement them incrementally in later milestones.

State is kept purely in-memory; each test creates and deletes its own user,
so isolation is maintained across the sequential pytest run.
"""
from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse

app = FastAPI(title="Ghostfolio pytx skeleton")

# ---------------------------------------------------------------------------
# In-memory store
# ---------------------------------------------------------------------------

@dataclass
class UserState:
    access_token: str
    auth_token: str
    base_currency: str = "USD"
    activities: list[dict] = field(default_factory=list)
    # market_data[data_source][symbol] = [{"date": ..., "marketPrice": ...}]
    market_data: dict[str, dict[str, list[dict]]] = field(default_factory=dict)


_lock = threading.Lock()
# keyed by auth_token (the Bearer value)
_users: dict[str, UserState] = {}
# access_token → auth_token (for DELETE /user)
_access_to_auth: dict[str, str] = {}


def _make_tokens() -> tuple[str, str]:
    return str(uuid.uuid4()), str(uuid.uuid4())


def _get_user(authorization: str | None = Header(default=None)) -> UserState:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    token = authorization.removeprefix("Bearer ")
    with _lock:
        user = _users.get(token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown token")
    return user


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/api/v1/health")
def health() -> dict:
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# User lifecycle
# ---------------------------------------------------------------------------

@app.post("/api/v1/user")
def create_user() -> dict:
    access_token, auth_token = _make_tokens()
    user = UserState(access_token=access_token, auth_token=auth_token)
    with _lock:
        _users[auth_token] = user
        _access_to_auth[access_token] = auth_token
    return {"accessToken": access_token, "authToken": auth_token}


@app.put("/api/v1/user/setting")
def update_user_setting(
    body: dict[str, Any],
    user: UserState = Depends(_get_user),
) -> dict:
    if "baseCurrency" in body:
        user.base_currency = body["baseCurrency"]
    return {"baseCurrency": user.base_currency}


@app.delete("/api/v1/user")
def delete_user(
    body: dict[str, Any],
    user: UserState = Depends(_get_user),
) -> JSONResponse:
    access_token = body.get("accessToken", "")
    with _lock:
        auth = _access_to_auth.pop(access_token, None)
        if auth:
            _users.pop(auth, None)
    return JSONResponse(status_code=status.HTTP_200_OK, content={})


# ---------------------------------------------------------------------------
# Activities import
# ---------------------------------------------------------------------------

@app.post("/api/v1/import")
async def import_activities(
    request: Request,
    user: UserState = Depends(_get_user),
) -> dict:
    body = await request.json()
    activities = body.get("activities", [])
    user.activities.extend(activities)
    return {"activities": activities}


# ---------------------------------------------------------------------------
# Market data seeding (admin)
# ---------------------------------------------------------------------------

@app.post("/api/v1/market-data/{data_source}/{symbol}")
async def seed_market_data(
    data_source: str,
    symbol: str,
    request: Request,
    user: UserState = Depends(_get_user),
) -> dict:
    body = await request.json()
    prices = body.get("marketData", [])
    user.market_data.setdefault(data_source, {})[symbol] = prices
    return {}


# ---------------------------------------------------------------------------
# Portfolio — performance (v2)
# ---------------------------------------------------------------------------

@app.get("/api/v2/portfolio/performance")
def get_performance(
    range: str = "max",
    user: UserState = Depends(_get_user),
) -> dict:
    """Stub: returns zero performance and an empty chart."""
    total_investment = sum(
        a.get("quantity", 0) * a.get("unitPrice", 0)
        for a in user.activities
        if a.get("type") == "BUY"
    ) - sum(
        a.get("quantity", 0) * a.get("unitPrice", 0)
        for a in user.activities
        if a.get("type") == "SELL"
    )
    return {
        "chart": [],
        "firstOrderDate": None,
        "performance": {
            "currentNetWorth": 0.0,
            "currentValue": 0.0,
            "netPerformance": 0.0,
            "netPerformancePercentage": 0.0,
            "netPerformancePercentageWithCurrencyEffect": 0.0,
            "netPerformanceWithCurrencyEffect": 0.0,
            "totalFees": sum(a.get("fee", 0) for a in user.activities),
            "totalInvestment": total_investment,
            "totalLiabilities": 0.0,
            "totalValueables": 0.0,
        },
    }


# ---------------------------------------------------------------------------
# Portfolio — investments (v1)
# ---------------------------------------------------------------------------

@app.get("/api/v1/portfolio/investments")
def get_investments(
    range: str = "max",
    groupBy: str | None = None,
    user: UserState = Depends(_get_user),
) -> dict:
    """Stub: returns an empty investments list."""
    return {"investments": []}


# ---------------------------------------------------------------------------
# Portfolio — holdings (v1)
# ---------------------------------------------------------------------------

@app.get("/api/v1/portfolio/holdings")
def get_holdings(
    range: str = "max",
    user: UserState = Depends(_get_user),
) -> dict:
    """Stub: returns an empty holdings dict."""
    return {"holdings": {}}
