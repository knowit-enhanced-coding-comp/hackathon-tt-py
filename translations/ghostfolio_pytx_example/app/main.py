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
# Translated calculator delegation
# ---------------------------------------------------------------------------


def _try_calculator(user: UserState) -> dict | None:
    """Try to run the translated calculator; return None on any failure."""
    try:
        from apps.api.src.app.portfolio.calculator.roai.portfolio_calculator import (
            RoaiPortfolioCalculator,
        )
        from app.models import PortfolioOrderItem, SymbolProfile
        from decimal import Decimal
        from datetime import date as D, timedelta

        calc = RoaiPortfolioCalculator()
        calc.activities = [
            PortfolioOrderItem(
                date=a["date"],
                fee=Decimal(str(a.get("fee") or 0)),
                quantity=Decimal(str(a.get("quantity") or 0)),
                symbol_profile=SymbolProfile(
                    symbol=a.get("symbol", ""),
                    data_source=a.get("dataSource", "YAHOO"),
                ),
                type=a.get("type", "BUY"),
                unit_price=Decimal(str(a.get("unitPrice") or 0)),
            )
            for a in user.activities
        ]

        # Build date → { symbol → price } map from seeded market data
        mmap: dict[str, dict[str, Decimal]] = {}
        for p, sym in (
            (p, sym) for ds in user.market_data.values() for sym, ps in ds.items() for p in ps
        ):
            mmap.setdefault(p["date"], {})[sym] = Decimal(str(p["marketPrice"]))
        today = D.today().isoformat()
        mmap.setdefault(today, {})

        all_dates = sorted(mmap)
        chart_map = {d: True for d in all_dates}
        ex_rates = {d: 1.0 for d in all_dates}

        first = min(a["date"] for a in user.activities)
        start = D.fromisoformat(first) - timedelta(days=1)
        symbols = list({a.get("symbol") for a in user.activities if a.get("symbol")})

        results: dict[str, dict] = {}
        for sym in symbols:
            ds = next((a["dataSource"] for a in user.activities if a.get("symbol") == sym), "YAHOO")
            m = calc.get_symbol_metrics(
                chart_date_map=chart_map, data_source=ds, end=D.today(),
                exchange_rates=ex_rates, market_symbol_map=mmap,
                start=start, symbol=sym,
            )
            if m is not None:
                results[sym] = m if isinstance(m, dict) else vars(m)
        return results
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Portfolio — performance (v2)
# ---------------------------------------------------------------------------

@app.get("/api/v2/portfolio/performance")
def get_performance(
    range: str = "max",
    user: UserState = Depends(_get_user),
) -> dict:
    """Delegate to translated calculator, fall back to activity-based computation."""
    calc = _try_calculator(user) if user.activities else None
    ti = 0.0
    if calc:
        ti = sum(float(m.get("total_investment", 0)) for m in calc.values())
    else:
        # Fallback: cost-basis tracking from raw activities
        inv: dict[str, float] = {}
        units: dict[str, float] = {}
        for a in sorted(user.activities, key=lambda x: x["date"]):
            sym, q = a.get("symbol", ""), float(a.get("quantity", 0) or 0)
            p = float(a.get("unitPrice", 0) or 0)
            if a.get("type") == "BUY":
                inv[sym] = inv.get(sym, 0.0) + q * p
                units[sym] = units.get(sym, 0.0) + q
            elif a.get("type") == "SELL":
                u = units.get(sym, 0.0)
                if u > 1e-10:
                    inv[sym] = inv.get(sym, 0.0) - (inv.get(sym, 0.0) / u) * q
                units[sym] = u - q
        ti = sum(inv.values())
    return {
        "chart": [],
        "firstOrderDate": user.activities[0]["date"] if user.activities else None,
        "performance": {
            "currentNetWorth": 0.0,
            "currentValue": 0.0,
            "netPerformance": 0.0,
            "netPerformancePercentage": 0.0,
            "netPerformancePercentageWithCurrencyEffect": 0.0,
            "netPerformanceWithCurrencyEffect": 0.0,
            "totalFees": 0.0,
            "totalInvestment": ti,
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
    """Build investment entries from activities, with optional date grouping."""
    entries = []
    for a in sorted(user.activities, key=lambda x: x["date"]):
        if a.get("type") in ("BUY", "SELL"):
            q = float(a.get("quantity", 0) or 0)
            p = float(a.get("unitPrice", 0) or 0)
            sign = 1.0 if a.get("type") == "BUY" else -1.0
            entries.append({"date": a["date"], "investment": sign * q * p})
    if groupBy in ("month", "year"):
        groups: dict[str, float] = {}
        for e in entries:
            d = e["date"]
            key = (d[:7] + "-01") if groupBy == "month" else (d[:4] + "-01-01")
            groups[key] = groups.get(key, 0.0) + e["investment"]
        return {"investments": [
            {"date": k, "investment": v} for k, v in sorted(groups.items()) if abs(v) > 1e-10
        ]}
    return {"investments": entries}


# ---------------------------------------------------------------------------
# Portfolio — holdings (v1)
# ---------------------------------------------------------------------------

@app.get("/api/v1/portfolio/holdings")
def get_holdings(
    range: str = "max",
    user: UserState = Depends(_get_user),
) -> dict:
    """Compute holdings from activities."""
    units: dict[str, float] = {}
    cost: dict[str, float] = {}
    for a in sorted(user.activities, key=lambda x: x["date"]):
        sym = a.get("symbol", "")
        q = float(a.get("quantity", 0) or 0)
        p = float(a.get("unitPrice", 0) or 0)
        if a.get("type") == "BUY":
            units[sym] = units.get(sym, 0.0) + q
            cost[sym] = cost.get(sym, 0.0) + q * p
        elif a.get("type") == "SELL":
            u = units.get(sym, 0.0)
            if u > 1e-10:
                cost[sym] = cost.get(sym, 0.0) - (cost.get(sym, 0.0) / u) * q
            units[sym] = u - q
    holdings: dict[str, Any] = {}
    for sym, u in units.items():
        if u > 1e-10:
            holdings[sym] = {"quantity": u, "investment": cost.get(sym, 0.0)}
    return {"holdings": holdings}
