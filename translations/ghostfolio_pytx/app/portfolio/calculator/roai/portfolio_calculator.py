"""Mirrors calculator/roai/portfolio-calculator.ts — ROAI implementation.

Return on Annualized Investment calculator. Processes activities
chronologically, tracks average cost basis, and computes realized /
unrealized P&L with time-weighted investment as the denominator for
closed positions.
"""
from __future__ import annotations

from ..portfolio_calculator import PortfolioCalculator
from ...interfaces import SymbolMetrics


class RoaiPortfolioCalculator(PortfolioCalculator):
    """ROAI (Return on Annualized Investment) calculator."""

    def compute(self) -> dict:
        sorted_acts = self.sorted_activities()

        symbols: dict[str, dict] = {}
        investment_deltas: list[dict] = []
        total_fees = 0.0

        for act in sorted_acts:
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
                self._process_buy(s, qty, price, act_date, investment_deltas, sym)
            elif act_type == "SELL":
                self._process_sell(s, qty, price, act_date, investment_deltas, sym)

        return {
            "symbols": symbols,
            "investment_deltas": investment_deltas,
            "total_fees": total_fees,
            "sorted_activities": sorted_acts,
        }

    def get_symbol_metrics(self, symbol: str) -> SymbolMetrics:
        result = self.compute()
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
