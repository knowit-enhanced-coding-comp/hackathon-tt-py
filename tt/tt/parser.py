"""Layer 1: TypeScript parser using tree-sitter."""

from functools import lru_cache
from pathlib import Path

import tree_sitter_typescript as tst
from tree_sitter import Language, Parser, Tree, Node


@lru_cache(maxsize=1)
def get_language() -> Language:
    """Return the TypeScript Language object (cached)."""
    return Language(tst.language_typescript())


def _get_parser() -> Parser:
    """Create a parser instance with the TypeScript language."""
    return Parser(get_language())


def parse_string(source: str) -> Tree:
    """Parse TypeScript source string → tree-sitter Tree."""
    parser = _get_parser()
    return parser.parse(source.encode("utf-8"))


def parse_file(path: Path) -> Tree:
    """Parse a TypeScript file → tree-sitter Tree."""
    source = Path(path).read_bytes()
    parser = _get_parser()
    return parser.parse(source)


def get_node_text(node: Node, source: bytes) -> str:
    """Extract text of a tree-sitter node from source bytes."""
    return source[node.start_byte:node.end_byte].decode("utf-8")
