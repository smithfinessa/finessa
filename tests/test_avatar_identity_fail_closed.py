import unittest
from unittest.mock import patch
from services import avatar_stack

class FakeFace:
    embedding = [0.0, 0.0]

class FakeCV2:
    @staticmethod
    def imread(path):
        return object()

class FakeFaceAnalysis:
    def __init__(self, name):
        self.name = name
    def prepare(self, **kwargs):
        pass
    def get(self, frame):
        return [FakeFace()]

class IdentityFailClosedTests(unittest.TestCase):
    def test_missing_reference_never_verifies(self):
        with patch.object(avatar_stack, "FaceAnalysis", FakeFaceAnalysis), \
             patch.object(avatar_stack, "cv2", FakeCV2), \
             patch.object(avatar_stack, "_reference_embedding", return_value=None), \
             patch("pathlib.Path.exists", return_value=True):
            result = avatar_stack.verify_face_image("example.png")
        self.assertFalse(result["ok"])
        self.assertFalse(result["verified"])

if __name__ == "__main__":
    unittest.main()
