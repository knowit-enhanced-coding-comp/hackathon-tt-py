from __future__ import annotations

from decimal import Decimal

from app.implementation.helpers.calculation_helper import getIntervalFromDateRange
from app.implementation.helpers.common_helper import DATE_FORMAT
from app.implementation.helpers.interfaces import AssetProfileIdentifier, SymbolMetrics
from app.implementation.helpers.models import PortfolioSnapshot, TimelinePosition
from app.implementation.helpers.portfolio_helper import getFactor
from app.implementation.helpers.types import DateRange
from app.implementation.shims.collections import cloneDeep, sortBy
from app.implementation.shims.dates import addMilliseconds, differenceInDays, eachYearOfInterval, format, isBefore, isThisYear
from app.implementation.shims.nulls import nullish, safe_get
from app.implementation.shims.numbers import to_decimal, big_sum, pct
from app.wrapper.portfolio.calculator.portfolio_calculator import PortfolioCalculator
class RoaiPortfolioCalculator(PortfolioCalculator):
    # field: chartDates: string[]

    def calculateOverallPerformance(self, positions):
        currentValueInBaseCurrency = to_decimal(0)
        grossPerformance = to_decimal(0)
        grossPerformanceWithCurrencyEffect = to_decimal(0)
        hasErrors = False
        netPerformance = to_decimal(0)
        totalFeesWithCurrencyEffect = to_decimal(0)
        totalInterestWithCurrencyEffect = to_decimal(0)
        totalInvestment = to_decimal(0)
        totalInvestmentWithCurrencyEffect = to_decimal(0)
        totalTimeWeightedInvestment = to_decimal(0)
        totalTimeWeightedInvestmentWithCurrencyEffect = to_decimal(0)

        for currentPosition in positions:
            if currentPosition.feeInBaseCurrency:
                totalFeesWithCurrencyEffect = totalFeesWithCurrencyEffect + to_decimal(
                    currentPosition.feeInBaseCurrency
                )

            if currentPosition.valueInBaseCurrency:
                currentValueInBaseCurrency = currentValueInBaseCurrency + to_decimal(
                    currentPosition.valueInBaseCurrency
                )
            else:
                hasErrors = True

            if currentPosition.investment:
                totalInvestment = totalInvestment + to_decimal(currentPosition.investment)

                totalInvestmentWithCurrencyEffect = totalInvestmentWithCurrencyEffect + to_decimal(
                        currentPosition.investmentWithCurrencyEffect
                    )
            else:
                hasErrors = True

            if currentPosition.grossPerformance:
                grossPerformance = grossPerformance + to_decimal(
                    currentPosition.grossPerformance
                )

                grossPerformanceWithCurrencyEffect = grossPerformanceWithCurrencyEffect + to_decimal(
                        currentPosition.grossPerformanceWithCurrencyEffect
                    )

                netPerformance = netPerformance + to_decimal(currentPosition.netPerformance)
            elif not currentPosition.quantity == to_decimal(0):
                hasErrors = True

            if currentPosition.timeWeightedInvestment:
                totalTimeWeightedInvestment = totalTimeWeightedInvestment + to_decimal(
                    currentPosition.timeWeightedInvestment
                )

                totalTimeWeightedInvestmentWithCurrencyEffect = totalTimeWeightedInvestmentWithCurrencyEffect + to_decimal(
                        currentPosition.timeWeightedInvestmentWithCurrencyEffect
                    )
            elif not currentPosition.quantity == to_decimal(0):

                hasErrors = True


        # TS: return {
            currentValueInBaseCurrency,
            hasErrors,
            positions,
            totalFeesWithCurrencyEffect,
            totalInterestWithCurrencyEffect,
            totalInvestment,
            totalInvestmentWithCurrencyEffect,
            # ts: activitiesCount
            0,
            # TS: "createdAt": datetime.now(),
            # TS: "errors": [],
            # TS: "historicalData": [],
            # TS: "totalLiabilitiesWithCurrencyEffect": to_decimal(0)

    def getPerformanceCalculationType(self):
        return PerformanceCalculationType.ROAI

    def getSymbolMetrics(self):
        pass  # body could not be fully translated
        # TS: currentExchangeRate = exchangeRates[format(datetime.now(), DATE_FORMAT)]
        # TS: currentValues = {}
        # TS: currentValuesWithCurrencyEffect = {}
        # TS: fees = to_decimal(0)
        # TS: feesAtStartDate = to_decimal(0)
        # TS: feesAtStartDateWithCurrencyEffect = to_decimal(0)
        # TS: feesWithCurrencyEffect = to_decimal(0)
        # TS: grossPerformance = to_decimal(0)
        # TS: grossPerformanceWithCurrencyEffect = to_decimal(0)
        # TS: grossPerformanceAtStartDate = to_decimal(0)
        # TS: grossPerformanceAtStartDateWithCurrencyEffect = to_decimal(0)
        # TS: grossPerformanceFromSells = to_decimal(0)
        # TS: grossPerformanceFromSellsWithCurrencyEffect = to_decimal(0)
        # ts: initialValue
        # ts: initialValueWithCurrencyEffect
        # ts: investmentAtStartDate
        # ts: investmentAtStartDateWithCurrencyEffect
        # TS: investmentValuesAccumulated = {}
        # TS: investmentValuesAccumulatedWithCurrencyEffect = {}
        # TS: investmentValuesWithCurrencyEffect = {}
        # TS: lastAveragePrice = to_decimal(0)
        # TS: lastAveragePriceWithCurrencyEffect = to_decimal(0)
        # TS: netPerformanceValues = {}
        # TS: netPerformanceValuesWithCurrencyEffect = {}
        # TS: timeWeightedInvestmentValues = {}

        # TS: timeWeightedInvestmentValuesWithCurrencyEffect = {}

        # TS: totalAccountBalanceInBaseCurrency = to_decimal(0)
        # TS: totalDividend = to_decimal(0)
        # TS: totalDividendInBaseCurrency = to_decimal(0)
        # TS: totalInterest = to_decimal(0)
        # TS: totalInterestInBaseCurrency = to_decimal(0)
        # TS: totalInvestment = to_decimal(0)
        # TS: totalInvestmentFromBuyTransactions = to_decimal(0)
        # TS: totalInvestmentFromBuyTransactionsWithCurrencyEffect = to_decimal(0)
        # TS: totalInvestmentWithCurrencyEffect = to_decimal(0)
        # TS: totalLiabilities = to_decimal(0)
        # TS: totalLiabilitiesInBaseCurrency = to_decimal(0)
        # TS: totalQuantityFromBuyTransactions = to_decimal(0)
        # TS: totalUnits = to_decimal(0)
        # ts: valueAtStartDate
        # ts: valueAtStartDateWithCurrencyEffect
        #  Clone orders to keep the original values in self.orders
        # TS: orders = cloneDeep(
            # TS: self.activities
        # TS: )

        # TS: isCash = orders[0].SymbolProfile.assetSubClass == 'CASH'

        # TS: if len(orders) <= 0:
            # TS: return {
                # TS: "currentValues": {},
                # TS: "currentValuesWithCurrencyEffect": {},
                # TS: "feesWithCurrencyEffect": to_decimal(0),
                # TS: "grossPerformance": to_decimal(0),
                # TS: "grossPerformancePercentage": to_decimal(0),
                # TS: "grossPerformancePercentageWithCurrencyEffect": to_decimal(0),
                # TS: "grossPerformanceWithCurrencyEffect": to_decimal(0),
                # TS: "hasErrors": False,
                # TS: "initialValue": to_decimal(0),
                # TS: "initialValueWithCurrencyEffect": to_decimal(0),
                # TS: "investmentValuesAccumulated": {},
                # TS: "investmentValuesAccumulatedWithCurrencyEffect": {},
                # TS: "investmentValuesWithCurrencyEffect": {},
                # TS: "netPerformance": to_decimal(0),
                # TS: "netPerformancePercentage": to_decimal(0),
                # TS: "netPerformancePercentageWithCurrencyEffectMap": {},
                # TS: "netPerformanceValues": {},
                # TS: "netPerformanceValuesWithCurrencyEffect": {},
                # TS: "netPerformanceWithCurrencyEffectMap": {},
                # TS: "timeWeightedInvestment": to_decimal(0),
                # TS: "timeWeightedInvestmentValues": {},
                # TS: "timeWeightedInvestmentValuesWithCurrencyEffect": {},
                # TS: "timeWeightedInvestmentWithCurrencyEffect": to_decimal(0),
                # TS: "totalAccountBalanceInBaseCurrency": to_decimal(0),
                # TS: "totalDividend": to_decimal(0),
                # TS: "totalDividendInBaseCurrency": to_decimal(0),
                # TS: "totalInterest": to_decimal(0),
                # TS: "totalInterestInBaseCurrency": to_decimal(0),
                # TS: "totalInvestment": to_decimal(0),
                # TS: "totalInvestmentWithCurrencyEffect": to_decimal(0),
                # TS: "totalLiabilities": to_decimal(0),
                # TS: "totalLiabilitiesInBaseCurrency": to_decimal(0)


        # TS: dateOfFirstTransaction = Date(orders[0].date)

        # TS: endDateString = format(end, DATE_FORMAT)
        # TS: startDateString = format(start, DATE_FORMAT)

        # TS: unitPriceAtStartDate = marketSymbolMap[startDateString].[symbol]
        # TS: unitPriceAtEndDate = marketSymbolMap[endDateString].[symbol]

        # TS: latestActivity = orders.at(-1)

        # TS: if dataSource == 'MANUAL' and ['BUY', 'SELL'].includes(latestActivity.type) and latestActivity.unitPrice and not unitPriceAtEndDate:
            #  For BUY / SELL activities with a MANUAL data source where no historical market price is available,
            #  the calculation should fall back to using the activity’s unit price.
            # TS: unitPriceAtEndDate = latestActivity.unitPrice
        # TS: elif isCash:
            # TS: unitPriceAtEndDate = to_decimal(1)

        # TS: if not unitPriceAtEndDate or (not unitPriceAtStartDate and isBefore(dateOfFirstTransaction, start)):
            # TS: return {
                # TS: "currentValues": {},
                # TS: "currentValuesWithCurrencyEffect": {},
                # TS: "feesWithCurrencyEffect": to_decimal(0),
                # TS: "grossPerformance": to_decimal(0),
                # TS: "grossPerformancePercentage": to_decimal(0),
                # TS: "grossPerformancePercentageWithCurrencyEffect": to_decimal(0),
                # TS: "grossPerformanceWithCurrencyEffect": to_decimal(0),
                # TS: "hasErrors": True,
                # TS: "initialValue": to_decimal(0),
                # TS: "initialValueWithCurrencyEffect": to_decimal(0),
                # TS: "investmentValuesAccumulated": {},
                # TS: "investmentValuesAccumulatedWithCurrencyEffect": {},
                # TS: "investmentValuesWithCurrencyEffect": {},
                # TS: "netPerformance": to_decimal(0),
                # TS: "netPerformancePercentage": to_decimal(0),
                # TS: "netPerformancePercentageWithCurrencyEffectMap": {},
                # TS: "netPerformanceWithCurrencyEffectMap": {},
                # TS: "netPerformanceValues": {},
                # TS: "netPerformanceValuesWithCurrencyEffect": {},
                # TS: "timeWeightedInvestment": to_decimal(0),
                # TS: "timeWeightedInvestmentValues": {},
                # TS: "timeWeightedInvestmentValuesWithCurrencyEffect": {},
                # TS: "timeWeightedInvestmentWithCurrencyEffect": to_decimal(0),
                # TS: "totalAccountBalanceInBaseCurrency": to_decimal(0),
                # TS: "totalDividend": to_decimal(0),
                # TS: "totalDividendInBaseCurrency": to_decimal(0),
                # TS: "totalInterest": to_decimal(0),
                # TS: "totalInterestInBaseCurrency": to_decimal(0),
                # TS: "totalInvestment": to_decimal(0),
                # TS: "totalInvestmentWithCurrencyEffect": to_decimal(0),
                # TS: "totalLiabilities": to_decimal(0),
                # TS: "totalLiabilitiesInBaseCurrency": to_decimal(0)


        #  Add a synthetic order at the start and the end date
        # TS: orders.append({
            # TS: "date": startDateString,
            # TS: "fee": to_decimal(0),
            # TS: "feeInBaseCurrency": to_decimal(0),
            # TS: "itemType": 'start',
            # TS: "quantity": to_decimal(0),
            # TS: "SymbolProfile": {
                # TS: dataSource,
                # TS: symbol,
                # TS: "assetSubClass": isCash ? 'CASH' : None

            # TS: "type": 'BUY',
            # ts: unitPrice
        # TS: orders.append({
            # TS: "date": endDateString,
            # TS: "fee": to_decimal(0),
            # TS: "feeInBaseCurrency": to_decimal(0),
            # TS: "itemType": 'end',
            # TS: "SymbolProfile": {
                # TS: dataSource,
                # TS: symbol,
                # TS: "assetSubClass": isCash ? 'CASH' : None

            # TS: "quantity": to_decimal(0),
            # TS: "type": 'BUY',
            # ts: unitPrice
        # ts: lastUnitPrice
        # TS: ordersByDate = {}

        # TS: for order in orders:
            # TS: ordersByDate[order.date] = (ordersByDate[order.date] if ordersByDate[order.date] is not None else [])
            # TS: ordersByDate[order.date].append(order)

        # TS: if not self.chartDates:
            # TS: self.chartDates = list(chartDateMap.keys()).sort()

        # TS: for dateString in self.chartDates:
            # TS: if dateString < startDateString:
                # TS: continue
            # TS: elif dateString > endDateString:
                # TS: break

            # TS: if ordersByDate[dateString].length > 0:
                # TS: for order in ordersByDate[dateString]:
                    # TS: order.unitPriceFromMarketData =
                        # TS: (marketSymbolMap[dateString].[symbol] if marketSymbolMap[dateString].[symbol] is not None else lastUnitPrice)

            # TS: else:
                # TS: orders.append({
                    # TS: "date": dateString,
                    # TS: "fee": to_decimal(0),
                    # TS: "feeInBaseCurrency": to_decimal(0),
                    # TS: "quantity": to_decimal(0),
                    # TS: "SymbolProfile": {
                        # TS: dataSource,
                        # TS: symbol,
                        # TS: "assetSubClass": isCash ? 'CASH' : None

                    # TS: "type": 'BUY',
                    # TS: "unitPrice": (marketSymbolMap[dateString].[symbol] if marketSymbolMap[dateString].[symbol] is not None else lastUnitPrice),
                    # TS: unitPriceFromMarketData:
                        # TS: (marketSymbolMap[dateString].[symbol] if marketSymbolMap[dateString].[symbol] is not None else lastUnitPrice)

            # TS: latestActivity = orders.at(-1)

            # TS: lastUnitPrice =
                # TS: (latestActivity.unitPriceFromMarketData if latestActivity.unitPriceFromMarketData is not None else latestActivity.unitPrice)

        #  Sort orders so that the start and end placeholder order are at the correct
        #  position
        # TS: orders = sortBylambda orders, ({ date, itemType }:  {
            # TS: sortIndex = Date(date)

            # TS: if itemType == 'end':
                # TS: sortIndex = addMilliseconds(sortIndex, 1)
            # TS: elif itemType == 'start':
                # TS: sortIndex = addMilliseconds(sortIndex, -1)

            # TS: return sortIndex.getTime()

        # TS: indexOfStartOrder = orders.index(0)  # findIndex placeholder

        # TS: indexOfEndOrder = orders.index(0)  # findIndex placeholder

        # TS: totalInvestmentDays = 0
        # TS: sumOfTimeWeightedInvestments = to_decimal(0)
        # TS: sumOfTimeWeightedInvestmentsWithCurrencyEffect = to_decimal(0)

        # TS: for i in range(len(orders)) = orders[i]

            # TS: if PortfolioCalculator.ENABLE_LOGGING:

            # TS: exchangeRateAtOrderDate = exchangeRates[order.date]

            # TS: if order.type == 'DIVIDEND':
                # TS: dividend = order.quantity.mul(order.unitPrice)

                # TS: totalDividend = totalDividend + to_decimal(dividend)
                # TS: totalDividendInBaseCurrency = totalDividendInBaseCurrency + to_decimal(
                    # TS: (dividend.mul(exchangeRateAtOrderDate if dividend.mul(exchangeRateAtOrderDate is not None else 1))
                # TS: )
            # TS: elif order.type == 'INTEREST':
                # TS: interest = order.quantity.mul(order.unitPrice)

                # TS: totalInterest = totalInterest + to_decimal(interest)
                # TS: totalInterestInBaseCurrency = totalInterestInBaseCurrency + to_decimal(
                    # TS: (interest.mul(exchangeRateAtOrderDate if interest.mul(exchangeRateAtOrderDate is not None else 1))
                # TS: )
            # TS: elif order.type == 'LIABILITY':
                # TS: liabilities = order.quantity.mul(order.unitPrice)

                # TS: totalLiabilities = totalLiabilities + to_decimal(liabilities)
                # TS: totalLiabilitiesInBaseCurrency = totalLiabilitiesInBaseCurrency + to_decimal(
                    # TS: (liabilities.mul(exchangeRateAtOrderDate if liabilities.mul(exchangeRateAtOrderDate is not None else 1))
                # TS: )

            # TS: if order.itemType == 'start':
                #  Take the unit price of the order
                #  orders of this symbol before the start date
                # TS: order.unitPrice = indexOfStartOrder == 0
                        # TS: ? orders[i + 1].unitPrice
                        # TS-ternary: unitPriceAtStartDate

            # TS: if order.fee:
                # TS: order.feeInBaseCurrency = (order.fee.mul(currentExchangeRate if order.fee.mul(currentExchangeRate is not None else 1))
                # TS: order.feeInBaseCurrencyWithCurrencyEffect = order.fee.mul(
                    # TS: (exchangeRateAtOrderDate if exchangeRateAtOrderDate is not None else 1)
                # TS: )

            # TS: unitPrice = ['BUY', 'SELL'].includes(order.type)
                # TS: ? order.unitPrice
                # TS-ternary: order.unitPriceFromMarketData

            # TS: if unitPrice:
                # TS: order.unitPriceInBaseCurrency = (unitPrice.mul(currentExchangeRate if unitPrice.mul(currentExchangeRate is not None else 1))

                # TS: order.unitPriceInBaseCurrencyWithCurrencyEffect = unitPrice.mul(
                    # TS: (exchangeRateAtOrderDate if exchangeRateAtOrderDate is not None else 1)
                # TS: )

            # TS: marketPriceInBaseCurrency =
                # TS: (order.unitPriceFromMarketData.mul(currentExchangeRate if order.unitPriceFromMarketData.mul(currentExchangeRate is not None else 1)) ??
                # TS: to_decimal(0)
            # TS: marketPriceInBaseCurrencyWithCurrencyEffect =
                # TS: (order.unitPriceFromMarketData.mul(exchangeRateAtOrderDate if order.unitPriceFromMarketData.mul(exchangeRateAtOrderDate is not None else 1)) ??
                # TS: to_decimal(0)

            # TS: valueOfInvestmentBeforeTransaction = totalUnits.mul(
                # TS: marketPriceInBaseCurrency
            # TS: )

            # TS: valueOfInvestmentBeforeTransactionWithCurrencyEffect = totalUnits.mul(marketPriceInBaseCurrencyWithCurrencyEffect)

            # TS: if not investmentAtStartDate and i >= indexOfStartOrder:
                # TS: investmentAtStartDate = (totalInvestment if totalInvestment is not None else to_decimal(0))

                # TS: investmentAtStartDateWithCurrencyEffect =
                    # TS: (totalInvestmentWithCurrencyEffect if totalInvestmentWithCurrencyEffect is not None else to_decimal(0))

                # TS: valueAtStartDate = valueOfInvestmentBeforeTransaction

                # TS: valueAtStartDateWithCurrencyEffect = valueOfInvestmentBeforeTransactionWithCurrencyEffect

            # TS: transactionInvestment = to_decimal(0)
            # TS: transactionInvestmentWithCurrencyEffect = to_decimal(0)

            # TS: if order.type == 'BUY':
                # TS: transactionInvestment = order.quantity
                    # TS: .mul(order.unitPriceInBaseCurrency)
                    # TS: .mul(getFactor(order.type))

                # TS: transactionInvestmentWithCurrencyEffect = order.quantity
                    # TS: .mul(order.unitPriceInBaseCurrencyWithCurrencyEffect)
                    # TS: .mul(getFactor(order.type))

                # TS: totalQuantityFromBuyTransactions = totalQuantityFromBuyTransactions + to_decimal(order.quantity)

                # TS: totalInvestmentFromBuyTransactions = totalInvestmentFromBuyTransactions + to_decimal(transactionInvestment)

                # TS: totalInvestmentFromBuyTransactionsWithCurrencyEffect = totalInvestmentFromBuyTransactionsWithCurrencyEffect + to_decimal(
                        # TS: transactionInvestmentWithCurrencyEffect
                    # TS: )
            # TS: elif order.type == 'SELL':
                # TS: if totalUnits > to_decimal(0):
                    # TS: transactionInvestment = totalInvestment
                          # TS: / to_decimal(totalUnits)
                        # TS: .mul(order.quantity)
                        # TS: .mul(getFactor(order.type))
                    # TS: transactionInvestmentWithCurrencyEffect = totalInvestmentWithCurrencyEffect
                              # TS: / to_decimal(totalUnits)
                            # TS: .mul(order.quantity)
                            # TS: .mul(getFactor(order.type))


            # TS: if PortfolioCalculator.ENABLE_LOGGING:


            # TS: totalInvestmentBeforeTransaction = totalInvestment

            # TS: totalInvestmentBeforeTransactionWithCurrencyEffect = totalInvestmentWithCurrencyEffect

            # TS: totalInvestment = totalInvestment + to_decimal(transactionInvestment)

            # TS: totalInvestmentWithCurrencyEffect = totalInvestmentWithCurrencyEffect + to_decimal(
                    # TS: transactionInvestmentWithCurrencyEffect
                # TS: )

            # TS: if i >= indexOfStartOrder and not initialValue:
                # TS: if i == indexOfStartOrder and not valueOfInvestmentBeforeTransaction == to_decimal(0):
                    # TS: initialValue = valueOfInvestmentBeforeTransaction

                    # TS: initialValueWithCurrencyEffect = valueOfInvestmentBeforeTransactionWithCurrencyEffect
                # TS: elif transactionInvestment > to_decimal(0):
                    # TS: initialValue = transactionInvestment

                    # TS: initialValueWithCurrencyEffect = transactionInvestmentWithCurrencyEffect


            # TS: fees = fees + (to_decimal(order.feeInBaseCurrency if to_decimal(order.feeInBaseCurrency is not None else 0))

            # TS: feesWithCurrencyEffect = feesWithCurrencyEffect + to_decimal(
                # TS: (order.feeInBaseCurrencyWithCurrencyEffect if order.feeInBaseCurrencyWithCurrencyEffect is not None else 0)
            # TS: )

            # TS: totalUnits = totalUnits + to_decimal(order.quantity.mul(getFactor(order.type)))

            # TS: valueOfInvestment = totalUnits.mul(marketPriceInBaseCurrency)

            # TS: valueOfInvestmentWithCurrencyEffect = totalUnits.mul(
                # TS: marketPriceInBaseCurrencyWithCurrencyEffect
            # TS: )

            # TS: grossPerformanceFromSell = order.type == 'SELL'
                    # TS: ? order.unitPriceInBaseCurrency
                              # TS: - to_decimal(lastAveragePrice)
                            # TS: .mul(order.quantity)
                    # TS-ternary: to_decimal(0)

            # TS: grossPerformanceFromSellWithCurrencyEffect = order.type == 'SELL'
                    # TS: ? order.unitPriceInBaseCurrencyWithCurrencyEffect
                              # TS: - to_decimal(lastAveragePriceWithCurrencyEffect)
                            # TS: .mul(order.quantity)
                    # TS-ternary: to_decimal(0)

            # TS: grossPerformanceFromSells = grossPerformanceFromSells + to_decimal(
                # TS: grossPerformanceFromSell
            # TS: )

            # TS: grossPerformanceFromSellsWithCurrencyEffect = grossPerformanceFromSellsWithCurrencyEffect + to_decimal(
                    # TS: grossPerformanceFromSellWithCurrencyEffect
                # TS: )

            # TS: lastAveragePrice = totalQuantityFromBuyTransactions == to_decimal(0)
                # TS: ? to_decimal(0)
                # TS-ternary: totalInvestmentFromBuyTransactions / to_decimal(
                        # TS: totalQuantityFromBuyTransactions
                    # TS: )

            # TS: lastAveragePriceWithCurrencyEffect = totalQuantityFromBuyTransactions == to_decimal(
                # TS: 0
            # TS: )
                # TS: ? to_decimal(0)
                # TS-ternary: totalInvestmentFromBuyTransactionsWithCurrencyEffect / to_decimal(
                        # TS: totalQuantityFromBuyTransactions
                    # TS: )

            # TS: if totalUnits == to_decimal(0):
                #  Reset tracking variables when position is fully closed
                # TS: totalInvestmentFromBuyTransactions = to_decimal(0)
                # TS: totalInvestmentFromBuyTransactionsWithCurrencyEffect = to_decimal(0)
                # TS: totalQuantityFromBuyTransactions = to_decimal(0)

            # TS: if PortfolioCalculator.ENABLE_LOGGING:

            # TS: newGrossPerformance = valueOfInvestment
                  # TS: - to_decimal(totalInvestment)
                  # TS: + to_decimal(grossPerformanceFromSells)

            # TS: newGrossPerformanceWithCurrencyEffect = valueOfInvestmentWithCurrencyEffect
                      # TS: - to_decimal(totalInvestmentWithCurrencyEffect)
                      # TS: + to_decimal(grossPerformanceFromSellsWithCurrencyEffect)

            # TS: grossPerformance = newGrossPerformance

            # TS: grossPerformanceWithCurrencyEffect = newGrossPerformanceWithCurrencyEffect

            # TS: if order.itemType == 'start':
                # TS: feesAtStartDate = fees
                # TS: feesAtStartDateWithCurrencyEffect = feesWithCurrencyEffect
                # TS: grossPerformanceAtStartDate = grossPerformance

                # TS: grossPerformanceAtStartDateWithCurrencyEffect = grossPerformanceWithCurrencyEffect

            # TS: if i > indexOfStartOrder:
                #  Only consider periods with an investment for the calculation of
                #  the time weighted investment
                # TS: if valueOfInvestmentBeforeTransaction > to_decimal(0) and ['BUY', 'SELL'].includes(order.type):
                    #  Calculate the number of days since the previous order
                    # TS: orderDate = Date(order.date)
                    # TS: previousOrderDate = Date(orders[i - 1].date)

                    # TS: daysSinceLastOrder = differenceInDays(
                        # TS: orderDate,
                        # TS: previousOrderDate
                    # TS: )
                    # TS: if daysSinceLastOrder <= 0:
                        #  The time between two activities on the same day is unknown
                        #  -> Set it to the smallest floating point number greater than 0
                        # TS: daysSinceLastOrder = Number.EPSILON

                    #  Sum up the total investment days since the start date to calculate
                    #  the time weighted investment
                    # TS: totalInvestmentDays += daysSinceLastOrder

                    # TS: sumOfTimeWeightedInvestments = sumOfTimeWeightedInvestments.add(
                        # TS: valueAtStartDate
                              # TS: - to_decimal(investmentAtStartDate)
                              # TS: + to_decimal(totalInvestmentBeforeTransaction)
                            # TS: .mul(daysSinceLastOrder)
                    # TS: )

                    # TS: sumOfTimeWeightedInvestmentsWithCurrencyEffect = sumOfTimeWeightedInvestmentsWithCurrencyEffect.add(
                            # TS: valueAtStartDateWithCurrencyEffect
                                  # TS: - to_decimal(investmentAtStartDateWithCurrencyEffect)
                                  # TS: + to_decimal(totalInvestmentBeforeTransactionWithCurrencyEffect)
                                # TS: .mul(daysSinceLastOrder)
                        # TS: )

                # TS: currentValues[order.date] = valueOfInvestment

                # TS: currentValuesWithCurrencyEffect[order.date] = valueOfInvestmentWithCurrencyEffect

                # TS: netPerformanceValues[order.date] = grossPerformance
                      # TS: - to_decimal(grossPerformanceAtStartDate)
                      # TS: - to_decimal(fees - to_decimal(feesAtStartDate))

                # TS: netPerformanceValuesWithCurrencyEffect[order.date] = grossPerformanceWithCurrencyEffect
                          # TS: - to_decimal(grossPerformanceAtStartDateWithCurrencyEffect)
                          # TS: - to_decimal(
                            # TS: feesWithCurrencyEffect - to_decimal(feesAtStartDateWithCurrencyEffect)
                        # TS: )

                # TS: investmentValuesAccumulated[order.date] = totalInvestment

                # TS: investmentValuesAccumulatedWithCurrencyEffect[order.date] = totalInvestmentWithCurrencyEffect

                # TS: investmentValuesWithCurrencyEffect[order.date] = (
                    # TS: (investmentValuesWithCurrencyEffect[order.date] if investmentValuesWithCurrencyEffect[order.date] is not None else to_decimal(0))
                # TS: ).add(transactionInvestmentWithCurrencyEffect)

                #  If duration is effectively zero (first day), use the actual investment
                #  Otherwise, use the calculated time-weighted average.
                # TS: timeWeightedInvestmentValues[order.date] = totalInvestmentDays > Number.EPSILON
                        # TS: ? sumOfTimeWeightedInvestments / to_decimal(totalInvestmentDays)
                        # TS-ternary: totalInvestment > to_decimal(0)
                            # TS: ? totalInvestment
                            # TS-ternary: to_decimal(0)

                # TS: timeWeightedInvestmentValuesWithCurrencyEffect[order.date] = totalInvestmentDays > Number.EPSILON
                        # TS: ? sumOfTimeWeightedInvestmentsWithCurrencyEffect / to_decimal(
                                # TS: totalInvestmentDays
                            # TS: )
                        # TS-ternary: totalInvestmentWithCurrencyEffect > to_decimal(0)
                            # TS: ? totalInvestmentWithCurrencyEffect
                            # TS-ternary: to_decimal(0)

            # TS: if PortfolioCalculator.ENABLE_LOGGING:




            # TS: if i == indexOfEndOrder:
                # TS: break


        # TS: totalGrossPerformance = grossPerformance - to_decimal(
            # TS: grossPerformanceAtStartDate
        # TS: )

        # TS: totalGrossPerformanceWithCurrencyEffect = grossPerformanceWithCurrencyEffect - to_decimal(
                # TS: grossPerformanceAtStartDateWithCurrencyEffect
            # TS: )

        # TS: totalNetPerformance = grossPerformance
              # TS: - to_decimal(grossPerformanceAtStartDate)
              # TS: - to_decimal(fees - to_decimal(feesAtStartDate))

        # TS: timeWeightedAverageInvestmentBetweenStartAndEndDate = totalInvestmentDays > 0
                # TS: ? sumOfTimeWeightedInvestments / to_decimal(totalInvestmentDays)
                # TS-ternary: to_decimal(0)

        # TS: timeWeightedAverageInvestmentBetweenStartAndEndDateWithCurrencyEffect = totalInvestmentDays > 0
                # TS: ? sumOfTimeWeightedInvestmentsWithCurrencyEffect / to_decimal(
                        # TS: totalInvestmentDays
                    # TS: )
                # TS-ternary: to_decimal(0)

        # TS: grossPerformancePercentage = timeWeightedAverageInvestmentBetweenStartAndEndDate > to_decimal(0)
                # TS: ? totalGrossPerformance / to_decimal(
                        # TS: timeWeightedAverageInvestmentBetweenStartAndEndDate
                    # TS: )
                # TS-ternary: to_decimal(0)

        # TS: grossPerformancePercentageWithCurrencyEffect = timeWeightedAverageInvestmentBetweenStartAndEndDateWithCurrencyEffect > to_decimal(
                # TS: 0
            # TS: )
                # TS: ? totalGrossPerformanceWithCurrencyEffect / to_decimal(
                        # TS: timeWeightedAverageInvestmentBetweenStartAndEndDateWithCurrencyEffect
                    # TS: )
                # TS-ternary: to_decimal(0)

        # TS: feesPerUnit = totalUnits > to_decimal(0)
            # TS: ? fees - to_decimal(feesAtStartDate) / to_decimal(totalUnits)
            # TS-ternary: to_decimal(0)

        # TS: feesPerUnitWithCurrencyEffect = totalUnits > to_decimal(0)
            # TS: ? feesWithCurrencyEffect
                      # TS: - to_decimal(feesAtStartDateWithCurrencyEffect)
                      # TS: / to_decimal(totalUnits)
            # TS-ternary: to_decimal(0)

        # TS: netPerformancePercentage = timeWeightedAverageInvestmentBetweenStartAndEndDate > to_decimal(0)
                # TS: ? totalNetPerformance / to_decimal(
                        # TS: timeWeightedAverageInvestmentBetweenStartAndEndDate
                    # TS: )
                # TS-ternary: to_decimal(0)

        # TS: netPerformancePercentageWithCurrencyEffectMap = {}

        # TS: netPerformanceWithCurrencyEffectMap = {}

        # TS: for dateRange in [
            # TS: '1d',
            # TS: '1y',
            # TS: '5y',
            # TS: 'max',
            # TS: 'mtd',
            # TS: 'wtd',
            # TS: 'ytd',
            # TS: *eachYearOfInterval({ end, start }:

        # TS: ]) {
            # TS: dateInterval = getIntervalFromDateRange(dateRange)
            # TS: endDate = dateInterval.endDate
            # TS: startDate = dateInterval.startDate

            # TS: if isBefore(startDate, start):
                # TS: startDate = start

            # TS: rangeEndDateString = format(endDate, DATE_FORMAT)
            # TS: rangeStartDateString = format(startDate, DATE_FORMAT)

            # TS: currentValuesAtDateRangeStartWithCurrencyEffect =
                # TS: (currentValuesWithCurrencyEffect[rangeStartDateString] if currentValuesWithCurrencyEffect[rangeStartDateString] is not None else to_decimal(0))

            # TS: investmentValuesAccumulatedAtStartDateWithCurrencyEffect =
                # TS: (investmentValuesAccumulatedWithCurrencyEffect[rangeStartDateString] if investmentValuesAccumulatedWithCurrencyEffect[rangeStartDateString] is not None else to_decimal(0))

            # TS: grossPerformanceAtDateRangeStartWithCurrencyEffect = currentValuesAtDateRangeStartWithCurrencyEffect - to_decimal(
                    # TS: investmentValuesAccumulatedAtStartDateWithCurrencyEffect
                # TS: )

            # TS: average = to_decimal(0)
            # TS: dayCount = 0

            # TS: for i in range(self.len(chartDates) - 1, -1, -1) = self.chartDates[i]

                # TS: if date > rangeEndDateString:
                    # TS: continue
                # TS: elif date < rangeStartDateString:
                    # TS: break

                # TS: if investmentValuesAccumulatedWithCurrencyEffect[date] instanceof Big and investmentValuesAccumulatedWithCurrencyEffect[date] > to_decimal(0):
                    # TS: average = average.add(
                        # TS: investmentValuesAccumulatedWithCurrencyEffect[date].add(
                            # TS: grossPerformanceAtDateRangeStartWithCurrencyEffect
                        # TS: )
                    # TS: )

                    # TS: dayCount++


            # TS: if dayCount > 0:
                # TS: average = average / to_decimal(dayCount)

            # TS: netPerformanceWithCurrencyEffectMap[dateRange] = netPerformanceValuesWithCurrencyEffect[rangeEndDateString]? - to_decimal(
                    #  If the date range is 'max', take 0,
                    #  the value of the end of the day of the start date is taken which
                    #  differs from the buying price.
                    # TS: dateRange == 'max'
                        # TS: ? to_decimal(0)
                        # TS-ternary: ((netPerformanceValuesWithCurrencyEffect[rangeStartDateString] if netPerformanceValuesWithCurrencyEffect[rangeStartDateString] is not None else to_decimal(0)))
                # TS: ) ?? to_decimal(0)

            # TS: netPerformancePercentageWithCurrencyEffectMap[dateRange] = average > to_decimal(0)
                # TS: ? netPerformanceWithCurrencyEffectMap[dateRange] / to_decimal(average)
                # TS-ternary: to_decimal(0)

        # TS: if PortfolioCalculator.ENABLE_LOGGING:

        # TS: return {
            # TS: currentValues,
            # TS: currentValuesWithCurrencyEffect,
            # TS: feesWithCurrencyEffect,
            # TS: grossPerformancePercentage,
            # TS: grossPerformancePercentageWithCurrencyEffect,
            # TS: initialValue,
            # TS: initialValueWithCurrencyEffect,
            # TS: investmentValuesAccumulated,
            # TS: investmentValuesAccumulatedWithCurrencyEffect,
            # TS: investmentValuesWithCurrencyEffect,
            # TS: netPerformancePercentage,
            # TS: netPerformancePercentageWithCurrencyEffectMap,
            # TS: netPerformanceValues,
            # TS: netPerformanceValuesWithCurrencyEffect,
            # TS: netPerformanceWithCurrencyEffectMap,
            # TS: timeWeightedInvestmentValues,
            # TS: timeWeightedInvestmentValuesWithCurrencyEffect,
            # TS: totalAccountBalanceInBaseCurrency,
            # TS: totalDividend,
            # TS: totalDividendInBaseCurrency,
            # TS: totalInterest,
            # TS: totalInterestInBaseCurrency,
            # TS: totalInvestment,
            # TS: totalInvestmentWithCurrencyEffect,
            # TS: totalLiabilities,
            # TS: totalLiabilitiesInBaseCurrency,
            # TS: "grossPerformance": totalGrossPerformance,
            # TS: grossPerformanceWithCurrencyEffect:
                # TS: totalGrossPerformanceWithCurrencyEffect,
            # TS: "hasErrors": totalUnits > to_decimal(0) and (not initialValue or not unitPriceAtEndDate),
            # TS: "netPerformance": totalNetPerformance,
            # TS: timeWeightedInvestment:
                # TS: timeWeightedAverageInvestmentBetweenStartAndEndDate,
            # ts: timeWeightedInvestmentWithCurrencyEffect
