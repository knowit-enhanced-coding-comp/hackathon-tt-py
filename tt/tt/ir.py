"""Layer 3: Intermediate representation — decoupled from tree-sitter nodes."""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class ImportIR:
    source: str
    names: list[tuple[str, str | None]] = field(default_factory=list)  # (name, alias)
    default_name: str | None = None


@dataclass
class ParamIR:
    name: str
    ts_type: str | None = None
    default: str | None = None
    access_modifier: str | None = None  # for constructor shorthand
    is_readonly: bool = False


@dataclass
class DecoratorIR:
    name: str
    args_text: str | None = None


@dataclass
class FieldIR:
    name: str
    ts_type: str | None = None
    initializer_text: str | None = None
    access_modifier: str | None = None
    is_readonly: bool = False


@dataclass
class MethodIR:
    name: str
    params: list[ParamIR] = field(default_factory=list)
    return_type: str | None = None
    body_text: str | None = None
    access_modifier: str | None = None
    is_async: bool = False
    is_abstract: bool = False
    decorators: list[DecoratorIR] = field(default_factory=list)


@dataclass
class ClassIR:
    name: str
    bases: list[str] = field(default_factory=list)
    fields: list[FieldIR] = field(default_factory=list)
    methods: list[MethodIR] = field(default_factory=list)
    decorators: list[DecoratorIR] = field(default_factory=list)
    is_abstract: bool = False
    di_metadata: dict = field(default_factory=dict)


@dataclass
class ModuleIR:
    source_path: str
    imports: list[ImportIR] = field(default_factory=list)
    classes: list[ClassIR] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Conversion helpers
# ---------------------------------------------------------------------------

def _convert_decorator(d: "DecoratorDecl") -> DecoratorIR:
    return DecoratorIR(name=d.name, args_text=d.args_text)


def _convert_param(p: "ParamDecl") -> ParamIR:
    return ParamIR(
        name=p.name,
        ts_type=p.ts_type,
        default=p.default,
        access_modifier=p.access_modifier,
        is_readonly=p.is_readonly,
    )


def _convert_field(f: "FieldDecl") -> FieldIR:
    return FieldIR(
        name=f.name,
        ts_type=f.ts_type,
        initializer_text=f.initializer,
        access_modifier=f.access_modifier,
        is_readonly=f.is_readonly,
    )


def _convert_method(m: "MethodDecl") -> MethodIR:
    return MethodIR(
        name=m.name,
        params=[_convert_param(p) for p in m.params],
        return_type=m.return_type,
        body_text=m.body_text,
        access_modifier=m.access_modifier,
        is_async=m.is_async,
        is_abstract=m.is_abstract,
        decorators=[_convert_decorator(d) for d in m.decorators],
    )


def _convert_import(imp: "ImportDecl") -> ImportIR:
    return ImportIR(
        source=imp.source,
        names=[(n.name, n.alias) for n in imp.names],
        default_name=imp.default_name,
    )


def _convert_class(cls: "ClassDecl") -> ClassIR:
    bases: list[str] = []
    if cls.base_class:
        bases.append(cls.base_class)

    return ClassIR(
        name=cls.name,
        bases=bases,
        fields=[_convert_field(f) for f in cls.fields],
        methods=[_convert_method(m) for m in cls.methods],
        decorators=[_convert_decorator(d) for d in cls.decorators],
        is_abstract=cls.is_abstract,
        di_metadata={},
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_ir(extraction: "ExtractionResult", source_path: str = "") -> ModuleIR:
    """Convert ExtractionResult → ModuleIR."""
    from tt.extractor import ExtractionResult, ImportDecl, ClassDecl, MethodDecl, FieldDecl  # noqa: F401

    return ModuleIR(
        source_path=source_path,
        imports=[_convert_import(imp) for imp in extraction.imports],
        classes=[_convert_class(cls) for cls in extraction.classes],
    )
