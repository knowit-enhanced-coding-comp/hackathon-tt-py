"""Layer 0: Repository inspector — discovers TS files and reads project config."""

from dataclasses import dataclass, field
from pathlib import Path
import json


@dataclass
class TranslationTarget:
    ts_path: Path
    output_path: Path  # absolute path in output dir


@dataclass
class TranslationManifest:
    targets: list[TranslationTarget] = field(default_factory=list)
    import_map: dict[str, str] = field(default_factory=dict)  # TS module path -> Python module path


def discover_targets(
    source_root: Path,
    output_root: Path,
    *,
    exclude_patterns: list[str] | None = None,
) -> list[TranslationTarget]:
    """Walk source_root for .ts files (excluding .spec.ts and .d.ts) and return targets."""
    exclude_patterns = exclude_patterns or []
    targets = []

    for ts_file in sorted(source_root.rglob("*.ts")):
        name = ts_file.name
        # Always exclude spec and declaration files
        if name.endswith(".spec.ts") or name.endswith(".d.ts"):
            continue

        # Check user-provided exclude patterns against the relative path string
        rel = ts_file.relative_to(source_root)
        rel_str = str(rel)
        skip = False
        for pattern in exclude_patterns:
            if rel.match(pattern) or ts_file.match(pattern):
                skip = True
                break
            # Simple substring match as fallback
            if pattern in rel_str:
                skip = True
                break
        if skip:
            continue

        # Compute output path: same relative structure but with .py extension
        rel_py = rel.with_suffix(".py")
        output_path = output_root / rel_py

        targets.append(TranslationTarget(ts_path=ts_file.resolve(), output_path=output_path.resolve()))

    return targets


def load_import_map(map_file: Path) -> dict[str, str]:
    """Load tt_import_map.json from scaffold directory."""
    if not map_file.exists():
        return {}
    with map_file.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        return {}
    return {str(k): str(v) for k, v in data.items()}


def build_manifest(
    source_root: Path,
    output_root: Path,
    import_map_file: Path | None = None,
) -> TranslationManifest:
    """Build a full TranslationManifest from source root."""
    targets = discover_targets(source_root, output_root)
    import_map: dict[str, str] = {}
    if import_map_file is not None:
        import_map = load_import_map(import_map_file)
    return TranslationManifest(targets=targets, import_map=import_map)
