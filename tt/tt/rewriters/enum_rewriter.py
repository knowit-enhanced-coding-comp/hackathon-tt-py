"""Enum rewriter — no-op for now (enums are rare in the target files)."""
from __future__ import annotations
from tt.ir import ModuleIR


def rewrite_enums(ir: ModuleIR) -> ModuleIR:
    return ir
