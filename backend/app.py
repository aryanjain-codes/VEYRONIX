"""Main Flask application entry point for VEYRONIX.

This creates a minimal Flask backend skeleton that keeps the existing
frontend static HTML/CSS/JS in index.html unchanged.
"""
from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, jsonify, send_file

from backend.database import get_db_health, init_db
from backend.routes import register_blueprints

BASE_DIR = Path(__file__).resolve().parent.parent


def create_app() -> Flask:
    """Create and configure the Flask application instance."""
    app = Flask(__name__)
    app.config["JSON_SORT_KEYS"] = False
    app.config["DATABASE"] = str(BASE_DIR / "data" / "veyronix.db")
    app.config["SECRET_KEY"] = os.environ["VEYRONIX_SECRET_KEY"]

    @app.after_request
    def add_cors_headers(response):
        """Allow the static frontend served from the local workspace to call Flask JSON APIs."""
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        return response

    # Ensure SQLite file/database tables exist and the demo seed data is ready.
    init_db()

    # Register all route blueprints.
    register_blueprints(app)

    @app.get("/")
    def frontend_root():
        """Serve the existing project-root static frontend file at the base URL."""
        return send_file(BASE_DIR / "index.html", mimetype="text/html")

    @app.get("/api/health")
    def api_health():
        """Return a simple API health/status response backed by the SQLite database helper."""
        return jsonify(get_db_health())

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=False)
