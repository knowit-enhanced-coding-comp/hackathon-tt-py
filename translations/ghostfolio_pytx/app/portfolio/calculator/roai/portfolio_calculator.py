"""Mirrors calculator/roai/portfolio-calculator.ts — ROAI implementation.

Return on Annualized Investment calculator. Processes activities
chronologically, tracks average cost basis, and computes realized /
unrealized P&L with time-weighted investment as the denominator for
closed positions.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date as D

from ..portfolio_calculator import PortfolioCalculator
from ...interfaces import SymbolMetrics


class RoaiPortfolioCalculator(PortfolioCalculator):
    """ROAI (Return on Annualized Investment) calculator."""

    def compute(self) -> dict:
        sorted_acts = self.sorted_activities()

        symbols: dict[str, dict] = {}
        investment_deltas: list[dict] = []
        total_fees = 0.0
        symbol_fees: dict[str, float] = {}

        for act in sorted_acts:
            sym = act.get("symbol", "")
            act_type = act.get("type", "BUY")
            qty = float(act.get("quantity") or 0)
            price = float(act.get("unitPrice") or 0)
            fee = float(act.get("fee") or 0)
            act_date = act.get("date", "")

            total_fees += fee
            if sym:
                symbol_fees[sym] = symbol_fees.get(sym, 0.0) + fee

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
                self._process_buy(s, qty, price, act_date, investment_deltas, sym)
            elif act_type == "SELL":
                self._process_sell(s, qty, price, act_date, investment_deltas, sym)

        return {
            "symbols": symbols,
            "investment_deltas": investment_deltas,
            "total_fees": total_fees,
            "sorted_activities": sorted_acts,
            "symbol_fees": symbol_fees,
        }

    def get_symbol_metrics(self, symbol: str) -> SymbolMetrics:
        result = self._ensure_computed()
        s = result["symbols"].get(symbol)
        if s is None:
            return SymbolMetrics()
        return SymbolMetrics(
            quantity=s["quantity"],
            investment=s["investment"],
            avg_price=s["avg_price"],
            total_buy_cost=s["total_buy_cost"],
            realized_pnl=s["realized_pnl"],
        )

    # ------------------------------------------------------------------
    # Holding details (for GET /portfolio/details)
    # ------------------------------------------------------------------

    def get_holding_details(self) -> dict[str, dict]:
        """Compute per-symbol holding details with performance metrics.

        Returns dict keyed by symbol. Each value contains: symbol, quantity,
        investment, marketPrice, netPerformance, netPerformancePercent,
        grossPerformance, grossPerformancePercent, valueInBaseCurrency,
        activitiesCount, dividend.
        """
        result = self._ensure_computed()
        symbols = result["symbols"]
        sym_fees = result["symbol_fees"]

        holdings: dict[str, dict] = {}
        for sym, s in symbols.items():
            qty = s["quantity"]
            inv = s["investment"]
            current_price = self.current_rate_service.get_latest_price(sym)
            current_value = abs(qty) * current_price if abs(qty) > 1e-12 else 0.0
            fees = sym_fees.get(sym, 0.0)

            # netPerformance = unrealized + realized - fees
            net_perf = (current_value - inv) + s["realized_pnl"] - fees

            if abs(inv) > 1e-10:
                net_perf_pct = net_perf / inv
            elif s["total_buy_cost"] > 1e-10:
                net_perf_pct = net_perf / s["total_buy_cost"]
            else:
                net_perf_pct = 0.0

            gross_perf = (current_value - inv) + s["realized_pnl"]
            if abs(inv) > 1e-10:
                gross_perf_pct = gross_perf / inv
            elif s["total_buy_cost"] > 1e-10:
                gross_perf_pct = gross_perf / s["total_buy_cost"]
            else:
                gross_perf_pct = 0.0

            holdings[sym] = {
                "symbol": sym,
                "quantity": qty,
                "investment": inv,
                "marketPrice": current_price,
                "averagePrice": s["avg_price"],
                "netPerformance": net_perf,
                "netPerformancePercent": net_perf_pct,
                "netPerformancePercentWithCurrencyEffect": net_perf_pct,
                "grossPerformance": gross_perf,
                "grossPerformancePercent": gross_perf_pct,
                "grossPerformancePercentWithCurrencyEffect": gross_perf_pct,
                "grossPerformanceWithCurrencyEffect": gross_perf,
                "netPerformanceWithCurrencyEffect": net_perf,
                "valueInBaseCurrency": current_value,
                "allocationInPercentage": 0.0,
                "activitiesCount": self._count_activities(sym),
                "dividend": self._total_dividends(sym),
                "dateOfFirstActivity": self._first_activity_date(sym),
            }

        return holdings

    # ------------------------------------------------------------------
    # Dividends (for GET /portfolio/dividends)
    # ------------------------------------------------------------------

    def get_dividends(self, group_by: str | None = None) -> list[dict]:
        """Extract DIVIDEND activities and return as investment items.

        Each item: {"date": str, "investment": float} where
        investment = quantity × unitPrice.
        """
        dividend_acts = [
            a for a in self.activities if a.get("type") == "DIVIDEND"
        ]
        if not dividend_acts:
            return []

        items: list[dict] = []
        for act in dividend_acts:
            qty = float(act.get("quantity") or 0)
            price = float(act.get("unitPrice") or 0)
            items.append({
                "date": act["date"],
                "investment": qty * price,
            })

        if group_by is None:
            return self._group_dividends_daily(items)
        elif group_by == "month":
            return self._group_dividends_by_month(items)
        elif group_by == "year":
            return self._group_dividends_by_year(items)
        return items

    # ------------------------------------------------------------------
    # Report (for GET /portfolio/report)
    # ------------------------------------------------------------------

    def evaluate_report(self) -> dict:
        """Evaluate portfolio rules and return x-ray report.

        Returns dict with xRay containing categories (list of rule groups)
        and statistics (active/fulfilled rule counts).
        """
        result = self._ensure_computed()
        symbols = result["symbols"]
        total_fees = result["total_fees"]

        has_holdings = any(
            abs(s["quantity"]) > 1e-12 for s in symbols.values()
        )

        total_investment = sum(s["investment"] for s in symbols.values())
        currencies = set(
            a.get("currency", "")
            for a in self.activities
            if a.get("type") in ("BUY", "SELL") and a.get("currency")
        )

        fee_ratio = (
            total_fees / total_investment
            if abs(total_investment) > 1e-10
            else 0.0
        )

        categories = [
            {
                "key": "accounts",
                "name": "Accounts",
                "rules": [
                    {
                        "key": "accountClusterRisk",
                        "name": "Account Cluster Risk",
                        "isActive": has_holdings,
                        "value": False,
                    },
                ],
            },
            {
                "key": "currencies",
                "name": "Currencies",
                "rules": [
                    {
                        "key": "currencyClusterRisk",
                        "name": "Currency Cluster Risk",
                        "isActive": has_holdings,
                        "value": len(currencies) > 1,
                    },
                ],
            },
            {
                "key": "fees",
                "name": "Fees",
                "rules": [
                    {
                        "key": "feeRatio",
                        "name": "Fee Ratio",
                        "isActive": has_holdings and total_fees > 0,
                        "value": fee_ratio < 0.015,
                    },
                ],
            },
        ]

        active = sum(
            1 for cat in categories for r in cat["rules"] if r["isActive"]
        )
        fulfilled = sum(
            1
            for cat in categories
            for r in cat["rules"]
            if r["isActive"] and r.get("value")
        )

        return {
            "xRay": {
                "categories": categories,
                "statistics": {
                    "rulesActiveCount": active,
                    "rulesFulfilledCount": fulfilled,
                },
            }
        }

    # ------------------------------------------------------------------
    # Transaction processing (computeTransactionPoints equivalent)
    # ------------------------------------------------------------------

    @staticmethod
    def _process_buy(
        s: dict, qty: float, price: float, act_date: str,
        deltas: list[dict], sym: str,
    ) -> None:
        if s["quantity"] < -1e-12:
            # BUY to cover short: investment uses BUY unitPrice
            cover_qty = min(qty, abs(s["quantity"]))
            cost = cover_qty * price
            s["realized_pnl"] += cover_qty * (abs(s["avg_price"]) - price)
            s["investment"] += cost
            s["total_buy_cost"] += cost
            deltas.append({"date": act_date, "investment": cost, "symbol": sym})
            remaining = qty - cover_qty
            s["quantity"] += cover_qty
            if remaining > 1e-12:
                new_cost = remaining * price
                new_qty = s["quantity"] + remaining
                if new_qty > 1e-12:
                    s["avg_price"] = (s["quantity"] * s["avg_price"] + new_cost) / new_qty
                s["investment"] += new_cost
                s["total_buy_cost"] += new_cost
                s["quantity"] = new_qty
                deltas.append({"date": act_date, "investment": new_cost, "symbol": sym})
        else:
            # BUY into long position
            cost = qty * price
            new_qty = s["quantity"] + qty
            if new_qty > 1e-12:
                s["avg_price"] = (s["quantity"] * s["avg_price"] + cost) / new_qty
            s["investment"] += cost
            s["total_buy_cost"] += cost
            s["quantity"] = new_qty
            deltas.append({"date": act_date, "investment": cost, "symbol": sym})

    @staticmethod
    def _process_sell(
        s: dict, qty: float, price: float, act_date: str,
        deltas: list[dict], sym: str,
    ) -> None:
        if s["quantity"] > 1e-12:
            # SELL from long position
            sell_qty = min(qty, s["quantity"])
            cost_returned = sell_qty * s["avg_price"]
            s["realized_pnl"] += sell_qty * (price - s["avg_price"])
            s["investment"] -= cost_returned
            deltas.append({"date": act_date, "investment": -cost_returned, "symbol": sym})
            s["quantity"] -= sell_qty
            remaining = qty - sell_qty
            if remaining > 1e-12:
                s["quantity"] -= remaining
                s["avg_price"] = price
        else:
            # SELL to open/extend short
            s["quantity"] -= qty
            if abs(s["quantity"] + qty) < 1e-12:
                s["avg_price"] = price
            else:
                prev_qty = abs(s["quantity"] + qty)
                s["avg_price"] = (prev_qty * abs(s["avg_price"]) + qty * price) / (prev_qty + qty)
            # Record short sell in deltas for investments endpoint
            deltas.append({"date": act_date, "investment": -qty * price, "symbol": sym})

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _count_activities(self, symbol: str) -> int:
        return sum(1 for a in self.activities if a.get("symbol") == symbol)

    def _total_dividends(self, symbol: str) -> float:
        return sum(
            float(a.get("quantity") or 0) * float(a.get("unitPrice") or 0)
            for a in self.activities
            if a.get("symbol") == symbol and a.get("type") == "DIVIDEND"
        )

    def _first_activity_date(self, symbol: str) -> str | None:
        dates = [a["date"] for a in self.activities if a.get("symbol") == symbol]
        return min(dates) if dates else None

    @staticmethod
    def _group_dividends_daily(items: list[dict]) -> list[dict]:
        by_date: dict[str, float] = {}
        for item in items:
            by_date[item["date"]] = by_date.get(item["date"], 0.0) + item["investment"]
        return [
            {"date": dt, "investment": inv}
            for dt, inv in sorted(by_date.items())
        ]

    @staticmethod
    def _group_dividends_by_month(items: list[dict]) -> list[dict]:
        by_month: dict[str, float] = {}
        for item in items:
            dt = D.fromisoformat(item["date"])
            key = D(dt.year, dt.month, 1).isoformat()
            by_month[key] = by_month.get(key, 0.0) + item["investment"]
        return [
            {"date": dt, "investment": inv}
            for dt, inv in sorted(by_month.items())
        ]

    @staticmethod
    def _group_dividends_by_year(items: list[dict]) -> list[dict]:
        by_year: dict[str, float] = {}
        for item in items:
            dt = D.fromisoformat(item["date"])
            key = D(dt.year, 1, 1).isoformat()
            by_year[key] = by_year.get(key, 0.0) + item["investment"]
        return [
            {"date": dt, "investment": inv}
            for dt, inv in sorted(by_year.items())
        ]
