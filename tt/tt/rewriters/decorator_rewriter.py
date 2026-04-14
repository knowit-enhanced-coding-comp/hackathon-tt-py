"""Convert NestJS decorators to Python di_metadata."""
from __future__ import annotations
from tt.ir import ModuleIR


def rewrite_decorators(ir: ModuleIR) -> ModuleIR:
    """Convert class-level decorators to __di_metadata__ attributes."""
    for cls in ir.classes:
        for dec in cls.decorators:
            name_lower = dec.name.lower()
            if name_lower == "injectable":
                cls.di_metadata["injectable"] = True
            elif name_lower == "controller":
                cls.di_metadata["controller"] = dec.args_text or ""
        cls.decorators = []  # clear — already encoded in di_metadata

        # Method decorators: strip @LogPerformance etc (keep as comment metadata)
        for method in cls.methods:
            method.decorators = []
    return ir
