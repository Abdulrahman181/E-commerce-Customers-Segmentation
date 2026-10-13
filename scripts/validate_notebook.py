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

NOTEBOOK = Path(__file__).resolve().parents[1] / "E-commerce-Customers.ipynb"
WINDOWS_PATH = re.compile(r"(?:[A-Za-z]:\\\\|C:/|/Users/|OneDrive)", re.IGNORECASE)


def main() -> int:
    try:
        notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read {NOTEBOOK}: {exc}", file=sys.stderr)
        return 1

    if notebook.get("nbformat") != 4 or not isinstance(notebook.get("cells"), list):
        print("ERROR: notebook is not a valid nbformat 4 document", file=sys.stderr)
        return 1

    python_sources: list[str] = []
    errors: list[str] = []
    for index, cell in enumerate(notebook["cells"]):
        if cell.get("cell_type") != "code":
            continue
        if cell.get("outputs"):
            errors.append(f"cell {index}: saved outputs must be cleared")
        if cell.get("execution_count") is not None:
            errors.append(f"cell {index}: execution_count must be null")
        source = "".join(cell.get("source", []))
        if WINDOWS_PATH.search(source):
            errors.append(f"cell {index}: machine-specific path detected")
        try:
            ast.parse(source, filename=f"{NOTEBOOK.name}:cell-{index}")
        except SyntaxError as exc:
            errors.append(f"cell {index}: syntax error: {exc}")
        python_sources.append(f"# notebook cell {index}\n{source}\n")

    if shutil.which("ruff"):
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

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"OK: {NOTEBOOK.name}; {len(python_sources)} code cells parsed; no saved outputs or portability violations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
