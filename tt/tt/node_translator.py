"""Translate tree-sitter TypeScript AST nodes to Python source.

Each method handles one node type, recursively translating children.
All domain-specific identifiers and values come from the AST — the
translator itself contains only generic structural patterns.
"""

from __future__ import annotations

from tree_sitter import Node

from tt.emitter import PythonEmitter
from tt.transforms.identifiers import to_py_ident, camel_to_snake


def _text(node: Node) -> str:
    """Extract source text from an AST node."""
    return node.text.decode("utf-8") if node else ""


def _field(node: Node, name: str) -> Node | None:
    """Get a named field child from a node."""
    return node.child_by_field_name(name)


# Maps TypeScript Big.js method names to Python binary operators
_ARITH_OPS = {
    "plus": "+",
    "add": "+",
    "minus": "-",
    "mul": "*",
    "div": "/",
}

_COMPARE_OPS = {
    "eq": "==",
    "gt": ">",
    "lt": "<",
    "gte": ">=",
    "lte": "<=",
}

# TS operators that map directly to Python
_BINARY_OP_MAP = {
    "===": "==",
    "!==": "!=",
    "||": " or ",
    "&&": " and ",
}


class NodeTranslator:
    """Translates tree-sitter TS nodes to Python code strings.

    The ``translate`` method returns a Python expression or statement
    string.  The ``emit_statement`` method writes a full statement
    (with newline) to the emitter.
    """

    def __init__(self, emitter: PythonEmitter) -> None:
        self.emitter = emitter
        # Track whether we are inside a class method (for self. handling)
        self.in_method = False

    # -------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------

    def translate(self, node: Node) -> str:
        """Translate a node to a Python expression string."""
        handler = getattr(self, "_tr_" + node.type, None)
        if handler:
            return handler(node)
        return self._tr_default(node)

    def emit_statement(self, node: Node) -> None:
        """Emit a translated statement to the emitter."""
        handler = getattr(self, "_emit_" + node.type, None)
        if handler:
            handler(node)
            return
        # Fall back to expression-level translation
        expr = self.translate(node)
        if expr.strip():
            self.emitter.emit(expr)

    def emit_block(self, block_node: Node) -> None:
        """Emit all statements in a statement_block node."""
        for child in block_node.children:
            if child.type in ("{", "}", ";"):
                continue
            # Skip logging statements
            if self._is_logging_statement(child):
                continue
            self.emit_statement(child)

    # -------------------------------------------------------------------
    # Statement emitters (_emit_*)
    # -------------------------------------------------------------------

    def _emit_lexical_declaration(self, node: Node) -> None:
        """Translate const/let declarations to Python assignments."""
        for child in node.children:
            if child.type == "variable_declarator":
                self._emit_var_declarator(child)

    def _emit_variable_declaration(self, node: Node) -> None:
        self._emit_lexical_declaration(node)

    def _emit_var_declarator(self, decl: Node) -> None:
        name_node = _field(decl, "name")
        value_node = _field(decl, "value")
        if name_node is None:
            return
        name = self._translate_binding(name_node)
        if value_node:
            val = self.translate(value_node)
            self.emitter.emit(name + " = " + val)
        else:
            # Uninitialized declaration: let x; -> x = None
            self.emitter.emit(name + " = None")

    def _emit_expression_statement(self, node: Node) -> None:
        for child in node.children:
            if child.type == ";":
                continue
            expr = self.translate(child)
            if expr.strip():
                self.emitter.emit(expr)

    def _emit_if_statement(self, node: Node) -> None:
        cond_node = _field(node, "condition")
        cons_node = _field(node, "consequence")
        alt_node = _field(node, "alternative")

        cond = self._translate_condition(cond_node)
        self.emitter.emit("if " + cond + ":")
        self.emitter.indent()
        if cons_node and cons_node.type == "statement_block":
            self.emit_block(cons_node)
        elif cons_node:
            self.emit_statement(cons_node)
        else:
            self.emitter.emit("pass")
        self.emitter.dedent()

        if alt_node:
            self._emit_else_clause(alt_node)

    def _emit_else_clause(self, node: Node) -> None:
        # else clause may contain an if_statement (elif) or a block
        for child in node.children:
            if child.type == "if_statement":
                cond_node = _field(child, "condition")
                cons_node = _field(child, "consequence")
                alt_node = _field(child, "alternative")
                cond = self._translate_condition(cond_node)
                self.emitter.emit("elif " + cond + ":")
                self.emitter.indent()
                if cons_node and cons_node.type == "statement_block":
                    self.emit_block(cons_node)
                elif cons_node:
                    self.emit_statement(cons_node)
                else:
                    self.emitter.emit("pass")
                self.emitter.dedent()
                if alt_node:
                    self._emit_else_clause(alt_node)
                return
            elif child.type == "statement_block":
                self.emitter.emit("else:")
                self.emitter.indent()
                self.emit_block(child)
                self.emitter.dedent()
                return

    def _emit_for_in_statement(self, node: Node) -> None:
        """Translate for...of to Python for...in."""
        left_node = _field(node, "left")
        right_node = _field(node, "right")
        body_node = _field(node, "body")

        var_name = self._translate_binding(left_node) if left_node else "_"
        iterable = self.translate(right_node) if right_node else "[]"

        self.emitter.emit("for " + var_name + " in " + iterable + ":")
        self.emitter.indent()
        if body_node:
            self.emit_block(body_node)
        else:
            self.emitter.emit("pass")
        self.emitter.dedent()

    def _emit_for_statement(self, node: Node) -> None:
        """Translate C-style for loops."""
        init_node = _field(node, "initializer")
        cond_node = _field(node, "condition")
        body_node = _field(node, "body")

        # Emit initializer before the loop
        if init_node:
            self.emit_statement(init_node)

        # Find the increment expression (after the second semicolon)
        increment = None
        for child in node.children:
            if child.type == "augmented_assignment_expression":
                increment = child
            elif child.type == "update_expression":
                increment = child

        # Use while loop pattern
        cond_str = self.translate(cond_node) if cond_node else "True"
        self.emitter.emit("while " + cond_str + ":")
        self.emitter.indent()
        if body_node:
            self.emit_block(body_node)
        if increment:
            self.emit_statement(increment)
        self.emitter.dedent()

    def _emit_return_statement(self, node: Node) -> None:
        # Find the return value (first non-keyword child)
        for child in node.children:
            if child.type in ("return", ";"):
                continue
            val = self.translate(child)
            self.emitter.emit("return " + val)
            return
        self.emitter.emit("return")

    def _emit_break_statement(self, _node: Node) -> None:
        self.emitter.emit("break")

    def _emit_continue_statement(self, _node: Node) -> None:
        self.emitter.emit("continue")

    def _emit_comment(self, node: Node) -> None:
        text = _text(node).strip()
        if text.startswith("//"):
            self.emitter.emit("# " + text[2:].strip())
        elif text.startswith("/*"):
            # Multi-line comment: emit as # lines
            body = text[2:-2].strip() if text.endswith("*/") else text[2:].strip()
            for line in body.split("\n"):
                clean = line.strip().lstrip("* ")
                if clean:
                    self.emitter.emit("# " + clean)

    # -------------------------------------------------------------------
    # Expression translators (_tr_*)
    # -------------------------------------------------------------------

    def _tr_default(self, node: Node) -> str:
        """Fallback: return raw text with basic transforms."""
        return _text(node)

    def _tr_identifier(self, node: Node) -> str:
        name = _text(node)
        return to_py_ident(name)

    def _tr_property_identifier(self, node: Node) -> str:
        return camel_to_snake(_text(node))

    def _tr_shorthand_property_identifier(self, node: Node) -> str:
        name = _text(node)
        py_name = camel_to_snake(name)
        return py_name + "=" + py_name

    def _tr_number(self, node: Node) -> str:
        return _text(node)

    def _tr_string(self, node: Node) -> str:
        raw = _text(node)
        # Convert single-quoted TS strings to Python strings
        return raw

    def _tr_template_string(self, node: Node) -> str:
        # Convert template literals to f-strings
        parts = []
        for child in node.children:
            if child.type == "string_fragment" or child.type == "template_content":
                parts.append(_text(child))
            elif child.type == "template_substitution":
                for sub in child.children:
                    if sub.type not in ("${", "}"):
                        parts.append("{" + self.translate(sub) + "}")
        return 'f"' + "".join(parts) + '"'

    def _tr_true(self, _node: Node) -> str:
        return "True"

    def _tr_false(self, _node: Node) -> str:
        return "False"

    def _tr_null(self, _node: Node) -> str:
        return "None"

    def _tr_undefined(self, _node: Node) -> str:
        return "None"

    def _tr_array(self, node: Node) -> str:
        elements = []
        for child in node.children:
            if child.type in ("[", "]", ","):
                continue
            elements.append(self.translate(child))
        return "[" + ", ".join(elements) + "]"

    def _tr_object(self, node: Node) -> str:
        pairs = []
        for child in node.children:
            if child.type == "pair":
                key_node = child.children[0]
                val_node = _field(child, "value")
                key = _text(key_node)
                val = self.translate(val_node) if val_node else "None"
                pairs.append(key + "=" + val)
            elif child.type == "shorthand_property_identifier":
                pairs.append(self._tr_shorthand_property_identifier(child))
            elif child.type == "spread_element":
                # **spread
                for sc in child.children:
                    if sc.type not in ("...",):
                        pairs.append("**" + self.translate(sc))
        if not pairs:
            return "dict()"
        return "dict(" + ", ".join(pairs) + ")"

    def _tr_parenthesized_expression(self, node: Node) -> str:
        for child in node.children:
            if child.type not in ("(", ")"):
                return "(" + self.translate(child) + ")"
        return "()"

    def _tr_binary_expression(self, node: Node) -> str:
        left = _field(node, "left")
        right = _field(node, "right")
        op_node = _field(node, "operator")
        op = _text(op_node) if op_node else "+"

        # Nullish coalescing: x ?? y -> x if x is not None else y
        if op == "??":
            left_str = self.translate(left)
            right_str = self.translate(right)
            return left_str + " if " + left_str + " is not None else " + right_str

        py_op = _BINARY_OP_MAP.get(op, " " + op + " ")
        if py_op == op and not py_op.startswith(" "):
            py_op = " " + py_op + " "
        return self.translate(left) + py_op + self.translate(right)

    def _tr_unary_expression(self, node: Node) -> str:
        op_node = _field(node, "operator")
        op = _text(op_node) if op_node else ""
        # Find the operand (non-operator child)
        for child in node.children:
            if child != op_node and child.type not in (
                "!",
                "-",
                "+",
                "~",
                "typeof",
                "void",
            ):
                operand = self.translate(child)
                if op == "!":
                    return "not " + operand
                return op + operand
        return _text(node)

    def _tr_assignment_expression(self, node: Node) -> str:
        left = _field(node, "left")
        right = _field(node, "right")
        left_str = self.translate(left) if left else ""
        right_str = self.translate(right) if right else ""
        return left_str + " = " + right_str

    def _tr_augmented_assignment_expression(self, node: Node) -> str:
        left = _field(node, "left")
        right = _field(node, "right")
        op_node = _field(node, "operator")
        op = _text(op_node) if op_node else "+="
        return self.translate(left) + " " + op + " " + self.translate(right)

    def _tr_ternary_expression(self, node: Node) -> str:
        cond = _field(node, "condition")
        cons = _field(node, "consequence")
        alt = _field(node, "alternative")
        return (
            self.translate(cons)
            + " if "
            + self.translate(cond)
            + " else "
            + self.translate(alt)
        )

    def _tr_member_expression(self, node: Node) -> str:
        obj_node = _field(node, "object")
        prop_node = _field(node, "property")

        # Check for optional chaining (?.)
        has_optional = any(child.type == "optional_chain" for child in node.children)

        obj_str = self.translate(obj_node) if obj_node else ""
        prop_str = _text(prop_node) if prop_node else ""

        # Special case: this.x -> self.x
        if obj_node and _text(obj_node) == "this":
            return "self." + camel_to_snake(prop_str)

        # Length property -> len()
        if prop_str == "length":
            return "len(" + obj_str + ")"

        if has_optional:
            # x?.y -> getattr(x, 'y', None)
            return (
                "getattr(" + obj_str + ", " + repr(camel_to_snake(prop_str)) + ", None)"
            )

        return obj_str + "." + camel_to_snake(prop_str)

    def _tr_subscript_expression(self, node: Node) -> str:
        obj = _field(node, "object")
        obj_str = self.translate(obj) if obj else ""
        # Get the index expression (between [ and ])
        idx_parts = []
        in_bracket = False
        for child in node.children:
            if child.type == "[":
                in_bracket = True
                continue
            if child.type == "]":
                break
            if in_bracket:
                idx_parts.append(self.translate(child))
        idx = "".join(idx_parts) if idx_parts else "0"
        return obj_str + "[" + idx + "]"

    def _tr_call_expression(self, node: Node) -> str:
        func_node = _field(node, "function")
        args_node = _field(node, "arguments")

        if func_node is None:
            return _text(node)

        # Handle Big.js method calls: x.plus(y) -> x + y
        if func_node.type == "member_expression":
            result = self._try_big_method(func_node, args_node)
            if result is not None:
                return result

            # Handle special methods
            result = self._try_special_method(func_node, args_node)
            if result is not None:
                return result

        func_str = self.translate(func_node)
        args_str = self._translate_args(args_node) if args_node else ""

        # new_expression is handled separately; this handles regular calls
        return func_str + "(" + args_str + ")"

    def _tr_new_expression(self, node: Node) -> str:
        args_node = _field(node, "arguments")
        # Find the constructor name
        name = ""
        for child in node.children:
            if child.type == "identifier":
                name = _text(child)
                break

        args_str = self._translate_args(args_node) if args_node else ""

        # new Big(x) -> D(str(x)) or D(x) for literals
        if name == "Big":
            if args_str and args_str.isdigit():
                return "D(" + args_str + ")"
            return "D(str(" + args_str + "))" if args_str else "D(0)"

        # new Date() -> date.today()  /  new Date(x) -> parse_date(x)
        if name == "Date":
            if not args_str:
                return "date.today()"
            return "parse_date(" + args_str + ")"

        return name + "(" + args_str + ")"

    def _tr_arrow_function(self, node: Node) -> str:
        params_node = None
        body_node = _field(node, "body")
        for child in node.children:
            if child.type == "formal_parameters":
                params_node = child
                break
            if child.type == "identifier":
                # Single param arrow: x => ...
                params_node = child
                break

        params = self._translate_params(params_node)
        if body_node and body_node.type == "statement_block":
            # Multi-statement arrow - translate to lambda if simple
            # Check for single return statement
            stmts = [c for c in body_node.children if c.type not in ("{", "}")]
            if len(stmts) == 1 and stmts[0].type == "return_statement":
                for rc in stmts[0].children:
                    if rc.type not in ("return", ";"):
                        return "lambda " + params + ": " + self.translate(rc)
            return "lambda " + params + ": None"
        elif body_node:
            return "lambda " + params + ": " + self.translate(body_node)
        return "lambda " + params + ": None"

    def _tr_type_assertion(self, node: Node) -> str:
        # x as Type -> x
        expr = node.children[0] if node.children else node
        return self.translate(expr)

    def _tr_non_null_expression(self, node: Node) -> str:
        # x! -> x
        for child in node.children:
            if child.type != "!":
                return self.translate(child)
        return _text(node)

    def _tr_spread_element(self, node: Node) -> str:
        for child in node.children:
            if child.type != "...":
                return "*" + self.translate(child)
        return _text(node)

    def _tr_update_expression(self, node: Node) -> str:
        # i++ -> i += 1, i-- -> i -= 1
        text = _text(node)
        for child in node.children:
            if child.type == "identifier":
                name = self.translate(child)
                if "++" in text:
                    return name + " += 1"
                elif "--" in text:
                    return name + " -= 1"
        return text

    # -------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------

    def _translate_binding(self, node: Node) -> str:
        """Translate a variable binding (may be destructured)."""
        if node.type == "identifier":
            return to_py_ident(_text(node))
        if node.type == "object_pattern":
            # { a, b } -> we need a, b as separate assignments
            names = []
            for child in node.children:
                if child.type == "shorthand_property_identifier_pattern":
                    names.append(camel_to_snake(_text(child)))
                elif child.type == "pair_pattern":
                    key = child.children[0]
                    names.append(camel_to_snake(_text(key)))
            if len(names) == 1:
                return names[0]
            return ", ".join(names)
        if node.type == "array_pattern":
            names = []
            for child in node.children:
                if child.type not in ("[", "]", ","):
                    names.append(self._translate_binding(child))
            return ", ".join(names)
        return camel_to_snake(_text(node))

    def _translate_condition(self, node: Node) -> str:
        """Translate a condition expression (unwrap parentheses)."""
        if node.type == "parenthesized_expression":
            for child in node.children:
                if child.type not in ("(", ")"):
                    return self.translate(child)
        return self.translate(node)

    def _translate_args(self, args_node: Node) -> str:
        """Translate a function arguments node to comma-separated string."""
        parts = []
        for child in args_node.children:
            if child.type in ("(", ")", ","):
                continue
            parts.append(self.translate(child))
        return ", ".join(parts)

    def _translate_params(self, params_node: Node | None) -> str:
        """Translate formal parameters to Python parameter string."""
        if params_node is None:
            return ""
        if params_node.type == "identifier":
            return camel_to_snake(_text(params_node))
        names = []
        for child in params_node.children:
            if child.type in ("(", ")", ","):
                continue
            if child.type == "required_parameter":
                # May have destructuring
                for pc in child.children:
                    if pc.type == "identifier":
                        names.append(camel_to_snake(_text(pc)))
                    elif pc.type == "object_pattern":
                        names.append(self._translate_binding(pc))
                    elif pc.type not in (":", "type_annotation"):
                        names.append(camel_to_snake(_text(pc)))
            elif child.type == "identifier":
                names.append(camel_to_snake(_text(child)))
        return ", ".join(names) if names else "_"

    def _try_big_method(self, func_node: Node, args_node: Node | None) -> str | None:
        """Try to translate Big.js method calls to operators."""
        prop_node = _field(func_node, "property")
        obj_node = _field(func_node, "object")
        if not prop_node:
            return None

        method = _text(prop_node)

        # Arithmetic: x.plus(y) -> x + (y)
        if method in _ARITH_OPS:
            obj_str = self.translate(obj_node)
            args_str = self._translate_args(args_node) if args_node else "0"
            return obj_str + " " + _ARITH_OPS[method] + " (" + args_str + ")"

        # Comparison: x.eq(0) -> x == D(0)
        if method in _COMPARE_OPS:
            obj_str = self.translate(obj_node)
            args_str = self._translate_args(args_node) if args_node else "0"
            # If arg is a plain number, wrap in D()
            if args_str.strip().isdigit():
                args_str = "D(" + args_str.strip() + ")"
            return obj_str + " " + _COMPARE_OPS[method] + " " + args_str

        # .abs() -> .copy_abs()
        if method == "abs":
            return self.translate(obj_node) + ".copy_abs()"

        # .toNumber() -> float(x)
        if method == "toNumber":
            return "float(" + self.translate(obj_node) + ")"

        # .toFixed(n) -> round(x, n)
        if method == "toFixed":
            args_str = self._translate_args(args_node) if args_node else "2"
            return "round(" + self.translate(obj_node) + ", " + args_str + ")"

        return None

    def _try_special_method(
        self, func_node: Node, args_node: Node | None
    ) -> str | None:
        """Handle special method translations."""
        prop_node = _field(func_node, "property")
        obj_node = _field(func_node, "object")
        if not prop_node:
            return None

        method = _text(prop_node)
        obj_str = self.translate(obj_node) if obj_node else ""
        args_str = self._translate_args(args_node) if args_node else ""

        # Try collection methods first, then utility methods
        result = self._try_collection_method(method, obj_str, args_str, args_node)
        if result is not None:
            return result
        return self._try_utility_method(method, obj_str, args_str)

    def _try_collection_method(
        self,
        method: str,
        obj_str: str,
        args_str: str,
        args_node: Node | None,
    ) -> str | None:
        """Translate JS collection methods to Python equivalents."""
        if method == "push":
            return obj_str + ".append(" + args_str + ")"
        if method == "includes":
            return args_str + " in " + obj_str
        if method == "filter":
            return self._translate_filter(obj_str, args_node)
        if method == "map":
            return self._translate_map(obj_str, args_node)
        if method == "find":
            return self._translate_find(obj_str, args_node)
        if method == "findIndex":
            return self._translate_find_index(obj_str, args_node)
        if method == "at":
            return obj_str + "[" + args_str + "]"
        if method == "sort":
            return obj_str + ".sort(" + args_str + ")"
        if method == "slice":
            return obj_str + "[" + args_str + ":]" if args_str else obj_str + "[:]"
        return None

    def _try_utility_method(
        self,
        method: str,
        obj_str: str,
        args_str: str,
    ) -> str | None:
        """Translate JS utility/accessor methods to Python."""
        if method == "keys":
            return obj_str + ".keys()"
        if method == "values":
            return obj_str + ".values()"
        if method == "entries":
            return obj_str + ".items()"
        if method == "getTime":
            return obj_str
        if obj_str == "console" and method == "log":
            return "pass"
        if obj_str == "Logger" and method == "warn":
            return "pass"
        return None

    def _translate_filter(self, obj_str: str, args_node: Node | None) -> str:
        """Translate .filter(fn) to list comprehension."""
        if not args_node:
            return "[x for x in " + obj_str + "]"

        fn_node = None
        for child in args_node.children:
            if child.type not in ("(", ")", ","):
                fn_node = child
                break

        if fn_node and fn_node.type == "arrow_function":
            param, body_expr = self._extract_arrow_body(fn_node)
            if body_expr:
                return (
                    "["
                    + param
                    + " for "
                    + param
                    + " in "
                    + obj_str
                    + " if "
                    + body_expr
                    + "]"
                )

        fn_str = self.translate(fn_node) if fn_node else "lambda x: x"
        return "[x for x in " + obj_str + " if (" + fn_str + ")(x)]"

    def _translate_map(self, obj_str: str, args_node: Node | None) -> str:
        if not args_node:
            return obj_str
        fn_node = None
        for child in args_node.children:
            if child.type not in ("(", ")", ","):
                fn_node = child
                break
        if fn_node and fn_node.type == "arrow_function":
            param, body_expr = self._extract_arrow_body(fn_node)
            if body_expr:
                return "[" + body_expr + " for " + param + " in " + obj_str + "]"
        return "[x for x in " + obj_str + "]"

    def _translate_find(self, obj_str: str, args_node: Node | None) -> str:
        if not args_node:
            return "None"
        fn_node = None
        for child in args_node.children:
            if child.type not in ("(", ")", ","):
                fn_node = child
                break
        if fn_node and fn_node.type == "arrow_function":
            param, body_expr = self._extract_arrow_body(fn_node)
            if body_expr:
                return (
                    "next(("
                    + param
                    + " for "
                    + param
                    + " in "
                    + obj_str
                    + " if "
                    + body_expr
                    + "), None)"
                )
        return "None"

    def _translate_find_index(self, obj_str: str, args_node: Node | None) -> str:
        if not args_node:
            return "-1"
        fn_node = None
        for child in args_node.children:
            if child.type not in ("(", ")", ","):
                fn_node = child
                break
        if fn_node and fn_node.type == "arrow_function":
            param, body_expr = self._extract_arrow_body(fn_node)
            if body_expr:
                return (
                    "next((_i for _i, "
                    + param
                    + " in enumerate("
                    + obj_str
                    + ") if "
                    + body_expr
                    + "), -1)"
                )
        return "-1"

    def _extract_arrow_body(self, arrow: Node) -> tuple[str, str | None]:
        """Extract parameter name and body expression from an arrow function."""
        params_node = None
        body_node = _field(arrow, "body")
        for child in arrow.children:
            if child.type == "formal_parameters":
                params_node = child
            elif child.type == "identifier" and child != body_node:
                params_node = child

        param = self._translate_params(params_node)

        if body_node:
            if body_node.type == "statement_block":
                stmts = [c for c in body_node.children if c.type not in ("{", "}")]
                if len(stmts) == 1 and stmts[0].type == "return_statement":
                    for rc in stmts[0].children:
                        if rc.type not in ("return", ";"):
                            return param, self.translate(rc)
            else:
                return param, self.translate(body_node)
        return param, None

    def _is_logging_statement(self, node: Node) -> bool:
        """Check if a statement is a logging/console call to skip."""
        text = _text(node).strip()
        # Only skip if the ENTIRE statement is a logging/console call
        # or an ENABLE_LOGGING guard — do NOT skip compound statements
        # (like for loops) that merely contain logging somewhere inside.
        if node.type == "if_statement":
            cond = _field(node, "condition")
            if cond and "ENABLE_LOGGING" in _text(cond):
                return True
        if text.startswith("console."):
            return True
        if text.startswith("Logger."):
            return True
        return False
