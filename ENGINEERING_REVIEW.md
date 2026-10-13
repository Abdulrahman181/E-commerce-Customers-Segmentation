# Engineering review — E-commerce Customers Segmentation

## Scope

Reviewed the repository at `/home/ubuntu/github_priority/E-commerce-Customers-Segmentation` on 2026-10-13. The review covered the tracked Jupyter notebook, README, repository contents, dataset artifact, and dependency/runtime assumptions. No other repository was changed and no changes were pushed to GitHub.

## Starting state

The repository contained only `E-commerce-Customers.ipynb`, `E-commerce_data.xlsx.pdf`, and `README.md`. There were no Python modules, dependency file, tests, or ignore rules. The notebook had saved outputs from a Windows/Anaconda environment and hard-coded a user-specific path to an `.xlsx` file that is not present in this repository.

The tracked PDF is a 127-page Google Sheets export. It is not an Excel workbook and cannot safely substitute for the six-sheet input expected by `pandas.read_excel`. I did not invent or reconstruct data from it.

## Critical issues found and fixed

1. **Non-portable, missing data path.** The notebook referenced `C:\Users\Right-click\OneDrive\سطح المكتب\...\\E-commerce_data.xlsx`. The notebook now resolves `ECOMMERCE_DATA_FILE` or documented repository/data locations and raises an actionable error when the workbook is absent.
2. **Missing dependency declaration.** Added `requirements.txt` covering pandas/openpyxl, NumPy, plotting, scikit-learn, SciPy, Jupyter, and nbformat with compatible major-version bounds.
3. **Stale and misleading notebook outputs.** Removed all saved outputs and execution counts. Old printed metrics are therefore not presented as current results.
4. **Fragile joins and column collision handling.** The original notebook assumed `burn_date_x`/`burn_date_y` would exist and dropped a specific suffix. The repaired loader selects required dimension columns, validates required sheets/columns, and uses `validate="many_to_one"` on joins.
5. **Transaction-level overweighting.** The original clustering used one row per transaction, so high-frequency customers dominated the fit. The repaired notebook aggregates to one row per customer before scaling and clustering.
6. **Metric/model robustness.** K-Means now uses explicit `n_init=10` and `random_state=42`, bounds candidate `k` by sample count, and avoids invalid silhouette calls for DBSCAN noise/degenerate clusters. Deprecated `affinity=` was replaced by `metric="euclidean"` for agglomerative clustering.
7. **Status/date quality.** Dates are parsed with `errors="coerce"`; status values are normalized and `burnt` is treated consistently as `burned`; derived coupon-use and elapsed-day features are explicit.
8. **Missing static validation.** Added `scripts/validate_notebook.py`, which parses every code cell with AST, runs Ruff `E9/F821` when available, and rejects saved outputs, execution counts, and machine-specific paths.
9. **Documentation drift.** Rewrote README to state the real data contract, setup, limitations, and the fact that no model results are claimable without the original workbook. Added `.gitignore` for local data, caches, environments, and generated outputs.

## Data leakage and split assessment

This notebook performs unsupervised descriptive clustering and has no target variable, so a supervised train/test split is not applicable to the exploratory fit. The scaler and clustering models are fit on the complete customer population being described. This is explicitly documented rather than presented as a predictive generalization estimate. For production use or future-customer scoring, the next step should be a time-based holdout plus a persisted preprocessing/model pipeline fitted only on the historical training period.

Customer-level aggregation prevents repeated transaction rows for the same customer from acting as accidental sampling weights. Features are transaction-history features available at segmentation time; customers with no transactions are excluded and called out as a separate limitation.

## Validation performed

- JSON/nbformat structure check: passed; 15 cells, 0 saved outputs, 0 execution counts.
- Python AST parse of every code cell: passed.
- `ruff check --select E9,F821` through `scripts/validate_notebook.py`: passed; direct Ruff validation of the validator also passed.
- Dependency availability check: pandas, NumPy, matplotlib, seaborn, and openpyxl were available in the sandbox; scikit-learn, SciPy, nbformat, and nbclient were not installed, so full model execution and notebook execution were not claimed.
- Dataset execution: not run because the executable Excel workbook is absent; only the PDF export is tracked.

## Changed files

- `E-commerce-Customers.ipynb`
- `README.md`
- `requirements.txt`
- `.gitignore`
- `scripts/validate_notebook.py`
- `ENGINEERING_REVIEW.md`

## Reproducibility caveat

Install `requirements.txt`, supply the original workbook through `ECOMMERCE_DATA_FILE` or the documented path, run `python scripts/validate_notebook.py`, and then execute the notebook. Any metrics or cluster interpretation must be generated from that supplied workbook; this review intentionally reports no fabricated numerical result.
