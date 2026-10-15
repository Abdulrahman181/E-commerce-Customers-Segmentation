#!/usr/bin/env python3
"""Static checks for the repository notebook; does not execute the data workflow."""
from __future__ import annotations

import ast
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

NOTEBOOK = Path(__file__).resolve().parents[1] / "E-commerce-Customers.ipynb"
WINDOWS_PATH = re.compile(r"(?:[A-Za-z]:\\\\|C:/|/Users/|OneDrive)", re.IGNORECASE)


def _cell_source(cell: dict[str, Any], index: int, errors: list[str]) -> str:
    source = cell.get("source", "")
    if isinstance(source, list) and all(isinstance(line, str) for line in source):
        return "".join(source)
    if isinstance(source, str):
        return source
    errors.append(f"cell {index}: source must be a string or list of strings")
    return ""


def validate_notebook(notebook: dict[str, Any]) -> list[str]:
    """Return actionable structural, syntax, and portability errors."""
    errors: list[str] = []
    if notebook.get("nbformat") != 4 or not isinstance(notebook.get("cells"), list):
        return ["notebook is not a valid nbformat 4 document"]

    python_sources: list[str] = []
    for index, cell in enumerate(notebook["cells"]):
        if not isinstance(cell, dict):
            errors.append(f"cell {index}: cell must be an object")
            continue
        cell_type = cell.get("cell_type")
        if cell_type not in {"code", "markdown", "raw"}:
            errors.append(f"cell {index}: unsupported cell_type {cell_type!r}")
        source = _cell_source(cell, index, errors)
        if WINDOWS_PATH.search(source):
            errors.append(f"cell {index}: machine-specific path detected")
        if cell_type == "code":
            if not isinstance(cell.get("outputs"), list):
                errors.append(f"cell {index}: code cell outputs must be a list")
            elif cell["outputs"]:
                errors.append(f"cell {index}: saved outputs must be cleared")
            if cell.get("execution_count") is not None:
                errors.append(f"cell {index}: execution_count must be null")
            try:
                ast.parse(source, filename=f"{NOTEBOOK.name}:cell-{index}")
            except SyntaxError as exc:
                errors.append(f"cell {index}: syntax error: {exc}")
            python_sources.append(f"# notebook cell {index}\n{source}\n")

    if shutil.which("ruff") and python_sources:
        with tempfile.TemporaryDirectory() as temporary_directory:
            extracted = Path(temporary_directory) / "notebook_cells.py"
            extracted.write_text("\n".join(python_sources), encoding="utf-8")
            result = subprocess.run(
                ["ruff", "check", "--select", "E9,F821", str(extracted)],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode:
                errors.append("ruff reported errors:\n" + result.stdout + result.stderr)
    return errors


def main() -> int:
    try:
        notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read {NOTEBOOK}: {exc}", file=sys.stderr)
        return 1

    errors = validate_notebook(notebook)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    code_cells = sum(cell.get("cell_type") == "code" for cell in notebook["cells"])
    print(
        f"OK: {NOTEBOOK.name}; {code_cells} code cells parsed; "
        "no saved outputs or portability violations"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
