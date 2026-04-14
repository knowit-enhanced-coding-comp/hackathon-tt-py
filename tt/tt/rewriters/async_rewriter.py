"""Strip async/await — Python output is synchronous."""
from __future__ import annotations
import re
from tt.ir import ModuleIR


def rewrite_async(ir: ModuleIR) -> ModuleIR:
    """Remove await keywords from body text, keep async flag for future use."""
    for cls in ir.classes:
        for method in cls.methods:
            if method.body_text:
                method.body_text = re.sub(r'\bawait\s+', '', method.body_text)
    return ir
