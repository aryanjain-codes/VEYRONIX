"""Authentication API routes for VEYRONIX."""
from __future__ import annotations

from flask import Blueprint, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from backend.database import get_db_connection
from backend.security import role_from_email_or_organization


auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/login")
def login():
    """Authenticate against the SQLite user row using Werkzeug password hashing.

    The server stores only the Flask session user_id and returns a minimal user
    object in the response. The existing UI endpoint route remains unchanged.
    """
    payload = request.get_json(silent=True) or {}
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""

    if not email or not password:
        return jsonify({"success": False, "message": "Email and password are required."}), 400

    conn = get_db_connection()
    try:
        user = conn.execute(
            "SELECT id, name, email, role, password_hash FROM users WHERE email = ?",
            (email,),
        ).fetchone()
    finally:
        conn.close()

    if not user:
        return jsonify({"success": False, "message": "Invalid email or password."}), 401

    if not check_password_hash(user["password_hash"], password):
        return jsonify({"success": False, "message": "Invalid email or password."}), 401

    session.clear()
    session["user_id"] = user["id"]

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


@auth_bp.post("/signup")
def signup():
    """Create a new local demo user record with a hashed password."""
    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""
    organization = payload.get("organization") or None

    if not name or not email or len(password) < 6:
        return jsonify({"success": False, "message": "Name, valid email, and password longer than 6 characters are required."}), 400

    # Ignore any client-sent role field. Determine role from server-side local policy.
    role = role_from_email_or_organization(email, organization)

    if role not in {"admin", "lea", "bank", "victim"}:
        role = "admin"

    conn = get_db_connection()
    try:
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            return jsonify({"success": False, "message": "User already exists."}), 409

        password_hash = generate_password_hash(password)
        conn.execute(
            "INSERT INTO users (name, email, password_hash, role, organization) VALUES (?, ?, ?, ?, ?)",
            (name, email, password_hash, role, organization),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        return jsonify({"success": False, "message": "Signup failed safely."}), 400
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


@auth_bp.post("/logout")
def logout():
    """Invalidate the encrypted Flask session cookie for this prototype session."""
    session.clear()
    return jsonify({"success": True, "message": "Logout successful"})
