"""
Ghostfolio pytx — FastAPI entry point.

Complete implementation of portfolio calculator with ROAI methodology.
"""
from __future__ import annotations

import threading
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date as D, timedelta
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse

app = FastAPI(title="Ghostfolio pytx")

# ---------------------------------------------------------------------------
# In-memory store
# ---------------------------------------------------------------------------

@dataclass
class UserState:
    access_token: str
    auth_token: str
    base_currency: str = "USD"
    activities: list[dict] = field(default_factory=list)
    market_data: dict[str, dict[str, list[dict]]] = field(default_factory=dict)


_lock = threading.Lock()
_users: dict[str, UserState] = {}
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
# Portfolio calculator helpers
# ---------------------------------------------------------------------------

def _get_market_price(user: UserState, symbol: str, target_date: str) -> float | None:
    for ds_map in user.market_data.values():
        if symbol in ds_map:
            for p in ds_map[symbol]:
                if p["date"] == target_date:
                    return float(p["marketPrice"])
    return None


def _get_latest_market_price(user: UserState, symbol: str) -> float:
    today = D.today().isoformat()
    price = _get_market_price(user, symbol, today)
    if price is not None:
        return price
    latest_price = None
    latest_date = ""
    for ds_map in user.market_data.values():
        if symbol in ds_map:
            for p in ds_map[symbol]:
                if p["date"] >= latest_date:
                    latest_date = p["date"]
                    latest_price = float(p["marketPrice"])
    return latest_price if latest_price is not None else 0.0


def _get_nearest_price(user: UserState, symbol: str, target_date: str) -> float:
    exact = _get_market_price(user, symbol, target_date)
    if exact is not None:
        return exact
    best_price = 0.0
    best_date = ""
    for ds_map in user.market_data.values():
        if symbol in ds_map:
            for p in ds_map[symbol]:
                if p["date"] <= target_date and p["date"] > best_date:
                    best_date = p["date"]
                    best_price = float(p["marketPrice"])
    return best_price


_TYPE_ORDER = {"BUY": 0, "SELL": 1, "DIVIDEND": 2, "FEE": 3, "LIABILITY": 4}


def _compute_portfolio(user: UserState) -> dict:
    sorted_activities = sorted(
        user.activities,
        key=lambda a: (a["date"], _TYPE_ORDER.get(a.get("type", ""), 5)),
    )

    symbols: dict[str, dict] = {}
    investment_deltas: list[dict] = []
    total_fees = 0.0

    for act in sorted_activities:
        sym = act.get("symbol", "")
        act_type = act.get("type", "BUY")
        qty = float(act.get("quantity") or 0)
        price = float(act.get("unitPrice") or 0)
        fee = float(act.get("fee") or 0)
        act_date = act.get("date", "")

        total_fees += fee

        if act_type in ("DIVIDEND", "FEE", "LIABILITY"):
            continue

        if sym not in symbols:
            symbols[sym] = {
                "quantity": 0.0,
                "investment": 0.0,
                "avg_price": 0.0,
                "total_buy_cost": 0.0,
                "realized_pnl": 0.0,
            }

        s = symbols[sym]

        if act_type == "BUY":
            if s["quantity"] < -1e-12:
                # BUY to cover short: investment uses BUY unitPrice
                cover_qty = min(qty, abs(s["quantity"]))
                cost = cover_qty * price
                s["realized_pnl"] += cover_qty * (abs(s["avg_price"]) - price)
                s["investment"] += cost
                s["total_buy_cost"] += cost
                investment_deltas.append({"date": act_date, "investment": cost, "symbol": sym})
                remaining = qty - cover_qty
                s["quantity"] += cover_qty
                if remaining > 1e-12:
                    # Remaining goes long
                    new_cost = remaining * price
                    new_qty = s["quantity"] + remaining
                    if new_qty > 1e-12:
                        s["avg_price"] = (s["quantity"] * s["avg_price"] + new_cost) / new_qty
                    s["investment"] += new_cost
                    s["total_buy_cost"] += new_cost
                    s["quantity"] = new_qty
                    investment_deltas.append({"date": act_date, "investment": new_cost, "symbol": sym})
            else:
                # BUY into long
                cost = qty * price
                new_qty = s["quantity"] + qty
                if new_qty > 1e-12:
                    s["avg_price"] = (s["quantity"] * s["avg_price"] + cost) / new_qty
                s["investment"] += cost
                s["total_buy_cost"] += cost
                s["quantity"] = new_qty
                investment_deltas.append({"date": act_date, "investment": cost, "symbol": sym})

        elif act_type == "SELL":
            if s["quantity"] > 1e-12:
                # SELL from long
                sell_qty = min(qty, s["quantity"])
                cost_returned = sell_qty * s["avg_price"]
                s["realized_pnl"] += sell_qty * (price - s["avg_price"])
                s["investment"] -= cost_returned
                investment_deltas.append({"date": act_date, "investment": -cost_returned, "symbol": sym})
                s["quantity"] -= sell_qty
                remaining = qty - sell_qty
                if remaining > 1e-12:
                    # Open short with remaining
                    s["quantity"] -= remaining
                    s["avg_price"] = price
                    # No investment delta for opening short
            else:
                # SELL to open/extend short
                s["quantity"] -= qty
                if abs(s["quantity"] + qty) < 1e-12:
                    # First short
                    s["avg_price"] = price
                else:
                    # Extend short: weighted avg
                    prev_qty = abs(s["quantity"] + qty)
                    s["avg_price"] = (prev_qty * abs(s["avg_price"]) + qty * price) / (prev_qty + qty)
                # Record short sell in deltas for investments endpoint
                # but don't change s["investment"] (short sell is proceeds, not cost)
                investment_deltas.append({"date": act_date, "investment": -qty * price, "symbol": sym})

    return {
        "symbols": symbols,
        "investment_deltas": investment_deltas,
        "total_fees": total_fees,
        "sorted_activities": sorted_activities,
    }


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
def update_user_setting(body: dict[str, Any], user: UserState = Depends(_get_user)) -> dict:
    if "baseCurrency" in body:
        user.base_currency = body["baseCurrency"]
    return {"baseCurrency": user.base_currency}


@app.delete("/api/v1/user")
def delete_user(body: dict[str, Any], user: UserState = Depends(_get_user)) -> JSONResponse:
    with _lock:
        auth = _access_to_auth.pop(body.get("accessToken", ""), None)
        if auth:
            _users.pop(auth, None)
    return JSONResponse(status_code=status.HTTP_200_OK, content={})


# ---------------------------------------------------------------------------
# Activities import & market data seeding
# ---------------------------------------------------------------------------

@app.post("/api/v1/import")
async def import_activities(request: Request, user: UserState = Depends(_get_user)) -> dict:
    body = await request.json()
    activities = body.get("activities", [])
    user.activities.extend(activities)
    return {"activities": activities}


@app.post("/api/v1/market-data/{data_source}/{symbol}")
async def seed_market_data(
    data_source: str, symbol: str, request: Request, user: UserState = Depends(_get_user),
) -> dict:
    body = await request.json()
    user.market_data.setdefault(data_source, {})[symbol] = body.get("marketData", [])
    return {}


# ---------------------------------------------------------------------------
# Portfolio — performance (v2)
# ---------------------------------------------------------------------------

@app.get("/api/v2/portfolio/performance")
def get_performance(range: str = "max", user: UserState = Depends(_get_user)) -> dict:
    if not user.activities:
        return {
            "chart": [],
            "firstOrderDate": None,
            "performance": {
                "currentNetWorth": 0,
                "currentValue": 0,
                "currentValueInBaseCurrency": 0,
                "netPerformance": 0,
                "netPerformancePercentage": 0,
                "netPerformancePercentageWithCurrencyEffect": 0,
                "netPerformanceWithCurrencyEffect": 0,
                "totalFees": 0,
                "totalInvestment": 0,
                "totalLiabilities": 0.0,
                "totalValueables": 0.0,
            },
        }

    portfolio = _compute_portfolio(user)
    symbols = portfolio["symbols"]
    total_fees = portfolio["total_fees"]

    total_investment = 0.0
    total_current_value = 0.0
    total_realized_pnl = 0.0
    total_twi = 0.0
    open_investment = 0.0  # investment only for open positions

    for sym, s in symbols.items():
        qty = s["quantity"]
        inv = s["investment"]
        total_investment += inv

        if abs(qty) > 1e-12:
            current_price = _get_latest_market_price(user, sym)
            total_current_value += abs(qty) * current_price
            open_investment += inv

        total_realized_pnl += s["realized_pnl"]
        total_twi += s["total_buy_cost"]

    unrealized_pnl = total_current_value - open_investment
    net_performance = total_realized_pnl + unrealized_pnl - total_fees

    if abs(total_investment) > 1e-10:
        denom = total_investment
    elif total_twi > 1e-10:
        denom = total_twi
    else:
        denom = 1.0

    net_perf_pct = net_performance / denom if abs(denom) > 1e-10 else 0.0

    chart = _build_chart(user, portfolio)
    first_date = min(a["date"] for a in user.activities)

    return {
        "chart": chart,
        "firstOrderDate": first_date,
        "performance": {
            "currentNetWorth": total_current_value,
            "currentValue": total_current_value,
            "currentValueInBaseCurrency": total_current_value,
            "netPerformance": net_performance,
            "netPerformancePercentage": net_perf_pct,
            "netPerformancePercentageWithCurrencyEffect": net_perf_pct,
            "netPerformanceWithCurrencyEffect": net_performance,
            "totalFees": total_fees,
            "totalInvestment": total_investment,
            "totalLiabilities": 0.0,
            "totalValueables": 0.0,
        },
    }


def _build_chart(user: UserState, portfolio: dict) -> list[dict]:
    if not user.activities:
        return []

    activity_dates = [a["date"] for a in user.activities]
    first_date = min(activity_dates)
    start = D.fromisoformat(first_date) - timedelta(days=1)
    end = D.today()

    # Collect all relevant dates for the chart
    chart_dates: set[str] = {start.isoformat()}

    for a in user.activities:
        d = D.fromisoformat(a["date"])
        if start <= d <= end:
            chart_dates.add(a["date"])

    # Market data dates in range
    for ds_map in user.market_data.values():
        for sym, prices in ds_map.items():
            for p in prices:
                d_str = p["date"]
                d = D.fromisoformat(d_str)
                if start <= d <= end:
                    chart_dates.add(d_str)

    # Year boundaries
    for year in range(start.year, end.year + 1):
        for boundary in (D(year, 1, 1), D(year, 12, 31)):
            if start < boundary <= end:
                chart_dates.add(boundary.isoformat())

    chart_dates.add(end.isoformat())
    sorted_dates = sorted(chart_dates)

    # Investment deltas by date
    inv_delta_by_date: dict[str, float] = defaultdict(float)
    for d in portfolio["investment_deltas"]:
        inv_delta_by_date[d["date"]] += d["investment"]

    # Replay activities to build chart state
    sorted_acts = sorted(
        user.activities,
        key=lambda a: (a["date"], _TYPE_ORDER.get(a.get("type", ""), 5)),
    )

    chart = []
    sym_state: dict[str, dict] = {}
    cumulative_fees = 0.0
    act_idx = 0

    for chart_date in sorted_dates:
        # Process activities up to this date
        while act_idx < len(sorted_acts) and sorted_acts[act_idx]["date"] <= chart_date:
            act = sorted_acts[act_idx]
            act_type = act.get("type", "BUY")
            sym = act.get("symbol", "")
            qty = float(act.get("quantity") or 0)
            price = float(act.get("unitPrice") or 0)
            fee = float(act.get("fee") or 0)

            cumulative_fees += fee

            if act_type in ("DIVIDEND", "FEE", "LIABILITY"):
                act_idx += 1
                continue

            if sym not in sym_state:
                sym_state[sym] = {"quantity": 0.0, "investment": 0.0, "avg_price": 0.0}

            ss = sym_state[sym]
            if act_type == "BUY":
                if ss["quantity"] < -1e-12:
                    cover_qty = min(qty, abs(ss["quantity"]))
                    cost = cover_qty * price
                    ss["investment"] += cost
                    ss["quantity"] += cover_qty
                    remaining = qty - cover_qty
                    if remaining > 1e-12:
                        new_cost = remaining * price
                        new_qty = ss["quantity"] + remaining
                        if new_qty > 1e-12:
                            ss["avg_price"] = (ss["quantity"] * ss["avg_price"] + new_cost) / new_qty
                        ss["investment"] += new_cost
                        ss["quantity"] = new_qty
                else:
                    cost = qty * price
                    new_qty = ss["quantity"] + qty
                    if new_qty > 1e-12:
                        ss["avg_price"] = (ss["quantity"] * ss["avg_price"] + cost) / new_qty
                    ss["investment"] += cost
                    ss["quantity"] = new_qty
            elif act_type == "SELL":
                if ss["quantity"] > 1e-12:
                    sell_qty = min(qty, ss["quantity"])
                    cost_returned = sell_qty * ss["avg_price"]
                    ss["investment"] -= cost_returned
                    ss["quantity"] -= sell_qty
                    remaining = qty - sell_qty
                    if remaining > 1e-12:
                        ss["quantity"] -= remaining
                        ss["avg_price"] = price
                else:
                    ss["quantity"] -= qty
                    if abs(ss["quantity"] + qty) < 1e-12:
                        ss["avg_price"] = price
                    else:
                        prev_qty = abs(ss["quantity"] + qty)
                        ss["avg_price"] = (prev_qty * abs(ss["avg_price"]) + qty * price) / (prev_qty + qty)

            act_idx += 1

        # Compute portfolio value
        total_value = 0.0
        cumulative_investment = 0.0
        for sym, ss in sym_state.items():
            cumulative_investment += ss["investment"]
            if abs(ss["quantity"]) > 1e-12:
                mp = _get_nearest_price(user, sym, chart_date)
                total_value += abs(ss["quantity"]) * mp

        net_perf = total_value - cumulative_investment - cumulative_fees
        net_perf_pct = net_perf / cumulative_investment if abs(cumulative_investment) > 1e-10 else 0.0

        chart.append({
            "date": chart_date,
            "netWorth": total_value,
            "value": total_value,
            "totalInvestment": cumulative_investment,
            "netPerformance": net_perf,
            "netPerformanceInPercentage": net_perf_pct,
            "netPerformanceInPercentageWithCurrencyEffect": net_perf_pct,
            "investmentValueWithCurrencyEffect": inv_delta_by_date.get(chart_date, 0.0),
        })

    return chart


# ---------------------------------------------------------------------------
# Portfolio — investments (v1)
# ---------------------------------------------------------------------------

_builtin_range = range  # save before FastAPI parameter shadows it

@app.get("/api/v1/portfolio/investments")
def get_investments(range: str = "max", groupBy: str | None = None, user: UserState = Depends(_get_user)) -> dict:
    if not user.activities:
        return {"investments": []}

    portfolio = _compute_portfolio(user)
    deltas = portfolio["investment_deltas"]

    if groupBy is None:
        by_date: dict[str, float] = {}
        for d in deltas:
            dt = d["date"]
            by_date[dt] = by_date.get(dt, 0.0) + d["investment"]
        investments = [
            {"date": dt, "investment": inv}
            for dt, inv in sorted(by_date.items())
            if abs(inv) > 1e-10
        ]
        return {"investments": investments}

    elif groupBy == "month":
        by_month: dict[str, float] = {}
        for d in deltas:
            dt = D.fromisoformat(d["date"])
            month_key = D(dt.year, dt.month, 1).isoformat()
            by_month[month_key] = by_month.get(month_key, 0.0) + d["investment"]

        activity_dates = [D.fromisoformat(a["date"]) for a in user.activities]
        first = min(activity_dates)
        end_date = D.today()

        all_months: list[str] = []
        current = D(first.year, first.month, 1)
        while current <= end_date:
            all_months.append(current.isoformat())
            if current.month == 12:
                current = D(current.year + 1, 1, 1)
            else:
                current = D(current.year, current.month + 1, 1)

        investments = [
            {"date": m, "investment": by_month.get(m, 0.0)}
            for m in all_months
        ]
        return {"investments": investments}

    elif groupBy == "year":
        by_year: dict[str, float] = {}
        for d in deltas:
            dt = D.fromisoformat(d["date"])
            year_key = D(dt.year, 1, 1).isoformat()
            by_year[year_key] = by_year.get(year_key, 0.0) + d["investment"]

        activity_dates = [D.fromisoformat(a["date"]) for a in user.activities]
        first_year = min(activity_dates).year
        last_year = D.today().year

        investments = [
            {"date": D(y, 1, 1).isoformat(), "investment": by_year.get(D(y, 1, 1).isoformat(), 0.0)}
            for y in _builtin_range(first_year, last_year + 1)
        ]
        return {"investments": investments}

    return {"investments": []}


# ---------------------------------------------------------------------------
# Portfolio — holdings (v1)
# ---------------------------------------------------------------------------

@app.get("/api/v1/portfolio/holdings")
def get_holdings(range: str = "max", user: UserState = Depends(_get_user)) -> dict:
    if not user.activities:
        return {"holdings": {}}

    portfolio = _compute_portfolio(user)
    symbols = portfolio["symbols"]

    holdings: dict[str, dict] = {}
    for sym, s in symbols.items():
        qty = s["quantity"]
        inv = s["investment"]
        if abs(qty) < 1e-12:
            continue

        current_price = _get_latest_market_price(user, sym)
        holdings[sym] = {
            "symbol": sym,
            "quantity": qty,
            "investment": inv,
            "marketPrice": current_price,
            "averagePrice": s["avg_price"],
        }

    return {"holdings": holdings}
