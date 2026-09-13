"""Hotspot and map API routes for VEYRONIX."""
from __future__ import annotations

from flask import Blueprint, jsonify, request

hotspots_bp = Blueprint("hotspots", __name__)


@hotspots_bp.get("")
def list_hotspots():
    """Return a synthetic hotspots list, compatible with current frontend demo data expectations."""
    sample_hotspots = [
        {
            "id": "h1",
            "name": "Mehjoor Nagar, Srinagar",
            "state": "Jammu & Kashmir",
            "category": "Digital-arrest scam",
            "lat": 34.1122,
            "lng": 74.8320,
            "risk": 91,
            "window": 24,
            "tier": "crit",
        },
        {
            "id": "h2",
            "name": "Kotwali branch, Ranchi",
            "state": "Jharkhand",
            "category": "UPI / payment fraud",
            "lat": 23.3629,
            "lng": 85.3346,
            "risk": 74,
            "window": 48,
            "tier": "warn",
        },
    ]

    state_filter = request.args.get("state")
    category_filter = request.args.get("category")
    conf = request.args.get("conf", default=0, type=int)
    window_value = request.args.get("window", default=48, type=int)

    filtered = sample_hotspots
    if state_filter and state_filter != "all":
        filtered = [x for x in filtered if x["state"] == state_filter]
    if category_filter and category_filter != "all":
        filtered = [x for x in filtered if x["category"] == category_filter]
    filtered = [x for x in filtered if x["risk"] >= conf and x["window"] <= window_value]

    return jsonify({"success": True, "data": filtered})
