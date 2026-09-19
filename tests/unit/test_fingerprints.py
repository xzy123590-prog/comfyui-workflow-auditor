import hashlib
import unittest
from unittest.mock import patch
from workflow_auditor.fingerprints import fingerprint


class FingerprintTests(unittest.TestCase):
    def test_default_does_not_hash(self):
        with patch("workflow_auditor.fingerprints.hashlib.sha256",
                   side_effect=RuntimeError("Hashing must not run.")):
            self.assertIsNone(fingerprint(b"synthetic"))

    def test_opt_in(self):
        data = b"synthetic"
        self.assertEqual(fingerprint(data, True),
                         dict(algorithm="sha256", user_opt_in=True,
                              value=hashlib.sha256(data).hexdigest()))

    def test_bool_required(self):
        with self.assertRaises(ValueError):
            fingerprint(b"synthetic", 1)
