import pathlib, sqlite3, unittest
class SchemaTests(unittest.TestCase):
    def test_schema_builds(self):
        schema=(pathlib.Path(__file__).resolve().parents[1]/'schema.sql').read_text()
        db=sqlite3.connect(':memory:'); db.executescript(schema)
        tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for required in {'jurisdictions','legal_authorities','case_workspaces','case_evidence','charge_elements','plan_entitlements','compliance_events'}:
            self.assertIn(required,tables)
if __name__=='__main__': unittest.main()
