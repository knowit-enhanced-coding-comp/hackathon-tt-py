"""
Tests for tt.import_resolver — Properties 1 & 2 from the hackathon-tt-competition spec.

Feature: hackathon-tt-competition
Property 1: Import Map Resolution Round-Trip
Property 2: Unmapped Import Produces Commented Placeholder
"""
from __future__ import annotations

import json
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pathlib import Path

from tt.import_resolver import (
    generate_import_statement,
    load_import_map,
    resolve,
    resolve_and_generate,
    resolve_third_party,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_MAP: dict = {
    "@ghostfolio/api/app/portfolio/calculator/portfolio-calculator": {
        "python_module": "app.wrapper.portfolio.calculator.portfolio_calculator",
        "symbols": {"PortfolioCalculator": "PortfolioCalculator"},
    },
    "@ghostfolio/common/interfaces": {
        "python_module": "app.wrapper.portfolio.interfaces",
        "symbols": {},
    },
    "@ghostfolio/api/helper/portfolio.helper": {
        "python_module": "app.implementation.helpers.portfolio_helper",
        "symbols": {"getFactor": "get_factor"},
    },
}


# ---------------------------------------------------------------------------
# load_import_map
# ---------------------------------------------------------------------------

def test_load_import_map_returns_empty_dict_when_file_missing(tmp_path: Path) -> None:
    result = load_import_map(tmp_path)
    assert result == {}


def test_load_import_map_returns_parsed_json(tmp_path: Path) -> None:
    (tmp_path / "tt_import_map.json").write_text(
        json.dumps(SAMPLE_MAP), encoding="utf-8"
    )
    result = load_import_map(tmp_path)
    assert result == SAMPLE_MAP


def test_load_import_map_returns_empty_on_invalid_json(tmp_path: Path) -> None:
    (tmp_path / "tt_import_map.json").write_text("{not valid json", encoding="utf-8")
    result = load_import_map(tmp_path)
    assert result == {}


# ---------------------------------------------------------------------------
# resolve
# ---------------------------------------------------------------------------

def test_resolve_returns_python_module_for_known_path() -> None:
    result = resolve(
        "@ghostfolio/api/app/portfolio/calculator/portfolio-calculator", SAMPLE_MAP
    )
    assert result == "app.wrapper.portfolio.calculator.portfolio_calculator"


def test_resolve_returns_none_for_unknown_path() -> None:
    assert resolve("@ghostfolio/unknown/path", SAMPLE_MAP) is None


def test_resolve_returns_none_for_empty_map() -> None:
    assert resolve("@ghostfolio/anything", {}) is None


# ---------------------------------------------------------------------------
# resolve_third_party
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("module,expected", [
    ("big.js", None),
    ("date-fns", None),
    ("date-fns/format", None),
    ("date-fns/differenceInDays", None),
    ("date-fns/isBefore", None),
    ("date-fns/isAfter", None),
    ("date-fns/addMilliseconds", None),
    ("date-fns/eachDayOfInterval", None),
    ("date-fns/eachYearOfInterval", None),
    ("date-fns/startOfDay", None),
    ("date-fns/endOfDay", None),
    ("date-fns/startOfYear", None),
    ("date-fns/endOfYear", None),
    ("date-fns/subDays", None),
    ("date-fns/isWithinInterval", None),
    ("date-fns/isThisYear", None),
    ("lodash", None),
    ("lodash/sortBy", None),
    ("lodash/cloneDeep", "copy"),
    ("lodash/isNumber", None),
])
def test_resolve_third_party_known_mappings(module: str, expected: str) -> None:
    assert resolve_third_party(module) == expected


@pytest.mark.parametrize("module", [
    "@nestjs/common",
    "@nestjs/core",
    "@nestjs/microservices",
])
def test_resolve_third_party_nestjs_returns_none(module: str) -> None:
    assert resolve_third_party(module) is None


def test_resolve_third_party_unknown_returns_none() -> None:
    assert resolve_third_party("some-unknown-lib") is None


# ---------------------------------------------------------------------------
# generate_import_statement
# ---------------------------------------------------------------------------

def test_generate_import_statement_with_symbols() -> None:
    assert generate_import_statement("decimal", ["Decimal"]) == "from decimal import Decimal"


def test_generate_import_statement_multiple_symbols() -> None:
    result = generate_import_statement("datetime", ["datetime", "timedelta"])
    assert result == "from datetime import datetime, timedelta"


def test_generate_import_statement_no_symbols() -> None:
    assert generate_import_statement("datetime", []) == "import datetime"


# ---------------------------------------------------------------------------
# resolve_and_generate
# ---------------------------------------------------------------------------

def test_resolve_and_generate_uses_import_map() -> None:
    result = resolve_and_generate(
        "@ghostfolio/api/app/portfolio/calculator/portfolio-calculator",
        ["PortfolioCalculator"],
        SAMPLE_MAP,
    )
    assert result == "from app.wrapper.portfolio.calculator.portfolio_calculator import PortfolioCalculator"


def test_resolve_and_generate_maps_symbols_via_symbol_map() -> None:
    result = resolve_and_generate(
        "@ghostfolio/api/helper/portfolio.helper",
        ["getFactor"],
        SAMPLE_MAP,
    )
    assert result == "from app.implementation.helpers.portfolio_helper import get_factor"


def test_resolve_and_generate_falls_back_to_third_party() -> None:
    result = resolve_and_generate("big.js", ["Big"], {})
    assert result.startswith("# suppressed:")


def test_resolve_and_generate_nestjs_produces_placeholder() -> None:
    result = resolve_and_generate("@nestjs/common", ["Logger"], {})
    assert result.startswith("# suppressed:")


def test_resolve_and_generate_unknown_produces_placeholder() -> None:
    result = resolve_and_generate("@ghostfolio/unknown/path", ["Foo"], {})
    assert result.startswith("# TODO: unmapped import:")
    assert "@ghostfolio/unknown/path" in result


# ---------------------------------------------------------------------------
# Property 1: Import Map Resolution Round-Trip
# Feature: hackathon-tt-competition, Property 1
# ---------------------------------------------------------------------------

@given(
    st.fixed_dictionaries({
        "python_module": st.from_regex(r"[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*", fullmatch=True),
        "symbols": st.dictionaries(
            st.from_regex(r"[A-Za-z][A-Za-z0-9_]*", fullmatch=True),
            st.from_regex(r"[A-Za-z][A-Za-z0-9_]*", fullmatch=True),
            max_size=5,
        ),
    })
)
@settings(max_examples=100)
def test_property1_import_map_round_trip(entry: dict) -> None:
    """Property 1: for any path in the import map, resolver produces a valid Python import."""
    ts_path = "@ghostfolio/some/module"
    import_map = {ts_path: entry}
    python_module = resolve(ts_path, import_map)
    assert python_module == entry["python_module"]

    # generate_import_statement must produce a syntactically valid string
    symbols = list(entry["symbols"].values())
    stmt = generate_import_statement(python_module, symbols)
    if symbols:
        assert stmt.startswith("from ")
        assert " import " in stmt
        assert python_module in stmt
    else:
        assert stmt == f"import {python_module}"


# ---------------------------------------------------------------------------
# Property 2: Unmapped Import Produces Commented Placeholder
# Feature: hackathon-tt-competition, Property 2
# ---------------------------------------------------------------------------

_KNOWN_THIRD_PARTY = {
    "big.js", "date-fns", "lodash",
    "date-fns/format", "date-fns/differenceInDays", "lodash/cloneDeep",
}

@given(
    st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="/@.-_"),
        min_size=3,
    ).filter(
        lambda s: not s.startswith("@nestjs/")
        and s not in _KNOWN_THIRD_PARTY
        and not any(s.startswith(k) for k in _KNOWN_THIRD_PARTY)
    )
)
@settings(max_examples=100)
def test_property2_unmapped_import_produces_placeholder(ts_path: str) -> None:
    """Property 2: any path not in the map and not a known third-party lib → commented placeholder."""
    result = resolve_and_generate(ts_path, ["SomeSymbol"], {})
    assert result.startswith("# TODO: unmapped import:")
    assert ts_path in result
