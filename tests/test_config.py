import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class DotenvTests(unittest.TestCase):
    def test_repository_env_file_is_loaded(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / ".env").write_text("FINESSA_SECRET=loaded-from-dotenv\n")
            (Path(tmp) / "config.py").write_text((root / "config.py").read_text())
            result = subprocess.run(
                [sys.executable, "-c", "import config; print(config.SECRET_KEY)"],
                cwd=tmp,
                capture_output=True,
                text=True,
                check=True,
                env={k: v for k, v in os.environ.items() if k != "FINESSA_SECRET"},
            )
            self.assertEqual(result.stdout.strip(), "loaded-from-dotenv")


if __name__ == "__main__":
    unittest.main()
