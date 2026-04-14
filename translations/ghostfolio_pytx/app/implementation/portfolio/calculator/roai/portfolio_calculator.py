"""
RoaiPortfolioCalculator — translated from TypeScript by tt.

Auto-generated. Do not edit manually.
"""
from __future__ import annotations

import copy
from datetime import datetime, date as _date_type, timedelta
from typing import Any

from app.wrapper.portfolio.calculator.portfolio_calculator import PortfolioCalculator
from app.helpers.big import Big
from app.helpers.date_fns import (
    format, is_before, is_after, add_milliseconds,
    difference_in_days, each_year_of_interval, is_this_year,
    parse_date, get_interval_from_date_range, start_of_year, end_of_year,
    start_of_day, end_of_day, reset_hours, each_day_of_interval,
    is_within_interval,
)
from app.helpers.lodash import sort_by, clone_deep, uniq_by, is_number, sum_values
from app.helpers.portfolio_helpers import get_factor

DATE_FORMAT = "yyyy-MM-dd"
_DATE_FMT = "%Y-%m-%d"


def _fmt(d) -> str:
    """Format a date to YYYY-MM-DD string."""
    if isinstance(d, str):
        return d
    if isinstance(d, datetime):
        return d.strftime(_DATE_FMT)
    if isinstance(d, _date_type):
        return d.strftime(_DATE_FMT)
    return str(d)


def _to_dt(s) -> datetime:
    """Parse a YYYY-MM-DD string to datetime."""
    if isinstance(s, datetime):
        return s
    if isinstance(s, _date_type):
        return datetime(s.year, s.month, s.day)
    if isinstance(s, str):
        return datetime.strptime(s, _DATE_FMT)
    raise ValueError(f"Cannot parse date: {s!r}")

class RoaiPortfolioCalculator(PortfolioCalculator):
private chartDates: string[]

protected calculateOverallPerformance(
positions = None
): PortfolioSnapshot:
  currentValueInBaseCurrency = Big(0)
  grossPerformance = Big(0)
  grossPerformanceWithCurrencyEffect = Big(0)
  hasErrors = False
  netPerformance = Big(0)
  totalFeesWithCurrencyEffect = Big(0)
  totalInterestWithCurrencyEffect = Big(0)
  totalInvestment = Big(0)
  totalInvestmentWithCurrencyEffect = Big(0)
  totalTimeWeightedInvestment = Big(0)
  totalTimeWeightedInvestmentWithCurrencyEffect = Big(0)

  for (currentPosition of positions.filter(
  ({ includeInTotalAssetValue }) => {
  return includeInTotalAssetValue
  }
  )):
  if currentPosition.feeInBaseCurrency:
  totalFeesWithCurrencyEffect = totalFeesWithCurrencyEffect.plus(
  currentPosition.feeInBaseCurrency
  )

  if currentPosition.valueInBaseCurrency:
  currentValueInBaseCurrency = currentValueInBaseCurrency.plus(
  currentPosition.valueInBaseCurrency
  )
  else:
  hasErrors = True

  if currentPosition.investment:
  totalInvestment = totalInvestment.plus(currentPosition.investment)

  totalInvestmentWithCurrencyEffect =
  totalInvestmentWithCurrencyEffect.plus(
  currentPosition.investmentWithCurrencyEffect
  )
  else:
  hasErrors = True

  if currentPosition.grossPerformance:
  grossPerformance = grossPerformance.plus(
  currentPosition.grossPerformance
  )

  grossPerformanceWithCurrencyEffect =
  grossPerformanceWithCurrencyEffect.plus(
  currentPosition.grossPerformanceWithCurrencyEffect
  )

  netPerformance = netPerformance.plus(currentPosition.netPerformance)
  elif not currentPosition.quantity.eq(0):
  hasErrors = True

  if currentPosition.timeWeightedInvestment:
  totalTimeWeightedInvestment = totalTimeWeightedInvestment.plus(
  currentPosition.timeWeightedInvestment
  )

  totalTimeWeightedInvestmentWithCurrencyEffect =
  totalTimeWeightedInvestmentWithCurrencyEffect.plus(
  currentPosition.timeWeightedInvestmentWithCurrencyEffect
  )
  elif not currentPosition.quantity.eq(0):
  # Logger.warn(
  f"Missing historical market data for {currentPosition.symbol} ({currentPosition.dataSource})",
  'PortfolioCalculator'
  )

  hasErrors = True

  return {
  "currentValueInBaseCurrency": currentValueInBaseCurrency,
  "hasErrors": hasErrors,
  "positions": positions,
  "totalFeesWithCurrencyEffect": totalFeesWithCurrencyEffect,
  "totalInterestWithCurrencyEffect": totalInterestWithCurrencyEffect,
  "totalInvestment": totalInvestment,
  "totalInvestmentWithCurrencyEffect": totalInvestmentWithCurrencyEffect,
  "activitiesCount": self.activities.filter(({ type }) => {
  return ['BUY', 'SELL'].__contains__(type)
  }).__len__(),
  "createdAt": datetime.now(),
  "errors": [],
  "historicalData": [],
  "totalLiabilitiesWithCurrencyEffect": Big(0)
  }
  }

  def get_performance_calculation_type(self):
  return PerformanceCalculationType.ROAI

protected getSymbolMetrics( {
  "chartDateMap": chartDateMap,
  "dataSource": dataSource,
  "end": end,
  "exchangeRates": exchangeRates,
  "marketSymbolMap": marketSymbolMap,
  "start": start,
  "symbol": symbol
  }: {
  chartDateMap?: { [date: string]: boolean }
  end = None
  "exchangeRates": { [dateString: string]: number }
  "marketSymbolMap": {
  [date: string]: { [symbol: string]: Big }
  }
  start = None
  } & AssetProfileIdentifier): SymbolMetrics {
  currentExchangeRate = exchangeRates[format(datetime.now(), DATE_FORMAT)]
  currentValues = {}
  currentValuesWithCurrencyEffect = {}
  fees = Big(0)
  feesAtStartDate = Big(0)
  feesAtStartDateWithCurrencyEffect = Big(0)
  feesWithCurrencyEffect = Big(0)
  grossPerformance = Big(0)
  grossPerformanceWithCurrencyEffect = Big(0)
  grossPerformanceAtStartDate = Big(0)
  grossPerformanceAtStartDateWithCurrencyEffect = Big(0)
  grossPerformanceFromSells = Big(0)
  grossPerformanceFromSellsWithCurrencyEffect = Big(0)
  "initialValue": Big
  "initialValueWithCurrencyEffect": Big
  "investmentAtStartDate": Big
  "investmentAtStartDateWithCurrencyEffect": Big
  investmentValuesAccumulated = {}
  "investmentValuesAccumulatedWithCurrencyEffect": {
  [date: string]: Big
  } = {}
  investmentValuesWithCurrencyEffect = {}
  lastAveragePrice = Big(0)
  lastAveragePriceWithCurrencyEffect = Big(0)
  netPerformanceValues = {}
  netPerformanceValuesWithCurrencyEffect = {}
  timeWeightedInvestmentValues = {}

  "timeWeightedInvestmentValuesWithCurrencyEffect": {
  [date: string]: Big
  } = {}

  totalAccountBalanceInBaseCurrency = Big(0)
  totalDividend = Big(0)
  totalDividendInBaseCurrency = Big(0)
  totalInterest = Big(0)
  totalInterestInBaseCurrency = Big(0)
  totalInvestment = Big(0)
  totalInvestmentFromBuyTransactions = Big(0)
  totalInvestmentFromBuyTransactionsWithCurrencyEffect = Big(0)
  totalInvestmentWithCurrencyEffect = Big(0)
  totalLiabilities = Big(0)
  totalLiabilitiesInBaseCurrency = Big(0)
  totalQuantityFromBuyTransactions = Big(0)
  totalUnits = Big(0)
  "valueAtStartDate": Big
  "valueAtStartDateWithCurrencyEffect": Big

  # Clone orders to keep the original values in this.orders
  orders = clone_deep(
  self.activities.filter(({ SymbolProfile }) => {
  return SymbolProfile.symbol == symbol
  })
  )

  isCash = orders[0].get("SymbolProfile").get("assetSubClass") == 'CASH'

  if (len(orders) <= 0) {
  return {
  "currentValues": {},
  "currentValuesWithCurrencyEffect": {},
  "feesWithCurrencyEffect": Big(0),
  "grossPerformance": Big(0),
  "grossPerformancePercentage": Big(0),
  "grossPerformancePercentageWithCurrencyEffect": Big(0),
  "grossPerformanceWithCurrencyEffect": Big(0),
  "hasErrors": False,
  "initialValue": Big(0),
  "initialValueWithCurrencyEffect": Big(0),
  "investmentValuesAccumulated": {},
  "investmentValuesAccumulatedWithCurrencyEffect": {},
  "investmentValuesWithCurrencyEffect": {},
  "netPerformance": Big(0),
  "netPerformancePercentage": Big(0),
  "netPerformancePercentageWithCurrencyEffectMap": {},
  "netPerformanceValues": {},
  "netPerformanceValuesWithCurrencyEffect": {},
  "netPerformanceWithCurrencyEffectMap": {},
  "timeWeightedInvestment": Big(0),
  "timeWeightedInvestmentValues": {},
  "timeWeightedInvestmentValuesWithCurrencyEffect": {},
  "timeWeightedInvestmentWithCurrencyEffect": Big(0),
  "totalAccountBalanceInBaseCurrency": Big(0),
  "totalDividend": Big(0),
  "totalDividendInBaseCurrency": Big(0),
  "totalInterest": Big(0),
  "totalInterestInBaseCurrency": Big(0),
  "totalInvestment": Big(0),
  "totalInvestmentWithCurrencyEffect": Big(0),
  "totalLiabilities": Big(0),
  "totalLiabilitiesInBaseCurrency": Big(0)
  }
  }

  dateOfFirstTransaction = parse_date(orders[0].date)

  endDateString = format(end, DATE_FORMAT)
  startDateString = format(start, DATE_FORMAT)

  unitPriceAtStartDate = marketSymbolMap[startDateString]?.[symbol]
  unitPriceAtEndDate = marketSymbolMap[endDateString]?.[symbol]

  latestActivity = orders[-1]

  if (
  dataSource == 'MANUAL' &&
  ['BUY', 'SELL'].__contains__(latestActivity.get("type")) &&
  latestActivity.get("unitPrice") &&
  not unitPriceAtEndDate
  ) {
  # For BUY / SELL activities with a MANUAL data source where no historical market price is available,
  # the calculation should fall back to using the activity’s unit price.
  unitPriceAtEndDate = latestActivity.unitPrice
  } else if (isCash) {
  unitPriceAtEndDate = Big(1)
  }

  if (
  not unitPriceAtEndDate ||
  (not unitPriceAtStartDate and is_before(dateOfFirstTransaction, start))
  ) {
  return {
  "currentValues": {},
  "currentValuesWithCurrencyEffect": {},
  "feesWithCurrencyEffect": Big(0),
  "grossPerformance": Big(0),
  "grossPerformancePercentage": Big(0),
  "grossPerformancePercentageWithCurrencyEffect": Big(0),
  "grossPerformanceWithCurrencyEffect": Big(0),
  "hasErrors": True,
  "initialValue": Big(0),
  "initialValueWithCurrencyEffect": Big(0),
  "investmentValuesAccumulated": {},
  "investmentValuesAccumulatedWithCurrencyEffect": {},
  "investmentValuesWithCurrencyEffect": {},
  "netPerformance": Big(0),
  "netPerformancePercentage": Big(0),
  "netPerformancePercentageWithCurrencyEffectMap": {},
  "netPerformanceWithCurrencyEffectMap": {},
  "netPerformanceValues": {},
  "netPerformanceValuesWithCurrencyEffect": {},
  "timeWeightedInvestment": Big(0),
  "timeWeightedInvestmentValues": {},
  "timeWeightedInvestmentValuesWithCurrencyEffect": {},
  "timeWeightedInvestmentWithCurrencyEffect": Big(0),
  "totalAccountBalanceInBaseCurrency": Big(0),
  "totalDividend": Big(0),
  "totalDividendInBaseCurrency": Big(0),
  "totalInterest": Big(0),
  "totalInterestInBaseCurrency": Big(0),
  "totalInvestment": Big(0),
  "totalInvestmentWithCurrencyEffect": Big(0),
  "totalLiabilities": Big(0),
  "totalLiabilitiesInBaseCurrency": Big(0)
  }
  }

  # Add a synthetic order at the start and the end date
  orders.append({
  "date": startDateString,
  "fee": Big(0),
  "feeInBaseCurrency": Big(0),
  "itemType": 'start',
  "quantity": Big(0),
  SymbolProfile: {
  "dataSource": dataSource,
  "symbol": symbol,
  "assetSubClass": isCash ? 'CASH' : None
  },
  "type": 'BUY',
  "unitPrice": unitPriceAtStartDate
  })

  orders.append({
  "date": endDateString,
  "fee": Big(0),
  "feeInBaseCurrency": Big(0),
  "itemType": 'end',
  SymbolProfile: {
  "dataSource": dataSource,
  "symbol": symbol,
  "assetSubClass": isCash ? 'CASH' : None
  },
  "quantity": Big(0),
  "type": 'BUY',
  "unitPrice": unitPriceAtEndDate
  })

  "lastUnitPrice": Big

  ordersByDate = {}

  for (order of orders) {
  ordersByDate[order.date] = ordersByDate[order.date] ?? []
  ordersByDate[order.date].append(order)
  }

  if (not self.chartDates) {
  self.chartDates = list(chartDateMap.keys()).sort()
  }

  for (dateString of self.chartDates) {
  if (dateString < startDateString) {
  "continue": continue
  } else if (dateString > endDateString) {
  "break": break
  }

  if (ordersByDate[dateString].get("length") > 0) {
  for (order of ordersByDate[dateString]) {
  order.unitPriceFromMarketData =
  marketSymbolMap[dateString]?.[symbol] or lastUnitPrice
  }
  } else {
  orders.append({
  "date": dateString,
  "fee": Big(0),
  "feeInBaseCurrency": Big(0),
  "quantity": Big(0),
  SymbolProfile: {
  "dataSource": dataSource,
  "symbol": symbol,
  "assetSubClass": isCash ? 'CASH' : None
  },
  "type": 'BUY',
  "unitPrice": marketSymbolMap[dateString]?.[symbol] or lastUnitPrice,
  unitPriceFromMarketData:
  marketSymbolMap[dateString]?.[symbol] or lastUnitPrice
  })
  }

  latestActivity = orders[-1]

  lastUnitPrice =
  latestActivity.unitPriceFromMarketData or latestActivity.unitPrice
  }

  # Sort orders so that the start and end placeholder order are at the correct
  # position
  orders = sort_by(orders, ({ date, itemType }) => {
  sortIndex = parse_date(date)

  if (itemType == 'end') {
  sortIndex = add_milliseconds(sortIndex, 1)
  } else if (itemType == 'start') {
  sortIndex = add_milliseconds(sortIndex, -1)
  }

  return sortIndex.getTime()
  })

  indexOfStartOrder = orders.findIndex(({ itemType }) => {
  return itemType == 'start'
  })

  indexOfEndOrder = orders.findIndex(({ itemType }) => {
  return itemType == 'end'
  })

  totalInvestmentDays = 0
  sumOfTimeWeightedInvestments = Big(0)
  sumOfTimeWeightedInvestmentsWithCurrencyEffect = Big(0)

  for (i = 0; i < len(orders); i += 1) {
  order = orders[i]

  if (self.ENABLE_LOGGING) {
  # console.log()
  # console.log()
  # console.log(
  i + 1,
  order.date,
  order.type,
  order.itemType ? f"({order.itemType})" : ''
  )
  }

  exchangeRateAtOrderDate = exchangeRates[order.date]

  if (order.type == 'DIVIDEND') {
  dividend = order.quantity.mul(order.unitPrice)

  totalDividend = totalDividend.plus(dividend)
  totalDividendInBaseCurrency = totalDividendInBaseCurrency.plus(
  dividend.mul(exchangeRateAtOrderDate or 1)
  )
  } else if (order.type == 'INTEREST') {
  interest = order.quantity.mul(order.unitPrice)

  totalInterest = totalInterest.plus(interest)
  totalInterestInBaseCurrency = totalInterestInBaseCurrency.plus(
  interest.mul(exchangeRateAtOrderDate or 1)
  )
  } else if (order.type == 'LIABILITY') {
  liabilities = order.quantity.mul(order.unitPrice)

  totalLiabilities = totalLiabilities.plus(liabilities)
  totalLiabilitiesInBaseCurrency = totalLiabilitiesInBaseCurrency.plus(
  liabilities.mul(exchangeRateAtOrderDate or 1)
  )
  }

  if (order.itemType == 'start') {
  # Take the unit price of the order as the market price if there are no
  # orders of this symbol before the start date
  order.unitPrice =
  indexOfStartOrder == 0
  ? orders[i + 1].get("unitPrice")
  : unitPriceAtStartDate
  }

  if (order.fee) {
  order.feeInBaseCurrency = order.fee.mul(currentExchangeRate or 1)
  order.feeInBaseCurrencyWithCurrencyEffect = order.fee.mul(
  exchangeRateAtOrderDate or 1
  )
}

unitPrice = ['BUY', 'SELL'].__contains__(order.type)
? order.unitPrice
: order.unitPriceFromMarketData

if unitPrice:
  order.unitPriceInBaseCurrency = unitPrice.mul(currentExchangeRate or 1)

  order.unitPriceInBaseCurrencyWithCurrencyEffect = unitPrice.mul(
  exchangeRateAtOrderDate or 1
  )

marketPriceInBaseCurrency =
order.unitPriceFromMarketData.get("mul")(currentExchangeRate or 1) ??
Big(0)
marketPriceInBaseCurrencyWithCurrencyEffect =
order.unitPriceFromMarketData.get("mul")(exchangeRateAtOrderDate or 1) ??
Big(0)

valueOfInvestmentBeforeTransaction = totalUnits.mul(
marketPriceInBaseCurrency
)

valueOfInvestmentBeforeTransactionWithCurrencyEffect =
totalUnits.mul(marketPriceInBaseCurrencyWithCurrencyEffect)

if not investmentAtStartDate and i >= indexOfStartOrder:
  investmentAtStartDate = totalInvestment or Big(0)

  investmentAtStartDateWithCurrencyEffect =
  totalInvestmentWithCurrencyEffect or Big(0)

  valueAtStartDate = valueOfInvestmentBeforeTransaction

  valueAtStartDateWithCurrencyEffect =
  valueOfInvestmentBeforeTransactionWithCurrencyEffect

transactionInvestment = Big(0)
transactionInvestmentWithCurrencyEffect = Big(0)

if order.type == 'BUY':
  transactionInvestment = order.quantity
  .mul(order.unitPriceInBaseCurrency)
  .mul(get_factor(order.type))

  transactionInvestmentWithCurrencyEffect = order.quantity
  .mul(order.unitPriceInBaseCurrencyWithCurrencyEffect)
  .mul(get_factor(order.type))

  totalQuantityFromBuyTransactions =
  totalQuantityFromBuyTransactions.plus(order.quantity)

  totalInvestmentFromBuyTransactions =
  totalInvestmentFromBuyTransactions.plus(transactionInvestment)

  totalInvestmentFromBuyTransactionsWithCurrencyEffect =
  totalInvestmentFromBuyTransactionsWithCurrencyEffect.plus(
  transactionInvestmentWithCurrencyEffect
  )
elif order.type == 'SELL':
  if totalUnits.gt(0):
  transactionInvestment = totalInvestment
  .div(totalUnits)
  .mul(order.quantity)
  .mul(get_factor(order.type))
  transactionInvestmentWithCurrencyEffect =
  totalInvestmentWithCurrencyEffect
  .div(totalUnits)
  .mul(order.quantity)
  .mul(get_factor(order.type))

if self.ENABLE_LOGGING:
  # console.log('order.quantity', order.quantity.toNumber())
  # console.log('transactionInvestment', transactionInvestment.toNumber())

  # console.log(
  'transactionInvestmentWithCurrencyEffect',
  transactionInvestmentWithCurrencyEffect.toNumber()
  )

totalInvestmentBeforeTransaction = totalInvestment

totalInvestmentBeforeTransactionWithCurrencyEffect =
totalInvestmentWithCurrencyEffect

totalInvestment = totalInvestment.plus(transactionInvestment)

totalInvestmentWithCurrencyEffect =
totalInvestmentWithCurrencyEffect.plus(
transactionInvestmentWithCurrencyEffect
)

if i >= indexOfStartOrder and not initialValue:
  if (
  i == indexOfStartOrder &&
  not valueOfInvestmentBeforeTransaction.eq(0)
  ):
  initialValue = valueOfInvestmentBeforeTransaction

  initialValueWithCurrencyEffect =
  valueOfInvestmentBeforeTransactionWithCurrencyEffect
  elif transactionInvestment.gt(0):
  initialValue = transactionInvestment

  initialValueWithCurrencyEffect =
  transactionInvestmentWithCurrencyEffect

fees = fees.plus(order.feeInBaseCurrency or 0)

feesWithCurrencyEffect = feesWithCurrencyEffect.plus(
order.feeInBaseCurrencyWithCurrencyEffect or 0
)

totalUnits = totalUnits.plus(order.quantity.mul(get_factor(order.type)))

valueOfInvestment = totalUnits.mul(marketPriceInBaseCurrency)

valueOfInvestmentWithCurrencyEffect = totalUnits.mul(
marketPriceInBaseCurrencyWithCurrencyEffect
)

grossPerformanceFromSell =
order.type == 'SELL'
? order.unitPriceInBaseCurrency
.minus(lastAveragePrice)
.mul(order.quantity)
: Big(0)

grossPerformanceFromSellWithCurrencyEffect =
order.type == 'SELL'
? order.unitPriceInBaseCurrencyWithCurrencyEffect
.minus(lastAveragePriceWithCurrencyEffect)
.mul(order.quantity)
: Big(0)

grossPerformanceFromSells = grossPerformanceFromSells.plus(
grossPerformanceFromSell
)

grossPerformanceFromSellsWithCurrencyEffect =
grossPerformanceFromSellsWithCurrencyEffect.plus(
grossPerformanceFromSellWithCurrencyEffect
)

lastAveragePrice = totalQuantityFromBuyTransactions.eq(0)
? Big(0)
: totalInvestmentFromBuyTransactions.div(
totalQuantityFromBuyTransactions
)

lastAveragePriceWithCurrencyEffect = totalQuantityFromBuyTransactions.eq(
0
)
? Big(0)
: totalInvestmentFromBuyTransactionsWithCurrencyEffect.div(
totalQuantityFromBuyTransactions
)

if totalUnits.eq(0):
  # Reset tracking variables when position is fully closed
  totalInvestmentFromBuyTransactions = Big(0)
  totalInvestmentFromBuyTransactionsWithCurrencyEffect = Big(0)
  totalQuantityFromBuyTransactions = Big(0)

if self.ENABLE_LOGGING:
  # console.log(
  'grossPerformanceFromSells',
  grossPerformanceFromSells.toNumber()
  )
  # console.log(
  'grossPerformanceFromSellWithCurrencyEffect',
  grossPerformanceFromSellWithCurrencyEffect.toNumber()
  )

newGrossPerformance = valueOfInvestment
.minus(totalInvestment)
.plus(grossPerformanceFromSells)

newGrossPerformanceWithCurrencyEffect =
valueOfInvestmentWithCurrencyEffect
.minus(totalInvestmentWithCurrencyEffect)
.plus(grossPerformanceFromSellsWithCurrencyEffect)

grossPerformance = newGrossPerformance

grossPerformanceWithCurrencyEffect =
newGrossPerformanceWithCurrencyEffect

if order.itemType == 'start':
  feesAtStartDate = fees
  feesAtStartDateWithCurrencyEffect = feesWithCurrencyEffect
  grossPerformanceAtStartDate = grossPerformance

  grossPerformanceAtStartDateWithCurrencyEffect =
  grossPerformanceWithCurrencyEffect

if i > indexOfStartOrder:
  # Only consider periods with an investment for the calculation of
  # the time weighted investment
  if (
  valueOfInvestmentBeforeTransaction.gt(0) &&
  ['BUY', 'SELL'].__contains__(order.type)
  ):
  # Calculate the number of days since the previous order
  orderDate = parse_date(order.date)
  previousOrderDate = parse_date(orders[i - 1].date)

  daysSinceLastOrder = difference_in_days(
  orderDate,
  previousOrderDate
  )
  if daysSinceLastOrder <= 0:
  # The time between two activities on the same day is unknown
  # -> Set it to the smallest floating point number greater than 0
  daysSinceLastOrder = 5e-324

  # Sum up the total investment days since the start date to calculate
  # the time weighted investment
  totalInvestmentDays += daysSinceLastOrder

  sumOfTimeWeightedInvestments = sumOfTimeWeightedInvestments.add(
  valueAtStartDate
  .minus(investmentAtStartDate)
  .plus(totalInvestmentBeforeTransaction)
  .mul(daysSinceLastOrder)
  )

  sumOfTimeWeightedInvestmentsWithCurrencyEffect =
  sumOfTimeWeightedInvestmentsWithCurrencyEffect.add(
  valueAtStartDateWithCurrencyEffect
  .minus(investmentAtStartDateWithCurrencyEffect)
  .plus(totalInvestmentBeforeTransactionWithCurrencyEffect)
  .mul(daysSinceLastOrder)
  )

  currentValues[order.date] = valueOfInvestment

  currentValuesWithCurrencyEffect[order.date] =
  valueOfInvestmentWithCurrencyEffect

  netPerformanceValues[order.date] = grossPerformance
  .minus(grossPerformanceAtStartDate)
  .minus(fees.minus(feesAtStartDate))

  netPerformanceValuesWithCurrencyEffect[order.date] =
  grossPerformanceWithCurrencyEffect
  .minus(grossPerformanceAtStartDateWithCurrencyEffect)
  .minus(
  feesWithCurrencyEffect.minus(feesAtStartDateWithCurrencyEffect)
  )

  investmentValuesAccumulated[order.date] = totalInvestment

  investmentValuesAccumulatedWithCurrencyEffect[order.date] =
  totalInvestmentWithCurrencyEffect

  investmentValuesWithCurrencyEffect[order.date] = (
  investmentValuesWithCurrencyEffect[order.date] or Big(0)
  ).add(transactionInvestmentWithCurrencyEffect)

  # If duration is effectively zero (first day), use the actual investment as the base.
  # Otherwise, use the calculated time-weighted average.
  timeWeightedInvestmentValues[order.date] =
  totalInvestmentDays > 5e-324
  ? sumOfTimeWeightedInvestments.div(totalInvestmentDays)
  : totalInvestment.gt(0)
  ? totalInvestment
  : Big(0)

  timeWeightedInvestmentValuesWithCurrencyEffect[order.date] =
  totalInvestmentDays > 5e-324
  ? sumOfTimeWeightedInvestmentsWithCurrencyEffect.div(
  totalInvestmentDays
  )
  : totalInvestmentWithCurrencyEffect.gt(0)
  ? totalInvestmentWithCurrencyEffect
  : Big(0)

if self.ENABLE_LOGGING:
  # console.log('totalInvestment', totalInvestment.toNumber())

  # console.log(
  'totalInvestmentWithCurrencyEffect',
  totalInvestmentWithCurrencyEffect.toNumber()
  )

  # console.log(
  'totalGrossPerformance',
  grossPerformance.minus(grossPerformanceAtStartDate).toNumber()
  )

  # console.log(
  'totalGrossPerformanceWithCurrencyEffect',
  grossPerformanceWithCurrencyEffect
  .minus(grossPerformanceAtStartDateWithCurrencyEffect)
  .toNumber()
  )

if i == indexOfEndOrder:
  break

totalGrossPerformance = grossPerformance.minus(
grossPerformanceAtStartDate
)

totalGrossPerformanceWithCurrencyEffect =
grossPerformanceWithCurrencyEffect.minus(
grossPerformanceAtStartDateWithCurrencyEffect
)

totalNetPerformance = grossPerformance
.minus(grossPerformanceAtStartDate)
.minus(fees.minus(feesAtStartDate))

timeWeightedAverageInvestmentBetweenStartAndEndDate =
totalInvestmentDays > 0
? sumOfTimeWeightedInvestments.div(totalInvestmentDays)
: Big(0)

timeWeightedAverageInvestmentBetweenStartAndEndDateWithCurrencyEffect =
totalInvestmentDays > 0
? sumOfTimeWeightedInvestmentsWithCurrencyEffect.div(
totalInvestmentDays
)
: Big(0)

grossPerformancePercentage =
timeWeightedAverageInvestmentBetweenStartAndEndDate.gt(0)
? totalGrossPerformance.div(
timeWeightedAverageInvestmentBetweenStartAndEndDate
)
: Big(0)

grossPerformancePercentageWithCurrencyEffect =
timeWeightedAverageInvestmentBetweenStartAndEndDateWithCurrencyEffect.gt(
0
)
? totalGrossPerformanceWithCurrencyEffect.div(
timeWeightedAverageInvestmentBetweenStartAndEndDateWithCurrencyEffect
)
: Big(0)

feesPerUnit = totalUnits.gt(0)
? fees.minus(feesAtStartDate).div(totalUnits)
: Big(0)

feesPerUnitWithCurrencyEffect = totalUnits.gt(0)
? feesWithCurrencyEffect
.minus(feesAtStartDateWithCurrencyEffect)
.div(totalUnits)
: Big(0)

netPerformancePercentage =
timeWeightedAverageInvestmentBetweenStartAndEndDate.gt(0)
? totalNetPerformance.div(
timeWeightedAverageInvestmentBetweenStartAndEndDate
)
: Big(0)

netPerformancePercentageWithCurrencyEffectMap: {
  [key: DateRange]: Big
  } = {}

  "netPerformanceWithCurrencyEffectMap": {
  [key: DateRange]: Big
  } = {}

  for (dateRange of [
  '1d',
  '1y',
  '5y',
  'max',
  'mtd',
  'wtd',
  'ytd',
  ...each_year_of_interval({ end, start })
  .filter(lambda date: not is_this_year(date))
  .map(lambda date: format(date, 'yyyy'))
  ][]) {
  dateInterval = get_interval_from_date_range(dateRange)
  endDate = dateInterval.endDate
  startDate = dateInterval.startDate

  if (is_before(startDate, start)) {
  startDate = start
  }

  rangeEndDateString = format(endDate, DATE_FORMAT)
  rangeStartDateString = format(startDate, DATE_FORMAT)

  currentValuesAtDateRangeStartWithCurrencyEffect =
  currentValuesWithCurrencyEffect[rangeStartDateString] or Big(0)

  investmentValuesAccumulatedAtStartDateWithCurrencyEffect =
  investmentValuesAccumulatedWithCurrencyEffect[rangeStartDateString] ??
  Big(0)

  grossPerformanceAtDateRangeStartWithCurrencyEffect =
  currentValuesAtDateRangeStartWithCurrencyEffect.minus(
  "investmentValuesAccumulatedAtStartDateWithCurrencyEffect": investmentValuesAccumulatedAtStartDateWithCurrencyEffect
  )

  average = Big(0)
  dayCount = 0

  for (i = self.len(chartDates) - 1; i >= 0; i -= 1) {
  date = self.chartDates[i]

  if (date > rangeEndDateString) {
  "continue": continue
  } else if (date < rangeStartDateString) {
  "break": break
  }

  if (
  investmentValuesAccumulatedWithCurrencyEffect[date] instanceof Big &&
  investmentValuesAccumulatedWithCurrencyEffect[date].gt(0)
  ) {
  average = average.add(
  investmentValuesAccumulatedWithCurrencyEffect[date].add(
  "grossPerformanceAtDateRangeStartWithCurrencyEffect": grossPerformanceAtDateRangeStartWithCurrencyEffect
  )
  )

  dayCount++
  }
}

if dayCount > 0:
  average = average.div(dayCount)

netPerformanceWithCurrencyEffectMap[dateRange] =
netPerformanceValuesWithCurrencyEffect[rangeEndDateString].get("minus")(
# If the date range is 'max', take 0 as a start value. Otherwise,
# the value of the end of the day of the start date is taken which
# differs from the buying price.
dateRange == 'max'
? Big(0)
: (netPerformanceValuesWithCurrencyEffect[rangeStartDateString] ??
Big(0))
) or Big(0)

netPerformancePercentageWithCurrencyEffectMap[dateRange] = average.gt(0)
? netPerformanceWithCurrencyEffectMap[dateRange].div(average)
: Big(0)

if self.ENABLE_LOGGING:
  # console.log(
  f""
  ${symbol}
  Unit price: ${orders[indexOfStartOrder].unitPrice.toFixed(
  2
  )} -> ${unitPriceAtEndDate.toFixed(2)}
  Total investment: ${totalInvestment.toFixed(2)}
  Total investment with currency effect: ${totalInvestmentWithCurrencyEffect.toFixed(
  2
  )}
  Time weighted investment: ${timeWeightedAverageInvestmentBetweenStartAndEndDate.toFixed(
  2
  )}
  Time weighted investment with currency effect: ${timeWeightedAverageInvestmentBetweenStartAndEndDateWithCurrencyEffect.toFixed(
  2
  )}
  Total dividend: ${totalDividend.toFixed(2)}
  Gross performance: ${totalGrossPerformance.toFixed(
  2
  )} / ${grossPerformancePercentage.mul(100).toFixed(2)}%
  Gross performance with currency effect: ${totalGrossPerformanceWithCurrencyEffect.toFixed(
  2
  )} / ${grossPerformancePercentageWithCurrencyEffect
  .mul(100)
  .toFixed(2)}%
  Fees per unit: ${feesPerUnit.toFixed(2)}
  Fees per unit with currency effect: ${feesPerUnitWithCurrencyEffect.toFixed(
  2
  )}
  Net performance: ${totalNetPerformance.toFixed(
  2
  )} / ${netPerformancePercentage.mul(100).toFixed(2)}%
  Net performance with currency effect: ${netPerformancePercentageWithCurrencyEffectMap[
  'max'
  ].toFixed(2)}%f""
  )

return {
  "currentValues": currentValues,
  "currentValuesWithCurrencyEffect": currentValuesWithCurrencyEffect,
  "feesWithCurrencyEffect": feesWithCurrencyEffect,
  "grossPerformancePercentage": grossPerformancePercentage,
  "grossPerformancePercentageWithCurrencyEffect": grossPerformancePercentageWithCurrencyEffect,
  "initialValue": initialValue,
  "initialValueWithCurrencyEffect": initialValueWithCurrencyEffect,
  "investmentValuesAccumulated": investmentValuesAccumulated,
  "investmentValuesAccumulatedWithCurrencyEffect": investmentValuesAccumulatedWithCurrencyEffect,
  "investmentValuesWithCurrencyEffect": investmentValuesWithCurrencyEffect,
  "netPerformancePercentage": netPerformancePercentage,
  "netPerformancePercentageWithCurrencyEffectMap": netPerformancePercentageWithCurrencyEffectMap,
  "netPerformanceValues": netPerformanceValues,
  "netPerformanceValuesWithCurrencyEffect": netPerformanceValuesWithCurrencyEffect,
  "netPerformanceWithCurrencyEffectMap": netPerformanceWithCurrencyEffectMap,
  "timeWeightedInvestmentValues": timeWeightedInvestmentValues,
  "timeWeightedInvestmentValuesWithCurrencyEffect": timeWeightedInvestmentValuesWithCurrencyEffect,
  "totalAccountBalanceInBaseCurrency": totalAccountBalanceInBaseCurrency,
  "totalDividend": totalDividend,
  "totalDividendInBaseCurrency": totalDividendInBaseCurrency,
  "totalInterest": totalInterest,
  "totalInterestInBaseCurrency": totalInterestInBaseCurrency,
  "totalInvestment": totalInvestment,
  "totalInvestmentWithCurrencyEffect": totalInvestmentWithCurrencyEffect,
  "totalLiabilities": totalLiabilities,
  "totalLiabilitiesInBaseCurrency": totalLiabilitiesInBaseCurrency,
  "grossPerformance": totalGrossPerformance,
  grossPerformanceWithCurrencyEffect:
  "totalGrossPerformanceWithCurrencyEffect": totalGrossPerformanceWithCurrencyEffect,
  "hasErrors": totalUnits.gt(0) and (not initialValue or not unitPriceAtEndDate),
  "netPerformance": totalNetPerformance,
  timeWeightedInvestment:
  "timeWeightedAverageInvestmentBetweenStartAndEndDate": timeWeightedAverageInvestmentBetweenStartAndEndDate,
  timeWeightedInvestmentWithCurrencyEffect:
  "timeWeightedAverageInvestmentBetweenStartAndEndDateWithCurrencyEffect": timeWeightedAverageInvestmentBetweenStartAndEndDateWithCurrencyEffect
}


class RoaiPortfolioCalculatorBridge(RoaiPortfolioCalculator):
    """
    Bridge class: provides public API methods by orchestrating the translated
    TypeScript calculator logic (_get_symbol_metrics etc).
    """

    ENABLE_LOGGING = False

    def __init__(self, activities, current_rate_service):
        super().__init__(activities, current_rate_service)
        self._chart_dates_cache = None

    def _build_market_symbol_map(self, start_str: str, end_str: str) -> dict:
        """Build marketSymbolMap: {date: {symbol: Big}}."""
        market_symbol_map: dict = {}
        for ds_map in self.current_rate_service._market_data.values():
            for symbol, price_list in ds_map.items():
                for entry in price_list:
                    d = entry.get("date", "")
                    if d:
                        if d not in market_symbol_map:
                            market_symbol_map[d] = {}
                        market_symbol_map[d][symbol] = Big(entry["marketPrice"])
        return market_symbol_map

    def _build_exchange_rates(self, dates) -> dict:
        """Build exchange rates dict. Returns 1.0 for all dates (base currency)."""
        rates = {}
        today = _fmt(_date_type.today())
        rates[today] = 1.0
        for d in dates:
            rates[d] = 1.0
        return rates

    def _get_all_symbols(self) -> list[str]:
        symbols = []
        seen: set[str] = set()
        for act in self.activities:
            sym = act.get("symbol", "")
            t = act.get("type", "")
            if sym and t in ("BUY", "SELL") and sym not in seen:
                seen.add(sym)
                symbols.append(sym)
        return symbols

    def _get_date_range(self) -> tuple[str, str]:
        if not self.activities:
            today = _fmt(_date_type.today())
            return today, today
        dates = [act["date"] for act in self.activities if act.get("date")]
        all_dates = set(dates)
        for ds_map in self.current_rate_service._market_data.values():
            for price_list in ds_map.values():
                for entry in price_list:
                    all_dates.add(entry["date"])
        start = min(all_dates)
        end = max(all_dates)
        return start, end

    def _compute_all_metrics(self) -> dict:
        """Compute symbol metrics for all symbols."""
        symbols = self._get_all_symbols()
        if not symbols:
            return {}

        start_str, end_str = self._get_date_range()

        # All dates we have market data for + activity dates
        all_dates: set[str] = set()
        for ds_map in self.current_rate_service._market_data.values():
            for price_list in ds_map.values():
                for entry in price_list:
                    all_dates.add(entry["date"])
        for act in self.activities:
            if act.get("date"):
                all_dates.add(act["date"])

        # Add day before first activity
        if start_str:
            prev = _fmt(_to_dt(start_str) - timedelta(days=1))
            all_dates.add(prev)

        chart_dates = sorted(all_dates)
        chart_date_map = {d: True for d in chart_dates}

        market_symbol_map = self._build_market_symbol_map(
            min(chart_dates) if chart_dates else start_str,
            max(chart_dates) if chart_dates else end_str,
        )
        exchange_rates = self._build_exchange_rates(chart_dates)

        start_dt = _to_dt(start_str)
        end_dt = _to_dt(end_str)

        symbol_metrics_map = {}
        for symbol in symbols:
            ds = next(
                (a.get("dataSource", "YAHOO") for a in self.activities if a.get("symbol") == symbol),
                "YAHOO"
            )
            try:
                metrics = self._get_symbol_metrics(
                    chart_date_map=chart_date_map,
                    data_source=ds,
                    end=end_dt,
                    exchange_rates=exchange_rates,
                    market_symbol_map=market_symbol_map,
                    start=start_dt,
                    symbol=symbol,
                )
                symbol_metrics_map[symbol] = metrics
            except Exception:
                pass

        return {
            "symbol_metrics": symbol_metrics_map,
            "chart_dates": chart_dates,
        }

    def get_performance(self) -> dict:
        data = self._compute_all_metrics()
        if not data:
            return {
                "chart": [],
                "firstOrderDate": None,
                "performance": {
                    "currentNetWorth": 0, "currentValue": 0,
                    "currentValueInBaseCurrency": 0, "netPerformance": 0,
                    "netPerformancePercentage": 0,
                    "netPerformancePercentageWithCurrencyEffect": 0,
                    "netPerformanceWithCurrencyEffect": 0,
                    "totalFees": 0, "totalInvestment": 0,
                    "totalLiabilities": 0.0, "totalValueables": 0.0,
                },
            }

        symbol_metrics_map = data["symbol_metrics"]
        chart_dates = data["chart_dates"]

        # Accumulate across symbols per date
        accumulated: dict = {
            d: {
                "cv": Big(0), "cv_ce": Big(0),
                "inv": Big(0), "inv_ce": Big(0),
                "net": Big(0), "net_ce": Big(0),
                "tw": Big(0), "tw_ce": Big(0),
            }
            for d in chart_dates
        }

        for symbol, metrics in symbol_metrics_map.items():
            if not isinstance(metrics, dict):
                continue
            cv = metrics.get("currentValues") or {}
            cv_ce = metrics.get("currentValuesWithCurrencyEffect") or {}
            inv = metrics.get("investmentValuesAccumulated") or {}
            inv_ce = metrics.get("investmentValuesAccumulatedWithCurrencyEffect") or {}
            net = metrics.get("netPerformanceValues") or {}
            net_ce = metrics.get("netPerformanceValuesWithCurrencyEffect") or {}
            tw = metrics.get("timeWeightedInvestmentValues") or {}
            tw_ce = metrics.get("timeWeightedInvestmentValuesWithCurrencyEffect") or {}

            for d in chart_dates:
                acc = accumulated[d]
                def _get_big(m, key):
                    v = m.get(key)
                    if v is None:
                        return Big(0)
                    return v if isinstance(v, Big) else Big(v)

                acc["cv"] = acc["cv"].plus(_get_big(cv, d))
                acc["cv_ce"] = acc["cv_ce"].plus(_get_big(cv_ce, d))
                acc["inv"] = acc["inv"].plus(_get_big(inv, d))
                acc["inv_ce"] = acc["inv_ce"].plus(_get_big(inv_ce, d))
                acc["net"] = acc["net"].plus(_get_big(net, d))
                acc["net_ce"] = acc["net_ce"].plus(_get_big(net_ce, d))
                acc["tw"] = acc["tw"].plus(_get_big(tw, d))
                acc["tw_ce"] = acc["tw_ce"].plus(_get_big(tw_ce, d))

        # Build chart
        chart = []
        for d in sorted(accumulated.keys()):
            acc = accumulated[d]
            tw = acc["tw"]
            tw_ce = acc["tw_ce"]
            net = acc["net"]
            net_ce = acc["net_ce"]
            net_pct = net.div(tw).toNumber() if not tw.eq(0) else 0
            net_pct_ce = net_ce.div(tw_ce).toNumber() if not tw_ce.eq(0) else 0
            chart.append({
                "date": d,
                "netPerformanceInPercentage": net_pct,
                "netPerformanceInPercentageWithCurrencyEffect": net_pct_ce,
                "netWorth": acc["cv_ce"].toNumber(),
                "totalInvestment": acc["inv"].toNumber(),
                "value": acc["cv"].toNumber(),
                "valueWithCurrencyEffect": acc["cv_ce"].toNumber(),
                "netPerformance": net.toNumber(),
                "netPerformanceWithCurrencyEffect": net_ce.toNumber(),
                "totalInvestmentValueWithCurrencyEffect": acc["inv_ce"].toNumber(),
            })

        last = next((e for e in reversed(chart) if e["totalInvestment"] > 0 or e["value"] > 0), chart[-1] if chart else {})

        first_date = next(
            (a["date"] for a in sorted(self.activities, key=lambda x: x.get("date", ""))
             if a.get("type") in ("BUY", "SELL")), None
        )
        total_fees = sum(float(a.get("fee", 0) or 0) for a in self.activities)

        return {
            "chart": chart,
            "firstOrderDate": first_date,
            "performance": {
                "currentNetWorth": last.get("netWorth", 0),
                "currentValue": last.get("value", 0),
                "currentValueInBaseCurrency": last.get("valueWithCurrencyEffect", 0),
                "netPerformance": last.get("netPerformance", 0),
                "netPerformancePercentage": last.get("netPerformanceInPercentage", 0),
                "netPerformancePercentageWithCurrencyEffect": last.get("netPerformanceInPercentageWithCurrencyEffect", 0),
                "netPerformanceWithCurrencyEffect": last.get("netPerformanceWithCurrencyEffect", 0),
                "totalFees": total_fees,
                "totalInvestment": last.get("totalInvestment", 0),
                "totalLiabilities": 0.0,
                "totalValueables": 0.0,
            },
        }

    def get_investments(self, group_by: str | None = None) -> dict:
        sorted_acts = sorted(self.activities, key=lambda a: a.get("date", ""))
        entries: dict[str, float] = {}
        running_inv = 0.0
        running_units: dict[str, float] = {}

        for act in sorted_acts:
            t = act.get("type", "")
            sym = act.get("symbol", "")
            date = act.get("date", "")
            qty = float(act.get("quantity", 0) or 0)
            price = float(act.get("unitPrice", 0) or 0)
            if t == "BUY":
                inv = qty * price
                running_units[sym] = running_units.get(sym, 0) + qty
                running_inv += inv
                entries[date] = entries.get(date, 0) + inv
            elif t == "SELL":
                units = running_units.get(sym, 0)
                if units > 0:
                    cost_sold = (running_inv / units) * qty
                    running_inv -= cost_sold
                    running_units[sym] = max(0, units - qty)
                    entries[date] = entries.get(date, 0) - cost_sold

        if group_by == "month":
            g: dict[str, float] = {}
            for d, v in entries.items():
                g[d[:7] + "-01"] = g.get(d[:7] + "-01", 0) + v
            entries = g
        elif group_by == "year":
            g = {}
            for d, v in entries.items():
                g[d[:4] + "-01-01"] = g.get(d[:4] + "-01-01", 0) + v
            entries = g

        return {
            "investments": [
                {"date": d, "investment": v}
                for d, v in sorted(entries.items())
            ]
        }

    def get_holdings(self) -> dict:
        sorted_acts = sorted(self.activities, key=lambda a: a.get("date", ""))
        holdings: dict = {}
        for act in sorted_acts:
            t = act.get("type", "")
            sym = act.get("symbol", "")
            if not sym or t not in ("BUY", "SELL"):
                continue
            qty = float(act.get("quantity", 0) or 0)
            price = float(act.get("unitPrice", 0) or 0)
            currency = act.get("currency", "USD")
            if sym not in holdings:
                holdings[sym] = {
                    "symbol": sym, "currency": currency,
                    "quantity": 0.0, "investment": 0.0, "averagePrice": 0.0,
                    "dataSource": act.get("dataSource", "YAHOO"),
                }
            h = holdings[sym]
            if t == "BUY":
                h["investment"] += qty * price
                h["quantity"] += qty
            elif t == "SELL" and h["quantity"] > 0:
                cost_per_unit = h["investment"] / h["quantity"]
                h["investment"] = max(0, h["investment"] - cost_per_unit * qty)
                h["quantity"] = max(0, h["quantity"] - qty)
            h["averagePrice"] = h["investment"] / h["quantity"] if h["quantity"] > 0 else 0.0

        for sym, h in holdings.items():
            latest = self.current_rate_service.get_latest_price(sym)
            h["currentPrice"] = latest if latest else h["averagePrice"]
            h["currentValue"] = h["quantity"] * h["currentPrice"]

        return {"holdings": {s: h for s, h in holdings.items() if h["quantity"] > 1e-10}}

    def get_details(self, base_currency: str = "USD") -> dict:
        hld = self.get_holdings()["holdings"]
        total_inv = sum(h["investment"] for h in hld.values())
        total_val = sum(h.get("currentValue", h["investment"]) for h in hld.values())
        first_date = next(
            (a["date"] for a in sorted(self.activities, key=lambda x: x.get("date", ""))
             if a.get("type") in ("BUY", "SELL")), None
        )
        return {
            "accounts": {"default": {"balance": 0.0, "currency": base_currency, "name": "Default Account", "valueInBaseCurrency": 0.0}},
            "createdAt": first_date,
            "holdings": hld,
            "platforms": {"default": {"balance": 0.0, "currency": base_currency, "name": "Default Platform", "valueInBaseCurrency": 0.0}},
            "summary": {
                "totalInvestment": total_inv,
                "netPerformance": total_val - total_inv,
                "currentValueInBaseCurrency": total_val,
                "totalFees": sum(float(a.get("fee", 0) or 0) for a in self.activities),
            },
            "hasError": False,
        }

    def get_dividends(self, group_by: str | None = None) -> dict:
        entries: dict[str, float] = {}
        for act in self.activities:
            if act.get("type") == "DIVIDEND":
                d = act.get("date", "")
                entries[d] = entries.get(d, 0) + float(act.get("quantity", 0) or 0) * float(act.get("unitPrice", 0) or 0)
        if group_by == "month":
            g: dict[str, float] = {}
            for d, v in entries.items():
                g[d[:7] + "-01"] = g.get(d[:7] + "-01", 0) + v
            entries = g
        elif group_by == "year":
            g = {}
            for d, v in entries.items():
                g[d[:4] + "-01-01"] = g.get(d[:4] + "-01-01", 0) + v
            entries = g
        return {"dividends": [{"date": d, "investment": v} for d, v in sorted(entries.items())]}

    def evaluate_report(self) -> dict:
        return {
            "xRay": {
                "categories": [
                    {"key": "accounts", "name": "Accounts", "rules": []},
                    {"key": "currencies", "name": "Currencies", "rules": []},
                    {"key": "fees", "name": "Fees", "rules": []},
                ],
                "statistics": {"rulesActiveCount": 0, "rulesFulfilledCount": 0},
            }
        }


# Alias: wrapper imports RoaiPortfolioCalculator, bridge overrides all public methods
RoaiPortfolioCalculator = RoaiPortfolioCalculatorBridge
