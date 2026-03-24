import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app import create_app


class AuthRouteTests(unittest.TestCase):
    def setUp(self):
        app = create_app()
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_signup_requires_required_fields(self):
        response = self.client.post("/api/auth/signup", json={"email": "user@example.com"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["status"], "error")
        self.assertEqual(
            response.get_json()["error"]["details"]["missing"],
            ["name", "password"],
        )

    def test_signup_rejects_short_password(self):
        response = self.client.post(
            "/api/auth/signup",
            json={
                "name": "Jane Doe",
                "email": "user@example.com",
                "password": "short",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json()["error"]["message"],
            "password must be at least 8 characters long",
        )

    def test_login_requires_email_and_password(self):
        response = self.client.post("/api/auth/login", json={"email": "user@example.com"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["status"], "error")
        self.assertEqual(response.get_json()["error"]["details"]["missing"], ["password"])

    def test_signup_returns_consistent_success_shape(self):
        auth_result = SimpleNamespace(
            user=SimpleNamespace(
                id="user-123",
                email="user@example.com",
                email_confirmed_at=None,
                last_sign_in_at=None,
                user_metadata={"name": "Jane Doe"},
            ),
            session=SimpleNamespace(
                access_token="token",
                refresh_token="refresh",
                token_type="bearer",
                expires_in=3600,
                expires_at=1234567890,
            ),
        )
        fake_client = SimpleNamespace(
            auth=SimpleNamespace(sign_up=lambda payload: auth_result),
            table=lambda name: SimpleNamespace(
                upsert=lambda payload, on_conflict=None: SimpleNamespace(execute=lambda: None)
            ),
        )

        with patch("routes.get_supabase_client", return_value=fake_client):
            response = self.client.post(
                "/api/auth/signup",
                json={
                    "name": "Jane Doe",
                    "email": "user@example.com",
                    "password": "securepass123",
                },
            )

        self.assertEqual(response.status_code, 201)
        body = response.get_json()
        self.assertEqual(body["status"], "success")
        self.assertEqual(body["data"]["user"]["email"], "user@example.com")
        self.assertEqual(body["data"]["session"]["access_token"], "token")

    def test_login_maps_invalid_credentials_to_401(self):
        fake_client = SimpleNamespace(
            auth=SimpleNamespace(
                sign_in_with_password=lambda payload: (_ for _ in ()).throw(
                    Exception("Invalid login credentials")
                )
            )
        )

        with patch("routes.get_supabase_client", return_value=fake_client):
            response = self.client.post(
                "/api/auth/login",
                json={
                    "email": "user@example.com",
                    "password": "securepass123",
                },
            )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json()["error"]["message"], "Invalid email or password")


if __name__ == "__main__":
    unittest.main()
