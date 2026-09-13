"""Audit log API routes for VEYRONIX."""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from backend.database import get_db_connection
from backend.security import login_required, roles_required

audit_bp = Blueprint("audit", __name__)


@audit_bp.get("/logs")
@login_required
@roles_required("admin", "bank", "lea", "victim")
def list_audit_logs():
    """Return a synthetic audit log record beginning from SQLite-backed storage if available."""
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT user, role, action, target, created_at FROM audit_logs ORDER BY created_at DESC LIMIT 50"
        ).fetchall()
    finally:
        conn.close()

    if rows:
        return jsonify({"success": True, "data": [dict(row) for row in rows]})

    return jsonify({
        "success": True,
        "data": [
            {
                "user": "utkarsh.k",
                "role": "I4C Admin",
                "action": "Viewed",
                "target": "Risk Heatmap — Srinagar cluster",
                "created_at": "2026-09-14T09:41:02",
            },
            {
                "user": "r.kaul",
                "role": "Field Investigator",
                "action": "Opened case",
                "target": "CYB-2026-4471",
                "created_at": "2026-09-14T09:38:47",
            },
        ],
    })


@audit_bp.post("/logs")
@login_required
@roles_required("admin", "bank", "lea")
def append_audit_log():
    """Create a minimal audit log entry skeleton."""
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return jsonify({"success": False, "message": "JSON object required."}), 400

    user = payload.get("user") or "system"
    role = payload.get("role") or "system"
    action = payload.get("action") or "Viewed"
    target = payload.get("target") or "VEYRONIX"

    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO audit_logs (user, role, action, target) VALUES (?, ?, ?, ?)",
            (user, role, action, target),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        return jsonify({"success": False, "message": "Audit log append failed safely."}), 400
    finally:
        conn.close()

    return jsonify({"success": True, "message": "Audit log entry added"})
