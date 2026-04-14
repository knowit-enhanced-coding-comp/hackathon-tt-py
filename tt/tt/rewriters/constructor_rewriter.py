"""Expand constructor shorthand params into explicit self.x = x assignments."""
from __future__ import annotations
from tt.ir import ModuleIR


def rewrite_constructors(ir: ModuleIR) -> ModuleIR:
    """
    For each class:
    - Rename the 'constructor' method to '__init__'.
    - Expand TypeScript constructor-shorthand parameters (those with an access
      modifier like public/protected/private, or readonly) into explicit
      ``self.name = name`` assignments at the start of the body.
    """
    for cls in ir.classes:
        for method in cls.methods:
            if method.name == "constructor":
                method.name = "__init__"
                _expand_shorthand_params(method)
    return ir


def _expand_shorthand_params(method) -> None:
    """Prepend self.x = x for every constructor-shorthand parameter."""
    assignments: list[str] = []
    for param in method.params:
        if param.access_modifier is not None or param.is_readonly:
            assignments.append(f"        self.{param.name} = {param.name}")

    if not assignments:
        return

    prefix = "\n".join(assignments) + "\n"
    if method.body_text:
        method.body_text = prefix + method.body_text
    else:
        method.body_text = prefix
