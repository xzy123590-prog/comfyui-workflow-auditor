import copy
import json
import unittest
from pathlib import Path
from workflow_auditor.formats.workflow_v1 import validate


def fixture(legacy=False):
    name = "workflow_v04_valid.json" if legacy else "workflow_v1_valid.json"
    return json.loads((Path("tests/fixtures") / name).read_text(encoding="utf-8"))


def rules(diagnostics):
    return {d.rule_id for d in diagnostics}


class WorkflowV1Tests(unittest.TestCase):
    def test_valid_and_optional_links(self):
        value = fixture()
        self.assertEqual(validate(value), [])
        del value["links"]
        self.assertEqual(validate(value), [])

    def test_required_fields(self):
        for field in ("version", "state", "nodes"):
            value = fixture()
            del value[field]
            self.assertIn("FMT_REQUIRED_FIELD_MISSING", rules(validate(value)))
        self.assertNotIn("FMT_REQUIRED_FIELD_MISSING", rules(validate(fixture())))

    def test_top_types(self):
        for field in ("state", "nodes", "links"):
            value = fixture()
            value[field] = None
            self.assertIn("FMT_FIELD_TYPE_INVALID", rules(validate(value)))
        for value in ([], None, True, "synthetic"):
            self.assertIn("FMT_FIELD_TYPE_INVALID", rules(validate(value)))
        self.assertNotIn("FMT_FIELD_TYPE_INVALID", rules(validate(fixture())))

    def test_version(self):
        for version in (True, False, None, "1", 0.4, float("inf"), float("nan")):
            value = fixture()
            value["version"] = version
            self.assertIn("FMT_VERSION_INVALID", rules(validate(value)))
        for version in (1, 1.0):
            value = fixture()
            value["version"] = version
            self.assertEqual(validate(value), [])

    def test_extra_fields(self):
        value = fixture()
        value["synthetic_extra"] = {"data": [1, 2]}
        value["nodes"][0]["synthetic_extra"] = True
        value["links"][0]["synthetic_extra"] = None
        self.assertEqual(validate(value), [])

    def test_string_ids(self):
        value = fixture()
        for i, side in enumerate(("origin_id", "target_id")):
            value["nodes"][i]["id"] = str(value["nodes"][i]["id"])
            value["links"][0][side] = value["nodes"][i]["id"]
        self.assertEqual(validate(value), [])

    def test_resource_limits(self):
        value = fixture()
        self.assertIn("WORKFLOW_TOO_MANY_NODES", rules(validate(value, max_nodes=1)))
        self.assertNotIn("WORKFLOW_TOO_MANY_NODES", rules(validate(value, max_nodes=2)))
        value["links"].append(copy.deepcopy(value["links"][0]))
        self.assertEqual(rules(validate(value, max_links=1)), {"WORKFLOW_TOO_MANY_LINKS"})
        self.assertNotIn("WORKFLOW_TOO_MANY_LINKS", rules(validate(value, max_links=2)))

    def test_limit_validation(self):
        for field, maximum in (("max_nodes", 100000), ("max_links", 500000)):
            for value in (True, False, 0, -1, maximum + 1, 1.5, "2"):
                with self.assertRaises(ValueError):
                    validate(fixture(), **{field: value})
            self.assertEqual(validate(fixture(), **{field: maximum}), [])
