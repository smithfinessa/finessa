import pathlib
import unittest


class PublicReadinessTests(unittest.TestCase):
    def test_main_readme_describes_honest_scope(self):
        root = pathlib.Path(__file__).resolve().parents[1]
        text = (root / "README.md").read_text()
        self.assertIn("controlled-access legal-research product", text.lower())
        self.assertIn("not a complete nationwide legal authority database", text.lower())

    def test_public_launch_gate_exists(self):
        root = pathlib.Path(__file__).resolve().parents[1]
        gate = root / "docs" / "legal" / "PUBLIC_LAUNCH_GATES.md"
        self.assertTrue(gate.exists())


if __name__ == "__main__":
    unittest.main()
