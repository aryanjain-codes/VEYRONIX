from __future__ import annotations

import unittest

from backend.app import create_app
from backend.database import get_db_connection


DEMO_COMPLAINT_ID = "NCRP-SYNTHETIC-SIH26184-DEL-001"


class DemoScenarioRouteChainTest(unittest.TestCase):
    """Regression-style no-framework test for the seeded SIH demo record and routes."""

    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_seeded_demo_scenario_exists(self):
        conn = get_db_connection()
        try:
            row = conn.execute(
                "SELECT complaint_id, complainant_name, fraud_type, amount, city, bank, branch FROM complaints WHERE complaint_id = ?",
                (DEMO_COMPLAINT_ID,),
            ).fetchone()
        finally:
            conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row["complainant_name"], "Synthetic Complainant")
        self.assertEqual(row["fraud_type"], "Digital-arrest scam")
        self.assertEqual(row["city"], "Srinagar")
        self.assertEqual(row["bank"], "State Bank of India")

    def test_demo_scenario_routes_are_deterministic_and_shape_safe(self):
        login = self.client.post(
            "/api/auth/login",
            json={
                "email": "admin@veyronix.demo",
                "password": "synthetic_hash",
            },
        )
        self.assertEqual(login.status_code, 200)

        complaint = self.client.post(
            "/api/complaints",
            json={
                "complaint_id": DEMO_COMPLAINT_ID,
                "complainant_name": "Synthetic Complainant",
                "fraud_type": "Digital-arrest scam",
                "amount": 85000,
                "city": "Srinagar",
                "bank": "State Bank of India",
                "branch": "Mehjoor Nagar, Srinagar",
                "complaint_date": "2026-09-14",
            },
        )
        self.assertEqual(complaint.status_code, 200)

        prediction = self.client.post(
            "/api/predictions",
            json={
                "complaint_id": DEMO_COMPLAINT_ID,
                "fraud_type": "Digital-arrest scam",
                "amount": 85000,
                "city": "Srinagar",
                "bank": "State Bank of India",
                "branch": "Mehjoor Nagar, Srinagar",
                "transaction_count": 2,
                "total_transaction_amount": 85000,
                "max_transaction_amount": 85000,
            },
        )
        self.assertEqual(prediction.status_code, 200)
        data = prediction.get_json()
        self.assertEqual(data["synthetic_data_flag"], "SYNTHETIC_DEMO")
        self.assertIn(data["priority"], {"HIGH", "CRITICAL"})
        self.assertGreaterEqual(data["risk_score"], 0)

        hotspots = self.client.get("/api/hotspots")
        self.assertEqual(hotspots.status_code, 200)
        alerts = self.client.get("/api/alerts")
        self.assertEqual(alerts.status_code, 200)
        cases = self.client.get("/api/cases")
        self.assertEqual(cases.status_code, 200)
        audit = self.client.get("/api/audit/logs")
        self.assertEqual(audit.status_code, 200)


if __name__ == "__main__":
    unittest.main()
