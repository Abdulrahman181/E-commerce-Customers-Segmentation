# E-commerce Customers Segmentation

This repository contains an exploratory Jupyter notebook for joining customer and transaction tables, visualizing transaction patterns, and comparing K-Means, DBSCAN, and hierarchical clustering. The notebook is the only analysis implementation currently included; a stakeholder dashboard is not present.

## Dataset requirements

The notebook needs an **Excel workbook** with these worksheets: `transactions`, `customers`, `genders`, `cities`, `branches`, and `merchants`. The tracked `E-commerce_data.xlsx.pdf` is a PDF export, not an Excel workbook, and cannot be passed to `pandas.read_excel`. The required workbook is not included, so the complete notebook cannot be run from a fresh clone until you provide the original workbook. Do not substitute the PDF or an invented dataset.

Use only a workbook you are authorized to access. The expected workbook is ignored by Git so a local copy is not accidentally committed.

## Setup and run

From the repository root, create an environment and install the bounded dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Set the workbook path before starting Jupyter. If omitted, the notebook looks for `E-commerce_data.xlsx` in the current working directory.

```bash
export ECOMMERCE_DATA_PATH="/path/to/your/E-commerce_data.xlsx"
jupyter lab E-commerce-Customers.ipynb
```

The dependency ranges are compatibility bounds, not a fully resolved lock file. `openpyxl` is included as the Excel reader engine.

## Analysis scope and limitations

The notebook uses `coupon_used` and `days_since_join` as clustering features and includes exploratory plots and example cluster counts. Its historical cell outputs have been cleared; rerun it against an authorized workbook to regenerate them. The previously stated segment findings are not retained as verified results: this repository does not include the workbook needed to reproduce them, and no model performance or business impact is asserted here. Validate data quality, cluster stability, fairness, and business usefulness before acting on any result.

## Repository contents

- `E-commerce-Customers.ipynb` — exploratory analysis notebook
- `E-commerce_data.xlsx.pdf` — PDF export; not a machine-readable Excel workbook for the notebook
- `requirements.txt` — bounded Python dependencies
