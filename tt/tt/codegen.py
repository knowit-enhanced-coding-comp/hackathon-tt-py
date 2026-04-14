"""Python code generator for the Branch B translation engine.

This module consumes the parse-tree contracts from ``contracts/`` and emits
valid Python source. The output is intentionally conservative: supported
TypeScript constructs are translated mechanically, while unsupported lines are
preserved as comments so the generated file remains valid Python.
"""
from __future__ import annotations

import re
from typing import Any

from contracts.parse_tree_schema import ClassNode, MethodNode

from .lib_map import PYTHON_IMPORTS, TS_TYPE_MAP


_BASIC_IMPORTS = [
    "from __future__ import annotations",
    "from typing import Any",
]

_CONTROL_KEYWORDS = ("if ", "elif ", "else", "for ", "while ", "try", "except", "finally")


def generate_python_class(
    class_node: ClassNode,
    import_map: dict[str, str],
) -> str:
    """Return a complete Python class definition as a source string."""
    class_name = class_node["name"]
    base_class = class_node.get("base_class") or "object"
    lines: list[str] = [f"class {class_name}({base_class}):"]

    property_lines = _generate_properties(class_node)
    method_lines = [generate_method(method) for method in class_node.get("methods", [])]

    if not property_lines and not method_lines:
        lines.append("    pass")
    else:
        lines.extend(property_lines)
        if property_lines and method_lines:
            lines.append("")
        for index, method_source in enumerate(method_lines):
            if index > 0:
                lines.append("")
            lines.extend(method_source.splitlines())

    return "\n".join(lines)


def generate_imports(
    used_libraries: list[str],
    import_map: dict[str, str],
) -> str:
    """Return the Python import block as a source string."""
    import_lines = list(_BASIC_IMPORTS)

    for library in used_libraries:
        if library in PYTHON_IMPORTS:
            import_lines.extend(PYTHON_IMPORTS[library])
        elif library in import_map:
            module_path = import_map[library]
            import_lines.append(f"import {module_path}")

    deduped = sorted({line for line in import_lines if line.strip()})
    return "\n".join(deduped)


def camel_to_snake(name: str) -> str:
    """Convert a camelCase identifier to snake_case."""
    step1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    step2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", step1)
    return step2.lower()


def translate_expression(ts_expr: str) -> str:
    """Translate a single TypeScript expression string to Python."""
    expr = ts_expr.strip()
    if not expr:
        return ""

    expr = _strip_trailing_semicolon(expr)
    expr = expr.replace("this.", "self.")
    expr = expr.replace("null", "None")
    expr = expr.replace("true", "True")
    expr = expr.replace("false", "False")
    expr = re.sub(r"\bundefined\b", "None", expr)
    expr = _translate_template_literals(expr)
    expr = _translate_object_keys_entries(expr)
    expr = _translate_new_big(expr)
    expr = _translate_nullish(expr)
    expr = _translate_optional_chaining(expr)
    expr = _translate_numeric_chain_methods(expr)
    expr = _translate_date_fns(expr)
    expr = _translate_lodash(expr)
    expr = _translate_arrow_functions(expr)
    expr = _translate_type_keywords(expr)
    return expr


def generate_helper_functions() -> str:
    """Return Python helper functions needed by the generated calculator."""
    return (
        "def each_day_of_interval(start, end):\n"
        "    current = start\n"
        "    while current <= end:\n"
        "        yield current\n"
        "        current = current + timedelta(days=1)\n"
        "\n"
        "def each_year_of_interval(start, end):\n"
        "    current = start\n"
        "    while current <= end:\n"
        "        yield current\n"
        "        current = current + relativedelta(years=1)\n"
    )


def generate_method(method_node: MethodNode) -> str:
    """Generate a Python method definition from a parsed method node."""
    method_name = camel_to_snake(method_node["name"])
    params = ["self"]
    for param in method_node.get("params", []):
        params.append(_format_parameter(param["name"], param.get("ts_type", "")))
    signature = ", ".join(params)
    return_type = _map_ts_type(method_node.get("return_type", ""))
    header = f"    def {method_name}({signature})"
    if return_type:
        header += f" -> {return_type}"
    header += ":"

    body_lines = _translate_body_lines(method_node.get("body_lines", []))
    if not body_lines:
        body_lines = ["        pass"]

    return "\n".join([header, *body_lines])


def _generate_properties(class_node: ClassNode) -> list[str]:
    lines: list[str] = []
    for prop in class_node.get("properties", []):
        name = camel_to_snake(prop["name"])
        ts_type = _map_ts_type(prop.get("ts_type", ""))
        annotation = f": {ts_type}" if ts_type else ""
        prefix = "    " if not prop.get("is_static") else "    "
        lines.append(f"{prefix}{name}{annotation} = None")
    return lines


def _translate_body_lines(body_lines: list[str]) -> list[str]:
    emitted: list[str] = []
    indent = 2
    block_stack: list[bool] = []

    for raw_line in body_lines:
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("}"):
            while line.startswith("}"):
                if block_stack and not block_stack[-1]:
                    emitted.append("    " * (indent + 1) + "pass")
                if block_stack:
                    block_stack.pop()
                indent = max(1, indent - 1)
                line = line[1:].strip()
            if not line:
                continue

        if line == "{":
            continue

        if line.startswith("else if "):
            if block_stack and not block_stack[-1]:
                emitted.append("    " * (indent + 1) + "pass")
            if block_stack:
                block_stack.pop()
            indent = max(1, indent - 1)
            line = "elif " + line[len("else if ") :]

        if line.startswith("else"):
            if block_stack and not block_stack[-1]:
                emitted.append("    " * (indent + 1) + "pass")
            if block_stack:
                block_stack.pop()
            indent = max(1, indent - 1)

        translated = _translate_statement(line)
        opens_block = translated.rstrip().endswith(":")

        if translated:
            emitted.append("    " * indent + translated)
            if block_stack:
                block_stack[-1] = True
        if opens_block:
            block_stack.append(False)
            indent += 1

    while block_stack:
        if not block_stack.pop():
            emitted.append("    " * (indent + 1) + "pass")
        indent = max(1, indent - 1)

    return emitted


def _translate_statement(line: str) -> str:
    stripped = _strip_trailing_semicolon(line.strip())

    if stripped in ("{", "}"):
        return ""

    if stripped.startswith("return "):
        return f"return {translate_expression(stripped[len('return '):])}"
    if stripped == "return":
        return "return"

    if stripped.startswith("const ") or stripped.startswith("let ") or stripped.startswith("var "):
        return _translate_variable_declaration(stripped)

    if stripped.startswith("if "):
        condition = _unwrap_parens(stripped[len("if "):]).rstrip("{").strip()
        return f"if {translate_expression(condition)}:"
    if stripped.startswith("elif "):
        condition = _unwrap_parens(stripped[len("elif "):]).rstrip("{").strip()
        return f"elif {translate_expression(condition)}:"
    if stripped.startswith("else"):
        return "else:"
    if stripped.startswith("for "):
        return _translate_for_loop(stripped)
    if stripped.startswith("while "):
        condition = _unwrap_parens(stripped[len("while "):]).rstrip("{").strip()
        return f"while {translate_expression(condition)}:"
    if stripped.startswith("try"):
        return "try:"
    if stripped.startswith("catch "):
        capture = _unwrap_parens(stripped[len("catch "):]).strip() or "error"
        return f"except Exception as {capture}:"
    if stripped.startswith("finally"):
        return "finally:"

    if stripped.startswith("//"):
        return f"# {stripped[2:].strip()}"

    translated = translate_expression(stripped)
    if translated:
        return translated
    return f"# ts: {stripped}"


def _translate_variable_declaration(line: str) -> str:
    line = re.sub(r"^(const|let|var)\s+", "", line)
    match = re.match(r"(?P<name>[^:=]+?)(?::\s*(?P<ts_type>.+?))?\s*=\s*(?P<value>.+)$", line)
    if not match:
        return f"# ts: {line}"
    name = _normalize_identifier(match.group("name"))
    value = translate_expression(match.group("value"))
    ts_type = match.group("ts_type")
    if ts_type:
        py_type = _map_ts_type(ts_type)
        if py_type:
            return f"{name}: {py_type} = {value}"
    return f"{name} = {value}"


def _translate_for_loop(line: str) -> str:
    loop = re.sub(r"^for\s*", "", line).rstrip("{").strip()
    loop = _unwrap_parens(loop)
    match = re.match(r"(const|let|var)\s+(.+?)\s+of\s+(.+)", loop)
    if match:
        target = _normalize_identifier(match.group(2))
        iterable = translate_expression(match.group(3))
        return f"for {target} in {iterable}:"
    return f"# ts: {line}"


def _format_parameter(name: str, ts_type: str) -> str:
    normalized = _normalize_identifier(name)
    py_type = _map_ts_type(ts_type)
    if py_type:
        return f"{normalized}: {py_type}"
    return normalized


def _map_ts_type(ts_type: str) -> str:
    cleaned = ts_type.strip()
    if not cleaned:
        return ""
    if cleaned in TS_TYPE_MAP:
        return TS_TYPE_MAP[cleaned]
    cleaned = cleaned.replace("Array<", "list[").replace(">", "]")
    cleaned = re.sub(r"Record<string,\s*(.+)>", r"dict[str, \1]", cleaned)
    cleaned = re.sub(r"\{\s*\[key:\s*string\]:\s*(.+)\}", r"dict[str, \1]", cleaned)
    cleaned = cleaned.replace("Promise<", "").replace(">", "")
    cleaned = cleaned.replace("Big", "Decimal")
    cleaned = cleaned.replace("boolean", "bool")
    cleaned = cleaned.replace("number", "float")
    cleaned = cleaned.replace("string", "str")
    cleaned = cleaned.replace("Date", "datetime")
    cleaned = cleaned.replace("any", "Any")
    cleaned = cleaned.replace("void", "None")
    return cleaned


def _normalize_identifier(name: str) -> str:
    normalized = name.strip()
    if normalized.startswith("{") and normalized.endswith("}"):
        inner = normalized[1:-1].strip()
        return inner.replace(":", "_").replace(",", "_")
    return camel_to_snake(normalized) if re.match(r"[a-z]+[A-Z]", normalized) else normalized


def _translate_new_big(expr: str) -> str:
    return re.sub(r"new\s+Big\((.+?)\)", r"Decimal(str(\1))", expr)


def _translate_numeric_chain_methods(expr: str) -> str:
    patterns = {
        "plus": "+",
        "add": "+",
        "minus": "-",
        "sub": "-",
        "times": "*",
        "mul": "*",
        "div": "/",
        "eq": "==",
        "gt": ">",
        "gte": ">=",
        "lt": "<",
        "lte": "<=",
    }
    for method, operator in patterns.items():
        expr = re.sub(
            rf"([A-Za-z0-9_\]\)\.]+)\.{method}\((.+?)\)",
            rf"(\1 {operator} \2)",
            expr,
        )
    expr = re.sub(r"([A-Za-z0-9_\]\)\.]+)\.toNumber\(\)", r"float(\1)", expr)
    expr = re.sub(r"([A-Za-z0-9_\]\)\.]+)\.toFixed\((.+?)\)", r"format(\1, f'.{\2}f')", expr)
    expr = re.sub(r"([A-Za-z0-9_\]\)\.]+)\.length\b", r"len(\1)", expr)
    expr = expr.replace(".includes(", ".__contains__(")
    return expr


def _translate_date_fns(expr: str) -> str:
    replacements = {
        "differenceInDays(": "difference_in_days(",
        "eachDayOfInterval(": "each_day_of_interval(",
        "eachYearOfInterval(": "each_year_of_interval(",
        "isBefore(": "is_before(",
        "isAfter(": "is_after(",
        "isWithinInterval(": "is_within_interval(",
        "startOfDay(": "start_of_day(",
        "endOfDay(": "end_of_day(",
        "startOfYear(": "start_of_year(",
        "endOfYear(": "end_of_year(",
        "subDays(": "sub_days(",
        "addMilliseconds(": "add_milliseconds(",
    }
    for old, new in replacements.items():
        expr = expr.replace(old, new)
    expr = re.sub(r"format\((.+?),\s*DATE_FORMAT\)", r"\1.strftime('%Y-%m-%d')", expr)
    return expr


def _translate_lodash(expr: str) -> str:
    expr = expr.replace("cloneDeep(", "copy.deepcopy(")
    expr = re.sub(r"sortBy\((.+?),\s*(.+)\)", r"sorted(\1, key=\2)", expr)
    expr = re.sub(r"sum\((.+)\)", r"sum(\1)", expr)
    expr = re.sub(r"uniqBy\((.+?),\s*(.+)\)", r"uniq_by(\1, \2)", expr)
    expr = re.sub(r"isNumber\((.+)\)", r"isinstance(\1, (int, float))", expr)
    return expr


def _translate_object_keys_entries(expr: str) -> str:
    expr = re.sub(r"Object\.keys\((.+?)\)", r"list(\1.keys())", expr)
    expr = re.sub(r"Object\.entries\((.+?)\)", r"list(\1.items())", expr)
    expr = re.sub(r"Object\.values\((.+?)\)", r"list(\1.values())", expr)
    return expr


def _translate_arrow_functions(expr: str) -> str:
    expr = re.sub(r"\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)\s*=>\s*([^,)\]}]+)", r"lambda \1: \2", expr)
    expr = re.sub(r"([A-Za-z_][A-Za-z0-9_]*)\s*=>\s*([^,)\]}]+)", r"lambda \1: \2", expr)
    return expr


def _translate_template_literals(expr: str) -> str:
    def _replace(match: re.Match[str]) -> str:
        template = match.group(1)
        return f'f"{template}"'

    return re.sub(r"`([^`]*)`", _replace, expr)


def _translate_optional_chaining(expr: str) -> str:
    while "?." in expr:
        expr = re.sub(
            r"([A-Za-z0-9_\]\)]+)\?\.\[([^\]]+)\]",
            r"(\1.get(\2) if \1 is not None else None)",
            expr,
        )
        expr = re.sub(
            r"([A-Za-z0-9_\]\)]+)\?\.([A-Za-z_][A-Za-z0-9_]*)",
            r"(getattr(\1, '\2', None) if \1 is not None else None)",
            expr,
        )
    return expr


def _translate_nullish(expr: str) -> str:
    return re.sub(r"(.+?)\s*\?\?\s*(.+)", r"(\1 if \1 is not None else \2)", expr)


def _translate_type_keywords(expr: str) -> str:
    expr = expr.replace("&&", " and ")
    expr = expr.replace("||", " or ")
    expr = expr.replace("!==", " != ")
    expr = re.sub(r"(?<![=!<>])===(?!=)", " == ", expr)
    expr = expr.replace("!.", ".")
    return expr


def _unwrap_parens(text: str) -> str:
    value = text.strip()
    if value.startswith("(") and value.endswith(")"):
        return value[1:-1].strip()
    return value


def _strip_trailing_semicolon(text: str) -> str:
    return text[:-1].rstrip() if text.endswith(";") else text
