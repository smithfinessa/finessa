"""Regression tests for mandatory private-workspace security controls.

Run with: python -m unittest discover -s tests
"""
import unittest
from unittest.mock import patch

class PrivateWorkspaceSecurityTests(unittest.TestCase):
    def setUp(self):
        import app as module
        self.module = module
        self.client = module.app.test_client()
        module.app.config["TESTING"] = True

    def test_private_workspace_requires_authentication(self):
        with patch.object(self.module, "ACCESS_PASSWORD", "test-secret"):
            response = self.client.get("/cases")
            self.assertEqual(response.status_code, 302)
            self.assertIn("/login", response.location)

    def test_authenticated_case_access(self):
        with patch.object(self.module, "ACCESS_PASSWORD", "test-secret"):
            with self.client.session_transaction() as sess:
                sess["authenticated"] = True
            response = self.client.get("/cases")
            self.assertEqual(response.status_code, 200)

    def test_missing_csrf_token_is_rejected(self):
        with patch.object(self.module, "ACCESS_PASSWORD", "test-secret"):
            response = self.client.post("/logout")
            self.assertEqual(response.status_code, 400)

    def test_no_password_configuration_denies_case_access(self):
        with patch.object(self.module, "ACCESS_PASSWORD", ""):
            response = self.client.get("/cases")
            self.assertIn(response.status_code, (401, 403, 503))

if __name__ == "__main__":
    unittest.main()
