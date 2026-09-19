import copy
import unittest
from workflow_auditor.formats import workflow_v1, workflow_v04
from tests.unit.test_workflow_v1 import fixture, rules


class ConnectionTests(unittest.TestCase):
    def check_both(self, rule, mutation):
        for legacy, adapter in ((False, workflow_v1), (True, workflow_v04)):
            value = fixture(legacy)
            mutation(value, legacy)
            diagnostics = adapter.validate(value)
            self.assertIn(rule, rules(diagnostics))
            self.assertNotIn(rule, rules(adapter.validate(fixture(legacy))))
            for d in diagnostics:
                if d.rule_id.endswith("NOT_CHECKED"):
                    self.assertEqual((d.status, d.severity), ("NOT_CHECKED", "INFO"))


def set_link(value, legacy, field, data):
    fields = ("id", "origin_id", "origin_slot", "target_id", "target_slot", "type")
    value["links"][0][fields.index(field) if legacy else field] = data


def duplicate(value, legacy):
    value["links"].append(copy.deepcopy(value["links"][0]))
    set_link(value, legacy, "id", 7.0)


CASES = {
    "LINK_SHAPE_INVALID": lambda v, l: set_link(v, l, "type", True),
    "LINK_ID_INVALID": lambda v, l: set_link(v, l, "id", True),
    "LINK_ID_DUPLICATE": duplicate,
    "LINK_ORIGIN_NODE_MISSING": lambda v, l: set_link(v, l, "origin_id", 999),
    "LINK_TARGET_NODE_MISSING": lambda v, l: set_link(v, l, "target_id", "20"),
    "LINK_ORIGIN_SLOT_INVALID": lambda v, l: set_link(v, l, "origin_slot", 1),
    "LINK_TARGET_SLOT_INVALID": lambda v, l: set_link(v, l, "target_slot", -1),
    "LINK_INPUT_BACKREF_MISMATCH": lambda v, l: v["nodes"][1]["inputs"][0].update(link=None),
    "LINK_OUTPUT_BACKREF_MISMATCH": lambda v, l: v["nodes"][0]["outputs"][0].update(links=[]),
    "LINK_SLOT_NOT_CHECKED": lambda v, l: set_link(v, l, "origin_slot", "0"),
    "LINK_BACKREF_NOT_CHECKED": lambda v, l: v["nodes"][1]["inputs"][0].clear(),
}


for _rule, _mutation in CASES.items():
    def test(self, rule=_rule, mutation=_mutation):
        self.check_both(rule, mutation)
    setattr(ConnectionTests, "test_" + _rule.lower(), test)


class ConnectionEdgeTests(unittest.TestCase):
    check_both = ConnectionTests.check_both

    def test_missing_ports(self):
        self.check_both("LINK_SLOT_NOT_CHECKED", lambda v, l: v["nodes"][0].pop("outputs"))
        self.check_both("LINK_BACKREF_NOT_CHECKED", lambda v, l: v["nodes"][1].pop("inputs"))

    def test_bool_and_invalid_slots(self):
        for side in ("origin", "target"):
            for slot in (True, False, -1, 1.0, [], None):
                self.check_both("LINK_" + side.upper() + "_SLOT_INVALID",
                                lambda v, l: set_link(v, l, side + "_slot", slot))

    def test_invalid_endpoints_and_ids(self):
        for side in ("origin_id", "target_id"):
            for value in (True, False, 1.0, [], None):
                self.check_both("LINK_SHAPE_INVALID", lambda v, l: set_link(v, l, side, value))
        for value in ("7", None, [], float("inf")):
            self.check_both("LINK_ID_INVALID", lambda v, l: set_link(v, l, "id", value))

    def test_link_type_alternatives(self):
        for legacy, adapter in ((False, workflow_v1), (True, workflow_v04)):
            for value in ("SyntheticTransform", [], ["SyntheticTransform"], 1.5, 10**400):
                data = fixture(legacy)
                set_link(data, legacy, "type", value)
                self.assertEqual(adapter.validate(data), [])

    def test_unverifiable_port_structures(self):
        for mutate in (
            lambda v, l: v["nodes"][0].update(outputs=[None]),
            lambda v, l: v["nodes"][0]["outputs"][0].update(links=None),
            lambda v, l: v["nodes"][0]["outputs"][0].update(links=[True]),
            lambda v, l: v["nodes"][1]["inputs"][0].update(link=True),
            lambda v, l: v["nodes"].append(copy.deepcopy(v["nodes"][0])),
        ):
            self.check_both("LINK_BACKREF_NOT_CHECKED", mutate)

    def test_required_named_fields(self):
        for field in ("id", "origin_id", "origin_slot", "target_id", "target_slot", "type"):
            value = fixture()
            del value["links"][0][field]
            self.assertIn("LINK_REQUIRED_FIELD_MISSING", rules(workflow_v1.validate(value)))
        self.assertNotIn("LINK_REQUIRED_FIELD_MISSING", rules(workflow_v1.validate(fixture())))

    def test_invalid_link_objects(self):
        for bad in (None, [], True):
            value = fixture()
            value["links"] = [bad]
            self.assertIn("LINK_SHAPE_INVALID", rules(workflow_v1.validate(value)))

    def test_integer_and_float_link_equality(self):
        for legacy, adapter in ((False, workflow_v1), (True, workflow_v04)):
            value = fixture(legacy)
            set_link(value, legacy, "id", 1)
            value["links"].append(copy.deepcopy(value["links"][0]))
            set_link(value, legacy, "id", 1.0)
            self.assertIn("LINK_ID_DUPLICATE", rules(adapter.validate(value)))
