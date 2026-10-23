import unittest
from services.avatar_config import validate_config, IDENTITY_ID, MASTER_IMAGE

class AvatarConfigTests(unittest.TestCase):
    def test_defaults(self):
        avatar = validate_config()
        self.assertEqual(avatar.identity_id, IDENTITY_ID)
        self.assertEqual(avatar.master_image, MASTER_IMAGE)
        self.assertEqual((avatar.wardrobe, avatar.hairstyle, avatar.environment, avatar.specialty),
                         ("executive", "original", "studio", "justice"))

    def test_face_cannot_be_overridden(self):
        with self.assertRaises(ValueError):
            validate_config({"master_image": "another-face.webp"})

    def test_unapproved_style_rejected(self):
        with self.assertRaises(ValueError):
            validate_config({"hairstyle": "new-face"})

if __name__ == "__main__":
    unittest.main()
