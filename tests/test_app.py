import os, tempfile, unittest
class AppSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(); os.environ['DATABASE_PATH']=cls.tmp.name+'/test.db'
        from db import init_db
        from seed import seed
        init_db(); seed()
        from app import app
        app.config.update(TESTING=True, SECRET_KEY='test')
        cls.client=app.test_client()
    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()
    def test_health(self):
        r=self.client.get('/health'); self.assertEqual(r.status_code,200); self.assertEqual(r.json['status'],'ok')
    def test_home(self): self.assertEqual(self.client.get('/').status_code,200)
    def test_plans(self): self.assertEqual(len(self.client.get('/api/plans').json['plans']),4)
    def test_jurisdiction(self): self.assertEqual(self.client.get('/api/jurisdiction/resolve?jurisdiction=MI').json['jurisdiction_code'],'MI')
    def test_provider_status(self): self.assertEqual(self.client.get('/api/legal/providers').status_code,200)
