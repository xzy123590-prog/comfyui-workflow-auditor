import unittest
from workflow_auditor.format_detection import detect_format
from tests.unit.test_workflow_v1 import fixture


class DetectionTests(unittest.TestCase):
    def test_explicit_signals(self):
        for value in (fixture(), {"version": 1}, {"nodes": [], "state": {}},
                      {"nodes": [], "links": fixture()["links"]}):
            self.assertEqual(detect_format(value), "workflow-v1")
        for value in (fixture(True), {"nodes": [], "last_node_id": 0},
                      {"nodes": [], "last_link_id": 0},
                      {"nodes": [], "links": fixture(True)["links"]}):
            self.assertEqual(detect_format(value), "workflow-v0.4")

    def test_ambiguous(self):
        value = fixture()
        value["last_node_id"] = 0
        self.assertEqual(detect_format(value), "ambiguous")
        value = fixture(True)
        value["links"].extend(fixture()["links"])
        self.assertEqual(detect_format(value), "ambiguous")

    def test_unknown_and_api_shape(self):
        self.assertEqual(detect_format({"1": {"class_type": "SyntheticSource", "inputs": {}}}), "api")
        for value in (None, [], {}, {"version": True}, {"version": "1"},
                      {"version": 0.4}, {"last_node_id": 0}, {"nodes": [], "links": []},
                      {"nodes": {"class_type": "SyntheticSource", "inputs": {}},
                       "version": {"class_type": "SyntheticSink", "inputs": {}}}):
            self.assertEqual(detect_format(value), "unknown")

    def test_ignores_node_type_widgets_and_unknown_keys(self):
        value = fixture()
        value["nodes"][0]["type"] = "SyntheticSink"
        value["nodes"][0]["widgets_values"] = [{"last_node_id": 2}]
        value["extra"] = {"last_node_id": 0}
        self.assertEqual(detect_format(value), "workflow-v1")
