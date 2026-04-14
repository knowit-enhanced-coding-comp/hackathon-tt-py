"""Layer 4: Rewriter pipeline — transforms ModuleIR from TS semantics to Python semantics."""
from __future__ import annotations
from tt.ir import ModuleIR
from tt.rewriters.import_rewriter import rewrite_imports
from tt.rewriters.class_rewriter import rewrite_classes
from tt.rewriters.constructor_rewriter import rewrite_constructors
from tt.rewriters.body_rewriter import rewrite_bodies
from tt.rewriters.async_rewriter import rewrite_async
from tt.rewriters.decorator_rewriter import rewrite_decorators
from tt.rewriters.enum_rewriter import rewrite_enums  # future use, noop for now


def rewrite(ir: ModuleIR, import_map: dict[str, str] | None = None) -> ModuleIR:
    """Apply all rewriters in order."""
    ir = rewrite_imports(ir, import_map or {})
    ir = rewrite_decorators(ir)
    ir = rewrite_classes(ir)
    ir = rewrite_constructors(ir)
    ir = rewrite_bodies(ir)
    ir = rewrite_async(ir)
    ir = rewrite_enums(ir)
    return ir
