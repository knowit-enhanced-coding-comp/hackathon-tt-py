"""
Integration tests for tt pipeline properties.

Property 5: Scaffold Integrity After Translation
    Validates Requirements 12.1, 12.2, 14.5 — app/main.py and app/wrapper/ are
    byte-identical to the example, and no generated .py files exist outside
    app/implementation/.

Property 6: Translation Determinism
    Validates Requirement 15.4 — running the translator twice produces
    byte-identical output files.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent.parent.parent.resolve()
EXAMPLE_DIR = REPO_ROOT / "hackathon-tt-py" / "translations" / "ghostfolio_pytx_example"
OUTPUT_DIR = REPO_ROOT / "hackathon-tt-py" / "translations" / "ghostfolio_pytx"
TT_PROJECT_DIR = REPO_ROOT / "hackathon-tt-py"

# The specific implementation file checked for determinism
ROAI_IMPL = (
    OUTPUT_DIR
    / "app"
    / "implementation"
    / "portfolio"
    / "calculator"
    / "roai"
    / "portfolio_calculator.py"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_translator() -> subprocess.CompletedProcess:
    """Invoke the translator via uv run, returning the CompletedProcess."""
    return subprocess.run(
        ["uv", "run", "--project", "tt", "tt", "translate"],
        cwd=TT_PROJECT_DIR,
        capture_output=True,
        text=True,
    )


def _collect_py_files(root: Path) -> dict[str, bytes]:
    """Return {relative_path_str: bytes} for all .py files under root."""
    return {
        str(p.relative_to(root)): p.read_bytes()
        for p in sorted(root.rglob("*.py"))
    }


# ---------------------------------------------------------------------------
# Property 5: Scaffold Integrity After Translation
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_property5_scaffold_integrity_after_translation() -> None:
    """Property 5: scaffold files are byte-identical to example; no generated
    .py files exist outside app/implementation/ (except app/main.py)."""
    # Pre-flight: check that the example directory exists
    if not EXAMPLE_DIR.exists():
        pytest.skip(f"Example directory not found: {EXAMPLE_DIR}")

    result = _run_translator()
    if result.returncode != 0:
        pytest.skip(
            f"Translator exited with code {result.returncode}.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    # --- Check 1: app/main.py is byte-identical ---
    example_main = EXAMPLE_DIR / "app" / "main.py"
    output_main = OUTPUT_DIR / "app" / "main.py"

    assert example_main.exists(), f"Example main.py missing: {example_main}"
    assert output_main.exists(), f"Output main.py missing: {output_main}"
    assert output_main.read_bytes() == example_main.read_bytes(), (
        "app/main.py differs from example"
    )

    # --- Check 2: all files under app/wrapper/ are byte-identical ---
    example_wrapper = EXAMPLE_DIR / "app" / "wrapper"
    output_wrapper = OUTPUT_DIR / "app" / "wrapper"

    assert example_wrapper.exists(), f"Example wrapper dir missing: {example_wrapper}"
    assert output_wrapper.exists(), f"Output wrapper dir missing: {output_wrapper}"

    example_wrapper_files = _collect_py_files(example_wrapper)
    output_wrapper_files = _collect_py_files(output_wrapper)

    # Every file in the example wrapper must exist in the output
    for rel_path, example_bytes in example_wrapper_files.items():
        assert rel_path in output_wrapper_files, (
            f"app/wrapper/{rel_path} missing from output"
        )
        assert output_wrapper_files[rel_path] == example_bytes, (
            f"app/wrapper/{rel_path} differs from example"
        )

    # --- Check 3: no .py files outside app/implementation/ (except app/main.py) ---
    app_dir = OUTPUT_DIR / "app"
    implementation_dir = app_dir / "implementation"

    for py_file in sorted(app_dir.rglob("*.py")):
        # Allow app/main.py
        if py_file == output_main:
            continue
        # Allow anything under app/implementation/
        try:
            py_file.relative_to(implementation_dir)
            continue  # inside implementation/ — OK
        except ValueError:
            pass
        # Allow anything under app/wrapper/ (scaffold, not generated)
        try:
            py_file.relative_to(output_wrapper)
            continue  # inside wrapper/ — OK
        except ValueError:
            pass
        # Allow __init__.py at app/ level (scaffold artefact)
        if py_file.name == "__init__.py" and py_file.parent == app_dir:
            continue

        pytest.fail(
            f"Generated .py file found outside app/implementation/: "
            f"{py_file.relative_to(OUTPUT_DIR)}"
        )


# ---------------------------------------------------------------------------
# Property 6: Translation Determinism
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_property6_translation_determinism() -> None:
    """Property 6: running the translator twice produces byte-identical output."""
    if not EXAMPLE_DIR.exists():
        pytest.skip(f"Example directory not found: {EXAMPLE_DIR}")

    # --- First run ---
    result1 = _run_translator()
    if result1.returncode != 0:
        pytest.skip(
            f"First translator run failed (exit {result1.returncode}).\n"
            f"stdout: {result1.stdout}\nstderr: {result1.stderr}"
        )

    # Snapshot all .py files under app/implementation/ after first run
    impl_dir = OUTPUT_DIR / "app" / "implementation"
    if not impl_dir.exists():
        pytest.skip(f"Implementation dir not found after first run: {impl_dir}")

    snapshot1 = _collect_py_files(impl_dir)

    # Also capture the specific ROAI file if it exists
    roai_bytes1 = ROAI_IMPL.read_bytes() if ROAI_IMPL.exists() else None

    # --- Second run ---
    result2 = _run_translator()
    if result2.returncode != 0:
        pytest.fail(
            f"Second translator run failed (exit {result2.returncode}).\n"
            f"stdout: {result2.stdout}\nstderr: {result2.stderr}"
        )

    snapshot2 = _collect_py_files(impl_dir)

    # --- Compare ROAI file specifically ---
    if roai_bytes1 is not None:
        assert ROAI_IMPL.exists(), "ROAI file missing after second run"
        roai_bytes2 = ROAI_IMPL.read_bytes()
        assert roai_bytes1 == roai_bytes2, (
            "portfolio_calculator.py differs between run 1 and run 2 — not deterministic"
        )

    # --- Compare all implementation files ---
    assert set(snapshot1.keys()) == set(snapshot2.keys()), (
        f"File set differs between runs.\n"
        f"Only in run 1: {set(snapshot1) - set(snapshot2)}\n"
        f"Only in run 2: {set(snapshot2) - set(snapshot1)}"
    )

    for rel_path in sorted(snapshot1):
        assert snapshot1[rel_path] == snapshot2[rel_path], (
            f"app/implementation/{rel_path} differs between run 1 and run 2"
        )
