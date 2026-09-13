"""Synthetic/demo preprocessing helpers for VEYRONIX ML prediction.

This module is intentionally lightweight and explainable. It prepares
complaint and transaction data from the SQLite-backed schema and from the
CSV training artifacts that are clearly labelled synthetic/demo data.
"""
from __future__ import annotations

from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
COMPLAINTS_CSV = DATA_DIR / "complaints.csv"
TRANSACTIONS_CSV = DATA_DIR / "transactions.csv"

REQUIRED_COMPLAINT_COLUMNS = {
    "complaint_id",
    "fraud_type",
    "amount",
    "city",
    "bank",
    "branch",
    "status",
}

REQUIRED_TRANSACTION_COLUMNS = {
    "transaction_id",
    "complaint_id",
    "amount",
    "bank",
    "city",
    "branch",
    "transaction_type",
    "status",
}


def load_csvs() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load the synthetic demo complaint and transactions CSV files."""
    complaints = pd.read_csv(COMPLAINTS_CSV)
    transactions = pd.read_csv(TRANSACTIONS_CSV)
    return complaints, transactions


def clean_data(complaints: pd.DataFrame, transactions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Validate and normalize columns safely for model training and predictions."""
    for col in REQUIRED_COMPLAINT_COLUMNS:
        if col not in complaints.columns:
            raise ValueError(f"Missing complaint column: {col}")
    for col in REQUIRED_TRANSACTION_COLUMNS:
        if col not in transactions.columns:
            raise ValueError(f"Missing transaction column: {col}")

    complaints = complaints.replace({np.nan: None})
    transactions = transactions.replace({np.nan: None})

    # Normalize numeric columns and text categories safely.
    complaints["amount"] = pd.to_numeric(complaints["amount"], errors="coerce").fillna(0)
    transactions["amount"] = pd.to_numeric(transactions["amount"], errors="coerce").fillna(0)
    complaints["risk_score"] = pd.to_numeric(complaints.get("risk_score", 0), errors="coerce").fillna(50)
    complaints["fraud_type"] = complaints["fraud_type"].fillna("UPI / payment fraud").astype(str)
    complaints["city"] = complaints["city"].fillna("Delhi").astype(str)
    complaints["bank"] = complaints["bank"].fillna("State Bank of India").astype(str)
    complaints["branch"] = complaints["branch"].fillna("Central Branch").astype(str)

    return complaints, transactions


def build_training_frame(complaints: pd.DataFrame, transactions: pd.DataFrame) -> pd.DataFrame:
    """Create a complaint-level feature matrix from the synthetic CSV files.

    Features include complaint amount, transaction amount, transaction count,
    city/bank/branch categories, fraud-type category and a mapped risk score label.
    """
    complaints, transactions = clean_data(complaints, transactions)

    transaction_summary = (
        transactions.groupby("complaint_id", as_index=False)
        .agg(
            transaction_count=("transaction_id", "nunique"),
            total_transaction_amount=("amount", "sum"),
            avg_transaction_amount=("amount", "mean"),
            max_transaction_amount=("amount", "max"),
        )
    )

    training = complaints.merge(transaction_summary, on="complaint_id", how="left")
    training["transaction_count"] = training["transaction_count"].fillna(0)
    training["total_transaction_amount"] = training["total_transaction_amount"].fillna(0)
    training["avg_transaction_amount"] = training["avg_transaction_amount"].fillna(0)
    training["max_transaction_amount"] = training["max_transaction_amount"].fillna(0)
    training["risk_score"] = training["risk_score"].clip(0, 100)

    # Synthetic demo labels track clearly label that this is synthetic demo data.
    training["synthetic_data_flag"] = training.get("synthetic_data_flag", "SYNTHETIC_DEMO")
    training["feature_high_amount"] = (training["amount"] >= 50000).astype(int)
    training["feature_high_transaction"] = (training["max_transaction_amount"] >= 50000).astype(int)
    training["feature_city_srinagar"] = (training["city"].str.lower() == "srinagar").astype(int)
    training["feature_city_delhi"] = (training["city"].str.lower() == "delhi").astype(int)
    training["feature_fraud_digital_arrest"] = (training["fraud_type"].str.lower().str.contains("digital-arrest")).astype(int)
    training["feature_fraud_upi"] = (training["fraud_type"].str.lower().str.contains("upi")).astype(int)

    return training


def feature_columns() -> list[str]:
    """Columns used by the baseline explainable scikit-learn model."""
    return [
        "amount",
        "transaction_count",
        "total_transaction_amount",
        "avg_transaction_amount",
        "max_transaction_amount",
        "feature_high_amount",
        "feature_high_transaction",
        "feature_city_srinagar",
        "feature_city_delhi",
        "feature_fraud_digital_arrest",
        "feature_fraud_upi",
    ]


def predict_payload_to_frame(payload: dict) -> pd.DataFrame:
    """Convert a complaint payload into a one-row feature frame for inference.

    Safely handles missing keys and invalid numeric values by using defaults.
    """
    complaint_type = str(payload.get("fraud_type") or "UPI / payment fraud")
    amount = float(payload.get("amount") or 0)
    city = str(payload.get("city") or "Delhi")
    bank = str(payload.get("bank") or "State Bank of India")
    branch = str(payload.get("branch") or "Central Branch")
    complaint_id = str(payload.get("complaint_id") or "NCRP-SYNTHETIC")

    # Safe transaction feature defaults.
    tx_count = int(payload.get("transaction_count") or 1)
    total_tx_amount = float(payload.get("total_transaction_amount") or amount)
    avg_tx_amount = float(payload.get("avg_transaction_amount") or max(amount / max(tx_count, 1), 0))
    max_tx_amount = float(payload.get("max_transaction_amount") or amount)

    row = pd.DataFrame([{
        "complaint_id": complaint_id,
        "fraud_type": complaint_type,
        "amount": amount,
        "city": city,
        "bank": bank,
        "branch": branch,
        "status": str(payload.get("status") or "new"),
        "transaction_count": tx_count,
        "total_transaction_amount": total_tx_amount,
        "avg_transaction_amount": avg_tx_amount,
        "max_transaction_amount": max_tx_amount,
        "feature_high_amount": int(amount >= 50000),
        "feature_high_transaction": int(max_tx_amount >= 50000),
        "feature_city_srinagar": int(city.lower() == "srinagar"),
        "feature_city_delhi": int(city.lower() == "delhi"),
        "feature_fraud_digital_arrest": int("digital-arrest" in complaint_type.lower()),
        "feature_fraud_upi": int("upi" in complaint_type.lower()),
    }])
    return row
