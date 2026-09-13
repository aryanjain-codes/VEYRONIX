"""Authentication API routes for VEYRONIX."""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from backend.database import get_db_connection


auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/login")
def login():
    """Return a minimal login simulation for the static frontend prototype."""
    payload = request.get_json(silent=True) or {}
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""
    role = payload.get("role") or "admin"

    if not email or not password:
        return jsonify({"success": False, "message": "Email and password are required."}), 400

    # First working version: allow demo signup/login by returning a synthetic session payload.
    # Password is not verified yet. This is intentionally a skeleton.
    conn = get_db_connection()
    try:
        user = conn.execute(
            "SELECT id, name, email, role FROM users WHERE email = ?",
            (email,),
        ).fetchone()
    finally:
        conn.close()

    if user:
        return jsonify({
            "success": True,
            "message": "Login successful",
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "role": user["role"],
            },
            "token": "demo-token",
        })

    return jsonify({
        "success": True,
        "message": "Demo login accepted",
        "user": {
            "id": 1,
            "name": "Demo User",
            "email": email,
            "role": role,
        },
        "token": "demo-token",
    })


@auth_bp.post("/signup")
def signup():
    """Create a new demo user record skeleton."""
    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""
    role = payload.get("role") or "admin"
    organization = payload.get("organization") or None

    if not name or not email or len(password) < 6:
        return jsonify({"success": False, "message": "Name, valid email, and password longer than 6 characters are required."}), 400

    conn = get_db_connection()
    try:
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            return jsonify({"success": False, "message": "User already exists."}), 409

        conn.execute(
            "INSERT INTO users (name, email, password_hash, role, organization) VALUES (?, ?, ?, ?, ?)",
            (name, email, password, role, organization),
        )
        conn.commit()
    finally:
        conn.close()

    return jsonify({
        "success": True,
        "message": "Signup successful",
        "user": {
            "name": name,
            "email": email,
            "role": role,
            "organization": organization,
        },
    })
