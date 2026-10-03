# E-commerce Customers Segmentation

This repository contains an exploratory Jupyter notebook and a small, reproducible K-Means workflow for customer-level exploratory segmentation. It does not contain a stakeholder dashboard, deployed service, or validated business segmentation.

## Dataset and privacy

The analysis expects an authorized Excel workbook with worksheets named `transactions`, `customers`, `genders`, `cities`, `branches`, and `merchants`. The tracked `E-commerce_data.xlsx.pdf` is a PDF export, not an Excel workbook. The required workbook is **not included**, so neither the notebook nor the model workflow can be run end-to-end from a fresh clone. Do not substitute the PDF or an invented dataset.

Use only a workbook you are authorized to access. Keep it local: the expected workbook, generated artifacts, and notebook checkpoint/output files are ignored by Git. The modelling workflow writes only aggregate JSON metadata/metrics and a fitted model, never customer-level assignments or identifiers. Model parameters and aggregate statistics can still be sensitive; treat the entire `artifacts/` directory as private and do not commit or share it. Only load model files that you created or otherwise trust (joblib files can execute code when loaded).

## Setup

Python 3.11 is used in CI. From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

To run the exploratory notebook, set the input path before launching Jupyter:

```bash
export ECOMMERCE_DATA_PATH="/path/to/your/E-commerce_data.xlsx"
jupyter lab E-commerce-Customers.ipynb
```

The notebook is for local descriptive exploration. It does not save a row-level export, and saved outputs are cleared in the committed version. Avoid saving or committing notebook outputs that may contain confidential source data.

## Reproducible customer-level clustering

The Python workflow reads the six-sheet workbook, validates the required transaction/customer columns and join cardinality, rejects invalid chronology, and derives one row per customer from `coupon_used_rate` and `mean_days_since_join`. These features are per-customer means of transaction-level coupon-use indicators and days since joining. The workflow deliberately excludes row-level IDs from model features and output JSON.

Run it with the environment variable above or an explicit path:

```bash
python -m customer_segmentation \
  --workbook "$ECOMMERCE_DATA_PATH" \
  --output-dir artifacts \
  --min-clusters 2 \
  --max-clusters 5 \
  --random-state 42
```

A deterministic customer-disjoint train/validation/test split is used. The scaler and candidate K-Means models are fit on train only; the candidate cluster count is selected using validation silhouette; the selected pipeline is refit on train plus validation; and test is held out from selection and fit. The test silhouette is reported once when its assigned labels permit calculation. Silhouette is only a geometric diagnostic for unsupervised clusters—not predictive accuracy, external validation, proof of segment stability, or evidence of business value. No segment count or result is asserted in advance. Very small or poorly separated datasets may not yield a valid score; the workflow then reports a clear error instead of inventing a result.

Outputs are written to the ignored `artifacts/` directory:

- `customer_segmentation.joblib` — fitted preprocessing and K-Means model
- `feature_schema.json` — feature definitions, split/model metadata, and library version
- `metrics.json` — selected candidate validation score and held-out descriptive metric

The dependency ranges in `requirements.txt` are compatibility bounds, not a fully resolved lock file. `requirements-dev.txt` adds test/lint tools. `openpyxl` reads Excel workbooks.

## Checks

```bash
python -m pip install -r requirements-dev.txt
python -m pip check
ruff check .
python -m pytest -q
```

Tests use synthetic fixtures only to verify code behavior; they are not dataset results or external validation.

## Repository contents

- `E-commerce-Customers.ipynb` — exploratory notebook; modelling is delegated to the leakage-aware CLI workflow above
- `customer_segmentation/` — validated loader, customer feature aggregation, split/evaluation, and artifact writer
- `tests/` — synthetic regression tests
- `.github/workflows/ci.yml` — lint, test, and dependency-consistency checks
- `E-commerce_data.xlsx.pdf` — PDF export, not a machine-readable workbook for this analysis
