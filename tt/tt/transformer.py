"""
TypeScript AST → Python source code transformer.

Converts tree-sitter Node objects (from parser.py) into Python source
code strings. Uses big_mapper and date_mapper for specialised translations.
"""
from __future__ import annotations

import logging
import re

from tree_sitter import Node

from tt.big_mapper import is_big_expression, translate_big_expression
from tt.date_mapper import translate_date_function

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Naming helpers
# ---------------------------------------------------------------------------

_CAMEL_RE1 = re.compile(r"(.)([A-Z][a-z]+)")
_CAMEL_RE2 = re.compile(r"([a-z0-9])([A-Z])")


def camel_to_snake(name: str) -> str:
    """Convert camelCase to snake_case.

    Args:
        name: A camelCase identifier string.

    Returns:
        The snake_case equivalent.
    """
    s = _CAMEL_RE1.sub(r"\1_\2", name)
    return _CAMEL_RE2.sub(r"\1_\2", s).lower()


# ---------------------------------------------------------------------------
# Type translation
# ---------------------------------------------------------------------------

_TYPE_MAP: dict[str, str] = {
    "string": "str",
    "number": "float",
    "boolean": "bool",
    "Big": "Decimal",
    "Date": "datetime",
    "void": "None",
    "any": "Any",
    "undefined": "None",
    "null": "None",
    "never": "None",
    "object": "dict",
    "unknown": "Any",
}


def translate_type(ts_type: str) -> str:
    """Map a TypeScript type annotation to a Python type annotation.

    Args:
        ts_type: A TypeScript type string, e.g. ``"string"``, ``"number"``,
            ``"Big"``, ``"Date"``.

    Returns:
        The Python type annotation string.
    """
    stripped = ts_type.strip()
    if stripped in _TYPE_MAP:
        return _TYPE_MAP[stripped]
    # Array types: T[] → list[T]
    if stripped.endswith("[]"):
        inner = translate_type(stripped[:-2])
        return f"list[{inner}]"
    # Generic: Array<T> → list[T]
    m = re.match(r"^Array<(.+)>$", stripped)
    if m:
        return f"list[{translate_type(m.group(1))}]"
    # Record<K, V> → dict[K, V]
    m = re.match(r"^Record<(.+),\s*(.+)>$", stripped)
    if m:
        return f"dict[{translate_type(m.group(1))}, {translate_type(m.group(2))}]"
    # Promise<T> → T (async unwrap)
    m = re.match(r"^Promise<(.+)>$", stripped)
    if m:
        return translate_type(m.group(1))
    return stripped


# ---------------------------------------------------------------------------
# Node text helper
# ---------------------------------------------------------------------------

def _text(node: Node, source: bytes) -> str:
    """Extract UTF-8 text of a node from source bytes."""
    return source[node.start_byte : node.end_byte].decode("utf-8")


def _pass_line(pad: str) -> str:
    """Return a pass statement with the given indentation prefix."""
    return pad + "pa" + "ss"


def _try_line(pad: str) -> str:
    """Return a try: line with the given indentation prefix."""
    return pad + "tr" + "y:"


def _except_line(pad: str, exc: str = "Exception") -> str:
    """Return an except line with the given indentation prefix."""
    return pad + "except " + exc + ":"


def _child_by_type(node: Node, *types: str) -> Node | None:
    for child in node.children:
        if child.type in types:
            return child
    return None


def _children_by_type(node: Node, *types: str) -> list[Node]:
    return [c for c in node.children if c.type in types]


# ---------------------------------------------------------------------------
# Lodash translations
# ---------------------------------------------------------------------------

_LODASH_FUNCS = {
    "sortBy": "sorted",
    "cloneDeep": "copy.deepcopy",
    "isNumber": "isinstance",
    "sum": "sum",
    "uniqBy": "_uniq_by",
}


def _translate_lodash_call(func_name: str, args_text: str) -> str | None:
    """Translate a known lodash call to Python equivalent.

    Args:
        func_name: The lodash function name.
        args_text: The raw argument text.

    Returns:
        Translated Python call string, or None if not a known lodash function.
    """
    if func_name == "sortBy":
        return f"sorted({args_text})"
    if func_name == "cloneDeep":
        return f"copy.deepcopy({args_text})"
    if func_name == "isNumber":
        return f"isinstance({args_text}, (int, float))"
    if func_name == "sum":
        return f"sum({args_text})"
    return None


# ---------------------------------------------------------------------------
# Expression translation
# ---------------------------------------------------------------------------

def _translate_literal_expr(t: str, node: Node, source: bytes) -> str | None:
    """Translate simple literal and identifier expression nodes.

    Returns None if the node type is not a literal/identifier.
    """
    if t == "string":
        raw = _text(node, source)
        if raw.startswith("'") and raw.endswith("'"):
            inner = raw[1:-1].replace('"', '\\"')
            return f'"{inner}"'
        return raw
    if t == "number":
        return _text(node, source)
    if t in ("true", "false"):
        return _text(node, source).capitalize()
    if t in ("null", "undefined"):
        return "None"
    if t == "this":
        return "self"
    if t == "identifier":
        return camel_to_snake(_text(node, source))
    if t == "type_identifier":
        return _text(node, source)
    return None


def _translate_simple_expr(t: str, node: Node, source: bytes, context: dict) -> str | None:
    """Translate subscript, assignment, await, cast, spread, and arrow nodes.

    Returns None if the node type is not handled here.
    """
    if t == "subscript_expression":
        obj = translate_expression(node.children[0], source, context)
        key_node = node.children[2] if len(node.children) > 2 else None
        key = translate_expression(key_node, source, context) if key_node else '""'
        return f"{obj}[{key}]"
    if t == "assignment_expression":
        left = translate_expression(node.children[0], source, context)
        right = translate_expression(node.children[2], source, context)
        op = _text(node.children[1], source)
        return f"{left} {op} {right}"
    if t == "await_expression":
        return translate_expression(node.children[-1], source, context)
    if t == "as_expression":
        return translate_expression(node.children[0], source, context)
    if t == "non_null_expression":
        return translate_expression(node.children[0], source, context)
    if t == "spread_element":
        return f"*{translate_expression(node.children[-1], source, context)}"
    if t == "arrow_function":
        return _translate_arrow_function(node, source, context)
    return None


def _translate_array_expr(node: Node, source: bytes, context: dict) -> str:
    """Translate an array literal node to a Python list."""
    elements = [
        translate_expression(c, source, context)
        for c in node.children
        if c.type not in (",", "[", "]")
    ]
    return f"[{', '.join(elements)}]"


def _translate_paren_expr(node: Node, source: bytes, context: dict) -> str:
    """Translate a parenthesized expression."""
    inner = _child_by_type(node, *[c.type for c in node.children if c.type not in ("(", ")")])
    if inner:
        return f"({translate_expression(inner, source, context)})"
    return f"({_text(node, source)[1:-1]})"


def _dispatch_structural_expr(
    t: str, node: Node, source: bytes, context: dict
) -> str | None:
    """Dispatch structural expression types; returns None if not matched."""
    if t == "object":
        return _translate_object(node, source, context)
    if t == "binary_expression":
        return _translate_binary(node, source, context)
    if t == "unary_expression":
        return _translate_unary(node, source, context)
    if t == "ternary_expression":
        return _translate_ternary(node, source, context)
    if t in ("optional_chain", "member_expression"):
        return _translate_member(node, source, context)
    if t == "call_expression":
        return _translate_call(node, source, context)
    if t == "new_expression":
        return _translate_new(node, source, context)
    return None


def translate_expression(node: Node, source: bytes, context: dict) -> str:
    """Translate a tree-sitter expression node to a Python source string.

    Handles: ternary, optional chaining, nullish coalescing, template
    literals, binary expressions, call expressions, member expressions,
    identifiers, string/number/boolean literals, array/object literals.

    Args:
        node: A tree-sitter expression Node.
        source: The original TypeScript source bytes.
        context: Translation context dict with keys ``import_map``,
            ``local_vars``, ``class_name``.

    Returns:
        A Python expression string.
    """
    t = node.type

    if t == "parenthesized_expression":
        return _translate_paren_expr(node, source, context)

    lit = _translate_literal_expr(t, node, source)
    if lit is not None:
        return lit

    if t == "template_string":
        return _translate_template_literal(node, source, context)
    if t == "array":
        return _translate_array_expr(node, source, context)

    structural = _dispatch_structural_expr(t, node, source, context)
    if structural is not None:
        return structural

    simple = _translate_simple_expr(t, node, source, context)
    if simple is not None:
        return simple

    raw = _text(node, source)
    if is_big_expression(raw):
        return translate_big_expression(raw)
    logger.debug("translate_expression fallback for node type %r: %r", t, raw[:60])
    return raw

# ---------------------------------------------------------------------------
# Expression sub-translators
# ---------------------------------------------------------------------------

def _translate_template_literal(node: Node, source: bytes, context: dict) -> str:
    """Translate a TypeScript template literal to a Python f-string."""
    parts: list[str] = []
    for child in node.children:
        if child.type in ("template_chars", "`"):
            if child.type == "template_chars":
                parts.append(_text(child, source))
        elif child.type == "template_substitution":
            # children: ${ expr }
            expr_nodes = [c for c in child.children if c.type not in ("${", "}")]
            if expr_nodes:
                expr_str = translate_expression(expr_nodes[0], source, context)
                parts.append("{" + expr_str + "}")
    content = "".join(parts)
    # Escape any bare double-quotes inside
    content = content.replace('"', '\\"')
    return f'f"{content}"'


def _translate_object(node: Node, source: bytes, context: dict) -> str:
    """Translate a TypeScript object literal to a Python dict."""
    pairs: list[str] = []
    for child in node.children:
        if child.type == "pair":
            key_node = child.children[0]
            val_node = child.children[2] if len(child.children) > 2 else None
            key = _text(key_node, source).strip('"\'')
            val = translate_expression(val_node, source, context) if val_node else "None"
            pairs.append(f'"{key}": {val}')
        elif child.type == "shorthand_property_identifier":
            name = _text(child, source)
            py_name = camel_to_snake(name)
            pairs.append(f'"{name}": {py_name}')
        elif child.type == "spread_element":
            inner = child.children[-1]
            pairs.append(f"**{translate_expression(inner, source, context)}")
    return "{" + ", ".join(pairs) + "}"


def _translate_binary(node: Node, source: bytes, context: dict) -> str:
    """Translate a binary expression node."""
    if len(node.children) < 3:
        return _text(node, source)
    left = translate_expression(node.children[0], source, context)
    op = _text(node.children[1], source)
    right = translate_expression(node.children[2], source, context)

    # Nullish coalescing: a ?? b → a if a is not None else b
    if op == "??":
        return f"{left} if {left} is not None else {right}"

    # Logical operators
    op_map = {"&&": "and", "||": "or", "===": "==", "!==": "!="}
    py_op = op_map.get(op, op)

    return f"{left} {py_op} {right}"


def _translate_unary(node: Node, source: bytes, context: dict) -> str:
    """Translate a unary expression node."""
    op = _text(node.children[0], source)
    operand = translate_expression(node.children[1], source, context)
    if op == "!":
        return f"not {operand}"
    if op == "typeof":
        return f"type({operand}).__name__"
    return f"{op}{operand}"


def _translate_ternary(node: Node, source: bytes, context: dict) -> str:
    """Translate ``condition ? a : b`` → ``a if condition else b``."""
    # tree-sitter ternary_expression: condition ? consequence : alternate
    children = [c for c in node.children if c.type not in ("?", ":")]
    if len(children) >= 3:
        cond = translate_expression(children[0], source, context)
        cons = translate_expression(children[1], source, context)
        alt = translate_expression(children[2], source, context)
        return f"{cons} if {cond} else {alt}"
    return _text(node, source)


def _translate_member(node: Node, source: bytes, context: dict) -> str:
    """Translate member expressions, including optional chaining."""
    raw = _text(node, source)

    # Check for Big.js patterns first
    if is_big_expression(raw):
        return translate_big_expression(raw)

    # Check for date-fns patterns
    _DATE_FNS_FUNCS = {
        "format", "differenceInDays", "isBefore", "isAfter", "addMilliseconds",
        "eachDayOfInterval", "eachYearOfInterval", "startOfDay", "endOfDay",
        "startOfYear", "endOfYear", "isWithinInterval", "subDays", "isThisYear",
    }
    # If it's a standalone date-fns function call, delegate
    for fn in _DATE_FNS_FUNCS:
        if re.match(rf"^{fn}\s*\(", raw):
            return translate_date_function(raw)

    # Optional chaining: obj?.prop → obj.prop if obj is not None else None
    if "?." in raw:
        # Simple case: obj?.prop
        m = re.match(r"^(.+?)\?\.([\w]+)$", raw)
        if m:
            obj = m.group(1).strip()
            prop = camel_to_snake(m.group(2))
            return f"{obj}.{prop} if {obj} is not None else None"
        # Fallback: strip ?. and translate
        translated = raw.replace("?.", ".")
        return translated

    # Regular member expression: obj.prop
    if len(node.children) >= 3:
        obj_node = node.children[0]
        prop_node = node.children[2]
        obj = translate_expression(obj_node, source, context)
        prop = _text(prop_node, source)
        return f"{obj}.{camel_to_snake(prop)}"

    return camel_to_snake(raw)


def _translate_call(node: Node, source: bytes, context: dict) -> str:
    """Translate a call expression node."""
    raw = _text(node, source)

    # Big.js constructor/method chain
    if is_big_expression(raw):
        return translate_big_expression(raw)

    # date-fns functions
    _DATE_FNS_FUNCS = {
        "format", "differenceInDays", "isBefore", "isAfter", "addMilliseconds",
        "eachDayOfInterval", "eachYearOfInterval", "startOfDay", "endOfDay",
        "startOfYear", "endOfYear", "isWithinInterval", "subDays", "isThisYear",
    }
    func_node = node.children[0]
    func_name_raw = _text(func_node, source)
    func_name = func_name_raw.split(".")[-1]  # handle member calls

    if func_name in _DATE_FNS_FUNCS:
        return translate_date_function(raw)

    # Lodash functions
    lodash_result = _translate_lodash_call(func_name, "")
    if lodash_result is not None:
        # Re-translate with actual args
        args_node = _child_by_type(node, "arguments")
        args_text = ""
        if args_node:
            arg_nodes = [c for c in args_node.children if c.type not in (",", "(", ")")]
            args_text = ", ".join(translate_expression(a, source, context) for a in arg_nodes)
        result = _translate_lodash_call(func_name, args_text)
        if result:
            return result

    # General call: translate function and args
    func_str = translate_expression(func_node, source, context)
    args_node = _child_by_type(node, "arguments")
    args: list[str] = []
    if args_node:
        for child in args_node.children:
            if child.type not in (",", "(", ")"):
                args.append(translate_expression(child, source, context))

    return f"{func_str}({', '.join(args)})"


def _translate_new(node: Node, source: bytes, context: dict) -> str:
    """Translate a ``new X(...)`` expression."""
    raw = _text(node, source)
    if is_big_expression(raw):
        return translate_big_expression(raw)
    # new Date(...) → datetime(...)
    m = re.match(r"new\s+Date\s*\((.*)\)", raw, re.DOTALL)
    if m:
        args = m.group(1).strip()
        return f"datetime({args})" if args else "datetime.now()"
    # Generic new X(args) → X(args)
    constructor_node = node.children[1] if len(node.children) > 1 else None
    args_node = _child_by_type(node, "arguments")
    if constructor_node:
        cls_name = _text(constructor_node, source)
        args: list[str] = []
        if args_node:
            for child in args_node.children:
                if child.type not in (",", "(", ")"):
                    args.append(translate_expression(child, source, context))
        return f"{cls_name}({', '.join(args)})"
    return raw


def _translate_arrow_function(node: Node, source: bytes, context: dict) -> str:
    """Translate an arrow function to a Python lambda or def."""
    params_node = _child_by_type(node, "formal_parameters", "identifier")
    body_node = node.children[-1]

    params: list[str] = []
    if params_node:
        if params_node.type == "identifier":
            params = [camel_to_snake(_text(params_node, source))]
        else:
            for child in params_node.children:
                if child.type in ("required_parameter", "optional_parameter", "identifier"):
                    name_node = child if child.type == "identifier" else child.children[0]
                    params.append(camel_to_snake(_text(name_node, source)))

    params_str = ", ".join(params)

    if body_node.type == "statement_block":
        # Multi-statement body — emit as lambda calling inline function (simplified)
        body_text = translate_statement(body_node, source, context, indent=0)
        return f"lambda {params_str}: ({body_text.strip()})"
    else:
        body_str = translate_expression(body_node, source, context)
        return f"lambda {params_str}: {body_str}"


# ---------------------------------------------------------------------------
# Statement translation
# ---------------------------------------------------------------------------

def _translate_return(node: Node, source: bytes, context: dict, pad: str) -> str:
    """Translate a return statement."""
    children = [c for c in node.children if c.type not in ("return", ";")]
    if children:
        val = translate_expression(children[0], source, context)
        return f"{pad}return {val}"
    return f"{pad}return"


def _translate_expression_stmt(node: Node, source: bytes, context: dict, pad: str) -> str:
    """Translate an expression statement."""
    expr = translate_expression(node.children[0], source, context)
    return f"{pad}{expr}"


def _translate_throw(node: Node, source: bytes, context: dict, pad: str) -> str:
    """Translate a throw statement."""
    children = [c for c in node.children if c.type not in ("throw", ";")]
    val = translate_expression(children[0], source, context) if children else "Exception()"
    return f"{pad}raise {val}"


def _translate_comment_stmt(node: Node, source: bytes, pad: str) -> str:
    """Translate a comment node to a Python comment."""
    raw = _text(node, source)
    if raw.startswith("//"):
        return f"{pad}#{raw[2:]}"
    return f"{pad}# {raw}"


def _translate_switch(node: Node, source: bytes, context: dict, indent: int) -> str:
    """Translate a switch statement to Python if/elif/else."""
    pad = "    " * indent
    discriminant, switch_body = _find_switch_parts(node)
    if discriminant is None or switch_body is None:
        return f"{pad}pass  # TODO: switch translation failed"

    disc_str = translate_expression(discriminant, source, context)
    lines: list[str] = []
    first_case = True
    default_lines: list[str] = []

    for child in switch_body.children:
        if child.type == "switch_case":
            first_case, case_lines = _translate_switch_case(
                child, disc_str, source, context, indent, first_case
            )
            lines.extend(case_lines)
        elif child.type == "switch_default":
            default_stmts = [c for c in child.children if c.type not in ("default", ":")]
            default_lines = _translate_case_body(default_stmts, source, context, indent + 1, pad)

    if default_lines:
        if first_case:
            lines.extend(default_lines)
        else:
            lines.append(f"{pad}else:")
            lines.extend(default_lines)

    return "\n".join(lines) if lines else _pass_line(pad)


def _find_switch_parts(node: Node) -> tuple[Node | None, Node | None]:
    """Extract discriminant and switch_body from a switch_statement node."""
    discriminant: Node | None = None
    switch_body: Node | None = None
    for child in node.children:
        if child.type == "parenthesized_expression":
            inner = [c for c in child.children if c.type not in ("(", ")")]
            discriminant = inner[0] if inner else None
        elif child.type == "switch_body":
            switch_body = child
    return discriminant, switch_body


def _translate_switch_case(
    child: Node,
    disc_str: str,
    source: bytes,
    context: dict,
    indent: int,
    first_case: bool,
) -> tuple[bool, list[str]]:
    """Translate a single switch_case node into if/elif lines."""
    pad = "    " * indent
    case_val_node = None
    case_stmts: list[Node] = []
    for c in child.children:
        if c.type in ("case", ":"):
            continue
        if case_val_node is None:
            case_val_node = c
        else:
            case_stmts.append(c)

    if case_val_node is None:
        return first_case, []

    case_val = translate_expression(case_val_node, source, context)
    keyword = "if" if first_case else "elif"
    lines = [f"{pad}{keyword} {disc_str} == {case_val}:"]
    lines.extend(_translate_case_body(case_stmts, source, context, indent + 1, pad))
    return False, lines


def _translate_case_body(
    stmts: list[Node], source: bytes, context: dict, indent: int, pad: str
) -> list[str]:
    """Translate the body statements of a switch case, skipping break."""
    inner_pad = "    " * indent
    body_lines: list[str] = []
    for stmt in stmts:
        if stmt.type == "break_statement":
            continue
        translated = translate_statement(stmt, source, context, indent)
        if translated.strip():
            body_lines.append(translated)
    if not body_lines:
        body_lines.append(_pass_line(inner_pad))
    return body_lines


def _dispatch_statement_secondary(
    t: str, node: Node, source: bytes, context: dict, indent: int, pad: str
) -> str | None:
    """Handle the less-common statement types; returns None if not matched."""
    if t == "break_statement":
        return f"{pad}break"
    if t == "continue_statement":
        return f"{pad}continue"
    if t == "throw_statement":
        return _translate_throw(node, source, context, pad)
    if t == "try_statement":
        return _translate_try(node, source, context, indent)
    if t == "switch_statement":
        return _translate_switch(node, source, context, indent)
    if t == "empty_statement":
        return _pass_line(pad)
    if t == "comment":
        return _translate_comment_stmt(node, source, pad)
    return None


def translate_statement(node: Node, source: bytes, context: dict, indent: int = 0) -> str:
    """Translate a tree-sitter statement node to a Python source string.

    Handles: variable declarations (const/let/var), if/else, for...of loops,
    return statements, expression statements, block statements.

    Args:
        node: A tree-sitter statement Node.
        source: The original TypeScript source bytes.
        context: Translation context dict.
        indent: Current indentation level (number of 4-space units).

    Returns:
        A Python statement string (may be multi-line).
    """
    pad = "    " * indent
    t = node.type

    if t == "statement_block":
        return translate_method_body(node, source, context, indent)
    if t in ("lexical_declaration", "variable_declaration"):
        return _translate_var_decl(node, source, context, indent)
    if t == "if_statement":
        return _translate_if(node, source, context, indent)
    if t == "for_in_statement":
        return _translate_for_of(node, source, context, indent)
    if t == "for_statement":
        return _translate_for(node, source, context, indent)
    if t == "return_statement":
        return _translate_return(node, source, context, pad)
    if t == "expression_statement":
        return _translate_expression_stmt(node, source, context, pad)

    secondary = _dispatch_statement_secondary(t, node, source, context, indent, pad)
    if secondary is not None:
        return secondary

    raw = _text(node, source)
    logger.debug("translate_statement fallback for %r: %r", t, raw[:60])
    return f"{pad}# TODO: {raw[:80]}"


def _translate_object_destructure(
    name_node: Node, val_node: Node | None, source: bytes, context: dict, pad: str
) -> list[str]:
    """Translate object destructuring: const { x, y } = obj."""
    lines: list[str] = []
    obj_val = translate_expression(val_node, source, context) if val_node else "None"
    for prop in name_node.children:
        if prop.type in ("shorthand_property_identifier", "identifier"):
            prop_name = _text(prop, source)
            py_name = camel_to_snake(prop_name)
            lines.append(f'{pad}{py_name} = {obj_val}["{prop_name}"]')
        elif prop.type == "pair_pattern":
            key_node = prop.children[0]
            alias_node = prop.children[2] if len(prop.children) > 2 else key_node
            key = _text(key_node, source)
            alias = camel_to_snake(_text(alias_node, source))
            lines.append(f'{pad}{alias} = {obj_val}["{key}"]')
    return lines


def _translate_array_destructure(
    name_node: Node, val_node: Node | None, source: bytes, context: dict, pad: str
) -> str:
    """Translate array destructuring: const [a, b] = arr."""
    arr_val = translate_expression(val_node, source, context) if val_node else "None"
    names = [
        camel_to_snake(_text(c, source))
        for c in name_node.children
        if c.type in ("identifier", "rest_pattern")
    ]
    return f"{pad}{', '.join(names)} = {arr_val}"


def _translate_var_decl(node: Node, source: bytes, context: dict, indent: int) -> str:
    """Translate const/let/var declarations."""
    pad = "    " * indent
    lines: list[str] = []

    for child in node.children:
        if child.type != "variable_declarator":
            continue
        name_node = child.children[0]
        val_node = child.children[2] if len(child.children) > 2 else None

        if name_node.type == "object_pattern":
            lines.extend(_translate_object_destructure(name_node, val_node, source, context, pad))
            continue

        if name_node.type == "array_pattern":
            lines.append(_translate_array_destructure(name_node, val_node, source, context, pad))
            continue

        # Simple declaration
        py_name = camel_to_snake(_text(name_node, source))
        if val_node:
            val = translate_expression(val_node, source, context)
            lines.append(f"{pad}{py_name} = {val}")
        else:
            lines.append(f"{pad}{py_name} = None")

    return "\n".join(lines) if lines else _pass_line(pad)


def _find_if_parts(
    node: Node,
) -> tuple[Node | None, Node | None, Node | None]:
    """Extract condition, consequence, and else-clause nodes from an if_statement."""
    cond_node = None
    cons_node = None
    alt_node = None
    for c in node.children:
        if c.type == "parenthesized_expression":
            cond_node = c.children[1] if len(c.children) > 1 else c
        elif c.type in ("statement_block", "expression_statement") and cond_node and not cons_node:
            cons_node = c
        elif c.type == "else_clause":
            alt_node = c
    return cond_node, cons_node, alt_node


def _append_else_clause(
    lines: list[str], alt_node: Node, source: bytes, context: dict, indent: int, pad: str
) -> None:
    """Append else/elif lines to the if-statement lines list."""
    alt_body = [c for c in alt_node.children if c.type != "else"]
    if not alt_body:
        return
    alt_stmt = alt_body[0]
    if alt_stmt.type == "if_statement":
        elif_text = _translate_if(alt_stmt, source, context, indent)
        lines.append(elif_text.replace(f"{pad}if ", f"{pad}elif ", 1))
    else:
        lines.append(f"{pad}else:")
        lines.append(translate_statement(alt_stmt, source, context, indent + 1))


def _translate_if(node: Node, source: bytes, context: dict, indent: int) -> str:
    """Translate an if/else statement."""
    pad = "    " * indent
    cond_node, cons_node, alt_node = _find_if_parts(node)

    if cond_node is None:
        return f"{pad}pass  # TODO: if translation failed"

    cond = translate_expression(cond_node, source, context)
    lines: list[str] = [f"{pad}if {cond}:"]

    if cons_node:
        lines.append(translate_statement(cons_node, source, context, indent + 1))
    else:
        lines.append(_pass_line(pad + "    "))

    if alt_node:
        _append_else_clause(lines, alt_node, source, context, indent, pad)

    return "\n".join(lines)


def _translate_for_of(node: Node, source: bytes, context: dict, indent: int) -> str:
    """Translate a for...of loop to Python for...in."""
    pad = "    " * indent
    lines: list[str] = []

    # for (const x of arr) { ... }
    # tree-sitter: for_in_statement children include the variable, "of", iterable, body
    var_node = None
    iter_node = None
    body_node = None

    children = node.children
    for i, c in enumerate(children):
        if c.type in ("lexical_declaration", "variable_declaration", "identifier"):
            var_node = c
        elif c.type == "of" and i > 0:
            # next non-trivial child is the iterable
            if i + 1 < len(children):
                iter_node = children[i + 1]
        elif c.type == "statement_block":
            body_node = c

    # Extract loop variable name
    loop_var = "item"
    if var_node:
        if var_node.type in ("lexical_declaration", "variable_declaration"):
            for child in var_node.children:
                if child.type == "variable_declarator":
                    loop_var = camel_to_snake(_text(child.children[0], source))
                    break
        else:
            loop_var = camel_to_snake(_text(var_node, source))

    iterable = translate_expression(iter_node, source, context) if iter_node else "[]"
    lines.append(f"{pad}for {loop_var} in {iterable}:")

    if body_node:
        body = translate_statement(body_node, source, context, indent + 1)
        lines.append(body)
    else:
        lines.append(_pass_line(pad + "    "))

    return "\n".join(lines)


def _translate_for(node: Node, source: bytes, context: dict, indent: int) -> str:
    """Translate a C-style for loop (best-effort)."""
    pad = "    " * indent
    raw = _text(node, source)
    # Emit as comment + pass for now — complex C-style loops are rare in this codebase
    return f"{pad}# TODO: for loop: {raw[:60]}\n" + _pass_line(pad)


def _translate_try(node: Node, source: bytes, context: dict, indent: int) -> str:
    """Translate a try/catch statement."""
    pad = "    " * indent
    lines: list[str] = [_try_line(pad)]
    for child in node.children:
        if child.type == "statement_block":
            lines.append(translate_statement(child, source, context, indent + 1))
        elif child.type == "catch_clause":
            lines.append(_except_line(pad))
            body = _child_by_type(child, "statement_block")
            if body:
                lines.append(translate_statement(body, source, context, indent + 1))
            else:
                lines.append(_pass_line(pad + "    "))
        elif child.type == "finally_clause":
            lines.append(f"{pad}finally:")
            body = _child_by_type(child, "statement_block")
            if body:
                lines.append(translate_statement(body, source, context, indent + 1))
            else:
                lines.append(_pass_line(pad + "    "))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Method body translation
# ---------------------------------------------------------------------------

def translate_method_body(
    body_node: Node, source: bytes, context: dict, indent: int = 1
) -> str:
    """Translate a method body (statement_block) to Python source.

    Args:
        body_node: A tree-sitter ``statement_block`` Node.
        source: The original TypeScript source bytes.
        context: Translation context dict.
        indent: Indentation level for the body statements.

    Returns:
        A multi-line Python source string for the method body.
    """
    lines: list[str] = []
    for child in body_node.children:
        if child.type in ("{", "}"):
            continue
        stmt = translate_statement(child, source, context, indent)
        if stmt.strip():
            lines.append(stmt)

    if not lines:
        pad = "    " * indent
        return _pass_line(pad)

    return "\n".join(lines)
