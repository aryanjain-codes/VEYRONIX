"""Complaint API routes for VEYRONIX."""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from backend.database import get_db_connection

complaints_bp = Blueprint("complaints", __name__)


@complaints_bp.get("")
def list_complaints():
    """Return a sample list of complaints from the SQLite database."""
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT complaint_id, complainant_name, fraud_type, amount, city, bank, branch, complaint_date, status FROM complaints ORDER BY created_at DESC LIMIT 50"
        ).fetchall()
    finally:
        conn.close()

    return jsonify({
        "success": True,
        "data": [dict(row) for row in rows],
    })


@complaints_bp.post("")
def create_complaint():
    """Create a synthetic complaint record skeleton."""
    payload = request.get_json(silent=True) or {}
    complaint_id = payload.get("complaint_id") or f"NCRP-2026-{100000 + len(payload)}"
    conn = get_db_connection()
    try:
        conn.execute(
            """
            INSERT OR IGNORE INTO complaints (
                complaint_id, complainant_name, fraud_type, amount, city, bank, branch,
                complaint_date, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'new')
            """,
            (
                complaint_id,
                payload.get("complainant_name") or "Demo Complainant",
                payload.get("fraud_type") or "UPI / payment fraud",
                payload.get("amount") or 0,
                payload.get("city") or "Delhi",
                payload.get("bank") or "State Bank of India",
                payload.get("branch") or "Central Branch",
                payload.get("complaint_date") or "2026-09-14",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return jsonify({"success": True, "message": "Complaint created", "complaint_id": complaint_id})
