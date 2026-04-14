"""Layer 2: Semantic extractor — walks tree-sitter AST and extracts symbol table."""

from dataclasses import dataclass, field
from tree_sitter import Node

from tt.parser import get_node_text


@dataclass
class ImportedName:
    name: str
    alias: str | None = None


@dataclass
class ImportDecl:
    source: str          # e.g. "big.js" or "@ghostfolio/common/helper"
    names: list[ImportedName] = field(default_factory=list)
    default_name: str | None = None


@dataclass
class ParamDecl:
    name: str
    ts_type: str | None = None
    default: str | None = None
    is_readonly: bool = False
    access_modifier: str | None = None  # "public" | "protected" | "private" | None


@dataclass
class DecoratorDecl:
    name: str
    args_text: str | None = None


@dataclass
class FieldDecl:
    name: str
    ts_type: str | None = None
    initializer: str | None = None
    access_modifier: str | None = None
    is_readonly: bool = False


@dataclass
class MethodDecl:
    name: str
    params: list[ParamDecl] = field(default_factory=list)
    return_type: str | None = None
    body_text: str | None = None   # raw TS body text (excluding outer braces)
    access_modifier: str | None = None
    is_async: bool = False
    is_abstract: bool = False
    decorators: list[DecoratorDecl] = field(default_factory=list)


@dataclass
class ClassDecl:
    name: str
    base_class: str | None = None
    type_params: list[str] = field(default_factory=list)
    fields: list[FieldDecl] = field(default_factory=list)
    methods: list[MethodDecl] = field(default_factory=list)
    decorators: list[DecoratorDecl] = field(default_factory=list)
    is_abstract: bool = False
    is_exported: bool = False


@dataclass
class ExtractionResult:
    imports: list[ImportDecl] = field(default_factory=list)
    classes: list[ClassDecl] = field(default_factory=list)
    source_bytes: bytes = field(default_factory=bytes)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _text(node: Node, src: bytes) -> str:
    return get_node_text(node, src)


def _child_by_type(node: Node, *types: str) -> Node | None:
    for child in node.children:
        if child.type in types:
            return child
    return None


def _children_by_type(node: Node, *types: str) -> list[Node]:
    return [c for c in node.children if c.type in types]


# ---------------------------------------------------------------------------
# Import extraction
# ---------------------------------------------------------------------------

def _extract_import(node: Node, src: bytes) -> ImportDecl:
    """Parse an import_statement node into ImportDecl."""
    source = ""
    names: list[ImportedName] = []
    default_name: str | None = None

    # Find source string
    source_node = _child_by_type(node, "string")
    if source_node:
        # Strip quotes: look for string_fragment child
        frag = _child_by_type(source_node, "string_fragment")
        if frag:
            source = _text(frag, src)
        else:
            raw = _text(source_node, src)
            source = raw.strip("'\"")

    # Find import_clause
    clause = _child_by_type(node, "import_clause")
    if clause:
        for child in clause.children:
            if child.type == "identifier":
                # default import
                default_name = _text(child, src)
            elif child.type == "named_imports":
                for spec in _children_by_type(child, "import_specifier"):
                    idents = [c for c in spec.children if c.type == "identifier"]
                    if len(idents) == 1:
                        names.append(ImportedName(name=_text(idents[0], src)))
                    elif len(idents) >= 2:
                        # "Bar as B" — first ident is original, second is alias
                        names.append(ImportedName(
                            name=_text(idents[0], src),
                            alias=_text(idents[1], src),
                        ))
            elif child.type == "namespace_import":
                # import * as X
                ident = _child_by_type(child, "identifier")
                if ident:
                    default_name = f"* as {_text(ident, src)}"

    return ImportDecl(source=source, names=names, default_name=default_name)


# ---------------------------------------------------------------------------
# Decorator extraction
# ---------------------------------------------------------------------------

def _extract_decorator(node: Node, src: bytes) -> DecoratorDecl:
    """Parse a decorator node into DecoratorDecl."""
    # Children: "@" + (identifier | call_expression | member_expression)
    name = ""
    args_text: str | None = None

    for child in node.children:
        if child.type == "@":
            continue
        elif child.type == "identifier":
            name = _text(child, src)
        elif child.type == "call_expression":
            func = _child_by_type(child, "identifier", "member_expression")
            if func:
                name = _text(func, src)
            args_node = _child_by_type(child, "arguments")
            if args_node:
                # Strip surrounding parens
                inner = _text(args_node, src)
                args_text = inner[1:-1] if inner.startswith("(") else inner
        elif child.type == "member_expression":
            name = _text(child, src)

    return DecoratorDecl(name=name, args_text=args_text)


# ---------------------------------------------------------------------------
# Parameter extraction
# ---------------------------------------------------------------------------

def _extract_param(node: Node, src: bytes) -> ParamDecl:
    """Parse required_parameter / optional_parameter / rest_parameter into ParamDecl."""
    name = ""
    ts_type: str | None = None
    default: str | None = None
    access_modifier: str | None = None
    is_readonly = False

    # Track whether we've already seen identifier (for assignment default)
    seen_identifier = False

    for child in node.children:
        ctype = child.type
        if ctype == "accessibility_modifier":
            access_modifier = _text(child, src)
        elif ctype == "readonly":
            is_readonly = True
        elif ctype in ("identifier", "object_pattern", "array_pattern"):
            if not seen_identifier:
                name = _text(child, src)
                seen_identifier = True
        elif ctype == "type_annotation":
            # ": SomeType" — strip the leading ": "
            type_text = _text(child, src)
            ts_type = type_text.lstrip(":").strip()
        elif ctype in ("string", "number", "true", "false", "null", "undefined",
                       "array", "object", "template_string", "call_expression",
                       "identifier", "unary_expression", "binary_expression",
                       "new_expression"):
            # Only treat as default if it comes after "="
            pass
        elif ctype == "=":
            pass  # signals next child is the default

    # Re-scan to find default value (appears after "=")
    children = node.children
    for i, child in enumerate(children):
        if child.type == "=":
            # Everything after "=" is the default expression
            if i + 1 < len(children):
                default = _text(children[i + 1], src)
            break

    # If name is still empty, use full node text as fallback
    if not name:
        name = _text(node, src)

    return ParamDecl(
        name=name,
        ts_type=ts_type,
        default=default,
        is_readonly=is_readonly,
        access_modifier=access_modifier,
    )


# ---------------------------------------------------------------------------
# Method extraction
# ---------------------------------------------------------------------------

def _extract_method(node: Node, src: bytes, leading_decorators: list[DecoratorDecl] | None = None) -> MethodDecl:
    """Parse a method_definition node into MethodDecl."""
    name = ""
    params: list[ParamDecl] = []
    return_type: str | None = None
    body_text: str | None = None
    access_modifier: str | None = None
    is_async = False
    is_abstract = False
    decorators: list[DecoratorDecl] = leading_decorators or []

    for child in node.children:
        ctype = child.type
        if ctype == "accessibility_modifier":
            access_modifier = _text(child, src)
        elif ctype == "async":
            is_async = True
        elif ctype == "abstract":
            is_abstract = True
        elif ctype in ("property_identifier", "identifier", "string", "computed_property_name"):
            if not name:
                name = _text(child, src)
        elif ctype == "decorator":
            decorators.append(_extract_decorator(child, src))
        elif ctype == "formal_parameters":
            for param_child in child.children:
                if param_child.type in ("required_parameter", "optional_parameter", "rest_parameter"):
                    params.append(_extract_param(param_child, src))
        elif ctype == "type_annotation":
            type_text = _text(child, src)
            return_type = type_text.lstrip(":").strip()
        elif ctype == "statement_block":
            # Extract inner text (excluding outer braces)
            raw = _text(child, src)
            # raw starts with "{" and ends with "}"
            if raw.startswith("{") and raw.endswith("}"):
                body_text = raw[1:-1]
            else:
                body_text = raw

    return MethodDecl(
        name=name,
        params=params,
        return_type=return_type,
        body_text=body_text,
        access_modifier=access_modifier,
        is_async=is_async,
        is_abstract=is_abstract,
        decorators=decorators,
    )


# ---------------------------------------------------------------------------
# Field extraction
# ---------------------------------------------------------------------------

def _extract_field(node: Node, src: bytes, leading_decorators: list[DecoratorDecl] | None = None) -> FieldDecl | None:
    """Parse a public_field_definition node into FieldDecl.

    Returns None if the node appears to be an abstract method (no body, has parens).
    """
    name = ""
    ts_type: str | None = None
    initializer: str | None = None
    access_modifier: str | None = None
    is_readonly = False

    child_types = [c.type for c in node.children]

    # If the field has formal_parameters or ERROR node that looks like params,
    # it's likely an abstract method — skip as field
    if "formal_parameters" in child_types:
        return None

    seen_eq = False
    for child in node.children:
        ctype = child.type
        if ctype == "accessibility_modifier":
            access_modifier = _text(child, src)
        elif ctype == "readonly":
            is_readonly = True
        elif ctype in ("property_identifier", "identifier", "private_property_identifier"):
            if not name:
                name = _text(child, src)
        elif ctype == "type_annotation":
            type_text = _text(child, src)
            ts_type = type_text.lstrip(":").strip()
        elif ctype == "=":
            seen_eq = True
        elif seen_eq and ctype not in (";"," ", "\n"):
            if not initializer:
                initializer = _text(child, src)
        elif ctype in ("abstract", "static", "override", "declare"):
            pass  # modifiers we track or ignore

    if not name:
        return None

    return FieldDecl(
        name=name,
        ts_type=ts_type,
        initializer=initializer,
        access_modifier=access_modifier,
        is_readonly=is_readonly,
    )


# ---------------------------------------------------------------------------
# Class extraction
# ---------------------------------------------------------------------------

def _extract_class(node: Node, src: bytes, is_exported: bool = False, is_abstract: bool = False,
                   leading_decorators: list[DecoratorDecl] | None = None) -> ClassDecl:
    """Parse a class_declaration / abstract_class_declaration into ClassDecl."""
    name = ""
    base_class: str | None = None
    type_params: list[str] = []
    fields: list[FieldDecl] = []
    methods: list[MethodDecl] = []
    decorators: list[DecoratorDecl] = leading_decorators or []

    for child in node.children:
        ctype = child.type
        if ctype == "type_identifier":
            if not name:
                name = _text(child, src)
        elif ctype == "type_parameters":
            for tp in _children_by_type(child, "type_parameter"):
                tp_name = _child_by_type(tp, "type_identifier")
                if tp_name:
                    type_params.append(_text(tp_name, src))
        elif ctype == "class_heritage":
            extends = _child_by_type(child, "extends_clause")
            if extends:
                # Get the base class identifier (first identifier or type_identifier)
                for ec in extends.children:
                    if ec.type in ("identifier", "type_identifier"):
                        base_class = _text(ec, src)
                        break
        elif ctype == "class_body":
            _extract_class_body(child, src, fields, methods)

    return ClassDecl(
        name=name,
        base_class=base_class,
        type_params=type_params,
        fields=fields,
        methods=methods,
        decorators=decorators,
        is_abstract=is_abstract,
        is_exported=is_exported,
    )


def _extract_class_body(
    body_node: Node,
    src: bytes,
    fields: list[FieldDecl],
    methods: list[MethodDecl],
) -> None:
    """Walk class_body children and populate fields and methods lists."""
    # Collect decorators preceding each member
    pending_decorators: list[DecoratorDecl] = []

    for child in body_node.children:
        ctype = child.type
        if ctype == "decorator":
            pending_decorators.append(_extract_decorator(child, src))
        elif ctype == "method_definition":
            method = _extract_method(child, src, leading_decorators=pending_decorators)
            methods.append(method)
            pending_decorators = []
        elif ctype == "public_field_definition":
            # Could be a field or an abstract method
            field_or_none = _extract_field(child, src, leading_decorators=pending_decorators)
            if field_or_none is not None:
                fields.append(field_or_none)
            else:
                # Try to interpret as method (abstract)
                method = _extract_method(child, src, leading_decorators=pending_decorators)
                if method.name:
                    method.is_abstract = True
                    methods.append(method)
            pending_decorators = []
        elif ctype in ("{", "}", ";", "comment"):
            pending_decorators = []  # reset on structural tokens
        # Other node types (static_block, etc.) are ignored


# ---------------------------------------------------------------------------
# Top-level walk
# ---------------------------------------------------------------------------

def _walk_program(root: Node, src: bytes) -> tuple[list[ImportDecl], list[ClassDecl]]:
    imports: list[ImportDecl] = []
    classes: list[ClassDecl] = []

    def walk(node: Node, pending_decorators: list[DecoratorDecl]) -> list[DecoratorDecl]:
        ctype = node.type

        if ctype == "import_statement":
            imports.append(_extract_import(node, src))
            return []

        elif ctype == "decorator":
            pending_decorators.append(_extract_decorator(node, src))
            return pending_decorators

        elif ctype == "class_declaration":
            cls = _extract_class(node, src, is_exported=False, is_abstract=False,
                                  leading_decorators=pending_decorators)
            classes.append(cls)
            return []

        elif ctype == "abstract_class_declaration":
            cls = _extract_class(node, src, is_exported=False, is_abstract=True,
                                  leading_decorators=pending_decorators)
            classes.append(cls)
            return []

        elif ctype == "export_statement":
            # Might contain decorators + class declaration
            inner_decorators: list[DecoratorDecl] = list(pending_decorators)
            for child in node.children:
                if child.type == "decorator":
                    inner_decorators.append(_extract_decorator(child, src))
                elif child.type == "class_declaration":
                    cls = _extract_class(child, src, is_exported=True, is_abstract=False,
                                          leading_decorators=inner_decorators)
                    classes.append(cls)
                elif child.type == "abstract_class_declaration":
                    cls = _extract_class(child, src, is_exported=True, is_abstract=True,
                                          leading_decorators=inner_decorators)
                    classes.append(cls)
            return []

        else:
            # Recurse into children, threading decorators
            current_decorators = list(pending_decorators)
            for child in node.children:
                current_decorators = walk(child, current_decorators)
            return current_decorators

    walk(root, [])
    return imports, classes


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract(tree, source_bytes: bytes) -> ExtractionResult:
    """Walk tree-sitter Tree and extract all declarations."""
    imports, classes = _walk_program(tree.root_node, source_bytes)
    return ExtractionResult(imports=imports, classes=classes, source_bytes=source_bytes)
