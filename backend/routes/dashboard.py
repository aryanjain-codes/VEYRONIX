"""Dashboard statistics and database health API routes for VEYRONIX."""
from __future__ import annotations

from flask import Blueprint, jsonify

from backend.database import get_db_health


dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.get("/health")
def get_database_health():
    """Return a simple SQLite-backed database health/status envelope.

    This endpoint is intentionally synthetic/demo-safe and uses the same
    SQLite file the app initializes at startup.
    """
    return jsonify(get_db_health())


@dashboard_bp.get("/stats")
def get_dashboard_stats():
    """Return synthetic dashboard KPIs in a machine-readable JSON shape."""
    return jsonify({
        "success": True,
        "stats": {
            "active_watch_zones": 247,
            "critical_alerts_today": 18,
            "flagged_fund_freeze_24h": "₹6.2 Cr",
            "model_hit_rate": "86%",
            "critical_alerts_trend": "+3 vs yesterday",
        },
    })
