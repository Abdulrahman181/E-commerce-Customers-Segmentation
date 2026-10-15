# E-commerce Customers Segmentation

This repository contains an exploratory customer-segmentation notebook for the six-table e-commerce coupon dataset. The workflow joins transactions to customer, gender, city, branch, and merchant dimensions, aggregates to **one row per customer**, and compares K-Means, DBSCAN, and agglomerative clustering.

## Repository contents

- `E-commerce-Customers.ipynb` — portable, output-free notebook with schema checks and deterministic model settings.
- `E-commerce_data.xlsx.pdf` — tracked PDF export/reference only; it is **not** an executable Excel workbook and is not read by the notebook.
- `requirements.txt` — Python dependencies.
- `scripts/validate_notebook.py` — static validation for notebook structure/syntax, Ruff `E9/F821` errors, stale outputs, and machine-specific paths.
- `tests/test_repository.py` — repository checks plus a synthetic-workbook runtime smoke test; it does not report metrics for the real dataset.
- `ENGINEERING_REVIEW.md` — engineering audit, fixes, validation results, and limitations.

## Data contract and setup

The notebook requires an `.xlsx` or `.xls` workbook with these sheets and columns:

| Sheet | Required columns |
| --- | --- |
| `transactions` | `transaction_id`, `customer_id`, `transaction_date`, `transaction_status`, `coupon_name`, `burn_date`, `branch_id` |
| `customers` | `customer_id`, `join_date`, `city_id`, `gender_id` |
| `genders` | `gender_id`, `gender_name` |
| `cities` | `city_id`, `city_name` |
| `branches` | `branch_id`, `merchant_id` |
| `merchants` | `merchant_id`, `merchant_name` |

The workbook is intentionally not fabricated or reconstructed from the PDF. Obtain the original workbook separately, then either:

1. set `ECOMMERCE_DATA_FILE=/absolute/path/to/E-commerce_data.xlsx`, or
2. place `E-commerce_data.xlsx` in the repository root or `data/` directory.

If no workbook is available, the notebook raises a clear `FileNotFoundError` and does not claim to have produced model results.

## Install and run

```bash
python -m venv .venv
. .venv/bin/activate                 # Windows: .venv\\Scripts\\activate
python -m pip install -r requirements.txt
python scripts/validate_notebook.py
jupyter notebook E-commerce-Customers.ipynb
```

Run Jupyter from the repository root, or use `ECOMMERCE_DATA_FILE` when working elsewhere. The notebook uses `random_state=42` and explicit `n_init=10` for K-Means. It clears outputs before commit so results are generated only from the supplied workbook and installed environment. The `.xls` option requires the declared `xlrd` dependency; `.xlsx` uses `openpyxl`.

Run the repository checks with:

```bash
python scripts/validate_notebook.py
python -m unittest discover -s tests -v
```

## Methodology and limitations

- Transactions and dimension tables are checked for required columns, non-null keys, and unique primary keys before joining. Joins also use `validate="many_to_one"` and fail on unmatched foreign keys.
- Dates are parsed with coercion and coupon status is normalized (`burnt` is treated as `burned`).
- Invalid non-null dates and transactions dated before a customer's join date fail validation instead of silently entering incomplete features.
- Segmentation is performed at customer level using transaction count, coupons used, coupon-use rate, and days since joining. This avoids overweighting customers with many transaction rows.
- This is unsupervised descriptive analysis, so there is no target-based train/test split. The scaler is fit once on the complete population being segmented. A production scoring system should use a temporal holdout and a persisted preprocessing/model pipeline.
- Customers with no transactions are not represented in transaction-derived features and require a separate business rule if they must be segmented.
- No numerical findings are asserted in this README because the executable workbook is not present in the repository.
