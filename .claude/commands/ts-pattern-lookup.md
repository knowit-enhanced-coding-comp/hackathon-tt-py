Look up the correct Python equivalent for a TypeScript pattern found in the ghostfolio source.

## Input

The user provides a TS pattern or construct (e.g., `.plus()`, `format(date, DATE_FORMAT)`, `cloneDeep`, `new Big(0)`, optional chaining `?.`)

## Steps

1. Search for the pattern in the TypeScript source files under `projects/ghostfolio/apps/api/src/app/portfolio/calculator/`
2. Show 2-3 actual usage examples from the source
3. Provide the correct Python equivalent with edge-case notes

## Reference mappings

### Big.js arithmetic (most critical, appears everywhere)
- `new Big(0)` / `new Big(value)` -> `Decimal(0)` / `Decimal(str(value))` - use `from decimal import Decimal`
- `.plus(x)` -> `+ x` (operator)
- `.minus(x)` -> `- x`
- `.mul(x)` -> `* x`
- `.div(x)` -> `/ x`
- `.eq(x)` -> `== x`
- `.gt(x)` / `.gte(x)` / `.lt(x)` / `.lte(x)` -> `>` / `>=` / `<` / `<=`
- `.toNumber()` -> `float(x)` (for JSON serialization at API boundary)
- `.abs()` -> `abs(x)`
- Rounding: Big.js default is ROUND_HALF_UP; Python Decimal default is ROUND_HALF_EVEN. They match for most cases but diverge on 0.5 -> check if this matters.

### date-fns to Python datetime
- `format(date, 'yyyy-MM-dd')` -> `date.strftime("%Y-%m-%d")` or `str(date)[:10]`
- `differenceInDays(a, b)` -> `(a - b).days`
- `isBefore(a, b)` -> `a < b`
- `isAfter(a, b)` -> `a > b`
- `addMilliseconds(d, n)` -> `d + timedelta(milliseconds=n)`
- `eachYearOfInterval({start, end})` -> `[date(y, 1, 1) for y in range(start.year, end.year + 1)]`
- `startOfDay(d)` -> `datetime.combine(d.date(), time.min)` or `d.replace(hour=0, minute=0, second=0, microsecond=0)`
- `endOfDay(d)` -> `d.replace(hour=23, minute=59, second=59, microsecond=999999)`
- `startOfYear(d)` -> `date(d.year, 1, 1)`
- `endOfYear(d)` -> `date(d.year, 12, 31)`
- `isThisYear(d)` -> `d.year == date.today().year`
- `subDays(d, n)` -> `d - timedelta(days=n)`
- `isWithinInterval(d, {start, end})` -> `start <= d <= end`

### lodash to Python builtins
- `cloneDeep(x)` -> `copy.deepcopy(x)`
- `sortBy(arr, key)` -> `sorted(arr, key=lambda x: x[key])`
- `isNumber(x)` -> `isinstance(x, (int, float, Decimal))`
- `sum(arr)` -> `sum(arr)`
- `uniqBy(arr, key)` -> `list({x[key]: x for x in arr}.values())`

### Structural
- `x?.y` -> `x.y if x is not None else None` or `getattr(x, "y", None)`
- `x ?? y` -> `x if x is not None else y`
- `const { a, b } = obj` -> `a, b = obj["a"], obj["b"]`
- `arr.filter(fn)` -> `[x for x in arr if fn(x)]`
- `arr.map(fn)` -> `[fn(x) for x in arr]`
- `arr.reduce(fn, init)` -> `functools.reduce(fn, arr, init)`
- `arr.at(-1)` -> `arr[-1]`
- `Object.keys(obj)` -> `list(obj.keys())`
- `Object.entries(obj)` -> `list(obj.items())`
- `Array.from(new Set(arr))` -> `list(set(arr))`

## Output

Show the TS pattern, its Python equivalent, any semantic gotchas, and a concrete before/after code example from the actual source.
