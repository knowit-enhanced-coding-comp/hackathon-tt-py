"""Mirrors portfolio.service.ts — orchestrates calculator and rate service.

In the original Ghostfolio this service is injected by NestJS and
coordinates between the PortfolioCalculatorFactory, CurrentRateService,
ExchangeRateDataService, and AccountBalanceService.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date as D, timedelta

from .calculator.roai.portfolio_calculator import RoaiPortfolioCalculator
from .current_rate_service import CurrentRateService


_TYPE_ORDER = {"BUY": 0, "SELL": 1, "DIVIDEND": 2, "FEE": 3, "LIABILITY": 4}


class PortfolioService:
    """Orchestrates portfolio calculations.

    Owns the high-level logic for performance, investments, and holdings
    endpoints. Delegates computation to the ROAI calculator and price
    lookups to the CurrentRateService.
    """

    def __init__(
        self,
        activities: list[dict],
        market_data: dict[str, dict[str, list[dict]]],
        base_currency: str = "USD",
    ) -> None:
        self._activities = activities
        self._base_currency = base_currency
        self._rate_service = CurrentRateService(market_data)
        self._calculator = RoaiPortfolioCalculator(activities, self._rate_service)
        self._portfolio: dict | None = None

    def _ensure_portfolio(self) -> dict:
        if self._portfolio is None:
            self._portfolio = self._calculator.compute()
        return self._portfolio

    # ------------------------------------------------------------------
    # Performance (GET /api/v2/portfolio/performance)
    # ------------------------------------------------------------------

    def get_performance(self) -> dict:
        if not self._activities:
            return self._empty_performance()

        portfolio = self._ensure_portfolio()
        symbols = portfolio["symbols"]
        total_fees = portfolio["total_fees"]

        total_investment = 0.0
        total_current_value = 0.0
        total_realized_pnl = 0.0
        total_twi = 0.0
        open_investment = 0.0

        for sym, s in symbols.items():
            qty = s["quantity"]
            inv = s["investment"]
            total_investment += inv

            if abs(qty) > 1e-12:
                current_price = self._rate_service.get_latest_price(sym)
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

        chart = self._build_chart(portfolio)
        first_date = min(a["date"] for a in self._activities)

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

    # ------------------------------------------------------------------
    # Investments (GET /api/v1/portfolio/investments)
    # ------------------------------------------------------------------

    def get_investments(self, group_by: str | None = None) -> dict:
        if not self._activities:
            return {"investments": []}

        deltas = self._ensure_portfolio()["investment_deltas"]

        if group_by is None:
            return self._investments_daily(deltas)
        elif group_by == "month":
            return self._investments_by_month(deltas)
        elif group_by == "year":
            return self._investments_by_year(deltas)
        return {"investments": []}

    # ------------------------------------------------------------------
    # Holdings (GET /api/v1/portfolio/holdings)
    # ------------------------------------------------------------------

    def get_holdings(self) -> dict:
        if not self._activities:
            return {"holdings": {}}

        symbols = self._ensure_portfolio()["symbols"]
        holdings: dict[str, dict] = {}

        for sym, s in symbols.items():
            if abs(s["quantity"]) < 1e-12:
                continue
            current_price = self._rate_service.get_latest_price(sym)
            holdings[sym] = {
                "symbol": sym,
                "quantity": s["quantity"],
                "investment": s["investment"],
                "marketPrice": current_price,
                "averagePrice": s["avg_price"],
            }

        return {"holdings": holdings}

    # ------------------------------------------------------------------
    # Details (GET /api/v1/portfolio/details)
    # ------------------------------------------------------------------

    def get_details(self) -> dict:
        if not self._activities:
            return {
                "accounts": {},
                "createdAt": None,
                "holdings": {},
                "platforms": {},
                "summary": {
                    "totalInvestment": 0,
                    "netPerformance": 0,
                    "currentValueInBaseCurrency": 0,
                },
                "hasError": False,
            }

        holdings = self._calculator.get_holding_details()

        # Aggregate summary from holdings
        portfolio = self._ensure_portfolio()
        symbols = portfolio["symbols"]
        total_fees = portfolio["total_fees"]
        total_investment = sum(s["investment"] for s in symbols.values())
        total_current_value = 0.0
        total_realized_pnl = 0.0

        for sym, s in symbols.items():
            if abs(s["quantity"]) > 1e-12:
                price = self._rate_service.get_latest_price(sym)
                total_current_value += abs(s["quantity"]) * price
            total_realized_pnl += s["realized_pnl"]

        open_investment = sum(
            s["investment"] for s in symbols.values() if abs(s["quantity"]) > 1e-12
        )
        unrealized_pnl = total_current_value - open_investment
        net_performance = total_realized_pnl + unrealized_pnl - total_fees

        return {
            "accounts": {
                "default": {
                    "balance": 0.0,
                    "currency": self._base_currency,
                    "name": "Default Account",
                    "valueInBaseCurrency": total_current_value,
                }
            },
            "createdAt": min(a["date"] for a in self._activities),
            "holdings": holdings,
            "platforms": {
                "default": {
                    "balance": 0.0,
                    "currency": self._base_currency,
                    "name": "Default Platform",
                    "valueInBaseCurrency": total_current_value,
                }
            },
            "summary": {
                "totalInvestment": total_investment,
                "netPerformance": net_performance,
                "currentValueInBaseCurrency": total_current_value,
                "totalFees": total_fees,
            },
            "hasError": False,
        }

    # ------------------------------------------------------------------
    # Dividends (GET /api/v1/portfolio/dividends)
    # ------------------------------------------------------------------

    def get_dividends(self, group_by: str | None = None) -> dict:
        dividends = self._calculator.get_dividends(group_by=group_by)
        return {"dividends": dividends}

    # ------------------------------------------------------------------
    # Report (GET /api/v1/portfolio/report)
    # ------------------------------------------------------------------

    def get_report(self) -> dict:
        return self._calculator.evaluate_report()

    # ------------------------------------------------------------------
    # Chart (historicalData equivalent)
    # ------------------------------------------------------------------

    def _build_chart(self, portfolio: dict) -> list[dict]:
        if not self._activities:
            return []

        activity_dates = [a["date"] for a in self._activities]
        first_date = min(activity_dates)
        start = D.fromisoformat(first_date) - timedelta(days=1)
        end = D.today()

        chart_dates: set[str] = {start.isoformat()}
        for a in self._activities:
            d = D.fromisoformat(a["date"])
            if start <= d <= end:
                chart_dates.add(a["date"])

        chart_dates.update(
            self._rate_service.all_dates_in_range(start.isoformat(), end.isoformat())
        )

        for year in range(start.year, end.year + 1):
            for boundary in (D(year, 1, 1), D(year, 12, 31)):
                if start < boundary <= end:
                    chart_dates.add(boundary.isoformat())
        chart_dates.add(end.isoformat())

        sorted_dates = sorted(chart_dates)

        inv_delta_by_date: dict[str, float] = defaultdict(float)
        for d in portfolio["investment_deltas"]:
            inv_delta_by_date[d["date"]] += d["investment"]

        sorted_acts = sorted(
            self._activities,
            key=lambda a: (a["date"], _TYPE_ORDER.get(a.get("type", ""), 5)),
        )

        chart = []
        sym_state: dict[str, dict] = {}
        cumulative_fees = 0.0
        act_idx = 0

        for chart_date in sorted_dates:
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
                    self._chart_buy(ss, qty, price)
                elif act_type == "SELL":
                    self._chart_sell(ss, qty, price)

                act_idx += 1

            total_value = 0.0
            cumulative_investment = 0.0
            for sym, ss in sym_state.items():
                cumulative_investment += ss["investment"]
                if abs(ss["quantity"]) > 1e-12:
                    mp = self._rate_service.get_nearest_price(sym, chart_date)
                    total_value += abs(ss["quantity"]) * mp

            net_perf = total_value - cumulative_investment - cumulative_fees
            net_perf_pct = (
                net_perf / cumulative_investment
                if abs(cumulative_investment) > 1e-10
                else 0.0
            )

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

    # -- chart-local position replay (mirrors calculator logic) ---------

    @staticmethod
    def _chart_buy(ss: dict, qty: float, price: float) -> None:
        if ss["quantity"] < -1e-12:
            cover_qty = min(qty, abs(ss["quantity"]))
            ss["investment"] += cover_qty * price
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

    @staticmethod
    def _chart_sell(ss: dict, qty: float, price: float) -> None:
        if ss["quantity"] > 1e-12:
            sell_qty = min(qty, ss["quantity"])
            ss["investment"] -= sell_qty * ss["avg_price"]
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

    # ------------------------------------------------------------------
    # Investment grouping helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _investments_daily(deltas: list[dict]) -> dict:
        by_date: dict[str, float] = {}
        for d in deltas:
            by_date[d["date"]] = by_date.get(d["date"], 0.0) + d["investment"]
        return {
            "investments": [
                {"date": dt, "investment": inv}
                for dt, inv in sorted(by_date.items())
                if abs(inv) > 1e-10
            ]
        }

    def _investments_by_month(self, deltas: list[dict]) -> dict:
        by_month: dict[str, float] = {}
        for d in deltas:
            dt = D.fromisoformat(d["date"])
            key = D(dt.year, dt.month, 1).isoformat()
            by_month[key] = by_month.get(key, 0.0) + d["investment"]

        first = min(D.fromisoformat(a["date"]) for a in self._activities)
        end_date = D.today()
        months: list[str] = []
        cur = D(first.year, first.month, 1)
        while cur <= end_date:
            months.append(cur.isoformat())
            cur = D(cur.year + 1, 1, 1) if cur.month == 12 else D(cur.year, cur.month + 1, 1)

        return {"investments": [{"date": m, "investment": by_month.get(m, 0.0)} for m in months]}

    def _investments_by_year(self, deltas: list[dict]) -> dict:
        by_year: dict[str, float] = {}
        for d in deltas:
            dt = D.fromisoformat(d["date"])
            key = D(dt.year, 1, 1).isoformat()
            by_year[key] = by_year.get(key, 0.0) + d["investment"]

        first_year = min(D.fromisoformat(a["date"]) for a in self._activities).year
        last_year = D.today().year

        return {
            "investments": [
                {"date": D(y, 1, 1).isoformat(), "investment": by_year.get(D(y, 1, 1).isoformat(), 0.0)}
                for y in range(first_year, last_year + 1)
            ]
        }

    # ------------------------------------------------------------------
    @staticmethod
    def _empty_performance() -> dict:
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
