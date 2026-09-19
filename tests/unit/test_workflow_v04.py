import copy
import unittest
from workflow_auditor.formats.workflow_v04 import validate
from tests.unit.test_workflow_v1 import fixture, rules


class WorkflowV04Tests(unittest.TestCase):
    def test_valid_extra_fields(self):
        value = fixture(True)
        value["extra"] = []
        self.assertEqual(validate(value), [])

    def test_required(self):
        for field in ("last_node_id", "last_link_id", "nodes", "links", "version"):
            value = fixture(True)
            del value[field]
            self.assertIn("FMT_REQUIRED_FIELD_MISSING", rules(validate(value)))

    def test_version_warning_only(self):
        for version in (0, -1, 1, 2.5):
            value = fixture(True)
            value["version"] = version
            diagnostics = validate(value)
            self.assertEqual([(d.rule_id, d.severity) for d in diagnostics],
                             [("FMT_VERSION_UNEXPECTED", "WARNING")])
        self.assertNotIn("FMT_VERSION_UNEXPECTED", rules(validate(fixture(True))))

    def test_invalid_version(self):
        for version in (True, None, "0.4", float("inf")):
            value = fixture(True)
            value["version"] = version
            self.assertIn("FMT_VERSION_INVALID", rules(validate(value)))

    def test_counter_types(self):
        for field, invalids in (("last_node_id", (True, 1.5, None)),
                                ("last_link_id", (False, "1", None))):
            for invalid in invalids:
                value = fixture(True)
                value[field] = invalid
                self.assertIn("FMT_FIELD_TYPE_INVALID", rules(validate(value)))
        value = fixture(True)
        value["last_node_id"] = "20"
        self.assertEqual(validate(value), [])

    def test_six_element_shape(self):
        for size in (0, 2, 5, 7, 8):
            value = fixture(True)
            value["links"] = [[None] * size]
            self.assertEqual(rules(validate(value)), {"LINK_SHAPE_INVALID"})
        value = fixture(True)
        value["links"] = [{}]
        self.assertEqual(rules(validate(value)), {"LINK_SHAPE_INVALID"})
        self.assertNotIn("LINK_SHAPE_INVALID", rules(validate(fixture(True))))

    def test_duplicate_nodes(self):
        value = fixture(True)
        value["nodes"].append(copy.deepcopy(value["nodes"][0]))
        self.assertIn("NODE_ID_DUPLICATE", rules(validate(value)))
        self.assertNotIn("NODE_ID_DUPLICATE", rules(validate(fixture(True))))
