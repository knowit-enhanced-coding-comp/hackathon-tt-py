"""
TypeScript AST parser using tree-sitter.

Parses TypeScript source files into tree-sitter ASTs and extracts
structured information about imports, classes, and methods.
"""
from __future__ import annotations

import logging
from pathlib import Path

import tree_sitter_typescript as ts_typescript
from tree_sitter import Language, Node, Parser, Tree

logger = logging.getLogger(__name__)

# Build the TypeScript language once at module load
_TS_LANGUAGE = Language(ts_typescript.language_typescript())
_PARSER = Parser(_TS_LANGUAGE)


def parse_file(path: Path) -> Tree:
    """Parse a TypeScript file into a tree-sitter AST.

    Args:
        path: Path to the TypeScript source file.

    Returns:
        The tree-sitter Tree for the file.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    source = path.read_bytes()
    tree = _PARSER.parse(source)
    if tree.root_node.has_error:
        logger.warning("Parse errors detected in %s", path)
    return tree


def _node_text(node: Node, source: bytes) -> str:
    """Extract the UTF-8 text of a node from the source bytes."""
    return source[node.start_byte:node.end_byte].decode("utf-8")


def extract_imports(root: Node) -> list[dict]:
    """Extract import statements from a TypeScript AST root node.

    Args:
        root: The root node of a tree-sitter TypeScript AST.

    Returns:
        A list of dicts, each with:
            - ``module_path`` (str): The imported module path string.
            - ``symbols`` (list[str]): Named symbols imported from the module.
    """
    source = root.text if hasattr(root, "text") else b""
    # Reconstruct source bytes from the root node's own text attribute
    # (tree-sitter Node.text is available when the tree was parsed from bytes)
    results: list[dict] = []

    for node in root.children:
        if node.type != "import_statement":
            continue
        try:
            module_path = _extract_import_module(node)
            symbols = _extract_import_symbols(node)
            results.append({"module_path": module_path, "symbols": symbols})
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not parse import node at line %d: %s", node.start_point[0] + 1, exc)

    return results


def _extract_import_module(node: Node) -> str:
    """Return the module path string from an import_statement node."""
    for child in node.children:
        if child.type == "string":
            # Strip surrounding quotes
            raw = child.text.decode("utf-8") if isinstance(child.text, bytes) else child.text
            return raw.strip("'\"")
    return ""


def _extract_import_symbols(node: Node) -> list[str]:
    """Return the list of named symbols from an import_statement node."""
    symbols: list[str] = []
    for child in node.children:
        if child.type == "import_clause":
            symbols.extend(_symbols_from_import_clause(child))
    return symbols


def _symbols_from_import_clause(clause: Node) -> list[str]:
    """Recursively collect symbol names from an import_clause node."""
    symbols: list[str] = []
    for child in clause.children:
        if child.type == "named_imports":
            for item in child.children:
                if item.type == "import_specifier":
                    # First identifier child is the imported name
                    for ident in item.children:
                        if ident.type == "identifier":
                            name = ident.text
                            if isinstance(name, bytes):
                                name = name.decode("utf-8")
                            symbols.append(name)
                            break
        elif child.type == "identifier":
            # Default import: `import Foo from '...'`
            name = child.text
            if isinstance(name, bytes):
                name = name.decode("utf-8")
            symbols.append(name)
        elif child.type == "namespace_import":
            # `import * as Foo from '...'`
            for ident in child.children:
                if ident.type == "identifier":
                    name = ident.text
                    if isinstance(name, bytes):
                        name = name.decode("utf-8")
                    symbols.append(f"* as {name}")
                    break
    return symbols


def extract_classes(root: Node) -> list[dict]:
    """Extract class declarations from a TypeScript AST root node.

    Walks the top-level statements and any export declarations to find
    class definitions.

    Args:
        root: The root node of a tree-sitter TypeScript AST.

    Returns:
        A list of dicts, each with:
            - ``name`` (str): The class name.
            - ``base_class`` (str | None): The name of the extended class, or None.
            - ``node`` (Node): The tree-sitter class_declaration node.
    """
    results: list[dict] = []

    def _visit(node: Node) -> None:
        if node.type in ("class_declaration", "class", "abstract_class_declaration"):
            try:
                info = _parse_class_node(node)
                results.append(info)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Could not parse class node at line %d: %s", node.start_point[0] + 1, exc)
            return  # don't recurse into class body here

        # Recurse into export statements and the program root
        if node.type in ("program", "export_statement"):
            for child in node.children:
                _visit(child)

    _visit(root)
    return results


def _parse_class_node(node: Node) -> dict:
    """Extract name, base_class, and node from a class_declaration node."""
    name: str | None = None
    base_class: str | None = None

    for child in node.children:
        if child.type == "type_identifier" and name is None:
            raw = child.text
            name = raw.decode("utf-8") if isinstance(raw, bytes) else raw
        elif child.type == "class_heritage":
            base_class = _extract_base_class(child)

    if name is None:
        raise ValueError(f"Class node at line {node.start_point[0] + 1} has no name")

    return {"name": name, "base_class": base_class, "node": node}


def _extract_base_class(heritage_node: Node) -> str | None:
    """Return the first extended class name from a class_heritage node."""
    for child in heritage_node.children:
        if child.type == "extends_clause":
            for item in child.children:
                if item.type in ("identifier", "type_identifier"):
                    raw = item.text
                    return raw.decode("utf-8") if isinstance(raw, bytes) else raw
    return None


def extract_methods(class_node: Node) -> list[dict]:
    """Extract method declarations from a class body node.

    Args:
        class_node: A tree-sitter class_declaration (or abstract_class_declaration) node.

    Returns:
        A list of dicts, each with:
            - ``name`` (str): The method name.
            - ``params`` (list[str]): Parameter names (without type annotations).
            - ``return_type`` (str | None): The declared return type, or None.
            - ``body_node`` (Node | None): The statement_block node for the body, or None
              for abstract methods.
            - ``access`` (str): One of ``"public"``, ``"protected"``, or ``"private"``.
    """
    results: list[dict] = []

    # Find the class_body child
    body: Node | None = None
    for child in class_node.children:
        if child.type == "class_body":
            body = child
            break

    if body is None:
        return results

    for member in body.children:
        if member.type in (
            "method_definition",
            "abstract_method_signature",
            "public_field_definition",
        ):
            try:
                info = _parse_method_node(member)
                if info is not None:
                    results.append(info)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Could not parse method at line %d: %s",
                    member.start_point[0] + 1,
                    exc,
                )

    return results


def _parse_method_node(node: Node) -> dict | None:
    """Extract method metadata from a method_definition or abstract_method_signature."""
    name: str | None = None
    params: list[str] = []
    return_type: str | None = None
    body_node: Node | None = None
    access = "public"

    for child in node.children:
        raw = child.text
        text = raw.decode("utf-8") if isinstance(raw, bytes) else (raw or "")

        if child.type == "accessibility_modifier":
            access = text.strip()
        elif child.type in ("property_identifier", "identifier"):
            if name is None:
                name = text
        elif child.type == "formal_parameters":
            params = _extract_params(child)
        elif child.type == "type_annotation":
            return_type = _extract_type_annotation(child)
        elif child.type == "statement_block":
            body_node = child

    if name is None:
        return None

    return {
        "name": name,
        "params": params,
        "return_type": return_type,
        "body_node": body_node,
        "access": access,
    }


def _extract_params(params_node: Node) -> list[str]:
    """Return a list of parameter names from a formal_parameters node."""
    names: list[str] = []
    for child in params_node.children:
        if child.type in ("required_parameter", "optional_parameter", "rest_pattern"):
            # First identifier child is the param name
            for sub in child.children:
                if sub.type in ("identifier", "object_pattern", "array_pattern"):
                    raw = sub.text
                    names.append(raw.decode("utf-8") if isinstance(raw, bytes) else raw)
                    break
        elif child.type == "identifier":
            raw = child.text
            names.append(raw.decode("utf-8") if isinstance(raw, bytes) else raw)
    return names


def _extract_type_annotation(node: Node) -> str | None:
    """Return the type string from a type_annotation node (strips the leading colon)."""
    parts: list[str] = []
    for child in node.children:
        if child.type == ":":
            continue
        raw = child.text
        text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
        if text:
            parts.append(text)
    return " ".join(parts) if parts else None
