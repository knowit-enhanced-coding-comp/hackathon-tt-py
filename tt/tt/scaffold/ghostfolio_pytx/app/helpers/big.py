"""Big — decimal arithmetic class mirroring the big.js API."""
from __future__ import annotations
from decimal import Decimal, ROUND_HALF_UP, getcontext

getcontext().prec = 28


class Big:
    """Mimics big.js: immutable decimal value with chainable arithmetic."""

    __slots__ = ("_v",)

    def __init__(self, value=0):
        if isinstance(value, Big):
            object.__setattr__(self, "_v", value._v)
        elif isinstance(value, Decimal):
            object.__setattr__(self, "_v", value)
        elif isinstance(value, float):
            object.__setattr__(self, "_v", Decimal(str(value)))
        elif isinstance(value, int):
            object.__setattr__(self, "_v", Decimal(value))
        elif isinstance(value, str):
            try:
                object.__setattr__(self, "_v", Decimal(value))
            except Exception:
                object.__setattr__(self, "_v", Decimal("0"))
        else:
            try:
                object.__setattr__(self, "_v", Decimal(str(value)))
            except Exception:
                object.__setattr__(self, "_v", Decimal("0"))

    @classmethod
    def _from_decimal(cls, d: Decimal) -> "Big":
        obj = cls.__new__(cls)
        object.__setattr__(obj, "_v", d)
        return obj

    def _coerce(self, other) -> "Big":
        return other if isinstance(other, Big) else Big(other)

    # Arithmetic
    def plus(self, other) -> "Big":
        return Big._from_decimal(self._v + self._coerce(other)._v)

    def add(self, other) -> "Big":
        return self.plus(other)

    def minus(self, other) -> "Big":
        return Big._from_decimal(self._v - self._coerce(other)._v)

    def sub(self, other) -> "Big":
        return self.minus(other)

    def mul(self, other) -> "Big":
        return Big._from_decimal(self._v * self._coerce(other)._v)

    def times(self, other) -> "Big":
        return self.mul(other)

    def div(self, other) -> "Big":
        o = self._coerce(other)._v
        if o == 0:
            raise ZeroDivisionError("Division by zero in Big.div()")
        return Big._from_decimal(self._v / o)

    def pow(self, exp) -> "Big":
        return Big._from_decimal(self._v ** int(exp))

    def neg(self) -> "Big":
        return Big._from_decimal(-self._v)

    def abs(self) -> "Big":
        return Big._from_decimal(abs(self._v))

    def sqrt(self) -> "Big":
        return Big._from_decimal(self._v.sqrt())

    # Comparison
    def eq(self, other) -> bool:
        return self._v == self._coerce(other)._v

    def gt(self, other) -> bool:
        return self._v > self._coerce(other)._v

    def gte(self, other) -> bool:
        return self._v >= self._coerce(other)._v

    def lt(self, other) -> bool:
        return self._v < self._coerce(other)._v

    def lte(self, other) -> bool:
        return self._v <= self._coerce(other)._v

    # Output
    def toNumber(self) -> float:
        return float(self._v)

    def toFixed(self, dp: int = 2) -> str:
        factor = Decimal(10) ** dp
        rounded = (self._v * factor).quantize(Decimal("1"), rounding=ROUND_HALF_UP) / factor
        return f"{rounded:.{dp}f}"

    def toPrecision(self, sd: int = 6) -> str:
        return f"{float(self._v):.{sd}g}"

    def __float__(self) -> float:
        return float(self._v)

    def __int__(self) -> int:
        return int(self._v)

    def __bool__(self) -> bool:
        return self._v != 0

    def __repr__(self) -> str:
        return f"Big({self._v})"

    def __str__(self) -> str:
        return str(self._v)

    def __setattr__(self, *_):
        raise AttributeError("Big is immutable")

    # Python arithmetic operators (for convenience)
    def __add__(self, other):
        return self.plus(other)

    def __radd__(self, other):
        return Big(other).plus(self)

    def __sub__(self, other):
        return self.minus(other)

    def __rsub__(self, other):
        return Big(other).minus(self)

    def __mul__(self, other):
        return self.mul(other)

    def __rmul__(self, other):
        return Big(other).mul(self)

    def __truediv__(self, other):
        return self.div(other)

    def __rtruediv__(self, other):
        return Big(other).div(self)

    def __neg__(self):
        return self.neg()

    def __abs__(self):
        return self.abs()

    def __eq__(self, other):
        if isinstance(other, (int, float, str, Decimal)):
            return self.eq(other)
        if isinstance(other, Big):
            return self._v == other._v
        return NotImplemented

    def __lt__(self, other):
        return self.lt(other)

    def __le__(self, other):
        return self.lte(other)

    def __gt__(self, other):
        return self.gt(other)

    def __ge__(self, other):
        return self.gte(other)

    def __hash__(self):
        return hash(self._v)

    # isinstance check helpers
    @classmethod
    def max(cls, *args) -> "Big":
        bigs = [cls(a) for a in args]
        return max(bigs, key=lambda b: b._v)

    @classmethod
    def min(cls, *args) -> "Big":
        bigs = [cls(a) for a in args]
        return min(bigs, key=lambda b: b._v)
