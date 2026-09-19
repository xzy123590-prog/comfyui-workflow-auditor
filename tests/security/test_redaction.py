import unittest
from workflow_auditor.redaction import safe_pointer, safe_parameters


class RedactionTests(unittest.TestCase):
    def test_allowed(self):
        self.assertEqual(safe_pointer("/$k1/0/$k0"), "/$k1/0/$k0")
        self.assertEqual(safe_parameters({"count": 2, "verified": True,
                                         "category": "file_uri"})["count"], 2)

    def test_rejected(self):
        for value in ("/arbitrary", "/$k0\n", "/-1", "/~1"):
            with self.assertRaises(ValueError):
                safe_pointer(value)
        for values in ({"count": True}, {"count": -1}, {"category": "arbitrary"},
                       {"secret": "arbitrary"}, {"verified": 1}):
            with self.assertRaises(ValueError):
                safe_parameters(values)
