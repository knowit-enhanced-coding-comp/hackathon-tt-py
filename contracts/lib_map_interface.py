"""Type annotations for the mapping dicts in tt/tt/lib_map.py (Branch B).

These names and types are the contract. Branch A's translator.py may import
any of these dicts for runtime use. Branch B must export them with exactly
these names and types.

DO NOT MODIFY after branching without agreement from both teams.
"""
from __future__ import annotations

# ts_method_name -> python operator or pattern string
# e.g. {"plus": "+", "toNumber": "float"}
BIG_JS_METHODS: dict[str, str]

# ts_fn_name -> python pattern key
# e.g. {"isBefore": "<", "format": "strftime"}
DATE_FNS_FUNCTIONS: dict[str, str]

# ts_fn_name -> python pattern key
# e.g. {"cloneDeep": "deepcopy", "sortBy": "sorted_by"}
LODASH_FUNCTIONS: dict[str, str]

# ts_type_name -> python_type_name
# e.g. {"Big": "Decimal", "string": "str", "Date": "date"}
TS_TYPE_MAP: dict[str, str]

# category_key -> list of Python import statement strings
# e.g. {"decimal": ["from decimal import Decimal, ROUND_HALF_UP"]}
PYTHON_IMPORTS: dict[str, list[str]]
