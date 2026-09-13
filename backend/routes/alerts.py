"""Alerts and live feed API routes for VEYRONIX."""
from __future__ import annotations

from flask import Blueprint, jsonify

from backend.database import get_db_connection
from backend.security import login_required, roles_required

alerts_bp = Blueprint("alerts", __name__)


@alerts_bp.get("")
@login_required
@roles_required("admin", "bank", "lea", "victim")
def list_alerts():
    """Return synthetic alert feed samples from the existing SQLite alerts table."""
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT alert_id, location, severity, message, created_at FROM alerts ORDER BY created_at DESC LIMIT 50"
        ).fetchall()
    finally:
        conn.close()

    if rows:
        data = []
        for row in rows:
            data.append({
                "location": row["location"],
                "severity": row["severity"],
                "message": row["message"],
                "time": row["created_at"],
            })
        return jsonify({"success": True, "data": data})

    return jsonify({
        "success": True,
        "data": [
            {
                "location": "Mehjoor Nagar, Srinagar",
                "severity": "crit",
                "message": "3 ATMs · mule cluster forming · fund-freeze auto-drafted",
                "time": "just now",
            },
            {
                "location": "Kotwali branch, Ranchi",
                "severity": "warn",
                "message": "Withdrawal pattern matches digital-arrest scam signature",
                "time": "just now",
            },
        ],
    })
