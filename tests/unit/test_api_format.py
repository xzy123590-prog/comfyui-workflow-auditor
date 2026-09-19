import copy
import unittest
from unittest.mock import patch
from workflow_auditor.formats.api_format import validate, is_api_id
from workflow_auditor.limits import HARD_MAX_NODES, HARD_MAX_LINKS
from workflow_auditor.report import make_report


def node(inputs=None):
    return {"class_type": "SyntheticSource", "inputs": {} if inputs is None else inputs}


def valid():
    return {"1": node(), "01": node({"feed": ["1", 0]})}


# Each case includes an exact safe location and a clean negative control.
RULE_CASES = {
    "API_WORKFLOW_EMPTY": ({}, "/api_nodes", "WARNING", "CHECKED"),
    "API_NODE_ID_INVALID": ({"invalid": node()}, "/api_nodes/0", "ERROR", "CHECKED"),
    "API_NODE_OBJECT_INVALID": ({"1": False}, "/api_nodes/0", "ERROR", "CHECKED"),
    "API_CLASS_TYPE_MISSING": ({"1": {"inputs": {}}}, "/api_nodes/0/class_type", "ERROR", "CHECKED"),
    "API_CLASS_TYPE_INVALID": ({"1": {"class_type": "", "inputs": {}}}, "/api_nodes/0/class_type", "ERROR", "CHECKED"),
    "API_INPUTS_MISSING": ({"1": {"class_type": "SyntheticSource"}}, "/api_nodes/0/inputs", "ERROR", "CHECKED"),
    "API_INPUTS_INVALID": ({"1": {"class_type": "SyntheticSource", "inputs": []}}, "/api_nodes/0/inputs", "ERROR", "CHECKED"),
    "API_META_INVALID": ({"1": dict(node(), _meta=False)}, "/api_nodes/0/_meta", "WARNING", "CHECKED"),
    "API_REFERENCE_SOURCE_MISSING": ({"1": node({"feed": ["99", 0]})}, "/api_nodes/0/inputs/$k0", "WARNING", "NOT_CHECKED"),
    "API_REFERENCE_INDEX_INVALID": ({"1": node({"feed": ["1", True]})}, "/api_nodes/0/inputs/$k0", "ERROR", "CHECKED"),
    "API_REFERENCE_AMBIGUOUS": ({"1": node({"feed": ["99", False]})}, "/api_nodes/0/inputs/$k0", "WARNING", "NOT_CHECKED"),
}


class ApiRuleTests(unittest.TestCase):
    pass


def rule_test(rule, case):
    def test(self):
        value, pointer, severity, status = case
        diagnostics = validate(copy.deepcopy(value))
        self.assertEqual([(d.rule_id, d.json_pointer, d.severity, d.status) for d in diagnostics],
                         [(rule, pointer, severity, status)])
        self.assertEqual(validate(valid()), [])
        self.assertEqual(make_report(diagnostics, format="api")["summary"]["not_checked_count"],
                         int(status == "NOT_CHECKED"))
    return test


for _rule, _case in RULE_CASES.items():
    setattr(ApiRuleTests, "test_" + _rule.lower(), rule_test(_rule, _case))


class ApiValueTests(unittest.TestCase):
    def test_valid_single_and_multiple(self):
        self.assertEqual(validate({"1": node()}), [])
        self.assertEqual(validate(valid()), [])

    def test_id_ascii_and_exact_identity(self):
        for value in ("", "-1", "1.0", " 1", "?", "?", 1, True, 0.0):
            self.assertFalse(is_api_id(value))
            self.assertIn("API_NODE_ID_INVALID", [d.rule_id for d in validate({value: node()})])
        self.assertTrue(is_api_id("01"))
        value = {"1": node({"feed": ["01", 0]})}
        self.assertEqual(validate(value)[0].rule_id, "API_REFERENCE_SOURCE_MISSING")
        value["01"] = node()
        self.assertEqual(validate(value), [])

    def test_root_types(self):
        for value in (None, [], 0, True, ""):
            self.assertEqual([d.rule_id for d in validate(value)], ["FMT_FIELD_TYPE_INVALID"])

    def test_class_type_types(self):
        for item in (None, [], {}, False, 0, ""):
            self.assertEqual([d.rule_id for d in validate({"1": dict(node(), class_type=item)})],
                             ["API_CLASS_TYPE_INVALID"])

    def test_inputs_types(self):
        for item in (None, [], False, 0, ""):
            self.assertEqual([d.rule_id for d in validate({"1": dict(node(), inputs=item)})],
                             ["API_INPUTS_INVALID"])

    def test_meta_and_unknown_fields(self):
        value = {"1": dict(node(), _meta={"title": [False]}, extra={"feed": ["99", -1]})}
        self.assertEqual(validate(value), [])

    def test_existing_source_index_types(self):
        for index in (True, False, -1, 0.0, "0", None, [], {}):
            self.assertEqual([d.rule_id for d in validate({"1": node({"feed": ["1", index]})})],
                             ["API_REFERENCE_INDEX_INVALID"])
        for index in (0, 999999999999999999999):
            self.assertEqual(validate({"1": node({"feed": ["1", index]})}), [])

    def test_missing_index_exception(self):
        self.assertEqual(validate({"1": node({"feed": ["1"]})})[0].rule_id,
                         "API_REFERENCE_INDEX_INVALID")
        self.assertEqual(validate({"1": node({"feed": ["99"]})}), [])

    def test_missing_source_invalid_index(self):
        for index in (True, -1, 0.0, "0", None, [], {}):
            d = validate({"1": node({"feed": ["99", index]})})[0]
            self.assertEqual((d.rule_id, d.severity, d.status),
                             ("API_REFERENCE_AMBIGUOUS", "WARNING", "NOT_CHECKED"))

    def test_literals_not_connections(self):
        literals = [[1, 0], [1, 2], [True, 0], ["alpha", "beta"], ["", 0],
                    ["?", 0], [["1", 0], ["2", 0]], {"feed": ["99", -1]},
                    [], [1], ["1", 0, 2], "literal", 0, None]
        self.assertEqual(validate({"1": node(dict(enumerate(literals)))}, max_links=1), [])

    def test_nodes_limit(self):
        self.assertEqual([d.rule_id for d in validate(valid(), max_nodes=1)],
                         ["WORKFLOW_TOO_MANY_NODES"])
        self.assertEqual(validate(valid(), max_nodes=2), [])

    def test_links_limit_includes_missing_sources(self):
        for source in ("1", "99"):
            value = {"1": node({"a": [source, 0], "b": [source, 0]})}
            rules = [d.rule_id for d in validate(value, max_links=1)]
            self.assertIn("WORKFLOW_TOO_MANY_LINKS", rules)
            self.assertNotIn("WORKFLOW_TOO_MANY_LINKS", [d.rule_id for d in validate(value, max_links=2)])

    def test_ambiguous_and_invalid_not_counted(self):
        for ref in (["99", False], ["1", -1]):
            value = {"1": node({"a": ref, "b": ref, "c": ["1", 0]})}
            self.assertNotIn("WORKFLOW_TOO_MANY_LINKS", [d.rule_id for d in validate(value, max_links=1)])

    def test_limit_arguments(self):
        for name, maximum in (("max_nodes", HARD_MAX_NODES), ("max_links", HARD_MAX_LINKS)):
            for limit in (True, False, 0, -1, maximum + 1, 1.0, "1"):
                with self.assertRaises(ValueError):
                    validate(valid(), **{name: limit})

    def test_no_mutation_and_no_resource_reads(self):
        value = valid()
        value["1"]["inputs"]["literal"] = "../synthetic-resource"
        before = copy.deepcopy(value)
        with patch("builtins.open", side_effect=AssertionError("Unexpected file read.")):
            self.assertEqual(validate(value), [])
        self.assertEqual(value, before)
