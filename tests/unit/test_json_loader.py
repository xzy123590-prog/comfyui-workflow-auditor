import unittest
from unittest.mock import patch
from workflow_auditor.diagnostics import Rejected
from workflow_auditor.json_loader import load_json
from workflow_auditor.limits import MAX_DEPTH


class LoaderTests(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(load_json(b'{"a":[1,true,null]}'), {"a": [1, True, None]})

    def test_bom(self):
        self.assertEqual(load_json(b"\xef\xbb\xbf{}"), {})

    def test_rejections(self):
        cases = [
            (b"", "JSON_EMPTY"), (b" \r\n ", "JSON_EMPTY"),
            (b"\xff", "JSON_INVALID"), (b'{"a":}', "JSON_INVALID"),
            (b'{"a":1,"a":2}', "JSON_DUPLICATE_KEY"),
            (b'{"a":1,"\\u0061":2}', "JSON_DUPLICATE_KEY"),
            (b"NaN", "JSON_NON_FINITE_NUMBER"),
            (b"Infinity", "JSON_NON_FINITE_NUMBER"),
            (b"-Infinity", "JSON_NON_FINITE_NUMBER"),
            (b"1e9999", "JSON_NON_FINITE_NUMBER"),
            (b"[" * 65 + b"0" + b"]" * 65, "JSON_TOO_DEEP"),
        ]
        for data, rule in cases:
            with self.subTest(rule=rule):
                with self.assertRaises(Rejected) as context:
                    load_json(data)
                self.assertEqual(context.exception.diagnostic.rule_id, rule)

    def test_depth_and_escaping(self):
        self.assertEqual(load_json(b'[[0]]', 2), [[0]])
        self.assertEqual(load_json(b'"[{\\"[{"', 1), '[{"[{')
        self.assertEqual(load_json(b'"NaN Infinity -Infinity"'), "NaN Infinity -Infinity")

    def test_recursion_mapping(self):
        with patch("workflow_auditor.json_loader.json.loads", side_effect=RecursionError):
            with self.assertRaises(Rejected) as context:
                load_json(b"{}")
        self.assertEqual(context.exception.diagnostic.rule_id, "JSON_TOO_DEEP")

    def test_bool_and_limits(self):
        for value in (True, False, 0, MAX_DEPTH + 1):
            with self.assertRaises(ValueError):
                load_json(b"{}", value)

    def test_no_false_positives(self):
        self.assertEqual(load_json(b'{"a":1,"b":{"a":2},"c":1.5}'),
                         {"a": 1, "b": {"a": 2}, "c": 1.5})
