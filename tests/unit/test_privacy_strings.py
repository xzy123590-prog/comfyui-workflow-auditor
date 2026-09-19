import unittest
from workflow_auditor.rules.privacy_strings import scan_strings


class PrivacyTests(unittest.TestCase):
    def test_hits(self):
        cases = [
            ("Z:" + "\\synthetic\\item", "STRING_ABSOLUTE_PATH"),
            ("/" + "synthetic/item", "STRING_ABSOLUTE_PATH"),
            ("\\\\" + "synthetic\\share\\item", "STRING_UNC_PATH"),
            ("file:" + "///synthetic/item", "STRING_FILE_URI"),
            ("https:" + "//synthetic:placeholder@invalid.test/item",
             "STRING_URL_WITH_CREDENTIALS"),
            ("../synthetic", "STRING_PATH_TRAVERSAL"),
            ("..\\synthetic", "STRING_PATH_TRAVERSAL"),
        ]
        for value, rule in cases:
            with self.subTest(rule=rule):
                self.assertIn(rule, [d.rule_id for d in scan_strings(value)])

    def test_no_false_positives(self):
        for value in ("ordinary text", "two..dots", "relative/item",
                      "https:" + "//invalid.test/item", 12, True, None):
            self.assertEqual(scan_strings(value), [])

    def test_safe_nested_location_and_keys_ignored(self):
        diagnostics = scan_strings({"private-key": ["../item"], "../ignored-key": 2})
        self.assertEqual(len(diagnostics), 1)
        self.assertEqual(diagnostics[0].json_pointer, "/$k0/0")

    def test_iterative(self):
        value = "../item"
        for _ in range(1500):
            value = [value]
        self.assertEqual(len(scan_strings(value)), 1)
