"""Run the reproducible customer segmentation workflow with ``python -m customer_segmentation``."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .pipeline import fit_and_evaluate, load_customer_features, write_artifacts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    default_workbook = os.environ.get("ECOMMERCE_DATA_PATH", "E-commerce_data.xlsx")
    parser.add_argument(
        "--workbook", type=Path, default=default_workbook, help="Authorized local .xlsx/.xlsm input"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts"),
        help="Private local artifact directory",
    )
    parser.add_argument("--min-clusters", type=int, default=2)
    parser.add_argument("--max-clusters", type=int, default=5)
    parser.add_argument("--validation-size", type=float, default=0.2)
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--random-state", type=int, default=42)
    args = parser.parse_args(argv)
    try:
        features = load_customer_features(args.workbook)
        model, metrics = fit_and_evaluate(
            features,
            min_clusters=args.min_clusters,
            max_clusters=args.max_clusters,
            validation_size=args.validation_size,
            test_size=args.test_size,
            random_state=args.random_state,
        )
        paths = write_artifacts(args.output_dir, model, metrics)
    except (FileNotFoundError, OSError, ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    report = {**metrics, "artifacts": {name: str(path) for name, path in paths.items()}}
    print(json.dumps(report, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
