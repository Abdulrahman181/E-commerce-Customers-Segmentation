from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from scripts.validate_notebook import validate_notebook


REPO = Path(__file__).resolve().parents[1]
NOTEBOOK = REPO / "E-commerce-Customers.ipynb"


class RepositoryTests(unittest.TestCase):
    def test_notebook_has_no_saved_state_or_static_errors(self) -> None:
        notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
        self.assertEqual(validate_notebook(notebook), [])
        self.assertTrue(notebook["cells"])
        for cell in notebook["cells"]:
            if cell["cell_type"] == "code":
                self.assertEqual(cell["outputs"], [])
                self.assertIsNone(cell["execution_count"])

    def test_requirements_cover_both_excel_extensions(self) -> None:
        requirements = (REPO / "requirements.txt").read_text(encoding="utf-8")
        self.assertIn("openpyxl", requirements)
        self.assertIn("xlrd", requirements)

    def test_notebook_runs_on_a_small_valid_workbook(self) -> None:
        transactions = pd.DataFrame(
            {
                "transaction_id": [f"t{i}" for i in range(1, 13)],
                "customer_id": [f"c{i}" for i in [1, 2, 3, 4, 5, 6, 1, 2, 3, 4, 5, 6]],
                "transaction_date": pd.to_datetime(
                    [
                        "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05", "2024-01-06", "2024-01-07",
                        "2024-02-02", "2024-02-03", "2024-02-04", "2024-02-05", "2024-02-06", "2024-02-07",
                    ]
                ),
                "transaction_status": ["used", "burnt", "used", "used", "burned", "used"] * 2,
                "coupon_name": ["coupon"] * 12,
                "burn_date": pd.to_datetime(
                    ["2024-01-10", None, "2024-01-11", None, "2024-01-12", None,
                     "2024-02-10", None, "2024-02-11", None, "2024-02-12", None]
                ),
                "branch_id": ["b1"] * 12,
            }
        )
        customers = pd.DataFrame(
            {
                "customer_id": [f"c{i}" for i in range(1, 7)],
                "join_date": pd.to_datetime(["2024-01-01"] * 6),
                "city_id": ["city"] * 6,
                "gender_id": ["gender"] * 6,
            }
        )
        genders = pd.DataFrame({"gender_id": ["gender"], "gender_name": ["Unknown"]})
        cities = pd.DataFrame({"city_id": ["city"], "city_name": ["Example"]})
        branches = pd.DataFrame({"branch_id": ["b1"], "merchant_id": ["m1"]})
        merchants = pd.DataFrame({"merchant_id": ["m1"], "merchant_name": ["Example merchant"]})

        with tempfile.TemporaryDirectory() as temporary_directory:
            workbook_path = Path(temporary_directory) / "E-commerce_data.xlsx"
            with pd.ExcelWriter(workbook_path, engine="openpyxl") as writer:
                for name, table in {
                    "transactions": transactions,
                    "customers": customers,
                    "genders": genders,
                    "cities": cities,
                    "branches": branches,
                    "merchants": merchants,
                }.items():
                    table.to_excel(writer, sheet_name=name, index=False)

            notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
            source = "\n\n".join(
                "".join(cell["source"])
                for cell in notebook["cells"]
                if cell["cell_type"] == "code"
            )
            old_value = os.environ.get("ECOMMERCE_DATA_FILE")
            os.environ["ECOMMERCE_DATA_FILE"] = str(workbook_path)
            old_backend = os.environ.get("MPLBACKEND")
            os.environ["MPLBACKEND"] = "Agg"
            try:
                namespace: dict[str, object] = {}
                exec(compile(source, str(NOTEBOOK), "exec"), namespace)
            finally:
                if old_value is None:
                    os.environ.pop("ECOMMERCE_DATA_FILE", None)
                else:
                    os.environ["ECOMMERCE_DATA_FILE"] = old_value
                if old_backend is None:
                    os.environ.pop("MPLBACKEND", None)
                else:
                    os.environ["MPLBACKEND"] = old_backend

            model_data = namespace["model_data"]
            self.assertEqual(len(model_data), 6)
            self.assertEqual(set(model_data["transaction_count"]), {2})
            self.assertIn("kmeans_cluster", model_data.columns)
            self.assertIn("dbscan_cluster", model_data.columns)
            self.assertIn("hierarchical_cluster", model_data.columns)


if __name__ == "__main__":
    unittest.main()
