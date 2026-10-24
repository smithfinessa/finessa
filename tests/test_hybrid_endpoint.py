import os
import tempfile
import unittest
from unittest.mock import patch

class HybridEndpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        os.environ["DATABASE_PATH"] = cls.tmp.name + "/hybrid.db"
        from db import init_db
        from seed import seed
        init_db()
        seed()
        from app import app
        app.config.update(TESTING=True, SECRET_KEY="test")
        cls.client = app.test_client()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def _post(self, message):
        with self.client.session_transaction() as session:
            session["csrf_token"] = "testing-token"
        return self.client.post("/api/finessa/chat", json={"message": message},
                                headers={"X-CSRF-Token": "testing-token"})

    @patch.dict(os.environ, {"FINESSA_AI_ENABLED": "1"})
    @patch("app.hybrid_infer")
    def test_model_response(self, mock_infer):
        from services.hybrid_ai import InferenceResult
        mock_infer.return_value = InferenceResult("A useful response", "local", "test-model")
        response = self._post("Explain research methods")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["answer"], "A useful response")
        self.assertEqual(response.json["ai_provider"], "local")

    @patch.dict(os.environ, {"FINESSA_AI_ENABLED": "1"})
    @patch("app.hybrid_infer")
    def test_model_unavailable_keeps_existing_assistant(self, mock_infer):
        from services.hybrid_ai import InferenceUnavailable
        mock_infer.side_effect = InferenceUnavailable("offline")
        response = self._post("Explain research methods")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["ai_provider"], "legacy_fallback")
        self.assertTrue(response.json["answer"])

    @patch.dict(os.environ, {"FINESSA_AI_ENABLED": "0"})
    @patch("app.hybrid_infer")
    def test_disabled_mode_does_not_call_model(self, mock_infer):
        response = self._post("Explain research methods")
        self.assertEqual(response.status_code, 200)
        mock_infer.assert_not_called()

if __name__ == "__main__":
    unittest.main()
