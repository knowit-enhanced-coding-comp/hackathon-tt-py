"""Layer 4: Body text rewriter — transforms TS body text to Python syntax."""
from __future__ import annotations
import re
from tt.ir import ModuleIR


def rewrite_bodies(ir: ModuleIR) -> ModuleIR:
    """Rewrite body_text of all methods."""
    for cls in ir.classes:
        for method in cls.methods:
            if method.body_text:
                method.body_text = transform_body(method.body_text)
    return ir


def transform_body(body: str) -> str:
    """Apply all TS→Python text transforms to a method body."""
    # Pre-processing: handle complex multi-line TS constructs first
    body = _lower_filter_map_callbacks(body)
    body = _lower_push_to_append(body)
    body = _lower_spread_operator(body)
    body = _lower_c_style_for(body)
    body = _remove_type_annotations(body)
    body = _lower_keywords(body)
    body = _lower_operators(body)
    body = _lower_this(body)
    body = _lower_new_big(body)
    body = _lower_optional_chaining(body)
    body = _lower_nullish_coalescing(body)
    # For-loops must come BEFORE variable declarations so that
    # `for (const x of y)` is still intact when we transform it.
    body = _lower_for_loops(body)
    body = _lower_variable_declarations(body)
    body = _lower_ternary(body)
    body = _lower_arrow_functions(body)
    body = _lower_js_methods(body)
    body = _comment_out_console(body)
    body = _remove_semicolons(body)
    body = _strip_remaining_braces(body)
    body = _fix_indentation(body)
    return body


# ---------------------------------------------------------------------------
# 0a. Lower .filter / .map / .reduce callbacks (before arrow fn lowering)
# ---------------------------------------------------------------------------

def _lower_filter_map_callbacks(body: str) -> str:
    """Convert .filter(({x}) => { return x }) to list comprehensions
    and .filter(x => cond) to [item for item in X if cond].
    Also handle .map() and .forEach()."""

    # for (const x of y.filter(...)) → for x in y: + comment about filter
    # Must handle multi-line callbacks that span several lines
    # Strategy: replace entire .filter(...callback...) blocks

    # Multi-line .filter(({ prop }) => { return prop; })
    # In context of `for ... of X.filter(...)` → just remove .filter(...)
    body = re.sub(
        r"\.filter\(\s*\n?\s*\(\s*\{\s*(\w+(?:\s*,\s*\w+)*)\s*\}\s*\)\s*(?::\s*\w+)?\s*=>\s*\{\s*\n?\s*return\s+(\w+)\s*;?\s*\n?\s*\}\s*\n?\s*\)",
        "",
        body,
    )

    # Single-line .filter(({ prop }) => prop)
    body = re.sub(
        r"\.filter\(\s*\(\s*\{[^}]*\}\s*\)\s*(?::\s*\w+)?\s*=>\s*[^)]+\)",
        "",
        body,
    )

    # .filter(x => cond) — remove the filter call
    body = re.sub(
        r"\.filter\(\s*\(?\s*(\w+)\s*\)?\s*=>\s*\{[^}]*\}\s*\)",
        "",
        body,
    )

    # .filter(x => simpleExpr) single-line
    body = re.sub(
        r"\.filter\(\s*\(?\s*(\w+)\s*\)?\s*=>\s*[^)]+\)",
        "",
        body,
    )

    # .map(({ prop }) => expr) → drop for now
    body = re.sub(
        r"\.map\(\s*\(\s*\{[^}]*\}\s*\)\s*(?::\s*\w+)?\s*=>\s*([^{)]+)\)",
        "",
        body,
    )

    # .map(x => expr) single-line → drop
    body = re.sub(
        r"\.map\(\s*\(?\s*(\w+)\s*\)?\s*=>\s*[^)]+\)",
        "",
        body,
    )

    # .forEach(({ prop }) => { ... }) → comment
    body = re.sub(
        r"\.forEach\(\s*\(\s*\{[^}]*\}\s*\)\s*(?::\s*\w+)?\s*=>\s*\{",
        "  # forEach: ",
        body,
    )

    # .findIndex(({ prop }) => ...) → 0 (placeholder)
    body = re.sub(
        r"\.findIndex\(\s*\(\s*\{[^}]*\}\s*\)\s*(?::\s*\w+)?\s*=>\s*([^)]+)\)",
        ".index(0)  # findIndex placeholder",
        body,
    )

    # .findIndex(x => expr) → 0
    body = re.sub(
        r"\.findIndex\(\s*\(?\s*\w+\s*\)?\s*=>\s*[^)]+\)",
        ".index(0)  # findIndex placeholder",
        body,
    )

    return body


# ---------------------------------------------------------------------------
# 0b. Lower .push() to .append()
# ---------------------------------------------------------------------------

def _lower_push_to_append(body: str) -> str:
    return re.sub(r"\.push\(", ".append(", body)


# ---------------------------------------------------------------------------
# 0c. Lower spread operator
# ---------------------------------------------------------------------------

def _lower_spread_operator(body: str) -> str:
    # ...array → *array (in function calls) — approximate
    body = re.sub(r"\.\.\.(\w+)", r"*\1", body)
    return body


# ---------------------------------------------------------------------------
# 0d. Lower C-style for loops
# ---------------------------------------------------------------------------

def _lower_c_style_for(body: str) -> str:
    # for (i = 0; i < N; i += 1) { → for i in range(N):
    body = re.sub(
        r"for\s*\(\s*(?:let|var|const)?\s*(\w+)\s*=\s*0\s*;\s*\1\s*<\s*([^;]+)\s*;\s*\1\s*\+=\s*1\s*\)\s*\{?",
        lambda m: f"for {m.group(1)} in range({m.group(2).strip()}):",
        body,
    )
    # for (i = N; i >= 0; i -= 1) { → for i in range(N, -1, -1):
    body = re.sub(
        r"for\s*\(\s*(?:let|var|const)?\s*(\w+)\s*=\s*([^;]+)\s*;\s*\1\s*>=\s*0\s*;\s*\1\s*-=\s*1\s*\)\s*\{?",
        lambda m: f"for {m.group(1)} in range({m.group(2).strip()}, -1, -1):",
        body,
    )
    return body


# ---------------------------------------------------------------------------
# 0e. Lower JS-specific methods
# ---------------------------------------------------------------------------

def _lower_js_methods(body: str) -> str:
    # .toString() → str(...)  — approximate: just remove .toString()
    body = re.sub(r"\.toString\(\)", "", body)
    # .toFixed(N) → keep as-is, Python Decimal has quantize
    # Object.keys(x) → list(x.keys())
    body = re.sub(r"\bObject\.keys\(([^)]+)\)", r"list(\1.keys())", body)
    # Object.entries(x) → x.items()
    body = re.sub(r"\bObject\.entries\(([^)]+)\)", r"\1.items()", body)
    # Object.values(x) → list(x.values())
    body = re.sub(r"\bObject\.values\(([^)]+)\)", r"list(\1.values())", body)
    # Array.isArray(x) → isinstance(x, list)
    body = re.sub(r"\bArray\.isArray\(([^)]+)\)", r"isinstance(\1, list)", body)
    # x.includes(y) → y in x
    body = re.sub(r"(\w+)\.includes\(([^)]+)\)", r"\2 in \1", body)
    # typeof x === "string" → isinstance(x, str)
    body = re.sub(r'\btypeof\s+(\w+)\s*==\s*["\']string["\']', r"isinstance(\1, str)", body)
    body = re.sub(r'\btypeof\s+(\w+)\s*==\s*["\']number["\']', r"isinstance(\1, (int, float))", body)
    # x instanceof Big → isinstance(x, Decimal)
    body = re.sub(r"(\w+)\s+instanceof\s+Big", r"isinstance(\1, Decimal)", body)
    # Math.abs(x) → abs(x)
    body = re.sub(r"\bMath\.abs\(", "abs(", body)
    # Math.max(a, b) → max(a, b)
    body = re.sub(r"\bMath\.max\(", "max(", body)
    body = re.sub(r"\bMath\.min\(", "min(", body)
    return body


# ---------------------------------------------------------------------------
# 0f. Strip remaining lone braces that survived other transforms
# ---------------------------------------------------------------------------

def _strip_remaining_braces(body: str) -> str:
    # Remove trailing { at end of lines — but only if the line already ends with
    # a Python-style colon-worthy statement (if/elif/else/for/while/def/class)
    # or if the { is truly standalone.  Don't convert arbitrary lines.
    body = re.sub(r"^(\s*(?:if|elif|else|for|while|def|class|try|except|finally|with)\b.+?)\s*\{\s*$",
                  r"\1:", body, flags=re.MULTILINE)
    # Lines that are ONLY a closing brace (possibly with semicolons/parens)
    body = re.sub(r"^\s*\}\s*[;)]*\s*$", "", body, flags=re.MULTILINE)
    # Lines that are only ]);
    body = re.sub(r"^\s*\]\s*\)\s*;?\s*$", "", body, flags=re.MULTILINE)
    return body


# ---------------------------------------------------------------------------
# 1. Remove TypeScript type annotations
# ---------------------------------------------------------------------------

# Matches `: SomeType` after a variable/param name in declarations, but not `:`
# used in ternary or dict literals.  We target common patterns conservatively.
_TYPE_ANNOTATION_RE = re.compile(
    r":\s*(?:[A-Z][A-Za-z0-9_]*|[a-z][A-Za-z0-9_]*)(?:<[^>]*>)?(?:\[\])*"
    r"(?=\s*[=,)\];{])"
)

# `as SomeType` casts
_AS_CAST_RE = re.compile(r"\s+as\s+[A-Za-z_][A-Za-z0-9_.<>\[\] |&]*")

# Non-null assertion `!` — only match `!.` or `!;` or `!)` patterns
# (TS non-null assertion always appears before `.`, `)`, `;`, or end-of-expression)
# Do NOT match `!(expr)` which is logical negation
_NON_NULL_RE = re.compile(r"!(?=[.;)\],\s])")

# Generic calls: method<Type>(  →  method(
_GENERIC_CALL_RE = re.compile(r"(<[A-Za-z_][A-Za-z0-9_,\s.<>\[\]|&]*>)\s*(?=\()")


def _remove_type_annotations(body: str) -> str:
    body = _GENERIC_CALL_RE.sub("", body)
    body = _AS_CAST_RE.sub("", body)
    body = _NON_NULL_RE.sub("", body)
    # Remove `const x: Type =` style — strip `: Type` before `=`
    body = re.sub(r":\s*[A-Za-z_][A-Za-z0-9_.<>\[\] |&]*(?=\s*=)", "", body)
    # Fix spacing around `=` that may have been left without a leading space
    body = re.sub(r"([A-Za-z0-9_\]\)])(\s*)=(?!=)", lambda m: m.group(1) + " =" if not m.group(2) else m.group(0), body)
    return body


# ---------------------------------------------------------------------------
# 2. Lower keywords
# ---------------------------------------------------------------------------

def _lower_keywords(body: str) -> str:
    # Use word-boundary replacements to avoid partial matches
    body = re.sub(r"\btrue\b", "True", body)
    body = re.sub(r"\bfalse\b", "False", body)
    body = re.sub(r"\bnull\b", "None", body)
    body = re.sub(r"\bundefined\b", "None", body)
    return body


# ---------------------------------------------------------------------------
# 3. Lower operators
# ---------------------------------------------------------------------------

def _lower_operators(body: str) -> str:
    # Strict equality / inequality first (before `==` / `!=`)
    body = body.replace("===", "==")
    body = body.replace("!==", "!=")
    # Logical operators — use word boundaries to avoid mangling identifiers
    body = re.sub(r"\s*&&\s*", " and ", body)
    body = re.sub(r"\s*\|\|\s*", " or ", body)
    # Logical NOT: `!expr` → `not expr`
    # Only replace `!` not followed by `=`, and not inside `!=` (already handled)
    body = re.sub(r"(?<![!<>=])!(?!=)", "not ", body)
    return body


# ---------------------------------------------------------------------------
# 4. Lower this
# ---------------------------------------------------------------------------

def _lower_this(body: str) -> str:
    return re.sub(r"\bthis\.", "self.", body)


# ---------------------------------------------------------------------------
# 5. Lower new Big / Big.js method chains
# ---------------------------------------------------------------------------

def _lower_new_big(body: str) -> str:
    # new Big(x) → to_decimal(x)
    body = re.sub(r"\bnew\s+Big\s*\(", "to_decimal(", body)
    # Big(x) alone (without new) → to_decimal(x)
    body = re.sub(r"\bBig\s*\(", "to_decimal(", body)

    # Chain method replacements — approximate text substitution
    body = re.sub(r"\.plus\s*\(", " + to_decimal(", body)
    body = re.sub(r"\.minus\s*\(", " - to_decimal(", body)
    body = re.sub(r"\.times\s*\(", " * to_decimal(", body)
    body = re.sub(r"\.div\s*\(", " / to_decimal(", body)
    body = re.sub(r"\.eq\s*\(", " == to_decimal(", body)
    body = re.sub(r"\.gt\s*\(", " > to_decimal(", body)
    body = re.sub(r"\.lt\s*\(", " < to_decimal(", body)
    body = re.sub(r"\.gte\s*\(", " >= to_decimal(", body)
    body = re.sub(r"\.lte\s*\(", " <= to_decimal(", body)

    # .toNumber() — leave a comment so translators know it was there
    body = re.sub(r"\.toNumber\s*\(\s*\)", "  # .toNumber() needed", body)

    return body


# ---------------------------------------------------------------------------
# 6. Lower optional chaining
# ---------------------------------------------------------------------------

def _lower_optional_chaining(body: str) -> str:
    # First pass: approximate replacement of `?.` with `.`
    # This is not perfectly safe but is a good-enough first pass.
    body = body.replace("?.", ".")
    return body


# ---------------------------------------------------------------------------
# 7. Lower nullish coalescing
# ---------------------------------------------------------------------------

# Simple pattern: expr ?? fallback where both sides are non-complex expressions
_NULLISH_RE = re.compile(
    r"([A-Za-z_][A-Za-z0-9_.()'\"\[\]]*)\s*\?\?\s*([A-Za-z_0-9'.\"()\[\]]+)"
)


def _lower_nullish_coalescing(body: str) -> str:
    def _replace(m: re.Match) -> str:
        expr = m.group(1)
        fallback = m.group(2)
        return f"({expr} if {expr} is not None else {fallback})"

    return _NULLISH_RE.sub(_replace, body)


# ---------------------------------------------------------------------------
# 8. Lower variable declarations
# ---------------------------------------------------------------------------

def _lower_variable_declarations(body: str) -> str:
    # Remove leading `const `, `let `, `var ` from lines
    body = re.sub(r"\bconst\s+", "", body)
    body = re.sub(r"\blet\s+", "", body)
    body = re.sub(r"\bvar\s+", "", body)
    return body


# ---------------------------------------------------------------------------
# 9. Lower for-loops and control flow
# ---------------------------------------------------------------------------

def _lower_for_loops(body: str) -> str:
    # for (const [k, v] of Object.entries(m)) → for k, v in m.items():
    body = re.sub(
        r"for\s*\(\s*(?:const|let|var)\s+\[([^,\]]+),\s*([^\]]+)\]\s+of\s+Object\.entries\(([^)]+)\)\s*\)\s*\{?",
        r"for \1, \2 in \3.items():",
        body,
    )
    # for (const x of y) → for x in y:
    body = re.sub(
        r"for\s*\(\s*(?:const|let|var)\s+(\S+)\s+of\s+([^)]+)\)\s*\{?",
        r"for \1 in \2:",
        body,
    )
    # } else if (...) { → elif ...: (with balanced paren matching)
    body = _replace_balanced_control(body, r"\}\s*else\s+if\s*", "elif")
    # } else { → else:
    body = re.sub(r"\}\s*else\s*\{?", "else:", body)
    # if (...) { → if ...: (with balanced paren matching)
    body = _replace_balanced_control(body, r"\bif\s*", "if")
    # elif cond { (where { wasn't caught)
    body = re.sub(r"\belif\s+(.+?)\s*\{\s*$", lambda m: f"elif {m.group(1).strip()}:", body, flags=re.MULTILINE)
    # while (...) { → while ...:
    body = _replace_balanced_control(body, r"\bwhile\s*", "while")
    # Lone closing brace lines → remove (Python uses indentation)
    body = re.sub(r"^\s*\}\s*;?\s*$", "", body, flags=re.MULTILINE)
    return body


def _replace_balanced_control(body: str, prefix_pattern: str, keyword: str) -> str:
    """Replace control flow with balanced paren matching, e.g. if (...nested...) { → if ...:"""
    full_pattern = re.compile(prefix_pattern + r"\(")
    result = []
    i = 0
    while i < len(body):
        m = full_pattern.search(body, i)
        if not m:
            result.append(body[i:])
            break
        result.append(body[i:m.start()])
        # Find balanced closing paren
        paren_start = m.end() - 1  # the (
        depth = 1
        j = m.end()
        while j < len(body) and depth > 0:
            if body[j] == '(':
                depth += 1
            elif body[j] == ')':
                depth -= 1
            j += 1
        if depth != 0:
            result.append(body[m.start():m.end()])
            i = m.end()
            continue
        cond = body[paren_start + 1:j - 1].strip()
        # Skip trailing whitespace and optional { on same line, but not content after newline
        rest_start = j
        rest_match = re.match(r"[ \t]*\{?[ \t]*(?=\n|$)", body[rest_start:])
        if rest_match:
            rest_start += rest_match.end()
        result.append(f"{keyword} {cond}:")
        i = rest_start
    return "".join(result)


# ---------------------------------------------------------------------------
# 10. Lower ternary expressions
# ---------------------------------------------------------------------------

# Simple one-line ternary: cond ? a : b  →  (a if cond else b)
# We only attempt to rewrite lines that look like:
#   <something> = <cond> ? <a> : <b>
# where cond is the part AFTER the `=` and before `?`.
_TERNARY_ASSIGN_RE = re.compile(
    r"^(\s*\S+\s*=\s*)([^?=\n][^?\n]*?)\s*\?\s*([^?:\n]+?)\s*:\s*([^?:\n;]+?)\s*;?\s*$"
)
# Also handle bare ternary (not in an assignment): cond ? a : b
_TERNARY_BARE_RE = re.compile(
    r"(?<![=!<>])(?<!\w)\b([A-Za-z_][A-Za-z0-9_.()'\"\[\] ]*?)\s*\?\s*([^?:\n]+?)\s*:\s*([^?:\n]+)"
)


def _lower_ternary(body: str) -> str:
    lines = []
    for line in body.splitlines():
        # Only process lines with exactly one `?` that isn't `?.` or `??`
        if line.count("?") == 1 and "?." not in line and "??" not in line:
            m = _TERNARY_ASSIGN_RE.match(line)
            if m:
                prefix = m.group(1)
                cond = m.group(2).strip()
                a = m.group(3).strip()
                b = m.group(4).strip()
                line = f"{prefix}({a} if {cond} else {b})"
        lines.append(line)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 11. Lower arrow functions
# ---------------------------------------------------------------------------

# Simple: (x) => expr  or  x => expr  on a single line
_ARROW_SIMPLE_RE = re.compile(
    r"\(([^)]*)\)\s*=>\s*([^{][^\n]*)"
)
_ARROW_NO_PARENS_RE = re.compile(
    r"\b([A-Za-z_][A-Za-z0-9_]*)\s*=>\s*([^{][^\n]*)"
)


def _lower_arrow_functions(body: str) -> str:
    body = _ARROW_SIMPLE_RE.sub(lambda m: f"lambda {m.group(1)}: {m.group(2).rstrip()}", body)
    body = _ARROW_NO_PARENS_RE.sub(lambda m: f"lambda {m.group(1)}: {m.group(2).rstrip()}", body)
    return body


# ---------------------------------------------------------------------------
# 12. Comment out console statements
# ---------------------------------------------------------------------------

def _comment_out_console(body: str) -> str:
    return re.sub(r"^(\s*)console\.", r"\1# console.", body, flags=re.MULTILINE)


# ---------------------------------------------------------------------------
# 13. Remove trailing semicolons
# ---------------------------------------------------------------------------

def _remove_semicolons(body: str) -> str:
    # Remove `;` at end of line (possibly followed by whitespace)
    return re.sub(r";(\s*)$", r"\1", body, flags=re.MULTILINE)


# ---------------------------------------------------------------------------
# 14. Fix indentation (2-space → 4-space)
# ---------------------------------------------------------------------------

def _fix_indentation(body: str) -> str:
    """Convert 2-space indentation to 4-space indentation."""
    lines = body.splitlines()
    result = []
    for line in lines:
        # Count leading spaces
        stripped = line.lstrip(" ")
        num_spaces = len(line) - len(stripped)
        # Round up to nearest even number and double it
        # 2 spaces → 4, 4 spaces → 8, etc.
        new_indent = (num_spaces // 2) * 4 + (num_spaces % 2) * 2
        result.append(" " * new_indent + stripped)
    return "\n".join(result)
