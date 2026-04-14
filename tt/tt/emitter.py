"""Python source code emitter with indentation tracking.

Provides a simple API for building Python source code line-by-line
with automatic indentation management.
"""

from __future__ import annotations


class PythonEmitter:
    """Accumulates Python source lines with managed indentation."""

    def __init__(self, indent_unit: str = "    ") -> None:
        self._lines: list[str] = []
        self._indent_level: int = 0
        self._indent_unit = indent_unit

    @property
    def prefix(self) -> str:
        return self._indent_unit * self._indent_level

    def indent(self) -> None:
        """Increase indentation by one level."""
        self._indent_level += 1

    def dedent(self) -> None:
        """Decrease indentation by one level."""
        if self._indent_level > 0:
            self._indent_level -= 1

    def emit(self, line: str) -> None:
        """Emit a single line at the current indentation level."""
        self._lines.append(self.prefix + line)

    def emit_raw(self, line: str) -> None:
        """Emit a line without adding indentation prefix."""
        self._lines.append(line)

    def emit_blank(self) -> None:
        """Emit a blank line."""
        self._lines.append("")

    def get_code(self) -> str:
        """Return all accumulated lines joined with newlines."""
        return "\n".join(self._lines) + "\n"

    def line_count(self) -> int:
        return len(self._lines)
