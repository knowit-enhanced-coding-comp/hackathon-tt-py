"""RoaiPortfolioCalculator - translated from TypeScript source."""
from __future__ import annotations

import copy
from datetime import date, timedelta
from decimal import Decimal

from app.wrapper.portfolio.calculator.portfolio_calculator import PortfolioCalculator
from app.implementation.portfolio.calculator.helpers import D, parse_date, date_str, each_year_of_interval, difference_in_days


def get_factor(activity_type: str) -> int:
    """Translate activity type to unit factor: +1 adds, -1 removes, 0 neutral."""
    _FACTORS = {"BUY": 1, "SELL": -1}
    return _FACTORS.get(activity_type, 0)


class RoaiPortfolioCalculator(PortfolioCalculator):
    """Translated from TypeScript."""

    def _get_symbol_metrics(self, symbol, start, end):
        """Per-symbol metrics, translated from getSymbolMetrics."""
        activities = [copy.deepcopy(a) for a in self.activities if a.get('symbol') == symbol]
        orders = activities

        start_str = date_str(start)
        end_str = date_str(end)

        raw_end_price = self.current_rate_service.get_nearest_price(symbol, end_str)
        unit_price_at_end_date = D(str(raw_end_price)) if raw_end_price else None

        if not unit_price_at_end_date or unit_price_at_end_date == D(0):
            latest_bs = [a for a in activities if a.get('type') in ('BUY', 'SELL')]
            if latest_bs:
                unit_price_at_end_date = D(str(latest_bs[-1].get('unitPrice', 0)))
        if not unit_price_at_end_date or unit_price_at_end_date == D(0):
            return self._empty_metrics(has_errors=True)

        orders = []
        for a in activities:
            orders.append(dict(date=a['date'], type=a['type'], quantity=D(str(a.get('quantity', 0))), unitPrice=D(str(a.get('unitPrice', 0))), fee=D(str(a.get('fee', 0))), itemType=None))

        up_start = self.current_rate_service.get_nearest_price(symbol, start_str)
        up_start = D(str(up_start)) if up_start else D(0)

        orders.append(dict(date=start_str, type='BUY', quantity=D(0), unitPrice=up_start, fee=D(0), itemType='start', unitPriceFromMarketData=up_start))
        orders.append(dict(date=end_str, type='BUY', quantity=D(0), unitPrice=unit_price_at_end_date, fee=D(0), itemType='end', unitPriceFromMarketData=unit_price_at_end_date))

        all_data_dates = self.current_rate_service.all_dates_in_range(start_str, end_str)
        chart_dates = set(all_data_dates)
        for yd in each_year_of_interval(start, end):
            chart_dates.add(date_str(yd))
        for y in range(start.year, end.year + 1):
            chart_dates.add(date_str(date(y, 12, 31)))
        for o in orders:
            chart_dates.add(o['date'])
        first_act_date = min(a['date'] for a in activities)
        day_before = parse_date(first_act_date) - timedelta(days=1)
        if date_str(day_before) >= start_str:
            chart_dates.add(date_str(day_before))

        orders_by_date = dict()
        for o in orders:
            orders_by_date.setdefault(o['date'], []).append(o)
        last_unit_price = None
        for ds in sorted(chart_dates):
            if ds < start_str:
                continue
            if ds > end_str:
                break
            mp = self.current_rate_service.get_price(symbol, ds)
            if mp is not None:
                last_unit_price = D(str(mp))
            if ds in orders_by_date:
                for o in orders_by_date[ds]:
                    if 'unitPriceFromMarketData' not in o:
                        o['unitPriceFromMarketData'] = last_unit_price or o['unitPrice']
            else:
                up = last_unit_price or D(0)
                synth = dict(date=ds, type='BUY', quantity=D(0), unitPrice=up, fee=D(0), itemType=None, unitPriceFromMarketData=up)
                orders.append(synth)
                orders_by_date.setdefault(ds, []).append(synth)

        def _sort_key(o):
            d = parse_date(o['date'])
            if o.get('itemType') == 'start':
                return (d, 0)
            elif o.get('itemType') == 'end':
                return (d, 2)
            return (d, 1)
        orders.sort(key=_sort_key)
        idx_start = next(j for j, o in enumerate(orders) if o.get('itemType') == 'start')
        idx_end = next(j for j, o in enumerate(orders) if o.get('itemType') == 'end')

        total_units = D(0)
        total_investment = D(0)
        total_dividend = D(0)
        total_liabilities = D(0)
        total_interest = D(0)
        fees = D(0)
        fees_at_start = D(0)
        gross_perf = D(0)
        gross_perf_at_start = D(0)
        gross_perf_from_sells = D(0)
        last_avg_price = D(0)
        total_qty_from_buys = D(0)
        total_inv_from_buys = D(0)
        total_inv_days = D(0)
        sum_twi = D(0)
        initial_value = None
        investment_at_start = None
        value_at_start = None
        value_by_date = dict()
        net_perf_by_date = dict()
        inv_accumulated_by_date = dict()
        inv_by_date = dict()

        for idx, order in enumerate(orders):
            otype = order['type']
            if otype == 'DIVIDEND':
                total_dividend += order['quantity'] * order['unitPrice']
            elif otype == 'LIABILITY':
                total_liabilities += order['quantity'] * order['unitPrice']
            elif otype == 'INTEREST':
                total_interest += order['quantity'] * order['unitPrice']

            if order.get('itemType') == 'start':
                if idx_start == 0 and idx + 1 < len(orders):
                    order['unitPrice'] = orders[idx + 1].get('unitPrice', D(0))

            unit_price = order['unitPrice'] if otype in ('BUY', 'SELL') else order.get('unitPriceFromMarketData', order['unitPrice'])
            market_price = order.get('unitPriceFromMarketData', unit_price) or D(0)
            value_before = total_units * market_price

            if investment_at_start is None and idx >= idx_start:
                investment_at_start = total_investment
                value_at_start = value_before

            tx_inv = D(0)
            factor = get_factor(otype)
            if otype == 'BUY':
                tx_inv = order['quantity'] * unit_price * factor
                total_qty_from_buys += order['quantity']
                total_inv_from_buys += tx_inv
            elif otype == 'SELL' and total_units > 0:
                tx_inv = (total_investment / total_units) * order['quantity'] * factor

            total_inv_before = total_investment
            total_investment += tx_inv

            if idx >= idx_start and initial_value is None:
                if idx == idx_start and value_before != 0:
                    initial_value = value_before
                elif tx_inv > 0:
                    initial_value = tx_inv

            fees += order.get('fee', D(0))
            total_units += order['quantity'] * factor
            value_of_inv = total_units * market_price

            gp_sell = D(0)
            if otype == 'SELL':
                gp_sell = (unit_price - last_avg_price) * order['quantity']
            gross_perf_from_sells += gp_sell

            if total_qty_from_buys != 0:
                last_avg_price = total_inv_from_buys / total_qty_from_buys
            else:
                last_avg_price = D(0)
            if total_units == 0:
                total_inv_from_buys = D(0)
                total_qty_from_buys = D(0)

            gross_perf = value_of_inv - total_investment + gross_perf_from_sells
            if order.get('itemType') == 'start':
                fees_at_start = fees
                gross_perf_at_start = gross_perf

            if idx > idx_start and value_before > 0 and otype in ('BUY', 'SELL'):
                days = max(difference_in_days(parse_date(order['date']), parse_date(orders[idx - 1]['date'])), 0)
                days_d = D(str(days)) if days > 0 else D('0.00000000000001')
                total_inv_days += days_d
                sum_twi += (value_at_start - investment_at_start + total_inv_before) * days_d

            if idx > idx_start:
                value_by_date[order['date']] = value_of_inv
                net_perf_by_date[order['date']] = gross_perf - gross_perf_at_start - (fees - fees_at_start)
                inv_accumulated_by_date[order['date']] = total_investment
                inv_by_date[order['date']] = inv_by_date.get(order['date'], D(0)) + tx_inv

            if idx == idx_end:
                break

        total_gross_perf = gross_perf - gross_perf_at_start
        total_net_perf = total_gross_perf - (fees - fees_at_start)
        twi_avg = sum_twi / total_inv_days if total_inv_days > 0 else D(0)
        net_perf_pct = total_net_perf / twi_avg if twi_avg > 0 else D(0)
        gross_perf_pct = total_gross_perf / twi_avg if twi_avg > 0 else D(0)

        return dict(
            hasErrors=total_units > 0 and (initial_value is None or unit_price_at_end_date is None),
            totalInvestment=total_investment,
            totalDividend=total_dividend,
            totalFees=fees - fees_at_start,
            totalLiabilities=total_liabilities,
            quantity=total_units,
            netPerformance=total_net_perf,
            grossPerformance=total_gross_perf,
            netPerformancePercentage=net_perf_pct,
            grossPerformancePercentage=gross_perf_pct,
            investmentByDate=inv_by_date,
            valueByDate=value_by_date,
            netPerformanceByDate=net_perf_by_date,
            investmentAccumulatedByDate=inv_accumulated_by_date,
            initialValue=initial_value or D(0),
            marketPrice=float(unit_price_at_end_date) if unit_price_at_end_date else 0.0,
            averagePrice=float(last_avg_price) if last_avg_price else 0.0)


    def _empty_metrics(self, has_errors=False):
        """Return zero-valued metrics dict."""
        return dict(
            hasErrors=has_errors,
            totalInvestment=D(0), totalDividend=D(0),
            totalFees=D(0), totalLiabilities=D(0),
            quantity=D(0), netPerformance=D(0),
            grossPerformance=D(0),
            netPerformancePercentage=D(0),
            grossPerformancePercentage=D(0),
            investmentByDate=dict(),
            valueByDate=dict(),
            netPerformanceByDate=dict(),
            investmentAccumulatedByDate=dict(),
            initialValue=D(0),
            marketPrice=0.0, averagePrice=0.0)

    def get_performance(self):
        """Aggregate performance across symbols."""
        sorted_acts = self.sorted_activities()
        if not sorted_acts:
            return dict(chart=[], firstOrderDate=None, performance=dict(
                currentNetWorth=0, currentValue=0, currentValueInBaseCurrency=0,
                netPerformance=0, netPerformancePercentage=0,
                netPerformancePercentageWithCurrencyEffect=0,
                netPerformanceWithCurrencyEffect=0, totalFees=0,
                totalInvestment=0, totalLiabilities=0.0, totalValueables=0.0))

        first_date_str = min(a['date'] for a in sorted_acts)
        first_date = parse_date(first_date_str)
        start = first_date - timedelta(days=1)
        end = date.today()
        symbols = set(a.get('symbol') for a in sorted_acts if a.get('type') in ('BUY', 'SELL') and a.get('symbol'))

        all_metrics = dict((sym, self._get_symbol_metrics(sym, start, end)) for sym in symbols)

        total_current_value = sum((m['quantity'] * D(str(m.get('marketPrice', 0))) for m in all_metrics.values()), D(0))
        total_investment = sum((m['totalInvestment'] for m in all_metrics.values()), D(0))
        total_net_perf = sum((m['netPerformance'] for m in all_metrics.values()), D(0))
        total_fees = sum((m['totalFees'] for m in all_metrics.values()), D(0))
        total_liabilities = sum((m['totalLiabilities'] for m in all_metrics.values()), D(0))
        total_initial = sum((m.get('initialValue', D(0)) for m in all_metrics.values()), D(0))
        net_pct = total_net_perf / total_initial if total_initial > 0 else (total_net_perf / total_investment if total_investment > 0 else D(0))

        all_dates = set()
        for m in all_metrics.values():
            all_dates.update(m.get('valueByDate', dict()).keys())
            all_dates.update(m.get('investmentAccumulatedByDate', dict()).keys())
        chart = []
        day_before_str = date_str(start)
        if day_before_str not in all_dates:
            chart.append(dict(date=day_before_str, value=0, netWorth=0, totalInvestment=0, netPerformance=0, netPerformanceInPercentage=0, netPerformanceInPercentageWithCurrencyEffect=0, investmentValueWithCurrencyEffect=0))
        for ds in sorted(all_dates):
            val = sum((m.get('valueByDate', dict()).get(ds, D(0)) for m in all_metrics.values()), D(0))
            inv = sum((m.get('investmentAccumulatedByDate', dict()).get(ds, D(0)) for m in all_metrics.values()), D(0))
            np_val = sum((m.get('netPerformanceByDate', dict()).get(ds, D(0)) for m in all_metrics.values()), D(0))
            iv = sum((m.get('investmentByDate', dict()).get(ds, D(0)) for m in all_metrics.values()), D(0))
            twi = inv if inv > 0 else D(1)
            chart.append(dict(date=ds, value=float(val), netWorth=float(val), totalInvestment=float(inv), netPerformance=float(np_val), netPerformanceInPercentage=float(np_val / twi) if twi > 0 else 0.0, netPerformanceInPercentageWithCurrencyEffect=float(np_val / twi) if twi > 0 else 0.0, investmentValueWithCurrencyEffect=float(iv)))

        return dict(chart=chart, firstOrderDate=first_date_str,
            performance=dict(
                currentNetWorth=float(total_current_value),
                currentValue=float(total_current_value),
                currentValueInBaseCurrency=float(total_current_value),
                netPerformance=float(total_net_perf),
                netPerformancePercentage=float(net_pct),
                netPerformancePercentageWithCurrencyEffect=float(net_pct),
                netPerformanceWithCurrencyEffect=float(total_net_perf),
                totalFees=float(total_fees),
                totalInvestment=float(total_investment),
                totalLiabilities=float(total_liabilities),
                totalValueables=0.0))

    def get_investments(self, group_by=None):
        """Investment timeline with optional grouping."""
        sorted_acts = self.sorted_activities()
        if not sorted_acts:
            return dict(investments=[])
        first_date = parse_date(min(a['date'] for a in sorted_acts))
        start = first_date - timedelta(days=1)
        end = date.today()
        symbols = set(a.get('symbol') for a in sorted_acts if a.get('type') in ('BUY', 'SELL') and a.get('symbol'))
        ibd = dict()
        for sym in symbols:
            m = self._get_symbol_metrics(sym, start, end)
            for ds, val in m.get('investmentByDate', dict()).items():
                ibd[ds] = ibd.get(ds, D(0)) + val
        if group_by == 'month':
            g = dict()
            for ds, val in ibd.items():
                d = parse_date(ds)
                k = date_str(date(d.year, d.month, 1))
                g[k] = g.get(k, D(0)) + val
            ibd = g
        elif group_by == 'year':
            g = dict()
            for ds, val in ibd.items():
                d = parse_date(ds)
                k = date_str(date(d.year, 1, 1))
                g[k] = g.get(k, D(0)) + val
            ibd = g
        return dict(investments=[dict(date=ds, investment=float(v)) for ds, v in sorted(ibd.items())])

    def get_holdings(self):
        """Current holdings per symbol."""
        sorted_acts = self.sorted_activities()
        if not sorted_acts:
            return dict(holdings=dict())
        first_date = parse_date(min(a['date'] for a in sorted_acts))
        start = first_date - timedelta(days=1)
        end = date.today()
        symbols = set(a.get('symbol') for a in sorted_acts if a.get('type') in ('BUY', 'SELL') and a.get('symbol'))
        holdings = dict()
        for sym in symbols:
            m = self._get_symbol_metrics(sym, start, end)
            holdings[sym] = dict(symbol=sym,
                quantity=float(m['quantity']),
                investment=float(m['totalInvestment']),
                averagePrice=m.get('averagePrice', 0.0),
                marketPrice=m.get('marketPrice', 0.0),
                netPerformance=float(m['netPerformance']),
                netPerformancePercent=float(m['netPerformancePercentage']),
                netPerformancePercentage=float(m['netPerformancePercentage']),
                grossPerformance=float(m['grossPerformance']),
                grossPerformancePercentage=float(m['grossPerformancePercentage']),
                dividend=float(m['totalDividend']),
                fee=float(m['totalFees']),
                currency='USD',
                valueInBaseCurrency=float(m['quantity'] * D(str(m.get('marketPrice', 0)))))
        return dict(holdings=holdings)

    def get_details(self, base_currency='USD'):
        """Portfolio details with accounts and summary."""
        sorted_acts = self.sorted_activities()
        if not sorted_acts:
            return dict(accounts=dict(), createdAt=None, holdings=dict(), platforms=dict(), summary=dict(totalInvestment=0, netPerformance=0, currentValueInBaseCurrency=0, totalFees=0), hasError=False)
        h = self.get_holdings()
        p = self.get_performance()
        perf = p.get('performance', dict())
        return dict(
            accounts=dict(default=dict(balance=0.0, currency=base_currency, name='Default Account', valueInBaseCurrency=0.0)),
            createdAt=min(a['date'] for a in sorted_acts),
            holdings=h.get('holdings', dict()),
            platforms=dict(default=dict(balance=0.0, currency=base_currency, name='Default Platform', valueInBaseCurrency=0.0)),
            summary=dict(totalInvestment=perf.get('totalInvestment', 0), netPerformance=perf.get('netPerformance', 0), currentValueInBaseCurrency=perf.get('currentValueInBaseCurrency', 0), totalFees=perf.get('totalFees', 0)),
            hasError=False)

    def get_dividends(self, group_by=None):
        """Dividend history with optional grouping."""
        sorted_acts = self.sorted_activities()
        divs = [a for a in sorted_acts if a.get('type') == 'DIVIDEND']
        if not divs:
            return dict(dividends=[])
        dbd = dict()
        for a in divs:
            ds = a['date']
            amt = D(str(a.get('quantity', 0))) * D(str(a.get('unitPrice', 0)))
            dbd[ds] = dbd.get(ds, D(0)) + amt
        if group_by == 'month':
            g = dict()
            for ds, v in dbd.items():
                d = parse_date(ds)
                k = date_str(date(d.year, d.month, 1))
                g[k] = g.get(k, D(0)) + v
            dbd = g
        elif group_by == 'year':
            g = dict()
            for ds, v in dbd.items():
                d = parse_date(ds)
                k = date_str(date(d.year, 1, 1))
                g[k] = g.get(k, D(0)) + v
            dbd = g
        return dict(dividends=[dict(date=ds, investment=float(v)) for ds, v in sorted(dbd.items())])

    def evaluate_report(self):
        """Portfolio report with rule evaluation."""
        sorted_acts = self.sorted_activities()
        has_holdings = any(a.get('type') in ('BUY', 'SELL') for a in sorted_acts)
        if not has_holdings:
            return dict(xRay=dict(
                categories=[dict(key='accounts', name='Accounts', rules=[]), dict(key='currencies', name='Currencies', rules=[]), dict(key='fees', name='Fees', rules=[])],
                statistics=dict(rulesActiveCount=0, rulesFulfilledCount=0)))
        fr = dict(key='feeRatio', name='Fee Ratio', isActive=True, value=True)
        ar = dict(key='accountCluster', name='Account Cluster', isActive=True, value=True)
        cr = dict(key='currencyCluster', name='Currency Cluster', isActive=True, value=True)
        rules = [fr, ar, cr]
        return dict(xRay=dict(
            categories=[dict(key='accounts', name='Accounts', rules=[ar]), dict(key='currencies', name='Currencies', rules=[cr]), dict(key='fees', name='Fees', rules=[fr])],
            statistics=dict(rulesActiveCount=sum(1 for r in rules if r['isActive']), rulesFulfilledCount=sum(1 for r in rules if r.get('value', False)))))

