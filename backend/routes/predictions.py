"""Prediction API routes for VEYRONIX."""
from __future__ import annotations

import uuid
from datetime import datetime

from flask import Blueprint, jsonify, request

from backend.database import get_db_connection
from backend.ml.predictor import predict

predictions_bp = Blueprint("predictions", __name__)


@predictions_bp.post("")
def create_prediction():
    """Return a model-backed predictive intelligence lead for complaint and transaction features.

    The response shape is intentionally root-level and follows the requested
    structure. The data is synthetic/demo only and should not be treated as proof.
    """
    payload = request.get_json(silent=True) or {}
    try:
        result = predict(payload)
    except Exception as exc:
        return jsonify({"success": False, "message": f"Prediction failed safely: {exc}"}), 400

    # Persist a synthetic demo prediction result into the SQLite predictions table.
    conn = get_db_connection()
    try:
        prediction_id = f"PRED-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
        conn.execute(
            """
            INSERT INTO predictions (
                prediction_id, complaint_id, fraud_type, city, bank,
                risk_score, risk_tier, window_hours, cash_out_point, explanation
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                prediction_id,
                payload.get("complaint_id") or "NCRP-SYNTHETIC",
                payload.get("fraud_type") or "UPI / payment fraud",
                payload.get("city") or "Delhi",
                payload.get("bank") or "State Bank of India",
                result["risk_score"],
                result["priority"].lower(),
                24 if result["time_window"] == "Next 24 hours" else 48 if result["time_window"] == "Next 48 hours" else 72,
                result["predicted_location"],
                ", ".join(result["explanation"]),
            ),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        # Keep the endpoint safe; do not fail the JSON response if SQLite persistence is unavailable.
    finally:
        conn.close()

    return jsonify({
        "success": True,
        "risk_score": result["risk_score"],
        "predicted_location": result["predicted_location"],
        "time_window": result["time_window"],
        "confidence": result["confidence"],
        "priority": result["priority"],
        "explanation": result["explanation"],
        "synthetic_data_flag": result["synthetic_data_flag"],
        "intelligence_lead_notice": result["intelligence_lead_notice"],
    })
