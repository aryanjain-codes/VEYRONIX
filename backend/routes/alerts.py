"""Alerts and live feed API routes for VEYRONIX."""
from __future__ import annotations

from flask import Blueprint, jsonify

alerts_bp = Blueprint("alerts", __name__)


@alerts_bp.get("")
def list_alerts():
    """Return synthetic alert feed samples."""
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
