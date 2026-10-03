"""Leakage-aware, customer-level clustering utilities for the e-commerce workbook."""

from __future__ import annotations

import json
import os
import platform
import tempfile
import warnings
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

REQUIRED_SHEETS = {"transactions", "customers", "genders", "cities", "branches", "merchants"}
FEATURES = ("coupon_used_rate", "mean_days_since_join")
CUSTOMER_ID = "customer_id"


def _require_columns(frame: pd.DataFrame, required: set[str], table: str) -> None:
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"The {table} worksheet is missing required columns: {', '.join(missing)}")


def load_customer_features(workbook_path: str | Path) -> pd.DataFrame:
    """Load validated transaction/customer tables and aggregate features per customer.

    Identifiers are retained only in memory for splitting and are never written to artifacts.
    Customer means prevent frequent purchasers from receiving extra weight in clustering.
    """
    path = Path(workbook_path).expanduser()
    if not path.is_file():
        raise FileNotFoundError(
            f"Workbook not found: {path}. Set ECOMMERCE_DATA_PATH or pass --workbook. "
            "The tracked E-commerce_data.xlsx.pdf is a PDF, not an Excel workbook."
        )
    if path.suffix.lower() not in {".xlsx", ".xlsm"}:
        raise ValueError(
            "Expected an .xlsx or .xlsm Excel workbook; PDF/CSV files are not supported."
        )
    try:
        with pd.ExcelFile(path) as workbook:
            missing_sheets = sorted(REQUIRED_SHEETS.difference(workbook.sheet_names))
            if missing_sheets:
                raise ValueError(
                    f"Workbook is missing required worksheets: {', '.join(missing_sheets)}"
                )
            transactions = pd.read_excel(workbook, sheet_name="transactions")
            customers = pd.read_excel(workbook, sheet_name="customers")
    except (OSError, ValueError):
        raise
    except Exception as exc:
        raise ValueError(
            "Could not read the Excel workbook. Check that it is a valid, readable file."
        ) from exc

    _require_columns(transactions, {CUSTOMER_ID, "burn_date", "transaction_date"}, "transactions")
    _require_columns(customers, {CUSTOMER_ID, "join_date"}, "customers")
    if transactions.empty or customers.empty:
        raise ValueError("The transactions and customers worksheets must not be empty.")
    if transactions[CUSTOMER_ID].isna().any() or customers[CUSTOMER_ID].isna().any():
        raise ValueError("Customer identifiers must be present in both required worksheets.")
    if customers[CUSTOMER_ID].duplicated().any():
        raise ValueError("The customers worksheet must contain one row per customer_id.")
    if (~transactions[CUSTOMER_ID].isin(customers[CUSTOMER_ID])).any():
        raise ValueError(
            "Some transactions reference customers absent from the customers worksheet."
        )

    for frame, column, table in (
        (transactions, "transaction_date", "transactions"),
        (customers, "join_date", "customers"),
    ):
        original = frame[column]
        parsed = pd.to_datetime(original, errors="coerce")
        if (original.notna() & parsed.isna()).any():
            raise ValueError(f"The {table}.{column} column contains unparseable date values.")
        frame[column] = parsed

    merged = transactions[[CUSTOMER_ID, "burn_date", "transaction_date"]].merge(
        customers[[CUSTOMER_ID, "join_date"]], on=CUSTOMER_ID, how="left", validate="many_to_one"
    )
    valid_dates = merged["transaction_date"].notna() & merged["join_date"].notna()
    excluded = int((~valid_dates).sum())
    if excluded:
        warnings.warn(
            f"Excluded {excluded} transaction row(s) with missing transaction or join dates.",
            UserWarning,
            stacklevel=2,
        )
    merged = merged.loc[valid_dates].copy()
    if merged.empty:
        raise ValueError("No rows have both a transaction date and a customer join date.")
    merged["days_since_join"] = (merged["transaction_date"] - merged["join_date"]).dt.days
    if (merged["days_since_join"] < 0).any():
        raise ValueError(
            "Some transactions predate the customer's join date; correct the source data."
        )
    merged["coupon_used"] = merged["burn_date"].notna().astype(float)
    features = (
        merged.groupby(CUSTOMER_ID, sort=True, observed=True)
        .agg(
            coupon_used_rate=("coupon_used", "mean"),
            mean_days_since_join=("days_since_join", "mean"),
        )
        .reset_index()
    )
    if features.empty:
        raise ValueError("No customer-level features could be constructed from the workbook.")
    return features


def _split_indices(
    groups: pd.Series,
    *,
    validation_size: float,
    test_size: float,
    random_state: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Make deterministic disjoint customer-group train/validation/test indices."""
    if not (0 < validation_size < 1 and 0 < test_size < 1 and validation_size + test_size < 1):
        raise ValueError("validation_size and test_size must be positive and sum to less than 1.")
    if groups.isna().any():
        raise ValueError("Customer group identifiers must not be missing.")
    if groups.nunique() < 6:
        raise ValueError(
            "At least six distinct customers are required for train/validation/test splits."
        )
    first = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    train_validation, test = next(first.split(np.zeros(len(groups)), groups=groups))
    relative_validation = validation_size / (1.0 - test_size)
    second = GroupShuffleSplit(
        n_splits=1, test_size=relative_validation, random_state=random_state + 1
    )
    train_relative, validation_relative = next(
        second.split(
            np.zeros(len(train_validation)), groups=groups.iloc[train_validation].to_numpy()
        )
    )
    train = train_validation[train_relative]
    validation = train_validation[validation_relative]
    if min(len(train), len(validation), len(test)) < 3:
        raise ValueError(
            "Each split needs at least three customer records for silhouette diagnostics."
        )
    return train, validation, test


def fit_and_evaluate(
    customer_features: pd.DataFrame,
    *,
    min_clusters: int = 2,
    max_clusters: int = 5,
    validation_size: float = 0.2,
    test_size: float = 0.2,
    random_state: int = 42,
) -> tuple[Pipeline, dict[str, Any]]:
    """Select k on validation data, refit on train+validation, and assess test once.

    Silhouette values are descriptive geometric diagnostics for unsupervised clusters, not
    predictive accuracy or evidence that the segmentation is useful or stable.
    """
    _require_columns(customer_features, {CUSTOMER_ID, *FEATURES}, "customer feature table")
    if customer_features.empty or customer_features[CUSTOMER_ID].isna().any():
        raise ValueError("Customer feature table must contain rows with non-missing identifiers.")
    if customer_features[CUSTOMER_ID].duplicated().any():
        raise ValueError("Customer feature table must contain exactly one row per customer.")
    if not isinstance(random_state, int) or random_state < 0:
        raise ValueError("random_state must be a non-negative integer.")
    if not isinstance(min_clusters, int) or not isinstance(max_clusters, int):
        raise ValueError("Cluster bounds must be integers.")
    if min_clusters < 2 or max_clusters < min_clusters:
        raise ValueError("Cluster bounds must satisfy 2 <= min_clusters <= max_clusters.")

    values = (
        customer_features.loc[:, FEATURES]
        .apply(pd.to_numeric, errors="coerce")
        .to_numpy(dtype=float)
    )
    if not np.isfinite(values).all():
        raise ValueError("Clustering features must contain only finite numeric values.")
    groups = customer_features[CUSTOMER_ID].reset_index(drop=True)
    train_idx, validation_idx, test_idx = _split_indices(
        groups, validation_size=validation_size, test_size=test_size, random_state=random_state
    )
    scaler = StandardScaler().fit(values[train_idx])
    train_scaled = scaler.transform(values[train_idx])
    validation_scaled = scaler.transform(values[validation_idx])
    scores: dict[int, float] = {}
    for k in range(min_clusters, min(max_clusters, len(train_idx) - 1) + 1):
        candidate = KMeans(n_clusters=k, random_state=random_state, n_init=10)
        candidate.fit(train_scaled)
        labels = candidate.predict(validation_scaled)
        if 1 < np.unique(labels).size < len(labels):
            scores[k] = float(silhouette_score(validation_scaled, labels))
    if not scores:
        raise ValueError(
            "No cluster count produced at least two represented validation clusters; "
            "provide more varied customer data or narrow the cluster range."
        )
    selected_k = max(scores, key=lambda k: (scores[k], -k))

    final_model = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("kmeans", KMeans(n_clusters=selected_k, random_state=random_state, n_init=10)),
        ]
    )
    train_validation = np.concatenate((train_idx, validation_idx))
    final_model.fit(values[train_validation])
    test_scaled = final_model.named_steps["scaler"].transform(values[test_idx])
    test_labels = final_model.named_steps["kmeans"].predict(test_scaled)
    test_silhouette = None
    if 1 < np.unique(test_labels).size < len(test_labels):
        test_silhouette = float(silhouette_score(test_scaled, test_labels))
    metrics: dict[str, Any] = {
        "selected_k": int(selected_k),
        "validation_silhouette": scores[selected_k],
        "test_silhouette": test_silhouette,
        "validation_candidate_scores": {str(k): score for k, score in sorted(scores.items())},
        "random_state": random_state,
        "split_proportions": {
            "train": round(len(train_idx) / len(values), 6),
            "validation": round(len(validation_idx) / len(values), 6),
            "test": round(len(test_idx) / len(values), 6),
        },
        "test_metric_note": (
            "Silhouette on held-out feature geometry only; not predictive accuracy or external validation."
        ),
    }
    return final_model, metrics


def write_artifacts(
    output_dir: str | Path, model: Pipeline, metrics: dict[str, Any]
) -> dict[str, Path]:
    """Persist a model and privacy-conscious feature/metric JSON without row-level data."""
    destination = Path(output_dir).expanduser()
    destination.mkdir(parents=True, exist_ok=True)
    model_path = destination / "customer_segmentation.joblib"
    schema_path = destination / "feature_schema.json"
    metrics_path = destination / "metrics.json"
    metadata = {
        "schema_version": 1,
        "features": [
            {
                "name": "coupon_used_rate",
                "type": "float",
                "definition": "Per-customer arithmetic mean of transaction burn_date-present indicators.",
            },
            {
                "name": "mean_days_since_join",
                "type": "float",
                "definition": "Per-customer arithmetic mean of transaction_date minus join_date in days.",
            },
        ],
        "model": "StandardScaler followed by KMeans; fitted on train plus validation only.",
        "selected_k": int(metrics["selected_k"]),
        "selection": "Highest valid validation silhouette among the requested candidate cluster counts.",
        "split": "Deterministic disjoint customer_id train/validation/test groups; test is not used for selection.",
        "random_state": int(metrics["random_state"]),
        "silhouette_interpretation": metrics["test_metric_note"],
        "versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "joblib": joblib.__version__,
            "scikit_learn": sklearn.__version__,
        },
        "privacy": "No customer identifiers, row-level assignments, or source workbook data are stored in JSON.",
    }
    temporary: list[tuple[Path, Path]] = []
    try:
        writers = (
            (model_path, lambda p: joblib.dump(model, p)),
            (
                schema_path,
                lambda p: p.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8"),
            ),
            (
                metrics_path,
                lambda p: p.write_text(
                    json.dumps(metrics, indent=2, allow_nan=False) + "\n", encoding="utf-8"
                ),
            ),
        )
        for final_path, writer in writers:
            with tempfile.NamedTemporaryFile(
                dir=destination, prefix=f".{final_path.name}.", delete=False
            ) as handle:
                temp_path = Path(handle.name)
            temporary.append((temp_path, final_path))
            writer(temp_path)
        for temp_path, final_path in temporary:
            os.replace(temp_path, final_path)
    finally:
        for temp_path, _ in temporary:
            temp_path.unlink(missing_ok=True)
    return {"model": model_path, "schema": schema_path, "metrics": metrics_path}
