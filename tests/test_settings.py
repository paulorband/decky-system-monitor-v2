import json
import os
import tempfile
import unittest

from sysmon import settings


class SettingsTest(unittest.TestCase):  # spec 008 REQ-670, AC-2
    def test_defaults_and_sanitize(self):
        self.assertEqual(settings.sanitize(None), settings.DEFAULTS)
        self.assertEqual(settings.sanitize({"auto_check": False})["auto_check"], False)
        self.assertEqual(settings.sanitize({"auto_check": "no"})["auto_check"], True)
        self.assertEqual(settings.sanitize({"test_channel": True})["test_channel"], True)
        self.assertEqual(settings.sanitize({"test_channel": "yes"})["test_channel"], False)  # REQ-650 default off
        self.assertNotIn("other", settings.sanitize({"other": 1}))

    def test_roundtrip_atomic_and_corrupt(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "sub", "settings.json")
            saved = settings.save(path, {"test_channel": True})
            self.assertEqual(settings.load(path), saved)
            self.assertTrue(saved["test_channel"])
            with open(path, "w") as f:
                f.write("{not json")
            self.assertEqual(settings.load(path), settings.DEFAULTS)
            self.assertTrue(json.loads(json.dumps(settings.DEFAULTS)))


if __name__ == "__main__":
    unittest.main()
