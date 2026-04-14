"""Parse tree TypedDicts — the data contract between:
  - parser.py (Branch B produces ParseTree)
  - translator.py (Branch A consumes ParseTree)

These TypedDicts define the exact shape of the dict returned by
parse_ts_file(). Branch B must return dicts that conform to this schema.
Branch A must only access keys defined in this schema.

DO NOT MODIFY after branching without agreement from both teams.
"""
from __future__ import annotations
from typing import TypedDict


class ParamNode(TypedDict):
    name: str
    ts_type: str       # raw TypeScript type string, e.g. "Big", "string", "Date"


class MethodNode(TypedDict):
    name: str          # camelCase, as written in TypeScript source
    visibility: str    # "public" | "protected" | "private" | ""
    params: list[ParamNode]
    return_type: str   # raw TypeScript return type string, e.g. "Big", "void"
    body_lines: list[str]  # raw TypeScript body lines, untranslated


class PropertyNode(TypedDict):
    name: str
    ts_type: str
    visibility: str
    is_static: bool


class ClassNode(TypedDict):
    name: str
    base_class: str | None
    methods: list[MethodNode]
    properties: list[PropertyNode]


class ImportNode(TypedDict):
    symbols: list[str]   # e.g. ["Big"] from "import { Big } from 'big.js'"
    module: str          # e.g. "big.js" or "@ghostfolio/common/helper"


class ParseTree(TypedDict):
    classes: list[ClassNode]
    imports: list[ImportNode]
    top_level_vars: list[dict]   # {name: str, ts_type: str, initializer: str}
