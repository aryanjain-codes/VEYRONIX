"""Blueprint registration for VEYRONIX backend routes."""
from __future__ import annotations

from flask import Flask

from .auth import auth_bp
from .complaints import complaints_bp
from .dashboard import dashboard_bp
from .hotspots import hotspots_bp
from .predictions import predictions_bp
from .alerts import alerts_bp
from .cases import cases_bp
from .audit import audit_bp


def register_blueprints(app: Flask) -> None:
    """Register all API route blueprints with the Flask app."""
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(complaints_bp, url_prefix="/api/complaints")
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
    app.register_blueprint(hotspots_bp, url_prefix="/api/hotspots")
    app.register_blueprint(predictions_bp, url_prefix="/api/predictions")
    app.register_blueprint(alerts_bp, url_prefix="/api/alerts")
    app.register_blueprint(cases_bp, url_prefix="/api/cases")
    app.register_blueprint(audit_bp, url_prefix="/api/audit")
