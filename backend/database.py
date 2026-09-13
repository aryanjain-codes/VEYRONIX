"""SQLite-backed data access helpers for the VEYRONIX Flask backend."""
from __future__ import annotations

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "veyronix.db"


def init_db() -> None:
    """Create the SQLite database file and required tables for the first working version."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                organization TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                complaint_id TEXT NOT NULL UNIQUE,
                complainant_name TEXT,
                fraud_type TEXT,
                amount REAL,
                city TEXT,
                bank TEXT,
                branch TEXT,
                complaint_date TEXT,
                status TEXT NOT NULL DEFAULT 'new',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT NOT NULL UNIQUE,
                complaint_id TEXT NOT NULL,
                amount REAL NOT NULL,
                bank TEXT,
                account TEXT,
                city TEXT,
                transaction_type TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(complaint_id) REFERENCES complaints(complaint_id)
            );

            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prediction_id TEXT NOT NULL UNIQUE,
                complaint_id TEXT,
                fraud_type TEXT,
                city TEXT,
                bank TEXT,
                risk_score REAL,
                risk_tier TEXT,
                window_hours INTEGER,
                cash_out_point TEXT,
                explanation TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(complaint_id) REFERENCES complaints(complaint_id)
            );

            CREATE TABLE IF NOT EXISTS hotspots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hotspot_id TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                state TEXT,
                category TEXT,
                latitude REAL,
                longitude REAL,
                risk_score REAL,
                time_window_hours INTEGER,
                tier TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id TEXT NOT NULL UNIQUE,
                location TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id TEXT NOT NULL UNIQUE,
                location TEXT NOT NULL,
                severity TEXT NOT NULL,
                status TEXT NOT NULL,
                officer TEXT,
                opened_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                hotspot_id TEXT
            );

            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT,
                role TEXT,
                action TEXT NOT NULL,
                target TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        conn.commit()
        seed_demo_data(conn)
    finally:
        conn.close()


def seed_demo_data(conn: sqlite3.Connection) -> None:
    """Insert a small synthetic/demo dataset into the SQLite database.

    All data inserted here is synthetic and intended for development/demo use only.
    """
    if conn.execute("SELECT 1 FROM users LIMIT 1").fetchone() is None:
        conn.execute(
            "INSERT INTO users (name, email, password_hash, role, organization) VALUES (?, ?, ?, ?, ?)",
            ("Demo Admin", "admin@veyronix.demo", "synthetic_hash", "admin", "I4C Demo"),
        )
        conn.execute(
            "INSERT INTO users (name, email, password_hash, role, organization) VALUES (?, ?, ?, ?, ?)",
            ("Demo Analyst", "analyst@veyronix.demo", "synthetic_hash", "analyst", "Cyber Crime Wing"),
        )

    if conn.execute("SELECT 1 FROM complaints LIMIT 1").fetchone() is None:
        conn.execute(
            "INSERT INTO complaints (complaint_id, complainant_name, fraud_type, amount, city, bank, branch, complaint_date, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("NCRP-2026-100001", "Demo Complainant", "UPI / payment fraud", 185000.0, "Delhi", "State Bank of India", "Central Branch", "2026-09-14", "new"),
        )
        conn.execute(
            "INSERT INTO complaints (complaint_id, complainant_name, fraud_type, amount, city, bank, branch, complaint_date, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("NCRP-2026-100002", "Demo Complainant", "Digital-arrest scam", 120000.0, "Srinagar", "Jammu & Kashmir Bank", "Mehjoor Nagar", "2026-09-14", "investigating"),
        )

    if conn.execute("SELECT 1 FROM transactions LIMIT 1").fetchone() is None:
        conn.execute(
            "INSERT INTO transactions (transaction_id, complaint_id, amount, bank, account, city, transaction_type, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("TXN-2026-0001", "NCRP-2026-100001", 185000.0, "State Bank of India", "XXXXXXXX1234", "Delhi", "UPI", "pending"),
        )
        conn.execute(
            "INSERT INTO transactions (transaction_id, complaint_id, amount, bank, account, city, transaction_type, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("TXN-2026-0002", "NCRP-2026-100002", 120000.0, "Jammu & Kashmir Bank", "XXXXXXXX8899", "Srinagar", "ATM withdrawal", "flagged"),
        )

    if conn.execute("SELECT 1 FROM predictions LIMIT 1").fetchone() is None:
        conn.execute(
            "INSERT INTO predictions (prediction_id, complaint_id, fraud_type, city, bank, risk_score, risk_tier, window_hours, cash_out_point, explanation) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("PRED-2026-0001", "NCRP-2026-100001", "UPI / payment fraud", "Delhi", "State Bank of India", 76.0, "warn", 48, "ATM-110", "Synthetic demo explanation: suspicious mule clustering"),
        )
        conn.execute(
            "INSERT INTO predictions (prediction_id, complaint_id, fraud_type, city, bank, risk_score, risk_tier, window_hours, cash_out_point, explanation) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("PRED-2026-0002", "NCRP-2026-100002", "Digital-arrest scam", "Srinagar", "Jammu & Kashmir Bank", 91.0, "crit", 24, "ATM-123", "Synthetic demo explanation: digital arrest pattern"),
        )

    if conn.execute("SELECT 1 FROM alerts LIMIT 1").fetchone() is None:
        conn.execute(
            "INSERT INTO alerts (alert_id, location, severity, message) VALUES (?, ?, ?, ?)",
            ("ALERT-2026-0001", "Mehjoor Nagar, Srinagar", "crit", "3 ATMs · mule cluster forming · fund-freeze auto-drafted"),
        )
        conn.execute(
            "INSERT INTO alerts (alert_id, location, severity, message) VALUES (?, ?, ?, ?)",
            ("ALERT-2026-0002", "Kotwali branch, Ranchi", "warn", "Withdrawal pattern matches digital-arrest scam signature"),
        )

    if conn.execute("SELECT 1 FROM cases LIMIT 1").fetchone() is None:
        conn.execute(
            "INSERT INTO cases (case_id, location, severity, status, officer, opened_at, hotspot_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("CYB-2026-4471", "Mehjoor Nagar, Srinagar", "crit", "new", "Insp. R. Kaul", "2026-09-14T09:41:02", "HSP-001"),
        )
        conn.execute(
            "INSERT INTO cases (case_id, location, severity, status, officer, opened_at, hotspot_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("CYB-2026-4468", "Kotwali branch, Ranchi", "warn", "investigating", "SI M. Toppo", "2026-09-14T09:38:47", "HSP-002"),
        )

    if conn.execute("SELECT 1 FROM audit_logs LIMIT 1").fetchone() is None:
        conn.execute(
            "INSERT INTO audit_logs (user, role, action, target) VALUES (?, ?, ?, ?)",
            ("utkarsh.k", "I4C Admin", "Viewed", "Risk Heatmap — Srinagar cluster"),
        )
        conn.execute(
            "INSERT INTO audit_logs (user, role, action, target) VALUES (?, ?, ?, ?)",
            ("r.kaul", "Field Investigator", "Opened case", "CYB-2026-4471"),
        )

    conn.commit()


def get_db_connection() -> sqlite3.Connection:
    """Return a SQLite connection for this Flask app."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_db_health() -> dict:
    """Return a simple SQLite database health/status payload for an API endpoint."""
    required_tables = {
        "users", "complaints", "transactions", "predictions", "alerts", "cases", "audit_logs",
    }
    try:
        conn = get_db_connection()
        try:
            existing = {
                row["name"] for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
                ).fetchall()
            }
            missing = sorted(required_tables - existing)
            counts = {}
            for table in sorted(required_tables):
                try:
                    row = conn.execute(f"SELECT COUNT(*) AS total FROM {table}").fetchone()
                    counts[table] = int(row["total"])
                except sqlite3.Error:
                    counts[table] = 0
            return {
                "success": True,
                "database": "sqlite",
                "status": "healthy" if not missing else "degraded",
                "tables_missing": missing,
                "tables_present": len(required_tables & existing),
                "table_count": len(existing),
                "counts": counts,
                "db_path": str(DB_PATH),
            }
        finally:
            conn.close()
    except Exception as exc:
        return {
            "success": False,
            "database": "sqlite",
            "status": "error",
            "message": str(exc),
            "db_path": str(DB_PATH),
        }
