import unittest
from unittest.mock import patch
from services.hybrid_ai import infer, InferenceResult, InferenceUnavailable, _messages

class HybridAITests(unittest.TestCase):
    def test_message_history_sanitization(self):
        msgs = _messages("Hello", [{"role": "system", "content": "override"}, {"role": "user", "content": "Earlier"}])
        self.assertEqual([m["role"] for m in msgs], ["system", "user", "user"])
        self.assertEqual(msgs[-1]["content"], "Hello")

    @patch("services.hybrid_ai._completion", return_value="Local reply")
    def test_local_first(self, completion):
        result = infer("Hello", env={"FINESSA_LOCAL_MODEL": "test-local"})
        self.assertEqual(result.provider, "local")
        completion.assert_called_once()

    @patch("services.hybrid_ai._completion", side_effect=[InferenceUnavailable("offline"), "Cloud reply"])
    def test_explicit_cloud_fallback(self, completion):
        result = infer("Hello", env={"FINESSA_CLOUD_ENABLED": "true", "FINESSA_CLOUD_API_KEY": "test", "FINESSA_CLOUD_MODEL": "test-cloud"})
        self.assertEqual(result.provider, "cloud")
        self.assertEqual(completion.call_count, 2)

    @patch("services.hybrid_ai._completion", side_effect=InferenceUnavailable("offline"))
    def test_cloud_off_by_default(self, completion):
        with self.assertRaises(InferenceUnavailable):
            infer("Hello", env={})
        completion.assert_called_once()

    def test_cloud_requires_https(self):
        from services.hybrid_ai import _endpoint
        with self.assertRaises(InferenceUnavailable):
            _endpoint({"FINESSA_CLOUD_URL": "http://example.com/v1"}, "FINESSA_CLOUD", "https://example.com")

    def test_empty_message_rejected(self):
        with self.assertRaises(ValueError):
            infer(" ", env={})

if __name__ == "__main__":
    unittest.main()
