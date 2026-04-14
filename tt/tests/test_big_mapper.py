"""
Tests for tt.big_mapper — Property 3 from the hackathon-tt-competition spec.

# Feature: hackathon-tt-competition, Property 3: Big.js Arithmetic Translation Preserves Semantics
"""
from __future__ import annotations

import pytest
from decimal import Decimal
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from tt.big_mapper import is_big_expression, translate_big_expression


# ---------------------------------------------------------------------------
# Unit tests — is_big_expression
# ---------------------------------------------------------------------------

def test_is_big_expression_detects_new_big() -> None:
    assert is_big_expression("new Big(5)") is True


def test_is_big_expression_detects_bare_big() -> None:
    assert is_big_expression("Big(0)") is True


def test_is_big_expression_returns_false_for_plain_expr() -> None:
    assert is_big_expression("x + y") is False


def test_is_big_expression_returns_false_for_empty() -> None:
    assert is_big_expression("") is False


def test_is_big_expression_detects_method_chain() -> None:
    assert is_big_expression("new Big(1).plus(2)") is True


# ---------------------------------------------------------------------------
# Unit tests — constructor translation
# ---------------------------------------------------------------------------

def test_translate_new_big_with_number() -> None:
    result = translate_big_expression("new Big(5)")
    assert result == "Decimal(str(5))"


def test_translate_new_big_with_variable() -> None:
    result = translate_big_expression("new Big(value)")
    assert result == "Decimal(str(value))"


def test_translate_bare_big_with_variable() -> None:
    result = translate_big_expression("Big(x)")
    assert result == "Decimal(str(x))"


def test_translate_big_zero_identity() -> None:
    result = translate_big_expression("Big(0)")
    assert result == "Decimal('0')"


def test_translate_new_big_zero() -> None:
    result = translate_big_expression("new Big(0)")
    assert result == "Decimal(str(0))"


# ---------------------------------------------------------------------------
# Unit tests — arithmetic method chains
# ---------------------------------------------------------------------------

def test_translate_plus() -> None:
    result = translate_big_expression("new Big(1).plus(2)")
    assert "+ 2" in result


def test_translate_minus() -> None:
    result = translate_big_expression("new Big(10).minus(3)")
    assert "- 3" in result


def test_translate_mul() -> None:
    result = translate_big_expression("new Big(4).mul(5)")
    assert "* 5" in result


def test_translate_div() -> None:
    result = translate_big_expression("new Big(10).div(2)")
    assert "/ 2" in result


def test_translate_add_alias() -> None:
    result = translate_big_expression("new Big(1).add(2)")
    assert "+ 2" in result


# ---------------------------------------------------------------------------
# Unit tests — comparison method chains
# ---------------------------------------------------------------------------

def test_translate_eq() -> None:
    result = translate_big_expression("x.eq(0)")
    assert "== 0" in result


def test_translate_gt() -> None:
    result = translate_big_expression("x.gt(0)")
    assert "> 0" in result


def test_translate_lt() -> None:
    result = translate_big_expression("x.lt(0)")
    assert "< 0" in result


def test_translate_gte() -> None:
    result = translate_big_expression("x.gte(0)")
    assert ">= 0" in result


def test_translate_lte() -> None:
    result = translate_big_expression("x.lte(0)")
    assert "<= 0" in result


# ---------------------------------------------------------------------------
# Unit tests — conversion methods
# ---------------------------------------------------------------------------

def test_translate_to_number() -> None:
    result = translate_big_expression("new Big(3).toNumber()")
    assert result.startswith("float(")


def test_translate_to_fixed() -> None:
    result = translate_big_expression("new Big(3.14159).toFixed(2)")
    assert result.startswith("round(")
    assert "2" in result


def test_translate_to_fixed_zero_places() -> None:
    result = translate_big_expression("x.toFixed(0)")
    assert result.startswith("round(")
    assert "0" in result


# ---------------------------------------------------------------------------
# Unit tests — chained expressions
# ---------------------------------------------------------------------------

def test_translate_chained_plus_minus() -> None:
    result = translate_big_expression("new Big(10).plus(5).minus(3)")
    assert "+ 5" in result
    assert "- 3" in result


def test_translate_chained_mul_div() -> None:
    result = translate_big_expression("new Big(6).mul(2).div(3)")
    assert "* 2" in result
    assert "/ 3" in result


# ---------------------------------------------------------------------------
# Property 3: Big.js Arithmetic Translation Preserves Semantics
# Feature: hackathon-tt-competition, Property 3: Big.js Arithmetic Translation Preserves Semantics
# ---------------------------------------------------------------------------

# Strategies for generating valid numeric values
_numeric = st.one_of(
    st.integers(min_value=-1000, max_value=1000),
    st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
)

_safe_numeric = st.integers(min_value=-100, max_value=100)


@st.composite
def big_chain_and_values(draw: st.DrawFn) -> tuple[str, dict[str, Decimal]]:
    """Generate a Big.js method chain and corresponding numeric values."""
    base_val = draw(_safe_numeric)
    ops = draw(st.lists(
        st.sampled_from(["plus", "minus", "mul"]),
        min_size=1,
        max_size=4,
    ))
    arg_vals = [draw(_safe_numeric) for _ in ops]

    # Build TS expression using variable names
    chain = f"new Big(base)"
    for op, val in zip(ops, arg_vals):
        chain += f".{op}(arg{ops.index(op)}_{val})"

    # Build values dict
    values: dict[str, Decimal] = {"base": Decimal(str(base_val))}
    for op, val in zip(ops, arg_vals):
        values[f"arg{ops.index(op)}_{val}"] = Decimal(str(val))

    return chain, values


@given(
    base=st.integers(min_value=-100, max_value=100),
    arg=st.integers(min_value=-100, max_value=100),
    op=st.sampled_from(["plus", "minus", "mul"]),
)
@settings(max_examples=100)
def test_property3_translated_expression_is_syntactically_valid_python(
    base: int, arg: int, op: str
) -> None:
    """Property 3: translated Big.js expression is syntactically valid Python."""
    ts_expr = f"new Big({base}).{op}({arg})"
    py_expr = translate_big_expression(ts_expr)

    # Must be syntactically valid Python
    try:
        compile(py_expr, "<string>", "eval")
    except SyntaxError as e:
        pytest.fail(f"Translated expression is not valid Python: {py_expr!r}\nError: {e}")


@given(
    base=st.integers(min_value=-100, max_value=100),
    arg=st.integers(min_value=1, max_value=100),  # avoid div by zero
    op=st.sampled_from(["plus", "minus", "mul", "div"]),
)
@settings(max_examples=100)
def test_property3_translated_expression_semantically_equivalent(
    base: int, arg: int, op: str
) -> None:
    """Property 3: translated Big.js expression is semantically equivalent to Decimal arithmetic."""
    assume(not (op == "div" and arg == 0))

    ts_expr = f"new Big({base}).{op}({arg})"
    py_expr = translate_big_expression(ts_expr)

    # Evaluate the translated expression
    try:
        result = eval(py_expr, {"Decimal": Decimal})  # noqa: S307
    except Exception as e:
        pytest.fail(f"Translated expression raised: {e}\nExpression: {py_expr!r}")

    # Compute expected result using Decimal directly
    b = Decimal(str(base))
    a = Decimal(str(arg))
    expected_map = {
        "plus": b + a,
        "minus": b - a,
        "mul": b * a,
        "div": b / a,
    }
    expected = expected_map[op]

    assert result == expected, (
        f"Semantic mismatch for {ts_expr!r}\n"
        f"Translated: {py_expr!r}\n"
        f"Got: {result}, Expected: {expected}"
    )


@given(
    base=st.integers(min_value=-50, max_value=50),
    arg1=st.integers(min_value=-50, max_value=50),
    arg2=st.integers(min_value=-50, max_value=50),
    ops=st.lists(
        st.sampled_from(["plus", "minus", "mul"]),
        min_size=2,
        max_size=3,
    ),
)
@settings(max_examples=100)
def test_property3_chained_expression_is_valid_python(
    base: int, arg1: int, arg2: int, ops: list[str]
) -> None:
    """Property 3: chained Big.js method calls produce valid Python."""
    chain = f"new Big({base})"
    args = [arg1, arg2] + [0] * max(0, len(ops) - 2)
    for op, arg in zip(ops, args):
        chain += f".{op}({arg})"

    py_expr = translate_big_expression(chain)

    try:
        compile(py_expr, "<string>", "eval")
    except SyntaxError as e:
        pytest.fail(f"Chained expression not valid Python: {py_expr!r}\nError: {e}")


@given(
    val=st.integers(min_value=-1000, max_value=1000),
    op=st.sampled_from(["eq", "gt", "lt", "gte", "lte"]),
    cmp=st.integers(min_value=-1000, max_value=1000),
)
@settings(max_examples=100)
def test_property3_comparison_chain_is_valid_python(
    val: int, op: str, cmp: int
) -> None:
    """Property 3: Big.js comparison chains produce valid Python."""
    ts_expr = f"new Big({val}).{op}({cmp})"
    py_expr = translate_big_expression(ts_expr)

    try:
        compile(py_expr, "<string>", "eval")
    except SyntaxError as e:
        pytest.fail(f"Comparison expression not valid Python: {py_expr!r}\nError: {e}")


@given(
    val=st.integers(min_value=-1000, max_value=1000),
    op=st.sampled_from(["plus", "minus", "mul"]),
    arg=st.integers(min_value=-1000, max_value=1000),
)
@settings(max_examples=100)
def test_property3_to_number_chain_is_valid_python(
    val: int, op: str, arg: int
) -> None:
    """Property 3: Big.js chain ending in .toNumber() produces valid Python."""
    ts_expr = f"new Big({val}).{op}({arg}).toNumber()"
    py_expr = translate_big_expression(ts_expr)

    try:
        compile(py_expr, "<string>", "eval")
    except SyntaxError as e:
        pytest.fail(f"toNumber chain not valid Python: {py_expr!r}\nError: {e}")

    # Must evaluate to a float
    result = eval(py_expr, {"Decimal": Decimal})  # noqa: S307
    assert isinstance(result, float), f"Expected float, got {type(result)}: {result}"
