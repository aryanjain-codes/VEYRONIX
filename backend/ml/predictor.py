"""Baseline explainable ML prediction pipeline for VEYRONIX.

This file uses a synthetic/demo dataset and a local scikit-learn regression
model. It is intentionally an intelligence lead generator and not a real-world
proof system.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from joblib import dump, load
from sklearn.ensemble import RandomForestRegressor

from backend.ml.preprocessing import feature_columns, predict_payload_to_frame, load_csvs, build_training_frame

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = BASE_DIR / "models"
MODEL_PATH = MODELS_DIR / "veyronix_risk_model.joblib"


def build_model() -> RandomForestRegressor:
    """Train and persist a baseline RandomForestRegressor model from synthetic CSV data."""
    complaints, transactions = load_csvs()
    training = build_training_frame(complaints, transactions)

    feature_names = feature_columns()
    X = training[feature_names]
    y = training["risk_score"].clip(0, 100)

    model = RandomForestRegressor(
        n_estimators=30,
        max_depth=5,
        min_samples_leaf=1,
        random_state=42,
    )
    model.fit(X, y)

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    dump(model, MODEL_PATH)
    return model


def load_model() -> RandomForestRegressor:
    """Load the locally saved model, or train one if the artifact is missing."""
    if not MODEL_PATH.exists():
        return build_model()
    return load(MODEL_PATH)


def predict(payload: dict) -> dict:
    """Predict a synthetic/demo risk assessment from complaint and transaction features.

    Returns a JSON-style dictionary that follows the requested structure and
    includes an explanation field for the feature contributors.
    """
    if not isinstance(payload, dict):
        raise ValueError("Prediction payload must be a dictionary.")

    payload = payload.copy()

    # Safe, defensive normalization.
    payload.setdefault("fraud_type", "UPI / payment fraud")
    payload.setdefault("amount", 50000)
    payload.setdefault("city", "Delhi")
    payload.setdefault("bank", "State Bank of India")
    payload.setdefault("branch", "Central Branch")
    payload.setdefault("transaction_count", 1)
    payload.setdefault("total_transaction_amount", float(payload.get("amount") or 0))
    payload.setdefault("avg_transaction_amount", float(payload.get("amount") or 0) / max(1, int(payload.get("transaction_count") or 1)))
    payload.setdefault("max_transaction_amount", float(payload.get("amount") or 0))

    try:
        amount = float(payload.get("amount") or 0)
        if amount < 0:
            amount = 0
    except (TypeError, ValueError):
        amount = 0

    try:
        tx_total = float(payload.get("total_transaction_amount") or 0)
        if tx_total < 0:
            tx_total = 0
    except (TypeError, ValueError):
        tx_total = 0

    try:
        tx_max = float(payload.get("max_transaction_amount") or 0)
        if tx_max < 0:
            tx_max = 0
    except (TypeError, ValueError):
        tx_max = 0

    try:
        tx_count = int(payload.get("transaction_count") or 1)
        if tx_count < 1:
            tx_count = 1
    except (TypeError, ValueError):
        tx_count = 1

    frame = predict_payload_to_frame(payload)
    # Attach the same feature columns used by the training stage.
    model = load_model()
    X = frame[feature_columns()]
    risk_score = int(np.clip(float(model.predict(X)[0]), 0, 100))

    # Convert scores into a time-window and location representation.
    fraud_type = str(payload.get("fraud_type") or "UPI / payment fraud")
    city = str(payload.get("city") or "Delhi")
    branch = str(payload.get("branch") or "Central Branch")
    bank = str(payload.get("bank") or "State Bank of India")

    if risk_score >= 85:
        priority = "CRITICAL"
        predicted_location = f"{city}, {branch}"
        time_window = "Next 24 hours"
    elif risk_score >= 60:
        priority = "HIGH"
        predicted_location = f"{city}, {branch}"
        time_window = "Next 48 hours"
    elif risk_score >= 35:
        priority = "MEDIUM"
        predicted_location = city
        time_window = "Next 72 hours"
    else:
        priority = "LOW"
        predicted_location = city
        time_window = "Next 7 days"

    # Confidence is a rough probability-like value in [0,1].
    confidence = float(np.clip(0.50 + (risk_score / 100) * 0.45, 0.0, 0.99))

    # Explainability: feature reasons list.
    reasons = []
    if amount >= 50000:
        reasons.append("complaint_amount_high")
    if tx_max >= 50000:
        reasons.append("transaction_amount_high")
    if city.lower() == "srinagar":
        reasons.append("city_srinagar_signal")
    if "digital-arrest" in fraud_type.lower():
        reasons.append("fraud_type_digital_arrest")
    if "upi" in fraud_type.lower():
        reasons.append("fraud_type_upi")
    if tx_count > 3:
        reasons.append("multiple_transactions")
    if not reasons:
        reasons.append("base_pattern")

    return {
        "risk_score": risk_score,
        "predicted_location": predicted_location,
        "time_window": time_window,
        "confidence": round(confidence, 2),
        "priority": priority,
        "explanation": reasons,
        "synthetic_data_flag": "SYNTHETIC_DEMO",
        "intelligence_lead_notice": "This is an intelligence lead, not proof that a person or location is involved in a crime.",
    }
