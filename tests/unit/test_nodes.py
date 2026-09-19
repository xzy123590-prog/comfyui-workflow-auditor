import copy
import unittest
from workflow_auditor.rules.nodes import check_nodes, NODE_FIELDS
from tests.unit.test_workflow_v1 import fixture, rules


class NodeTests(unittest.TestCase):
    def test_duplicate_evidence_and_typed_identity(self):
        node = fixture()["nodes"][0]
        node["id"] = 1
        other = copy.deepcopy(node)
        other["id"] = "1"
        self.assertEqual(check_nodes([node, other])[0], [])
        diagnostics, index = check_nodes([node, node, other, node])
        self.assertEqual(sum(d.rule_id == "NODE_ID_DUPLICATE" for d in diagnostics), 2)
        self.assertEqual(len(index[(int, 1)]), 3)

    def test_id_types(self):
        for value in (True, False, 1.0, None, [], {}):
            node = fixture()["nodes"][0]
            node["id"] = value
            self.assertIn("NODE_ID_INVALID", rules(check_nodes([node])[0]))
        self.assertNotIn("NODE_ID_INVALID", rules(check_nodes(fixture()["nodes"])[0]))

    def test_required_fields(self):
        for field in NODE_FIELDS:
            node = fixture()["nodes"][0]
            del node[field]
            self.assertIn("NODE_REQUIRED_FIELD_MISSING", rules(check_nodes([node])[0]))
        self.assertNotIn("NODE_REQUIRED_FIELD_MISSING", rules(check_nodes(fixture()["nodes"])[0]))

    def test_field_types(self):
        for field in ("type", "pos", "size", "flags", "order", "mode", "properties", "inputs", "outputs"):
            node = fixture()["nodes"][0]
            node[field] = True
            self.assertIn("NODE_FIELD_TYPE_INVALID", rules(check_nodes([node])[0]))
        self.assertIn("NODE_FIELD_TYPE_INVALID", rules(check_nodes([None])[0]))
        self.assertNotIn("NODE_FIELD_TYPE_INVALID", rules(check_nodes(fixture()["nodes"])[0]))

    def test_pair_validation(self):
        for value in ([0], [0, 1, 2], [True, 0], {"0": False, "1": 1}, {"0": 0}):
            node = fixture()["nodes"][0]
            node["pos"] = value
            self.assertIn("NODE_FIELD_TYPE_INVALID", rules(check_nodes([node])[0]))
        for value in ([1.5, -2], {"0": 0, "1": 2.5, "extra": None}):
            node = fixture()["nodes"][0]
            node["pos"] = value
            self.assertEqual(check_nodes([node])[0], [])
