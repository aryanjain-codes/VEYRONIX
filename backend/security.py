"""Lightweight local SIH prototype authentication and role enforcement helpers.

These helpers intentionally emphasize a small, inspectable server-side session model
for the existing static HTML frontend. They are not a production government/banking
identity system.
"""
from __future__ import annotations

from functools import wraps
from typing import Callable

from flask import g, jsonify, request, session

from backend.database import get_db_connection

VALID_ROLES = {"admin", "lea", "bank", "victim"}


def get_current_user_from_session() -> dict | None:
    """Return the current authenticated user from the database-backed Flask session.

    The session stores only the minimum user identifier. Role is always resolved
    from the database row for the current user ID; it is never trusted from the
    request payload or any client-sent role field.
    """
    user_id = session.get("user_id")
    if not user_id:
        return None

    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT id, name, email, role FROM users WHERE id = ?",
            (int(user_id),),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        session.clear()
        return None

    return {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "role": row["role"],
    }


def login_required(fn: Callable):
    """Ensure the current request has a server-side session for a known user."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = get_current_user_from_session()
        if user is None:
            return jsonify({
                "success": False,
                "message": "Authentication required. Local SIH prototype session missing or expired.",
            }), 401

        g.current_user = user
        return fn(*args, **kwargs)

    return wrapper


def roles_required(*allowed_roles: str):
    """Require one of the provided server-side role values.

    The active role is always re-read from the database-backed session user.
    The client cannot control this check by sending a role field.
    """

    allowed = {role.lower() for role in allowed_roles}

    def decorator(fn: Callable):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = get_current_user_from_session()
            if user is None:
                return jsonify({
                    "success": False,
                    "message": "Authentication required. Local SIH prototype session missing or expired.",
                }), 401

            role = (user.get("role") or "").lower()
            if role not in VALID_ROLES:
                return jsonify({
                    "success": False,
                    "message": "Forbidden role. Local SIH prototype role is not recognized.",
                }), 403

            if role not in allowed:
                return jsonify({
                    "success": False,
                    "message": "Forbidden. Your authenticated local SIH prototype role cannot access this API.",
                }), 403

            g.current_user = user
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def require_json_object() -> tuple[dict | None, object | None]:
    """Return a validated JSON object payload or a 400 response tuple if malformed."""
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return None, (jsonify({"success": False, "message": "JSON object body required."}), 400)
    return payload, None


def role_from_email_or_organization(email: str, organization: str | None = None) -> str:
    """Map a signup request to an allowed role without trusting the frontend's role field.

    This is a local SIH prototype-safe default mapping. The server side determines
    the requested role from the email and organization metadata rather than trusting
    a client-sent role value.
    """
    lowered = (email or "").lower()
    org = (organization or "").lower()

    if "bank" in lowered or "bank" in org or "fi" in lowered or "financial" in org:
        return "bank"
    if "lea" in lowered or "police" in lowered or "investigator" in org or "cyber" in org:
        return "lea"
    if "victim" in lowered or "citizen" in lowered or "complainant" in org:
        return "victim"
    return "admin"
