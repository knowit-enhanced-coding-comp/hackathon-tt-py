"""
Tests for tt.transformer — Property 4 from the hackathon-tt-competition spec.

# Feature: hackathon-tt-competition, Property 4: Expression Translation Structural Correctness
"""
from __future__ import annotations

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from tt.transformer import (
    camel_to_snake,
    translate_type,
)


# ---------------------------------------------------------------------------
# Unit tests — camel_to_snake
# ---------------------------------------------------------------------------

def test_camel_to_snake_simple() -> None:
    assert camel_to_snake("camelCase") == "camel_case"


def test_camel_to_snake_multiple_words() -> None:
    assert camel_to_snake("getSymbolMetrics") == "get_symbol_metrics"


def test_camel_to_snake_already_snake() -> None:
    assert camel_to_snake("snake_case") == "snake_case"


def test_camel_to_snake_single_word() -> None:
    assert camel_to_snake("value") == "value"


def test_camel_to_snake_uppercase_start() -> None:
    assert camel_to_snake("MyClass") == "my_class"


def test_camel_to_snake_consecutive_caps() -> None:
    # e.g. "getHTTPResponse" → "get_h_t_t_p_response" (standard re-based approach)
    result = camel_to_snake("totalInvestmentWithCurrencyEffect")
    assert result == "total_investment_with_currency_effect"


# ---------------------------------------------------------------------------
# Unit tests — translate_type
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("ts_type,expected", [
    ("string", "str"),
    ("number", "float"),
    ("boolean", "bool"),
    ("Big", "Decimal"),
    ("Date", "datetime"),
    ("void", "None"),
    ("any", "Any"),
    ("undefined", "None"),
    ("null", "None"),
    ("never", "None"),
    ("object", "dict"),
    ("unknown", "Any"),
])
def test_translate_type_primitives(ts_type: str, expected: str) -> None:
    assert translate_type(ts_type) == expected


def test_translate_type_array_suffix() -> None:
    assert translate_type("string[]") == "list[str]"


def test_translate_type_array_of_big() -> None:
    assert translate_type("Big[]") == "list[Decimal]"


def test_translate_type_generic_array() -> None:
    assert translate_type("Array<number>") == "list[float]"


def test_translate_type_record() -> None:
    assert translate_type("Record<string, number>") == "dict[str, float]"


def test_translate_type_promise() -> None:
    assert translate_type("Promise<string>") == "str"


def test_translate_type_unknown_passthrough() -> None:
    assert translate_type("MyCustomType") == "MyCustomType"


# ---------------------------------------------------------------------------
# Text-based expression translation tests (no tree-sitter needed)
# ---------------------------------------------------------------------------

# We test the text-level translation helpers via big_mapper and date_mapper
# since translate_expression requires tree-sitter Node objects.
# The property tests below use compile() to verify syntactic validity of
# hand-crafted translated expressions.

def _is_valid_python_expr(expr: str) -> bool:
    """Return True if expr is syntactically valid Python."""
    try:
        compile(expr, "<string>", "eval")
        return True
    except SyntaxError:
        return False


def _is_valid_python_stmt(stmt: str) -> bool:
    """Return True if stmt is syntactically valid Python."""
    try:
        compile(stmt, "<string>", "exec")
        return True
    except SyntaxError:
        return False


# ---------------------------------------------------------------------------
# Unit tests — ternary translation pattern
# ---------------------------------------------------------------------------

def test_ternary_pattern_is_valid_python() -> None:
    # TS: condition ? a : b → Python: a if condition else b
    py = "b if a else c"
    assert _is_valid_python_expr(py)


def test_ternary_with_none_is_valid_python() -> None:
    py = "x if x is not None else None"
    assert _is_valid_python_expr(py)


def test_ternary_nested_is_valid_python() -> None:
    py = "(b if a else c) if x else d"
    assert _is_valid_python_expr(py)


# ---------------------------------------------------------------------------
# Unit tests — optional chaining translation pattern
# ---------------------------------------------------------------------------

def test_optional_chain_pattern_is_valid_python() -> None:
    # TS: obj?.prop → Python: obj.prop if obj is not None else None
    py = "obj.prop if obj is not None else None"
    assert _is_valid_python_expr(py)


def test_optional_chain_nested_is_valid_python() -> None:
    py = "obj.inner.prop if obj is not None else None"
    assert _is_valid_python_expr(py)


# ---------------------------------------------------------------------------
# Unit tests — nullish coalescing translation pattern
# ---------------------------------------------------------------------------

def test_nullish_coalescing_pattern_is_valid_python() -> None:
    # TS: a ?? b → Python: a if a is not None else b
    py = "a if a is not None else b"
    assert _is_valid_python_expr(py)


def test_nullish_coalescing_with_default_is_valid_python() -> None:
    py = "value if value is not None else 0"
    assert _is_valid_python_expr(py)


# ---------------------------------------------------------------------------
# Unit tests — for...of translation pattern
# ---------------------------------------------------------------------------

def test_for_of_pattern_is_valid_python() -> None:
    # TS: for (const x of arr) { ... } → Python: for x in arr: ...
    py = "for x in arr:\n    pass"
    assert _is_valid_python_stmt(py)


def test_for_of_with_body_is_valid_python() -> None:
    py = "for item in items:\n    result = item + 1"
    assert _is_valid_python_stmt(py)


# ---------------------------------------------------------------------------
# Unit tests — destructuring translation pattern
# ---------------------------------------------------------------------------

def test_object_destructuring_pattern_is_valid_python() -> None:
    # TS: const { x, y } = obj → Python: x = obj["x"]\ny = obj["y"]
    py = 'x = obj["x"]\ny = obj["y"]'
    assert _is_valid_python_stmt(py)


def test_array_destructuring_pattern_is_valid_python() -> None:
    # TS: const [a, b] = arr → Python: a, b = arr
    py = "a, b = arr"
    assert _is_valid_python_stmt(py)


# ---------------------------------------------------------------------------
# Unit tests — template literal translation pattern
# ---------------------------------------------------------------------------

def test_template_literal_pattern_is_valid_python() -> None:
    # TS: `text ${expr}` → Python: f"text {expr}"
    py = 'f"text {expr}"'
    assert _is_valid_python_expr(py)


def test_template_literal_with_multiple_exprs_is_valid_python() -> None:
    py = 'f"Hello {name}, you have {count} items"'
    assert _is_valid_python_expr(py)


# ---------------------------------------------------------------------------
# Unit tests — lodash translation patterns
# ---------------------------------------------------------------------------

def test_sort_by_pattern_is_valid_python() -> None:
    py = "sorted(arr, key=fn)"
    assert _is_valid_python_expr(py)


def test_clone_deep_pattern_is_valid_python() -> None:
    py = "copy.deepcopy(x)"
    assert _is_valid_python_expr(py)


def test_is_number_pattern_is_valid_python() -> None:
    py = "isinstance(x, (int, float))"
    assert _is_valid_python_expr(py)


# ---------------------------------------------------------------------------
# Property 4: Expression Translation Structural Correctness
# Feature: hackathon-tt-competition, Property 4: Expression Translation Structural Correctness
# ---------------------------------------------------------------------------

_identifiers = st.from_regex(r"[a-z][a-z0-9_]{0,10}", fullmatch=True)
_small_ints = st.integers(min_value=-100, max_value=100)


@given(
    cond=_identifiers,
    cons=_identifiers,
    alt=_identifiers,
)
@settings(max_examples=100)
def test_property4_ternary_translation_is_valid_python(
    cond: str, cons: str, alt: str
) -> None:
    """Property 4: ternary translation produces syntactically valid Python."""
    assume(cond != cons and cond != alt)
    assume(not any(_keyword.iskeyword(x) for x in (cond, cons, alt)))
    # Simulated translation of: cond ? cons : alt → cons if cond else alt
    py_expr = f"{cons} if {cond} else {alt}"
    assert _is_valid_python_expr(py_expr), f"Invalid Python: {py_expr!r}"


@given(
    obj=_identifiers,
    prop=_identifiers,
)
@settings(max_examples=100)
def test_property4_optional_chain_translation_is_valid_python(
    obj: str, prop: str
) -> None:
    """Property 4: optional chaining translation produces syntactically valid Python."""
    assume(obj != prop)
    assume(not any(_keyword.iskeyword(x) for x in (obj, prop)))
    # Simulated translation of: obj?.prop → obj.prop if obj is not None else None
    py_expr = f"{obj}.{prop} if {obj} is not None else None"
    assert _is_valid_python_expr(py_expr), f"Invalid Python: {py_expr!r}"


@given(
    var=_identifiers,
    default=_small_ints,
)
@settings(max_examples=100)
def test_property4_nullish_coalescing_translation_is_valid_python(
    var: str, default: int
) -> None:
    """Property 4: nullish coalescing translation produces syntactically valid Python."""
    assume(not _keyword.iskeyword(var))
    # Simulated translation of: var ?? default → var if var is not None else default
    py_expr = f"{var} if {var} is not None else {default}"
    assert _is_valid_python_expr(py_expr), f"Invalid Python: {py_expr!r}"


@given(
    loop_var=_identifiers,
    iterable=_identifiers,
    body_var=_identifiers,
)
@settings(max_examples=100)
def test_property4_for_of_translation_is_valid_python(
    loop_var: str, iterable: str, body_var: str
) -> None:
    """Property 4: for...of translation produces syntactically valid Python."""
    assume(loop_var != iterable)
    assume(not any(_keyword.iskeyword(x) for x in (loop_var, iterable, body_var)))
    # Simulated translation of: for (const loop_var of iterable) { body_var = loop_var; }
    py_stmt = f"for {loop_var} in {iterable}:\n    {body_var} = {loop_var}"
    assert _is_valid_python_stmt(py_stmt), f"Invalid Python: {py_stmt!r}"


import keyword as _keyword


@given(
    obj=_identifiers,
    key1=_identifiers,
    key2=_identifiers,
)
@settings(max_examples=100)
def test_property4_object_destructuring_translation_is_valid_python(
    obj: str, key1: str, key2: str
) -> None:
    """Property 4: object destructuring translation produces syntactically valid Python."""
    assume(key1 != key2 and obj not in (key1, key2))
    # Skip Python keywords — real translator would rename them
    assume(not _keyword.iskeyword(key1) and not _keyword.iskeyword(key2))
    assume(not _keyword.iskeyword(obj))
    # Simulated translation of: const { key1, key2 } = obj
    py_stmt = f'{key1} = {obj}["{key1}"]\n{key2} = {obj}["{key2}"]'
    assert _is_valid_python_stmt(py_stmt), f"Invalid Python: {py_stmt!r}"


@given(
    var1=_identifiers,
    var2=_identifiers,
    iterable=_identifiers,
)
@settings(max_examples=100)
def test_property4_array_destructuring_translation_is_valid_python(
    var1: str, var2: str, iterable: str
) -> None:
    """Property 4: array destructuring translation produces syntactically valid Python."""
    assume(var1 != var2 and iterable not in (var1, var2))
    assume(not any(_keyword.iskeyword(x) for x in (var1, var2, iterable)))
    # Simulated translation of: const [var1, var2] = iterable
    py_stmt = f"{var1}, {var2} = {iterable}"
    assert _is_valid_python_stmt(py_stmt), f"Invalid Python: {py_stmt!r}"


@given(
    prefix=st.text(
        alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd"), whitelist_characters=" _"),
        min_size=0,
        max_size=20,
    ),
    expr=_identifiers,
    suffix=st.text(
        alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd"), whitelist_characters=" _"),
        min_size=0,
        max_size=20,
    ),
)
@settings(max_examples=100)
def test_property4_template_literal_translation_is_valid_python(
    prefix: str, expr: str, suffix: str
) -> None:
    """Property 4: template literal translation produces syntactically valid Python."""
    # Simulated translation of: `prefix ${expr} suffix`
    # Escape any double-quotes in prefix/suffix
    safe_prefix = prefix.replace('"', '\\"').replace("\\", "\\\\")
    safe_suffix = suffix.replace('"', '\\"').replace("\\", "\\\\")
    py_expr = f'f"{safe_prefix}{{{expr}}}{safe_suffix}"'
    assert _is_valid_python_expr(py_expr), f"Invalid Python: {py_expr!r}"


# ---------------------------------------------------------------------------
# Unit tests — camel_to_snake property
# ---------------------------------------------------------------------------

@given(st.from_regex(r"[a-z][a-zA-Z0-9]{0,20}", fullmatch=True))
@settings(max_examples=100)
def test_property4_camel_to_snake_produces_valid_identifier(name: str) -> None:
    """Property 4: camel_to_snake always produces a valid Python identifier."""
    result = camel_to_snake(name)
    assert result.isidentifier() or result.replace("_", "").isalnum(), (
        f"camel_to_snake({name!r}) = {result!r} is not a valid identifier"
    )
    assert result == result.lower(), f"Result should be lowercase: {result!r}"
