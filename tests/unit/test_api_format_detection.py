import copy
import unittest
from unittest.mock import patch
from workflow_auditor.format_detection import detect_format, api_format_evidence, save_format_evidence
from tests.unit.test_api_format import node, valid
from tests.unit.test_workflow_v1 import fixture


class ApiDetectionTests(unittest.TestCase):
    def test_high_confidence(self):
        for value in (valid(), {"1": node()}, {"1": node(), "2": {"inputs": {}}},
                      {"1": node(), "2": {"class_type": None}}):
            self.assertEqual(api_format_evidence(value), ("api",))
            self.assertEqual(save_format_evidence(value), ())
            self.assertEqual(detect_format(value), "api")

    def test_unknown(self):
        for value in ({}, [], None, {"1": {}}, {"1": False}, {"x": node()},
                      {"?": node()}, {"": node()}, {1: node()},
                      {"1": {"inputs": {}}}, {"1": node(), "2": {}},
                      {"1": node(), "metadata": {}}):
            self.assertEqual(api_format_evidence(value), ())
            self.assertEqual(detect_format(value), "unknown")

    def test_values_not_inspected(self):
        value = {"1": {"class_type": None, "inputs": False, "extra": ["anything"]}}
        self.assertEqual(detect_format(value), "api")

    def test_save_formats_excluded(self):
        for legacy, expected in ((False, "workflow-v1"), (True, "workflow-v0.4")):
            value = fixture(legacy)
            self.assertEqual(api_format_evidence(value), ())
            self.assertEqual(detect_format(value), expected)

    def test_independent_conflicting_evidence(self):
        with patch("workflow_auditor.format_detection.api_format_evidence", return_value=("api",)):
            self.assertEqual(detect_format(fixture()), "ambiguous")

    def test_no_adapter_or_mutation(self):
        value = valid(); before = copy.deepcopy(value)
        with patch("workflow_auditor.formats.api_format.validate", side_effect=AssertionError):
            self.assertEqual(detect_format(value), "api")
        self.assertEqual(value, before)
