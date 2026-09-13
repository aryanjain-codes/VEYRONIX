"""Case workflow API routes for VEYRONIX."""
from __future__ import annotations

from flask import Blueprint, jsonify, request

cases_bp = Blueprint("cases", __name__)


@cases_bp.get("")
def list_cases():
    """Return synthetic case management sample records."""
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
def update_case_status(case_id: str):
    """Update case status by sample case ID; skeleton only."""
    payload = request.get_json(silent=True) or {}
    new_status = payload.get("status") or "investigating"
    return jsonify({
        "success": True,
        "message": "Case status updated",
        "case_id": case_id,
        "status": new_status,
    })
