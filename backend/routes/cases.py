"""Case workflow API routes for VEYRONIX."""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from backend.database import get_db_connection
from backend.security import login_required, roles_required

cases_bp = Blueprint("cases", __name__)


@cases_bp.get("")
@login_required
@roles_required("admin", "bank", "lea", "victim")
def list_cases():
    """Return synthetic case management records from the existing SQLite cases table."""
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT case_id, location, severity, status, officer, opened_at, hotspot_id FROM cases ORDER BY opened_at DESC LIMIT 50"
        ).fetchall()
    finally:
        conn.close()

    if rows:
        data = []
        for row in rows:
            data.append({
                "case_id": row["case_id"],
                "location": row["location"],
                "severity": row["severity"],
                "status": row["status"],
                "officer": row["officer"],
                "opened_at": row["opened_at"],
                "hotspot_id": row["hotspot_id"],
            })
        return jsonify({"success": True, "data": data})

    return jsonify({
        "success": True,
        "data": [
            {
                "case_id": "CYB-2026-4471",
                "location": "Mehjoor Nagar, Srinagar",
                "severity": "crit",
                "status": "new",
                "officer": "Insp. R. Kaul",
                "opened_at": "2 min ago",
            },
            {
                "case_id": "CYB-2026-4468",
                "location": "Kotwali branch, Ranchi",
                "severity": "warn",
                "status": "investigating",
                "officer": "SI M. Toppo",
                "opened_at": "14 min ago",
            },
        ],
    })


@cases_bp.post("/<case_id>/status")
@login_required
@roles_required("admin", "lea")
def update_case_status(case_id: str):
    """Update case status by sample case ID; skeleton only."""
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return jsonify({"success": False, "message": "JSON object required."}), 400

    new_status = payload.get("status") or "investigating"
    return jsonify({
        "success": True,
        "message": "Case status updated",
        "case_id": case_id,
        "status": new_status,
    })
