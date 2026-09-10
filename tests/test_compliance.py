import unittest
from services.compliance_gateway import assess
class ComplianceTests(unittest.TestCase):
    def test_blocks_evidence_destruction(self): self.assertEqual(assess('destroy evidence')['decision'],'BLOCK')
    def test_reframes_plea_direction(self): self.assertEqual(assess('should I plead guilty')['decision'],'REFRAME')
    def test_allows_research(self): self.assertEqual(assess('what are the elements of this statute')['decision'],'ALLOW')
