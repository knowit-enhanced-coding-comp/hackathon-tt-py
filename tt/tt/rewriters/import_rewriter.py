"""Map TypeScript import paths to Python using the import_map."""
from __future__ import annotations
from tt.ir import ModuleIR, ImportIR

# Sources that are always dropped (NestJS DI framework, Prisma ORM)
_DROP_PREFIXES = ("@nestjs/", "@prisma/")

# Fallback mappings when source is not in the user-supplied import_map
_FALLBACK_MAP: dict[str, str] = {
    "big.js": "decimal",
    "date-fns": "app.implementation.shims.dates",
    "lodash": "app.implementation.shims.collections",
}

# Rename Big → Decimal for named imports from big.js
_BIG_JS_NAME_MAP: dict[str, str] = {
    "Big": "Decimal",
}

# Shim imports always injected into every module
_SHIM_IMPORTS: list[ImportIR] = [
    ImportIR(source="app.implementation.shims.nulls", names=[("nullish", None), ("safe_get", None)]),
    ImportIR(source="app.implementation.shims.numbers", names=[("to_decimal", None), ("big_sum", None), ("pct", None)]),
    ImportIR(source="decimal", names=[("Decimal", None)]),
]


def rewrite_imports(ir: ModuleIR, import_map: dict[str, str]) -> ModuleIR:
    """Map TS import sources to Python equivalents; drop framework imports; inject shims."""
    kept: list[ImportIR] = []
    unmapped: list[str] = []

    for imp in ir.imports:
        source = imp.source

        # 1. Check explicit import_map first
        if source in import_map:
            mapped = import_map[source]
            new_names = _remap_names(imp.names, source)
            kept.append(ImportIR(source=mapped, names=new_names, default_name=imp.default_name))
            continue

        # 2. Drop NestJS / Prisma prefixes
        if any(source.startswith(pfx) for pfx in _DROP_PREFIXES):
            continue

        # 3. Fallback mappings
        if source in _FALLBACK_MAP:
            mapped = _FALLBACK_MAP[source]
            new_names = _remap_names(imp.names, source)
            kept.append(ImportIR(source=mapped, names=new_names, default_name=imp.default_name))
            continue

        # 4. Unknown import — keep but record
        unmapped.append(source)
        kept.append(imp)

    # Inject shim imports (deduplicate by source)
    existing_sources = {i.source for i in kept}
    for shim in _SHIM_IMPORTS:
        if shim.source not in existing_sources:
            kept.append(shim)

    ir.imports = kept
    # Attach unmapped list as a dynamic attribute for downstream use / reporting
    ir._unmapped_imports = unmapped  # type: ignore[attr-defined]
    return ir


def _remap_names(
    names: list[tuple[str, str | None]],
    source: str,
) -> list[tuple[str, str | None]]:
    """Rename known symbols (e.g. Big → Decimal for big.js imports)."""
    if source not in ("big.js", "decimal"):
        return names
    result = []
    for name, alias in names:
        new_name = _BIG_JS_NAME_MAP.get(name, name)
        result.append((new_name, alias))
    return result
