import sqlite3
import unittest
from services.legal_release_gate import STAGES, verification_state, candidate_authorities

class GateTests(unittest.TestCase):
    def test_missing_stage_denies(self):
        self.assertFalse(verification_state([{'stage': s, 'result': 'pass'} for s in STAGES[:-1]]))

    def test_later_failure_revokes(self):
        rows = [{'stage': s, 'result': 'pass'} for s in STAGES]
        rows.append({'stage': 'CURRENCY_VERIFIED', 'result': 'fail'})
        self.assertFalse(verification_state(rows))

    def test_all_pass(self):
        self.assertTrue(verification_state([{'stage': s, 'result': 'pass'} for s in STAGES]))

    def test_candidate_selection(self):
        db = sqlite3.connect(':memory:'); db.row_factory = sqlite3.Row
        db.executescript('CREATE TABLE legal_authorities(id INTEGER PRIMARY KEY,title TEXT,citation TEXT,proposition_text TEXT,jurisdiction_code TEXT,filing_ready INTEGER); CREATE TABLE authority_verification_records(id INTEGER PRIMARY KEY,authority_id INTEGER,stage TEXT,result TEXT);')
        db.execute("INSERT INTO legal_authorities VALUES(1,'Example','123 X 4','Example proposition','CO',1)")
        for stage in STAGES:
            db.execute('INSERT INTO authority_verification_records(authority_id,stage,result) VALUES(1,?,?)', (stage,'pass'))
        self.assertEqual(len(candidate_authorities(db,'CO')),1)
        self.assertEqual(candidate_authorities(db,'MI'),[])
        db.execute("INSERT INTO authority_verification_records(authority_id,stage,result) VALUES(1,'CITATION_VERIFIED','fail')")
        self.assertEqual(candidate_authorities(db,'CO'),[])

if __name__ == '__main__': unittest.main()
