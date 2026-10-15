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

## Second Senior Review

Reviewed the post-`83ec80c` repository again on 2026-10-15, including all tracked files, the full notebook JSON/source state, Python/config/test/documentation files, Git history and diff. The tracked PDF remains a reference export rather than an executable workbook; no real-data metrics were generated or claimed.

### Findings fixed in this review

1. **Documented `.xls` support was incomplete.** The notebook accepted `.xls` paths, but `xlrd` was not declared. Added `xlrd>=2.0,<3` to `requirements.txt`.
2. **Workbook validation was too permissive.** Added checks for duplicate column names, missing/null primary keys, duplicate transaction/dimension keys, invalid non-null dates, transactions before customer join dates, and unmatched foreign keys. Transaction columns are projected before joins to avoid accidental name collisions.
3. **Environment-variable typos could silently select another workbook.** When `ECOMMERCE_DATA_FILE` is set, the notebook now fails directly if the path is missing or has an unsupported suffix instead of falling back to an unrelated candidate.
4. **Silhouette evaluation could still raise on degenerate labels.** Added a shared precondition-checked `safe_silhouette` helper and used it for K-Means, DBSCAN non-noise observations, and agglomerative clustering; undefined scores are reported as such.
5. **Monthly aggregation relied on index alignment that was difficult to audit.** Rewrote it to derive an explicit month column before grouping.
6. **Static validation was not reusable and did not validate markdown/raw cell paths or malformed cell structures.** Refactored `scripts/validate_notebook.py` to expose `validate_notebook`, validate all cell sources/types, and retain AST/Ruff, output, execution-count, and portability checks.
7. **Regression coverage was absent.** Added `tests/test_repository.py` with notebook-state/dependency checks and a synthetic six-table workbook smoke test that exercises loading, joins, customer aggregation, and all clustering branches without claiming real-data performance.

### Validation performed in the second review

- `python scripts/validate_notebook.py`: passed; 9 code cells parsed, no saved outputs, no machine-specific paths.
- `python -m unittest discover -s tests -v`: passed, 3 tests; the runtime smoke test completed against an ephemeral synthetic workbook only.
- `python -m compileall -q scripts tests`: passed.
- `ruff check scripts tests`: passed.
- Notebook JSON state: 15 cells, 0 saved outputs, all code-cell execution counts `null`.
- No secrets, hard-coded user paths, generated outputs, or untracked data files were introduced. No push was performed.

### Remaining risks

- The original Excel workbook is still unavailable, so real schema/content validation and real notebook execution remain unverified here.
- The workflow is intentionally descriptive unsupervised clustering; it has no predictive holdout, persisted preprocessing/model artifact, drift monitoring, or scoring API.
- Customers without transactions are excluded from transaction-derived features and need an explicit business rule if they must be segmented.
- Dependency ranges are compatible bounds rather than a lockfile; production reproducibility still requires pinning and recording the resolved environment.

### Second-review changed files

- `E-commerce-Customers.ipynb`
- `README.md`
- `requirements.txt`
- `scripts/validate_notebook.py`
- `tests/test_repository.py`
