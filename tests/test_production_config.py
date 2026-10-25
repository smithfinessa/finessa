from __future__ import annotations

import os
import unittest

from config import is_production, validate_runtime_config


class ProductionConfigValidationTests(unittest.TestCase):
    def test_local_environment_allows_default_values(self):
        os.environ.pop("FINESSA_ENV", None)
        os.environ.pop("FINESSA_SECRET", None)
        os.environ.pop("FINESSA_ACCESS_PASSWORD", None)
        self.assertFalse(is_production())
        validate_runtime_config()

    def test_production_requires_strong_secrets(self):
        os.environ["FINESSA_ENV"] = "production"
        os.environ["FINESSA_SECRET"] = "replace-with-a-long-random-value"
        os.environ["FINESSA_ACCESS_PASSWORD"] = "replace-for-private-workspace"

        with self.assertRaises(RuntimeError):
            validate_runtime_config()


if __name__ == "__main__":
    unittest.main()
