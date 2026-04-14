"""Layer 5: Python emitter — generates Python source from ModuleIR."""
from __future__ import annotations

import ast
import re
import textwrap
from tt.ir import ModuleIR, ClassIR, MethodIR, ImportIR, FieldIR, ParamIR


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def emit_module(ir: ModuleIR) -> str:
    """Generate Python source code from a ModuleIR."""
    parts: list[str] = ["from __future__ import annotations\n"]

    # Imports section
    import_lines = _emit_imports(ir.imports)
    if import_lines:
        parts.append(import_lines)

    # Classes section
    for cls in ir.classes:
        parts.append(emit_class(cls))

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

def _sort_key(imp: ImportIR) -> tuple[int, str]:
    """Classify imports: 0=stdlib, 1=app., 2=other."""
    src = imp.source
    if src.startswith("@") or src.startswith("."):
        return (2, src)
    if src.startswith("app."):
        return (1, src)
    # stdlib-ish: no dots, not a package path (e.g. 'decimal', 'datetime')
    if "." not in src:
        return (0, src)
    return (2, src)


def _emit_imports(imports: list[ImportIR]) -> str:
    """Emit sorted, deduped import statements."""
    # Skip sources starting with @ (unmapped TS paths)
    filtered = [imp for imp in imports if not imp.source.startswith("@")]

    # Dedup by (source, name) — build a dict of source → set of names
    by_source: dict[str, ImportIR] = {}
    seen: set[tuple[str, str | None]] = set()

    for imp in filtered:
        src = imp.source
        if src not in by_source:
            by_source[src] = ImportIR(
                source=src,
                names=[],
                default_name=imp.default_name,
            )
        merged = by_source[src]
        if imp.default_name and not merged.default_name:
            merged.default_name = imp.default_name
        for name, alias in imp.names:
            key = (name, alias)
            if key not in seen:
                seen.add(key)
                merged.names.append((name, alias))

    sorted_imps = sorted(by_source.values(), key=_sort_key)

    lines: list[str] = []
    prev_group = -1
    for imp in sorted_imps:
        group = _sort_key(imp)[0]
        if prev_group != -1 and group != prev_group:
            lines.append("")
        prev_group = group

        src = imp.source
        if imp.names:
            name_parts = []
            for name, alias in imp.names:
                if alias:
                    name_parts.append(f"{name} as {alias}")
                else:
                    name_parts.append(name)
            lines.append(f"from {src} import {', '.join(name_parts)}")
        elif imp.default_name:
            dn = imp.default_name
            if dn.startswith("* as "):
                alias_name = dn[5:]
                lines.append(f"import {src} as {alias_name}")
            else:
                lines.append(f"from {src} import {dn}")
        else:
            lines.append(f"import {src}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------

def emit_class(cls: ClassIR) -> str:
    """Emit a Python class definition."""
    lines: list[str] = []

    # Build base class list
    bases = list(cls.bases)
    if cls.is_abstract and "ABC" not in bases:
        bases.append("ABC")

    if bases:
        bases_str = ", ".join(bases)
        lines.append(f"class {cls.name}({bases_str}):")
    else:
        lines.append(f"class {cls.name}:")

    body_lines: list[str] = []

    # DI metadata (first body item)
    if cls.di_metadata:
        body_lines.append(f"    __di_metadata__ = {cls.di_metadata!r}")
        body_lines.append("")

    # Fields — emit as annotations comments
    for field in cls.fields:
        if field.ts_type:
            body_lines.append(f"    # field: {field.name}: {field.ts_type}")
        else:
            body_lines.append(f"    # field: {field.name}")

    if cls.fields:
        body_lines.append("")

    # Methods
    for method in cls.methods:
        method_text = emit_method(method)
        body_lines.append(method_text)
        body_lines.append("")

    # If the body is empty, emit pass
    non_empty = [l for l in body_lines if l.strip()]
    if not non_empty:
        body_lines = ["    pass"]

    lines.extend(body_lines)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Methods
# ---------------------------------------------------------------------------

def emit_method(method: MethodIR) -> str:
    """Emit a Python method definition."""
    lines: list[str] = []

    # Decorators
    if method.is_abstract:
        lines.append("    @abstractmethod")

    # Signature
    param_strs = ["self"]
    for param in method.params:
        # Skip constructor-shorthand params without names
        if not param.name or param.name.startswith("{") or param.name.startswith("["):
            continue
        if param.default is not None:
            param_strs.append(f"{param.name}={param.default}")
        else:
            param_strs.append(param.name)

    params_joined = ", ".join(param_strs)
    async_prefix = "async " if method.is_async else ""
    lines.append(f"    {async_prefix}def {method.name}({params_joined}):")

    # Body
    body = _emit_body(method.body_text, method.is_abstract)
    lines.append(body)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Body indentation
# ---------------------------------------------------------------------------

def _clean_body_text(body_text: str) -> str:
    """Apply additional TS→Python fixes not handled by the body rewriter."""
    # Remove remaining destructured arrow params: ({ a, b }) => or ({ a }) =>
    body_text = re.sub(
        r"\(\s*\{[^}]*\}\s*\)\s*(?::\s*\w+)?\s*=>\s*\{",
        "lambda _: (",
        body_text,
    )
    body_text = re.sub(
        r"\(\s*\{[^}]*\}\s*\)\s*(?::\s*\w+)?\s*=>\s*",
        "lambda _: ",
        body_text,
    )
    # Template literals: `text ${expr} more` → f"text {expr} more"
    def _template_to_fstring(m: re.Match) -> str:
        content = m.group(1)
        content = re.sub(r"\$\{([^}]+)\}", r"{\1}", content)
        return f'f"{content}"'
    body_text = re.sub(r"`([^`]*)`", _template_to_fstring, body_text)
    # Remove remaining TS type annotations on variable declarations
    body_text = re.sub(
        r"^(\s*)(\w+)\s*:\s*\{[^}]*\}\s*=\s*",
        r"\1\2 = ",
        body_text,
        flags=re.MULTILINE,
    )
    # Remove TS type annotations on simple vars: varName: SomeType; → pass
    body_text = re.sub(
        r"^(\s*)(\w+)\s*:\s*[A-Za-z_][A-Za-z0-9_<>\[\] |&.]*\s*$",
        r"\1# ts: \2",
        body_text,
        flags=re.MULTILINE,
    )
    # Fix `new Date()` → `datetime.now()`
    body_text = re.sub(r"\bnew Date\(\)", "datetime.now()", body_text)
    # Remove `new` keyword before class instantiations
    body_text = re.sub(r"\bnew\s+([A-Z][A-Za-z0-9_]*)\s*\(", r"\1(", body_text)
    # `.length` property → len() — hard to do perfectly, remove it
    body_text = re.sub(r"(\w+)\.length\b", r"len(\1)", body_text)
    # Remove trailing `{` only on control-flow lines
    body_text = re.sub(r"^(\s*(?:if|elif|else|for|while|def|class|try|except|finally|with)\b.+?)\s*\{\s*$",
                        r"\1:", body_text, flags=re.MULTILINE)
    # Lines that are just }) or }); or ]) — remove
    body_text = re.sub(r"^\s*[}\]]\s*[;),]*\s*$", "", body_text, flags=re.MULTILINE)
    # `return {` on its own line → `return {` (dict literal is fine)
    # BUT `return {\n key: val` needs to become `return {"key": val`
    # For now leave return { ... } as-is — it's valid Python dict syntax
    # Fix `Logger.warn(` → just comment it out for now
    # Fix `Logger.warn(...)` — remove entire multi-line Logger calls
    body_text = _remove_logger_calls(body_text)
    # Remove JS method chains on closing braces: }).length, → 0,
    body_text = re.sub(r"\}\s*\)\s*\.\w+", "0", body_text)
    # Convert TS single-line comments // → #
    body_text = re.sub(r"//(.*)$", r"# \1", body_text, flags=re.MULTILINE)
    # Clean up orphaned ternary fragments: lines starting with `: expr` → comment out
    body_text = re.sub(r"^(\s*):\s+(.+)$", r"\1# TS-ternary: \2", body_text, flags=re.MULTILINE)
    # Remove trailing colon on lines ending ): where the line is NOT a control-flow statement
    def _fix_dangling_colon(m: re.Match) -> str:
        line = m.group(0)
        stripped = line.lstrip()
        keywords = ("if ", "elif ", "for ", "while ", "def ", "class ", "except ", "with ", "else:")
        if any(stripped.startswith(k) for k in keywords):
            return line
        return re.sub(r"\)\s*:\s*$", ")", line)
    body_text = re.sub(r"^.*\)\s*:\s*$", _fix_dangling_colon, body_text, flags=re.MULTILINE)
    # Multi-line assignment continuations: `x =\n    y` — join them
    body_text = re.sub(r"=\s*\n\s+(\w)", r"= \1", body_text)
    # Convert JS object shorthand in return statements
    # { prop, prop2 } → {"prop": prop, "prop2": prop2}
    # This is a simplified transform for common patterns
    body_text = _convert_js_object_literals(body_text)
    return body_text


def _remove_logger_calls(body_text: str) -> str:
    """Remove Logger.warn/error/log and console.log calls including multi-line args."""
    lines = body_text.splitlines()
    result = []
    skip_depth = 0
    for line in lines:
        stripped = line.lstrip()
        if skip_depth > 0:
            skip_depth += stripped.count("(") - stripped.count(")")
            if skip_depth <= 0:
                skip_depth = 0
            continue
        if re.match(r"(Logger\.\w+|# console\.\w+|console\.\w+)\s*\(", stripped):
            depth = stripped.count("(") - stripped.count(")")
            if depth > 0:
                skip_depth = depth
            continue
        result.append(line)
    return "\n".join(result)


def _convert_js_object_literals(body_text: str) -> str:
    """Convert JS object shorthand properties to Python dict syntax."""
    _PY_KEYWORDS = frozenset({
        "if", "elif", "else", "for", "while", "def", "class", "return",
        "try", "except", "finally", "with", "as", "import", "from",
        "pass", "break", "continue", "raise", "yield", "async", "await",
        "and", "or", "not", "in", "is", "lambda", "True", "False", "None",
        "self", "global", "nonlocal", "assert", "del",
    })

    def _is_keyword_line(line: str) -> bool:
        stripped = line.lstrip()
        if not stripped or ":" not in stripped:
            return True
        parts = stripped.split(":")[0].split()
        first_word = parts[0] if parts else ""
        return first_word in _PY_KEYWORDS

    lines = body_text.splitlines()
    result = []
    in_return_block = False
    brace_depth = 0

    for line in lines:
        stripped = line.lstrip()
        if "return {" in stripped or (stripped == "return" and "{" in stripped):
            in_return_block = True

        if in_return_block:
            brace_depth += stripped.count("{") - stripped.count("}")
            if brace_depth <= 0:
                in_return_block = False
                brace_depth = 0

        if not _is_keyword_line(line):
            # Convert shorthand properties: `prop,` → `"prop": prop,`
            line = re.sub(r"^(\s+)(\w+),\s*$", r'\1"\2": \2,', line)
            # Convert `key: expr` → `"key": expr` (only inside indented blocks)
            line = re.sub(r"^(\s{8,})(\w+):\s+(.+?)$", r'\1"\2": \3', line)

        result.append(line)

    return "\n".join(result)


def _sanitize_body_for_python(body_lines: list[str]) -> list[str]:
    """
    Try to make remaining lines syntactically valid.
    Lines that are still unparseable as Python statements get commented out.
    """
    # Dedent for parsing then re-indent
    if not body_lines:
        return body_lines

    min_indent = None
    for line in body_lines:
        if line.strip():
            indent = len(line) - len(line.lstrip())
            if min_indent is None or indent < min_indent:
                min_indent = indent
    if min_indent is None:
        min_indent = 0

    def _dedent(lines: list[str]) -> list[str]:
        return [l[min_indent:] if l.strip() else l for l in lines]

    def _reindent(lines: list[str]) -> list[str]:
        return [(" " * min_indent + l if l.strip() else l) for l in lines]

    def _try_parse(lines: list[str]) -> bool:
        src = "\n".join(lines)
        try:
            ast.parse(src)
            return True
        except SyntaxError:
            return False

    dedented = _dedent(body_lines)

    if _try_parse(dedented):
        return body_lines

    already_commented: set[int] = set()
    max_passes = min(len(dedented) + 1, 300)
    for _ in range(max_passes):
        if _try_parse(dedented):
            break
        broken_idx = _find_first_syntax_error_line(dedented)
        if broken_idx is None:
            break
        if broken_idx in already_commented:
            broken_idx = min(broken_idx + 1, len(dedented) - 1)
            if broken_idx in already_commented:
                break
        line = dedented[broken_idx]
        stripped = line.lstrip()
        indent_spaces = len(line) - len(stripped)
        if stripped.startswith("# TS:"):
            break
        dedented[broken_idx] = " " * indent_spaces + "# TS: " + stripped
        already_commented.add(broken_idx)

    return _reindent(dedented)


def _find_first_syntax_error_line(lines: list[str]) -> int | None:
    """Find the index of the first line contributing to a syntax error.
    Assumes lines are already dedented."""
    src = "\n".join(lines)
    try:
        ast.parse(src)
        return None
    except SyntaxError as e:
        if e.lineno:
            idx = e.lineno - 1
            return max(0, min(idx, len(lines) - 1))
    return len(lines) - 1 if lines else None


def _emit_body(body_text: str | None, is_abstract: bool = False) -> str:
    """Clean up and re-indent the method body. Returns indented body string."""
    if is_abstract or not body_text or not body_text.strip():
        return "        pass"

    # Apply additional TS→Python cleanup
    body_text = _clean_body_text(body_text)

    raw_lines = body_text.splitlines()

    # Strip leading/trailing blank lines
    while raw_lines and not raw_lines[0].strip():
        raw_lines.pop(0)
    while raw_lines and not raw_lines[-1].strip():
        raw_lines.pop()

    if not raw_lines:
        return "        pass"

    # Filter out lone TS braces
    filtered: list[str] = []
    for line in raw_lines:
        stripped = line.strip()
        if stripped in ("{", "}"):
            continue
        filtered.append(line)

    if not filtered:
        return "        pass"

    # Find minimum indentation (ignore empty lines)
    min_indent = None
    for line in filtered:
        if line.strip():
            indent = len(line) - len(line.lstrip(" "))
            if min_indent is None or indent < min_indent:
                min_indent = indent
    if min_indent is None:
        min_indent = 0

    # Re-indent: strip min_indent, then add 8 spaces (2 levels)
    result_lines: list[str] = []
    for line in filtered:
        if line.strip():
            stripped_line = line[min_indent:]
            result_lines.append("        " + stripped_line)
        else:
            result_lines.append("")

    # Safety pass: comment out lines that prevent valid Python syntax
    result_lines = _sanitize_body_for_python(result_lines)

    # Final verification: if still doesn't parse, return pass with commented body
    body_str = "\n".join(result_lines)
    dedented = "\n".join(l[8:] if l.startswith("        ") else l for l in result_lines if l.strip())
    try:
        ast.parse(dedented)
    except SyntaxError:
        # Last resort: comment out everything
        commented = []
        for l in result_lines:
            if l.strip() and not l.strip().startswith("#"):
                indent = len(l) - len(l.lstrip())
                commented.append(" " * indent + "# TS: " + l.lstrip())
            else:
                commented.append(l)
        commented.insert(0, "        pass  # body could not be fully translated")
        return "\n".join(commented)

    return "\n".join(result_lines)
