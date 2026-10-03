from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from customer_segmentation.pipeline import (
    FEATURES,
    REQUIRED_SHEETS,
    _split_indices,
    fit_and_evaluate,
    load_customer_features,
    write_artifacts,
)


def write_workbook(path, *, unknown_customer=False, duplicate_customer=False):
    customer_ids = list(range(40))
    customers = pd.DataFrame(
        {
            "customer_id": customer_ids + ([0] if duplicate_customer else []),
            "join_date": [pd.Timestamp("2020-01-01")] * (40 + int(duplicate_customer)),
        }
    )
    transaction_ids = [999 if unknown_customer else customer_ids[0]] + customer_ids[1:]
    transactions = pd.DataFrame(
        {
            "customer_id": transaction_ids,
            "burn_date": [pd.NaT if i % 2 else pd.Timestamp("2020-02-01") for i in range(40)],
            "transaction_date": [
                pd.Timestamp("2020-02-01") + pd.Timedelta(days=i * 10) for i in range(40)
            ],
        }
    )
    with pd.ExcelWriter(path) as writer:
        transactions.to_excel(writer, sheet_name="transactions", index=False)
        customers.to_excel(writer, sheet_name="customers", index=False)
        for sheet in sorted(REQUIRED_SHEETS - {"transactions", "customers"}):
            pd.DataFrame({"unused": []}).to_excel(writer, sheet_name=sheet, index=False)


def clustered_features(n=120):
    rng = np.random.default_rng(7)
    customer_id = np.arange(n)
    private_ids = [f"PRIVATE-CUSTOMER-{value:04d}" for value in customer_id]
    group = customer_id % 2
    return pd.DataFrame(
        {
            "customer_id": private_ids,
            "coupon_used_rate": np.clip(group * 0.75 + rng.normal(0, 0.04, n), 0, 1),
            "mean_days_since_join": group * 500 + rng.normal(0, 25, n),
        }
    )


def test_loads_and_aggregates_one_row_per_customer(tmp_path):
    path = tmp_path / "authorized.xlsx"
    write_workbook(path)
    result = load_customer_features(path)
    assert len(result) == 40
    assert result["customer_id"].is_unique
    assert result.loc[result.customer_id == 0, "coupon_used_rate"].item() == 1
    assert set(FEATURES).issubset(result.columns)


def test_loader_rejects_unknown_customer_and_duplicate_dimension(tmp_path):
    unknown_path = tmp_path / "unknown.xlsx"
    write_workbook(unknown_path, unknown_customer=True)
    with pytest.raises(ValueError, match="absent"):
        load_customer_features(unknown_path)
    duplicate_path = tmp_path / "duplicate.xlsx"
    write_workbook(duplicate_path, duplicate_customer=True)
    with pytest.raises(ValueError, match="one row per customer_id"):
        load_customer_features(duplicate_path)


def test_loader_rejects_pdf_and_missing_worksheets(tmp_path):
    pdf = tmp_path / "input.pdf"
    pdf.write_bytes(b"not an excel file")
    with pytest.raises(ValueError, match="Expected an .xlsx"):
        load_customer_features(pdf)
    incomplete = tmp_path / "incomplete.xlsx"
    with pd.ExcelWriter(incomplete) as writer:
        pd.DataFrame(
            {"customer_id": [1], "burn_date": [None], "transaction_date": ["2020-01-01"]}
        ).to_excel(writer, sheet_name="transactions", index=False)
    with pytest.raises(ValueError, match="missing required worksheets"):
        load_customer_features(incomplete)


def test_group_split_is_deterministic_and_disjoint():
    ids = pd.Series(np.arange(100))
    first = _split_indices(ids, validation_size=0.2, test_size=0.2, random_state=42)
    second = _split_indices(ids, validation_size=0.2, test_size=0.2, random_state=42)
    assert all(np.array_equal(left, right) for left, right in zip(first, second, strict=True))
    group_sets = [set(ids.iloc[index]) for index in first]
    assert group_sets[0].isdisjoint(group_sets[1])
    assert group_sets[0].isdisjoint(group_sets[2])
    assert group_sets[1].isdisjoint(group_sets[2])


def test_training_selects_on_validation_and_writes_aggregate_only_artifacts(tmp_path):
    frame = clustered_features()
    model, metrics = fit_and_evaluate(frame, min_clusters=2, max_clusters=3, random_state=23)
    assert metrics["selected_k"] == 2
    assert model.named_steps["scaler"].n_features_in_ == 2
    assert 0 <= metrics["validation_silhouette"] <= 1
    assert metrics["test_silhouette"] is None or -1 <= metrics["test_silhouette"] <= 1
    artifacts = write_artifacts(tmp_path, model, metrics)
    assert set(artifacts) == {"model", "schema", "metrics"}
    schema = json.loads(artifacts["schema"].read_text())
    report = json.loads(artifacts["metrics"].read_text())
    assert schema["selected_k"] == report["selected_k"] == 2
    serialized = artifacts["schema"].read_text() + artifacts["metrics"].read_text()
    assert all(str(value) not in serialized for value in frame.customer_id.tolist())
    assert artifacts["model"].is_file()


def test_rejects_invalid_features_and_duplicate_customers():
    frame = clustered_features()
    frame.loc[0, "coupon_used_rate"] = np.nan
    with pytest.raises(ValueError, match="finite numeric"):
        fit_and_evaluate(frame)
    frame = clustered_features()
    frame.loc[1, "customer_id"] = frame.loc[0, "customer_id"]
    with pytest.raises(ValueError, match="exactly one row per customer"):
        fit_and_evaluate(frame)
