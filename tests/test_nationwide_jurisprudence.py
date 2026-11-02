import json
import os
import unittest
from unittest.mock import patch

from services import nationwide_jurisprudence as research


class JurisprudenceRetrievalTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {}, clear=False)
        self.env.start()
        os.environ.pop(research.COURT_IDS_ENV, None)

    def tearDown(self):
        self.env.stop()

    def test_state_search_requires_explicit_court_scope(self):
        with self.assertRaisesRegex(research.JurisprudenceProviderError, "reviewed CourtListener court IDs"):
            research.search_opinions("contract", jurisdiction="CA")

    def test_configured_state_courts_are_normalized_and_deduplicated(self):
        os.environ[research.COURT_IDS_ENV] = json.dumps({"ca": ["Cal", "cal", "calctapp"]})
        self.assertEqual(research.configured_courts("CA"), ["cal", "calctapp"])

    def test_invalid_mapping_fails_closed(self):
        os.environ[research.COURT_IDS_ENV] = "not-json"
        with self.assertRaises(research.JurisprudenceProviderError):
            research.configured_courts("CA")

    @patch.object(research, "_get_json")
    def test_national_search_follows_safe_cursor_and_deduplicates(self, get_json):
        get_json.side_effect = [
            {"results": [{"id": 1, "caseName": "First", "absolute_url": "/opinion/1/"}],
             "next": "https://www.courtlistener.com/api/rest/v4/search/?cursor=next"},
            {"results": [{"id": 1, "caseName": "Duplicate"}, {"id": 2, "caseName": "Second"}], "next": None},
        ]
        payload = research.search_opinions("privacy", limit=10, max_pages_per_court=3)
        self.assertEqual([item["external_id"] for item in payload["results"]], ["1", "2"])
        self.assertEqual(payload["pages_fetched"], 2)
        self.assertFalse(payload["more_available"])
        self.assertEqual(get_json.call_count, 2)

    @patch.object(research, "_get_json")
    def test_state_search_passes_explicit_court_filter(self, get_json):
        os.environ[research.COURT_IDS_ENV] = json.dumps({"MI": ["mich"]})
        get_json.return_value = {"results": [{"id": "x", "court": "mich", "case_name": "Example"}], "next": None}
        payload = research.search_opinions("procedure", jurisdiction="MI")
        self.assertIn("court=mich", get_json.call_args.args[0])
        self.assertEqual(payload["results"][0]["jurisdiction_code"], "MI")

    @patch.object(research, "_get_json")
    def test_rejects_untrusted_pagination_url(self, get_json):
        get_json.return_value = {"results": [], "next": "https://attacker.example/collect"}
        with self.assertRaisesRegex(research.JurisprudenceProviderError, "unexpected pagination URL"):
            research.search_opinions("procedure")

    def test_validates_limit_and_date_order(self):
        with self.assertRaises(ValueError):
            research.search_opinions("x", limit=0)
        with self.assertRaises(ValueError):
            research.search_opinions("x", date_filed_min="2024-02-01", date_filed_max="2024-01-01")


if __name__ == "__main__":
    unittest.main()
