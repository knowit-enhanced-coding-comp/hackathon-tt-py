# Translated from: /Users/paalvibe/dev/work/knowit/enhancedhackathon/ghostfolio/apps/api/src/app/portfolio/calculator/roai/portfolio-calculator.ts
# (rule-based translation — review before use)
from __future__ import annotations

import copy
import logging
import sys
from decimal import Decimal
from datetime import datetime, timedelta, date
from typing import Any, Awaitable, Optional

from app.helpers.date_fns import _add_milliseconds
from app.helpers.date_fns import _difference_in_days
from app.helpers.date_fns import _each_year_of_interval
from app.helpers.date_fns import _format_date
from app.helpers.date_fns import _is_before
from app.helpers.date_fns import _is_this_year
from app.helpers.lodash import _sort_by
from app.portfolio.calculator_base import PortfolioCalculator
from app.models import PortfolioOrderItem
from app.helpers.portfolio import get_factor
from app.helpers.calculation import get_interval_from_date_range
from app.helpers.common import DATE_FORMAT
from app.models import AssetProfileIdentifier, SymbolMetrics
from app.models import PortfolioSnapshot, TimelinePosition
from app.types import DateRange
from app.types import PerformanceCalculationType
# TS import skipped: import { Logger } from '@nestjs/common';
# TS import skipped: import { Big } from 'big.js';
# TS import skipped: import { addMilliseconds, differenceInDays, eachYearOfInterval, format, isBefore, isThisYear } from 'date-fns';
# TS import skipped: import { cloneDeep, sortBy } from 'lodash';




class RoaiPortfolioCalculator(PortfolioCalculator):
    chartDates: list[str]

    def calculateOverallPerformance(self, positions):
        currentValueInBaseCurrency = Decimal(0)
        grossPerformance = Decimal(0)
        grossPerformanceWithCurrencyEffect = Decimal(0)
        hasErrors = False
        netPerformance = Decimal(0)
        totalFeesWithCurrencyEffect = Decimal(0)
        totalInterestWithCurrencyEffect = Decimal(0)
        totalInvestment = Decimal(0)
        totalInvestmentWithCurrencyEffect = Decimal(0)
        totalTimeWeightedInvestment = Decimal(0)
        totalTimeWeightedInvestmentWithCurrencyEffect = Decimal(0)

        for (const currentPosition of positions.filter(
        ({ includeInTotalAssetValue }) => {
            return includeInTotalAssetValue
        )) {
            if currentPosition.feeInBaseCurrency:
                totalFeesWithCurrencyEffect = totalFeesWithCurrencyEffect + (
                currentPosition.feeInBaseCurrency
                )

            if currentPosition.valueInBaseCurrency:
                currentValueInBaseCurrency = currentValueInBaseCurrency + (
                currentPosition.valueInBaseCurrency
                )
                else:
                    hasErrors = True

                if currentPosition.investment:
                    totalInvestment = totalInvestment + (currentPosition.investment)

                    totalInvestmentWithCurrencyEffect =
                    totalInvestmentWithCurrencyEffect + (
                    currentPosition.investmentWithCurrencyEffect
                    )
                    else:
                        hasErrors = True

                    if currentPosition.grossPerformance:
                        grossPerformance = grossPerformance + (
                        currentPosition.grossPerformance
                        )

                        grossPerformanceWithCurrencyEffect =
                        grossPerformanceWithCurrencyEffect + (
                        currentPosition.grossPerformanceWithCurrencyEffect
                        )

                        netPerformance = netPerformance + (currentPosition.netPerformance)
                        elif !currentPosition.quantity == 0:
                            hasErrors = True

                        if currentPosition.timeWeightedInvestment:
                            totalTimeWeightedInvestment = totalTimeWeightedInvestment + (
                            currentPosition.timeWeightedInvestment
                            )

                            totalTimeWeightedInvestmentWithCurrencyEffect =
                            totalTimeWeightedInvestmentWithCurrencyEffect + (
                            currentPosition.timeWeightedInvestmentWithCurrencyEffect
                            )
                            elif !currentPosition.quantity == 0:
                                logging.warning(
                                f"Missing historical market data for {currentPosition.symbol} ({currentPosition.dataSource})"
                                'PortfolioCalculator'
                                )

                                hasErrors = True

                        return {
                            currentValueInBaseCurrency
                            hasErrors
                            positions
                            totalFeesWithCurrencyEffect
                            totalInterestWithCurrencyEffect
                            totalInvestment
                            totalInvestmentWithCurrencyEffect
                            activitiesCount: self.activities.filter(({ type }) => {
                                return ['BUY', 'SELL'].includes(type)
                                }).length
                                createdAt: datetime()
                                errors: []
                                historicalData: []
                                totalLiabilitiesWithCurrencyEffect: Decimal(0)

                        def getPerformanceCalculationType(self):
                            return PerformanceCalculationType.ROAI

                        def getSymbolMetrics(self, chartDateMap, dataSource, end, exchangeRates, marketSymbolMap, start, symbol):
                            currentExchangeRate = exchangeRates[_format_date(datetime(), DATE_FORMAT)]
                            const currentValues: { [date: str]: Decimal } = {}
                            const currentValuesWithCurrencyEffect: { [date: str]: Decimal } = {}
                            fees = Decimal(0)
                            feesAtStartDate = Decimal(0)
                            feesAtStartDateWithCurrencyEffect = Decimal(0)
                            feesWithCurrencyEffect = Decimal(0)
                            grossPerformance = Decimal(0)
                            grossPerformanceWithCurrencyEffect = Decimal(0)
                            grossPerformanceAtStartDate = Decimal(0)
                            grossPerformanceAtStartDateWithCurrencyEffect = Decimal(0)
                            grossPerformanceFromSells = Decimal(0)
                            grossPerformanceFromSellsWithCurrencyEffect = Decimal(0)
                            initialValue: Any
                            initialValueWithCurrencyEffect: Any
                            investmentAtStartDate: Any
                            investmentAtStartDateWithCurrencyEffect: Any
                            const investmentValuesAccumulated: { [date: str]: Decimal } = {}
                            const investmentValuesAccumulatedWithCurrencyEffect: {
                                [date: str]: Decimal
                                } = {}
                                const investmentValuesWithCurrencyEffect: { [date: str]: Decimal } = {}
                                lastAveragePrice = Decimal(0)
                                lastAveragePriceWithCurrencyEffect = Decimal(0)
                                const netPerformanceValues: { [date: str]: Decimal } = {}
                                const netPerformanceValuesWithCurrencyEffect: { [date: str]: Decimal } = {}
                                const timeWeightedInvestmentValues: { [date: str]: Decimal } = {}

                                const timeWeightedInvestmentValuesWithCurrencyEffect: {
                                    [date: str]: Decimal
                                    } = {}

                                    totalAccountBalanceInBaseCurrency = Decimal(0)
                                    totalDividend = Decimal(0)
                                    totalDividendInBaseCurrency = Decimal(0)
                                    totalInterest = Decimal(0)
                                    totalInterestInBaseCurrency = Decimal(0)
                                    totalInvestment = Decimal(0)
                                    totalInvestmentFromBuyTransactions = Decimal(0)
                                    totalInvestmentFromBuyTransactionsWithCurrencyEffect = Decimal(0)
                                    totalInvestmentWithCurrencyEffect = Decimal(0)
                                    totalLiabilities = Decimal(0)
                                    totalLiabilitiesInBaseCurrency = Decimal(0)
                                    totalQuantityFromBuyTransactions = Decimal(0)
                                    totalUnits = Decimal(0)
                                    valueAtStartDate: Any
                                    valueAtStartDateWithCurrencyEffect: Any

                                    # Clone orders to keep the original values in self.orders
                                    orders = copy.deepcopy(
                                    self.activities.filter(({ SymbolProfile }) => {
                                        return SymbolProfile.symbol === symbol
                                        })
                                        )

                                        isCash = orders[0]?.(SymbolProfile or {}).assetSubClass === 'CASH'

                                        if len(orders) <= 0:
                                            return {
                                                currentValues: {}
                                                currentValuesWithCurrencyEffect: {}
                                                feesWithCurrencyEffect: Decimal(0)
                                                grossPerformance: Decimal(0)
                                                grossPerformancePercentage: Decimal(0)
                                                grossPerformancePercentageWithCurrencyEffect: Decimal(0)
                                                grossPerformanceWithCurrencyEffect: Decimal(0)
                                                hasErrors: False
                                                initialValue: Decimal(0)
                                                initialValueWithCurrencyEffect: Decimal(0)
                                                investmentValuesAccumulated: {}
                                                investmentValuesAccumulatedWithCurrencyEffect: {}
                                                investmentValuesWithCurrencyEffect: {}
                                                netPerformance: Decimal(0)
                                                netPerformancePercentage: Decimal(0)
                                                netPerformancePercentageWithCurrencyEffectMap: {}
                                                netPerformanceValues: {}
                                                netPerformanceValuesWithCurrencyEffect: {}
                                                netPerformanceWithCurrencyEffectMap: {}
                                                timeWeightedInvestment: Decimal(0)
                                                timeWeightedInvestmentValues: {}
                                                timeWeightedInvestmentValuesWithCurrencyEffect: {}
                                                timeWeightedInvestmentWithCurrencyEffect: Decimal(0)
                                                totalAccountBalanceInBaseCurrency: Decimal(0)
                                                totalDividend: Decimal(0)
                                                totalDividendInBaseCurrency: Decimal(0)
                                                totalInterest: Decimal(0)
                                                totalInterestInBaseCurrency: Decimal(0)
                                                totalInvestment: Decimal(0)
                                                totalInvestmentWithCurrencyEffect: Decimal(0)
                                                totalLiabilities: Decimal(0)
                                                totalLiabilitiesInBaseCurrency: Decimal(0)

                                        dateOfFirstTransaction = datetime(orders[0].date)

                                        endDateString = _format_date(end, DATE_FORMAT)
                                        startDateString = _format_date(start, DATE_FORMAT)

                                        unitPriceAtStartDate = marketSymbolMap[startDateString]?.[symbol]
                                        unitPriceAtEndDate = marketSymbolMap[endDateString]?.[symbol]

                                        latestActivity = orders[-1]

                                        if (
                                        dataSource === 'MANUAL' &&
                                        ['BUY', 'SELL'].includes((latestActivity or {}).type) &&
                                        (latestActivity or {}).unitPrice &&
                                        !unitPriceAtEndDate
                                        ) {
                                            # For BUY / SELL activities with a MANUAL data source where no historical market price is available
                                            # the calculation should fall back to using the activity’s unit price.
                                            unitPriceAtEndDate = latestActivity.unitPrice
                                            elif isCash:
                                                unitPriceAtEndDate = Decimal(1)

                                            if (
                                            !unitPriceAtEndDate ||
                                            (!unitPriceAtStartDate && _is_before(dateOfFirstTransaction, start))
                                            ) {
                                                return {
                                                    currentValues: {}
                                                    currentValuesWithCurrencyEffect: {}
                                                    feesWithCurrencyEffect: Decimal(0)
                                                    grossPerformance: Decimal(0)
                                                    grossPerformancePercentage: Decimal(0)
                                                    grossPerformancePercentageWithCurrencyEffect: Decimal(0)
                                                    grossPerformanceWithCurrencyEffect: Decimal(0)
                                                    hasErrors: True
                                                    initialValue: Decimal(0)
                                                    initialValueWithCurrencyEffect: Decimal(0)
                                                    investmentValuesAccumulated: {}
                                                    investmentValuesAccumulatedWithCurrencyEffect: {}
                                                    investmentValuesWithCurrencyEffect: {}
                                                    netPerformance: Decimal(0)
                                                    netPerformancePercentage: Decimal(0)
                                                    netPerformancePercentageWithCurrencyEffectMap: {}
                                                    netPerformanceWithCurrencyEffectMap: {}
                                                    netPerformanceValues: {}
                                                    netPerformanceValuesWithCurrencyEffect: {}
                                                    timeWeightedInvestment: Decimal(0)
                                                    timeWeightedInvestmentValues: {}
                                                    timeWeightedInvestmentValuesWithCurrencyEffect: {}
                                                    timeWeightedInvestmentWithCurrencyEffect: Decimal(0)
                                                    totalAccountBalanceInBaseCurrency: Decimal(0)
                                                    totalDividend: Decimal(0)
                                                    totalDividendInBaseCurrency: Decimal(0)
                                                    totalInterest: Decimal(0)
                                                    totalInterestInBaseCurrency: Decimal(0)
                                                    totalInvestment: Decimal(0)
                                                    totalInvestmentWithCurrencyEffect: Decimal(0)
                                                    totalLiabilities: Decimal(0)
                                                    totalLiabilitiesInBaseCurrency: Decimal(0)

                                            # Add a synthetic order at the start and the end date
                                            orders.append({
                                                date: startDateString
                                                fee: Decimal(0)
                                                feeInBaseCurrency: Decimal(0)
                                                itemType: 'start'
                                                quantity: Decimal(0)
                                                SymbolProfile: {
                                                    dataSource
                                                    symbol
                                                    assetSubClass: isCash ? 'CASH' : None
                                                type: 'BUY'
                                                unitPrice: unitPriceAtStartDate
                                                })

                                                orders.append({
                                                    date: endDateString
                                                    fee: Decimal(0)
                                                    feeInBaseCurrency: Decimal(0)
                                                    itemType: 'end'
                                                    SymbolProfile: {
                                                        dataSource
                                                        symbol
                                                        assetSubClass: isCash ? 'CASH' : None
                                                    quantity: Decimal(0)
                                                    type: 'BUY'
                                                    unitPrice: unitPriceAtEndDate
                                                    })

                                                    lastUnitPrice: Any

                                                    const ordersByDate: { [date: str]: PortfolioOrderItem[] } = {}

                                                    for order in orders:
                                                        ordersByDate[order.date] = ordersByDate[order.date] ?? []
                                                        ordersByDate[order.date].append(order)

                                                    if !self.chartDates:
                                                        self.chartDates = Object.keys(chartDateMap).sort()

                                                    for dateString in self.chartDates:
                                                        if dateString < startDateString:
                                                            continue
                                                            elif dateString > endDateString:
                                                                break

                                                            if ordersByDate[dateString]?.length > 0:
                                                                for order in ordersByDate[dateString]:
                                                                    order.unitPriceFromMarketData =
                                                                    marketSymbolMap[dateString]?.[symbol] ?? lastUnitPrice
                                                                else:
                                                                    orders.append({
                                                                        date: dateString
                                                                        fee: Decimal(0)
                                                                        feeInBaseCurrency: Decimal(0)
                                                                        quantity: Decimal(0)
                                                                        SymbolProfile: {
                                                                            dataSource
                                                                            symbol
                                                                            assetSubClass: isCash ? 'CASH' : None
                                                                        type: 'BUY'
                                                                        unitPrice: marketSymbolMap[dateString]?.[symbol] ?? lastUnitPrice
                                                                        unitPriceFromMarketData:
                                                                            marketSymbolMap[dateString]?.[symbol] ?? lastUnitPrice
                                                                            })

                                                                        latestActivity = orders[-1]

                                                                        lastUnitPrice =
                                                                        latestActivity.(unitPriceFromMarketData if unitPriceFromMarketData is not None else latestActivity).unitPrice

                                                                    # Sort orders so that the start and end placeholder order are at the correct
                                                                    # position
                                                                    orders = _sort_by(orders, ({ date, itemType }) => {
                                                                        sortIndex = datetime(date)

                                                                        if itemType === 'end':
                                                                            sortIndex = _add_milliseconds(sortIndex, 1)
                                                                            elif itemType === 'start':
                                                                                sortIndex = _add_milliseconds(sortIndex, -1)

                                                                            return sortIndex.getTime()
                                                                            })

                                                                            indexOfStartOrder = orders._findIndex(  # TODO ({ itemType }) => {
                                                                                return itemType === 'start'
                                                                                })

                                                                                indexOfEndOrder = orders._findIndex(  # TODO ({ itemType }) => {
                                                                                    return itemType === 'end'
                                                                                    })

                                                                                    totalInvestmentDays = 0
                                                                                    sumOfTimeWeightedInvestments = Decimal(0)
                                                                                    sumOfTimeWeightedInvestmentsWithCurrencyEffect = Decimal(0)

                                                                                    for i in range(0, len(orders)):
                                                                                        order = orders[i]

                                                                                        if PortfolioCalculator.ENABLE_LOGGING:
                                                                                            print()
                                                                                            print()
                                                                                            print(
                                                                                            i + 1
                                                                                            order.date
                                                                                            order.type
                                                                                            order.itemType ? f"({order.itemType})" : ''
                                                                                            )

                                                                                        exchangeRateAtOrderDate = exchangeRates[order.date]

                                                                                        if order.type === 'DIVIDEND':
                                                                                            dividend = order.quantity * (order.unitPrice)

                                                                                            totalDividend = totalDividend + (dividend)
                                                                                            totalDividendInBaseCurrency = totalDividendInBaseCurrency + (
                                                                                            dividend * ((exchangeRateAtOrderDate if exchangeRateAtOrderDate is not None else 1))
                                                                                            )
                                                                                            elif order.type === 'INTEREST':
                                                                                                interest = order.quantity * (order.unitPrice)

                                                                                                totalInterest = totalInterest + (interest)
                                                                                                totalInterestInBaseCurrency = totalInterestInBaseCurrency + (
                                                                                                interest * ((exchangeRateAtOrderDate if exchangeRateAtOrderDate is not None else 1))
                                                                                                )
                                                                                                elif order.type === 'LIABILITY':
                                                                                                    liabilities = order.quantity * (order.unitPrice)

                                                                                                    totalLiabilities = totalLiabilities + (liabilities)
                                                                                                    totalLiabilitiesInBaseCurrency = totalLiabilitiesInBaseCurrency + (
                                                                                                    liabilities * ((exchangeRateAtOrderDate if exchangeRateAtOrderDate is not None else 1))
                                                                                                    )

                                                                                                if order.itemType === 'start':
                                                                                                    # Take the unit price of the order as the market price if there are no
                                                                                                    # orders of this symbol before the start date
                                                                                                    order.unitPrice =
                                                                                                    indexOfStartOrder === 0
                                                                                                    ? orders[i + 1]?.unitPrice
                                                                                                    : unitPriceAtStartDate

                                                                                                if order.fee:
                                                                                                    order.feeInBaseCurrency = order.fee * ((currentExchangeRate if currentExchangeRate is not None else 1))
                                                                                                    order.feeInBaseCurrencyWithCurrencyEffect = order.fee * (
                                                                                                    (exchangeRateAtOrderDate if exchangeRateAtOrderDate is not None else 1)
                                                                                                    )

                                                                                                unitPrice = ['BUY', 'SELL'].includes(order.type)
                                                                                                ? order.unitPrice
                                                                                                : order.unitPriceFromMarketData

                                                                                                if unitPrice:
                                                                                                    order.unitPriceInBaseCurrency = unitPrice * ((currentExchangeRate if currentExchangeRate is not None else 1))

                                                                                                    order.unitPriceInBaseCurrencyWithCurrencyEffect = unitPrice * (
                                                                                                    (exchangeRateAtOrderDate if exchangeRateAtOrderDate is not None else 1)
                                                                                                    )

                                                                                                marketPriceInBaseCurrency =
                                                                                                order.unitPriceFromMarketData? * ((currentExchangeRate if currentExchangeRate is not None else 1)) ??
                                                                                                Decimal(0)
                                                                                                marketPriceInBaseCurrencyWithCurrencyEffect =
                                                                                                order.unitPriceFromMarketData? * ((exchangeRateAtOrderDate if exchangeRateAtOrderDate is not None else 1)) ??
                                                                                                Decimal(0)

                                                                                                valueOfInvestmentBeforeTransaction = totalUnits * (
                                                                                                marketPriceInBaseCurrency
                                                                                                )

                                                                                                valueOfInvestmentBeforeTransactionWithCurrencyEffect =
                                                                                                totalUnits * (marketPriceInBaseCurrencyWithCurrencyEffect)

                                                                                                if !investmentAtStartDate && i >= indexOfStartOrder:
                                                                                                    investmentAtStartDate = (totalInvestment if totalInvestment is not None else Decimal)(0)

                                                                                                    investmentAtStartDateWithCurrencyEffect =
                                                                                                    (totalInvestmentWithCurrencyEffect if totalInvestmentWithCurrencyEffect is not None else Decimal)(0)

                                                                                                    valueAtStartDate = valueOfInvestmentBeforeTransaction

                                                                                                    valueAtStartDateWithCurrencyEffect =
                                                                                                    valueOfInvestmentBeforeTransactionWithCurrencyEffect

                                                                                                transactionInvestment = Decimal(0)
                                                                                                transactionInvestmentWithCurrencyEffect = Decimal(0)

                                                                                                if order.type === 'BUY':
                                                                                                    transactionInvestment = order.quantity
                                                                                                    * (order.unitPriceInBaseCurrency)
                                                                                                    * (getFactor(order.type))

                                                                                                    transactionInvestmentWithCurrencyEffect = order.quantity
                                                                                                    * (order.unitPriceInBaseCurrencyWithCurrencyEffect)
                                                                                                    * (getFactor(order.type))

                                                                                                    totalQuantityFromBuyTransactions =
                                                                                                    totalQuantityFromBuyTransactions + (order.quantity)

                                                                                                    totalInvestmentFromBuyTransactions =
                                                                                                    totalInvestmentFromBuyTransactions + (transactionInvestment)

                                                                                                    totalInvestmentFromBuyTransactionsWithCurrencyEffect =
                                                                                                    totalInvestmentFromBuyTransactionsWithCurrencyEffect + (
                                                                                                    transactionInvestmentWithCurrencyEffect
                                                                                                    )
                                                                                                    elif order.type === 'SELL':
                                                                                                        if totalUnits > 0:
                                                                                                            transactionInvestment = totalInvestment
                                                                                                            / (totalUnits)
                                                                                                            * (order.quantity)
                                                                                                            * (getFactor(order.type))
                                                                                                            transactionInvestmentWithCurrencyEffect =
                                                                                                            totalInvestmentWithCurrencyEffect
                                                                                                            / (totalUnits)
                                                                                                            * (order.quantity)
                                                                                                            * (getFactor(order.type))

                                                                                                    if PortfolioCalculator.ENABLE_LOGGING:
                                                                                                        print('order.quantity', order.quantity)
                                                                                                        print('transactionInvestment', transactionInvestment)

                                                                                                        print(
                                                                                                        'transactionInvestmentWithCurrencyEffect'
                                                                                                        transactionInvestmentWithCurrencyEffect
                                                                                                        )

                                                                                                    totalInvestmentBeforeTransaction = totalInvestment

                                                                                                    totalInvestmentBeforeTransactionWithCurrencyEffect =
                                                                                                    totalInvestmentWithCurrencyEffect

                                                                                                    totalInvestment = totalInvestment + (transactionInvestment)

                                                                                                    totalInvestmentWithCurrencyEffect =
                                                                                                    totalInvestmentWithCurrencyEffect + (
                                                                                                    transactionInvestmentWithCurrencyEffect
                                                                                                    )

                                                                                                    if i >= indexOfStartOrder && !initialValue:
                                                                                                        if
                                                                                                        i === indexOfStartOrder &&
                                                                                                        !valueOfInvestmentBeforeTransaction == 0
                                                                                                        :
                                                                                                            initialValue = valueOfInvestmentBeforeTransaction

                                                                                                            initialValueWithCurrencyEffect =
                                                                                                            valueOfInvestmentBeforeTransactionWithCurrencyEffect
                                                                                                            elif transactionInvestment > 0:
                                                                                                                initialValue = transactionInvestment

                                                                                                                initialValueWithCurrencyEffect =
                                                                                                                transactionInvestmentWithCurrencyEffect

                                                                                                        fees = fees + (order.(feeInBaseCurrency if feeInBaseCurrency is not None else 0))

                                                                                                        feesWithCurrencyEffect = feesWithCurrencyEffect + (
                                                                                                        order.(feeInBaseCurrencyWithCurrencyEffect if feeInBaseCurrencyWithCurrencyEffect is not None else 0)
                                                                                                        )

                                                                                                        totalUnits = totalUnits + (order.quantity * (getFactor(order.type)))

                                                                                                        valueOfInvestment = totalUnits * (marketPriceInBaseCurrency)

                                                                                                        valueOfInvestmentWithCurrencyEffect = totalUnits * (
                                                                                                        marketPriceInBaseCurrencyWithCurrencyEffect
                                                                                                        )

                                                                                                        grossPerformanceFromSell =
                                                                                                        order.type === 'SELL'
                                                                                                        ? order.unitPriceInBaseCurrency
                                                                                                        - (lastAveragePrice)
                                                                                                        * (order.quantity)
                                                                                                        : Decimal(0)

                                                                                                        grossPerformanceFromSellWithCurrencyEffect =
                                                                                                        order.type === 'SELL'
                                                                                                        ? order.unitPriceInBaseCurrencyWithCurrencyEffect
                                                                                                        - (lastAveragePriceWithCurrencyEffect)
                                                                                                        * (order.quantity)
                                                                                                        : Decimal(0)

                                                                                                        grossPerformanceFromSells = grossPerformanceFromSells + (
                                                                                                        grossPerformanceFromSell
                                                                                                        )

                                                                                                        grossPerformanceFromSellsWithCurrencyEffect =
                                                                                                        grossPerformanceFromSellsWithCurrencyEffect + (
                                                                                                        grossPerformanceFromSellWithCurrencyEffect
                                                                                                        )

                                                                                                        lastAveragePrice = totalQuantityFromBuyTransactions == 0
                                                                                                        ? Decimal(0)
                                                                                                        : totalInvestmentFromBuyTransactions / (
                                                                                                        totalQuantityFromBuyTransactions
                                                                                                        )

                                                                                                        lastAveragePriceWithCurrencyEffect = totalQuantityFromBuyTransactions ==
                                                                                                        0

                                                                                                        ? Decimal(0)
                                                                                                        : totalInvestmentFromBuyTransactionsWithCurrencyEffect / (
                                                                                                        totalQuantityFromBuyTransactions
                                                                                                        )

                                                                                                        if totalUnits == 0:
                                                                                                            # Reset tracking variables when position is fully closed
                                                                                                            totalInvestmentFromBuyTransactions = Decimal(0)
                                                                                                            totalInvestmentFromBuyTransactionsWithCurrencyEffect = Decimal(0)
                                                                                                            totalQuantityFromBuyTransactions = Decimal(0)

                                                                                                        if PortfolioCalculator.ENABLE_LOGGING:
                                                                                                            print(
                                                                                                            'grossPerformanceFromSells'
                                                                                                            grossPerformanceFromSells
                                                                                                            )
                                                                                                            print(
                                                                                                            'grossPerformanceFromSellWithCurrencyEffect'
                                                                                                            grossPerformanceFromSellWithCurrencyEffect
                                                                                                            )

                                                                                                        newGrossPerformance = valueOfInvestment
                                                                                                        - (totalInvestment)
                                                                                                        + (grossPerformanceFromSells)

                                                                                                        newGrossPerformanceWithCurrencyEffect =
                                                                                                        valueOfInvestmentWithCurrencyEffect
                                                                                                        - (totalInvestmentWithCurrencyEffect)
                                                                                                        + (grossPerformanceFromSellsWithCurrencyEffect)

                                                                                                        grossPerformance = newGrossPerformance

                                                                                                        grossPerformanceWithCurrencyEffect =
                                                                                                        newGrossPerformanceWithCurrencyEffect

                                                                                                        if order.itemType === 'start':
                                                                                                            feesAtStartDate = fees
                                                                                                            feesAtStartDateWithCurrencyEffect = feesWithCurrencyEffect
                                                                                                            grossPerformanceAtStartDate = grossPerformance

                                                                                                            grossPerformanceAtStartDateWithCurrencyEffect =
                                                                                                            grossPerformanceWithCurrencyEffect

                                                                                                        if i > indexOfStartOrder:
                                                                                                            # Only consider periods with an investment for the calculation of
                                                                                                            # the time weighted investment
                                                                                                            if (
                                                                                                            valueOfInvestmentBeforeTransaction > 0 &&
                                                                                                            ['BUY', 'SELL'].includes(order.type)
                                                                                                            ) {
                                                                                                                # Calculate the float of days since the previous order
                                                                                                                orderDate = datetime(order.date)
                                                                                                                previousOrderDate = datetime(orders[i - 1].date)

                                                                                                                daysSinceLastOrder = _difference_in_days(
                                                                                                                orderDate
                                                                                                                previousOrderDate
                                                                                                                )
                                                                                                                if daysSinceLastOrder <= 0:
                                                                                                                    # The time between two activities on the same day is unknown
                                                                                                                    # -> Set it to the smallest floating point float greater than 0
                                                                                                                    daysSinceLastOrder = sys.float_info.epsilon

                                                                                                                # Sum up the total investment days since the start date to calculate
                                                                                                                # the time weighted investment
                                                                                                                totalInvestmentDays += daysSinceLastOrder

                                                                                                                sumOfTimeWeightedInvestments = sumOfTimeWeightedInvestments + (
                                                                                                                valueAtStartDate
                                                                                                                - (investmentAtStartDate)
                                                                                                                + (totalInvestmentBeforeTransaction)
                                                                                                                * (daysSinceLastOrder)
                                                                                                                )

                                                                                                                sumOfTimeWeightedInvestmentsWithCurrencyEffect =
                                                                                                                sumOfTimeWeightedInvestmentsWithCurrencyEffect + (
                                                                                                                valueAtStartDateWithCurrencyEffect
                                                                                                                - (investmentAtStartDateWithCurrencyEffect)
                                                                                                                + (totalInvestmentBeforeTransactionWithCurrencyEffect)
                                                                                                                * (daysSinceLastOrder)
                                                                                                                )

                                                                                                            currentValues[order.date] = valueOfInvestment

                                                                                                            currentValuesWithCurrencyEffect[order.date] =
                                                                                                            valueOfInvestmentWithCurrencyEffect

                                                                                                            netPerformanceValues[order.date] = grossPerformance
                                                                                                            - (grossPerformanceAtStartDate)
                                                                                                            - (fees - (feesAtStartDate))

                                                                                                            netPerformanceValuesWithCurrencyEffect[order.date] =
                                                                                                            grossPerformanceWithCurrencyEffect
                                                                                                            - (grossPerformanceAtStartDateWithCurrencyEffect)
                                                                                                            - (
                                                                                                            feesWithCurrencyEffect - (feesAtStartDateWithCurrencyEffect)
                                                                                                            )

                                                                                                            investmentValuesAccumulated[order.date] = totalInvestment

                                                                                                            investmentValuesAccumulatedWithCurrencyEffect[order.date] =
                                                                                                            totalInvestmentWithCurrencyEffect

                                                                                                            investmentValuesWithCurrencyEffect[order.date] = (
                                                                                                            investmentValuesWithCurrencyEffect[order.date] ?? Decimal(0)
                                                                                                            ) + (transactionInvestmentWithCurrencyEffect)

                                                                                                            # If duration is effectively zero (first day), use the actual investment as the base.
                                                                                                            # Otherwise, use the calculated time-weighted average.
                                                                                                            timeWeightedInvestmentValues[order.date] =
                                                                                                            totalInvestmentDays > sys.float_info.epsilon
                                                                                                            ? sumOfTimeWeightedInvestments / (totalInvestmentDays)
                                                                                                            : totalInvestment > 0
                                                                                                            ? totalInvestment
                                                                                                            : Decimal(0)

                                                                                                            timeWeightedInvestmentValuesWithCurrencyEffect[order.date] =
                                                                                                            totalInvestmentDays > sys.float_info.epsilon
                                                                                                            ? sumOfTimeWeightedInvestmentsWithCurrencyEffect / (
                                                                                                            totalInvestmentDays
                                                                                                            )
                                                                                                            : totalInvestmentWithCurrencyEffect > 0
                                                                                                            ? totalInvestmentWithCurrencyEffect
                                                                                                            : Decimal(0)

                                                                                                        if PortfolioCalculator.ENABLE_LOGGING:
                                                                                                            print('totalInvestment', totalInvestment)

                                                                                                            print(
                                                                                                            'totalInvestmentWithCurrencyEffect'
                                                                                                            totalInvestmentWithCurrencyEffect
                                                                                                            )

                                                                                                            print(
                                                                                                            'totalGrossPerformance'
                                                                                                            grossPerformance - (grossPerformanceAtStartDate)
                                                                                                            )

                                                                                                            print(
                                                                                                            'totalGrossPerformanceWithCurrencyEffect'
                                                                                                            grossPerformanceWithCurrencyEffect
                                                                                                            - (grossPerformanceAtStartDateWithCurrencyEffect)

                                                                                                            )

                                                                                                        if i === indexOfEndOrder:
                                                                                                            break

                                                                                                    totalGrossPerformance = grossPerformance - (
                                                                                                    grossPerformanceAtStartDate
                                                                                                    )

                                                                                                    totalGrossPerformanceWithCurrencyEffect =
                                                                                                    grossPerformanceWithCurrencyEffect - (
                                                                                                    grossPerformanceAtStartDateWithCurrencyEffect
                                                                                                    )

                                                                                                    totalNetPerformance = grossPerformance
                                                                                                    - (grossPerformanceAtStartDate)
                                                                                                    - (fees - (feesAtStartDate))

                                                                                                    timeWeightedAverageInvestmentBetweenStartAndEndDate =
                                                                                                    totalInvestmentDays > 0
                                                                                                    ? sumOfTimeWeightedInvestments / (totalInvestmentDays)
                                                                                                    : Decimal(0)

                                                                                                    timeWeightedAverageInvestmentBetweenStartAndEndDateWithCurrencyEffect =
                                                                                                    totalInvestmentDays > 0
                                                                                                    ? sumOfTimeWeightedInvestmentsWithCurrencyEffect / (
                                                                                                    totalInvestmentDays
                                                                                                    )
                                                                                                    : Decimal(0)

                                                                                                    grossPerformancePercentage =
                                                                                                    timeWeightedAverageInvestmentBetweenStartAndEndDate > 0
                                                                                                    ? totalGrossPerformance / (
                                                                                                    timeWeightedAverageInvestmentBetweenStartAndEndDate
                                                                                                    )
                                                                                                    : Decimal(0)

                                                                                                    grossPerformancePercentageWithCurrencyEffect =
                                                                                                    timeWeightedAverageInvestmentBetweenStartAndEndDateWithCurrencyEffect >
                                                                                                    0

                                                                                                    ? totalGrossPerformanceWithCurrencyEffect / (
                                                                                                    timeWeightedAverageInvestmentBetweenStartAndEndDateWithCurrencyEffect
                                                                                                    )
                                                                                                    : Decimal(0)

                                                                                                    feesPerUnit = totalUnits > 0
                                                                                                    ? fees - (feesAtStartDate) / (totalUnits)
                                                                                                    : Decimal(0)

                                                                                                    feesPerUnitWithCurrencyEffect = totalUnits > 0
                                                                                                    ? feesWithCurrencyEffect
                                                                                                    - (feesAtStartDateWithCurrencyEffect)
                                                                                                    / (totalUnits)
                                                                                                    : Decimal(0)

                                                                                                    netPerformancePercentage =
                                                                                                    timeWeightedAverageInvestmentBetweenStartAndEndDate > 0
                                                                                                    ? totalNetPerformance / (
                                                                                                    timeWeightedAverageInvestmentBetweenStartAndEndDate
                                                                                                    )
                                                                                                    : Decimal(0)

                                                                                                    const netPerformancePercentageWithCurrencyEffectMap: {
                                                                                                        [key: DateRange]: Decimal
                                                                                                        } = {}

                                                                                                        const netPerformanceWithCurrencyEffectMap: {
                                                                                                            [key: DateRange]: Decimal
                                                                                                            } = {}

                                                                                                            for (const dateRange of [
                                                                                                            '1d'
                                                                                                            '1y'
                                                                                                            '5y'
                                                                                                            'max'
                                                                                                            'mtd'
                                                                                                            'wtd'
                                                                                                            'ytd'
                                                                                                            ..._each_year_of_interval({ end, start })
                                                                                                            .filter((date) => {
                                                                                                                return !_is_this_year(date)
                                                                                                                })
                                                                                                                .map((date) => {
                                                                                                                    return _format_date(date, 'yyyy')
                                                                                                                    })
                                                                                                                    ] as DateRange[]) {
                                                                                                                        dateInterval = getIntervalFromDateRange(dateRange)
                                                                                                                        endDate = dateInterval.endDate
                                                                                                                        startDate = dateInterval.startDate

                                                                                                                        if (_is_before(startDate, start)) {
                                                                                                                            startDate = start

                                                                                                                        rangeEndDateString = _format_date(endDate, DATE_FORMAT)
                                                                                                                        rangeStartDateString = _format_date(startDate, DATE_FORMAT)

                                                                                                                        currentValuesAtDateRangeStartWithCurrencyEffect =
                                                                                                                        currentValuesWithCurrencyEffect[rangeStartDateString] ?? Decimal(0)

                                                                                                                        investmentValuesAccumulatedAtStartDateWithCurrencyEffect =
                                                                                                                        investmentValuesAccumulatedWithCurrencyEffect[rangeStartDateString] ??
                                                                                                                        Decimal(0)

                                                                                                                        grossPerformanceAtDateRangeStartWithCurrencyEffect =
                                                                                                                        currentValuesAtDateRangeStartWithCurrencyEffect - (
                                                                                                                        investmentValuesAccumulatedAtStartDateWithCurrencyEffect
                                                                                                                        )

                                                                                                                        average = Decimal(0)
                                                                                                                        dayCount = 0

                                                                                                                        for i in range(int(self.len(chartDates) - 1), 0 - 1, -1):
                                                                                                                            date = self.chartDates[i]

                                                                                                                            if date > rangeEndDateString:
                                                                                                                                continue
                                                                                                                                elif date < rangeStartDateString:
                                                                                                                                    break

                                                                                                                                if
                                                                                                                                investmentValuesAccumulatedWithCurrencyEffect[date] instanceof Decimal &&
                                                                                                                                investmentValuesAccumulatedWithCurrencyEffect[date] > 0
                                                                                                                                :
                                                                                                                                    average = average + (
                                                                                                                                    investmentValuesAccumulatedWithCurrencyEffect[date] + (
                                                                                                                                    grossPerformanceAtDateRangeStartWithCurrencyEffect
                                                                                                                                    )
                                                                                                                                    )

                                                                                                                                    dayCount++

                                                                                                                            if dayCount > 0:
                                                                                                                                average = average / (dayCount)

                                                                                                                            netPerformanceWithCurrencyEffectMap[dateRange] =
                                                                                                                            netPerformanceValuesWithCurrencyEffect[rangeEndDateString]? - (
                                                                                                                            # If the date range is 'max', take 0 as a start value. Otherwise
                                                                                                                            # the value of the end of the day of the start date is taken which
                                                                                                                            # differs from the buying price.
                                                                                                                            dateRange === 'max'
                                                                                                                            ? Decimal(0)
                                                                                                                            : (netPerformanceValuesWithCurrencyEffect[rangeStartDateString] ??
                                                                                                                            Decimal(0))
                                                                                                                            ) ?? Decimal(0)

                                                                                                                            netPerformancePercentageWithCurrencyEffectMap[dateRange] = average > 0
                                                                                                                            ? netPerformanceWithCurrencyEffectMap[dateRange] / (average)
                                                                                                                            : Decimal(0)

                                                                                                                        if PortfolioCalculator.ENABLE_LOGGING:
                                                                                                                            print(
                                                                                                                            f"
                                                                                                                            {symbol}
                                                                                                                            Unit price: {orders[indexOfStartOrder].unitPrice.toFixed(
                                                                                                                                2
                                                                                                                                )} -> {unitPriceAtEndDate  # .toFixed(2)}
                                                                                                                            Total investment: {totalInvestment  # .toFixed(2)}
                                                                                                                            Total investment with currency effect: {totalInvestmentWithCurrencyEffect.toFixed(
                                                                                                                                2
                                                                                                                                )}
                                                                                                                            Time weighted investment: {timeWeightedAverageInvestmentBetweenStartAndEndDate.toFixed(
                                                                                                                                2
                                                                                                                                )}
                                                                                                                            Time weighted investment with currency effect: {timeWeightedAverageInvestmentBetweenStartAndEndDateWithCurrencyEffect.toFixed(
                                                                                                                                2
                                                                                                                                )}
                                                                                                                            Total dividend: {totalDividend  # .toFixed(2)}
                                                                                                                            Gross performance: {totalGrossPerformance.toFixed(
                                                                                                                                2
                                                                                                                                )} / {grossPerformancePercentage * (100)  # .toFixed(2)}%
                                                                                                                            Gross performance with currency effect: {totalGrossPerformanceWithCurrencyEffect.toFixed(
                                                                                                                                2
                                                                                                                                )} / {grossPerformancePercentageWithCurrencyEffect
                                                                                                                                * (100)
                                                                                                                                # .toFixed(2)}%
                                                                                                                                Fees per unit: {feesPerUnit  # .toFixed(2)}
                                                                                                                                Fees per unit with currency effect: {feesPerUnitWithCurrencyEffect.toFixed(
                                                                                                                                    2
                                                                                                                                    )}
                                                                                                                                Net performance: {totalNetPerformance.toFixed(
                                                                                                                                    2
                                                                                                                                    )} / {netPerformancePercentage * (100)  # .toFixed(2)}%
                                                                                                                                Net performance with currency effect: {netPerformancePercentageWithCurrencyEffectMap[
                                                                                                                                    'max'
                                                                                                                                    ]  # .toFixed(2)}%"
                                                                                                                                )

                                                                                                                            return {
                                                                                                                                currentValues
                                                                                                                                currentValuesWithCurrencyEffect
                                                                                                                                feesWithCurrencyEffect
                                                                                                                                grossPerformancePercentage
                                                                                                                                grossPerformancePercentageWithCurrencyEffect
                                                                                                                                initialValue
                                                                                                                                initialValueWithCurrencyEffect
                                                                                                                                investmentValuesAccumulated
                                                                                                                                investmentValuesAccumulatedWithCurrencyEffect
                                                                                                                                investmentValuesWithCurrencyEffect
                                                                                                                                netPerformancePercentage
                                                                                                                                netPerformancePercentageWithCurrencyEffectMap
                                                                                                                                netPerformanceValues
                                                                                                                                netPerformanceValuesWithCurrencyEffect
                                                                                                                                netPerformanceWithCurrencyEffectMap
                                                                                                                                timeWeightedInvestmentValues
                                                                                                                                timeWeightedInvestmentValuesWithCurrencyEffect
                                                                                                                                totalAccountBalanceInBaseCurrency
                                                                                                                                totalDividend
                                                                                                                                totalDividendInBaseCurrency
                                                                                                                                totalInterest
                                                                                                                                totalInterestInBaseCurrency
                                                                                                                                totalInvestment
                                                                                                                                totalInvestmentWithCurrencyEffect
                                                                                                                                totalLiabilities
                                                                                                                                totalLiabilitiesInBaseCurrency
                                                                                                                                grossPerformance: totalGrossPerformance
                                                                                                                                grossPerformanceWithCurrencyEffect:
                                                                                                                                    totalGrossPerformanceWithCurrencyEffect
                                                                                                                                    hasErrors: totalUnits > 0 && (!initialValue || !unitPriceAtEndDate)
                                                                                                                                    netPerformance: totalNetPerformance
                                                                                                                                    timeWeightedInvestment:
                                                                                                                                        timeWeightedAverageInvestmentBetweenStartAndEndDate
                                                                                                                                        timeWeightedInvestmentWithCurrencyEffect:
                                                                                                                                            timeWeightedAverageInvestmentBetweenStartAndEndDateWithCurrencyEffect
