"""Checks the schema vocabulary used here without third-party dependencies."""
import copy
import json
import re
import unittest
from pathlib import Path
from workflow_auditor.diagnostics import Diagnostic, TEMPLATES
from workflow_auditor.report import make_report
from workflow_auditor.fingerprints import fingerprint


def conforms(value, schema):
    types = {"object": dict, "array": list, "string": str,
             "integer": int, "boolean": bool, "null": type(None)}
    if "type" in schema and type(value) is not types[schema["type"]]:
        return False
    if "const" in schema and (type(value) is not type(schema["const"]) or value != schema["const"]):
        return False
    if "enum" in schema and value not in schema["enum"]:
        return False
    if "minimum" in schema and value < schema["minimum"]:
        return False
    if "pattern" in schema and re.fullmatch(schema["pattern"], value) is None:
        return False
    if "oneOf" in schema and sum(conforms(value, s) for s in schema["oneOf"]) != 1:
        return False
    if isinstance(value, dict):
        props = schema.get("properties", {})
        if any(k not in value for k in schema.get("required", [])):
            return False
        if schema.get("additionalProperties") is False and any(k not in props for k in value):
            return False
        if any(not conforms(value[k], subschema) for k, subschema in props.items() if k in value):
            return False
    if isinstance(value, list) and "items" in schema:
        return all(conforms(item, schema["items"]) for item in value)
    return True


class SchemaTests(unittest.TestCase):
    def setUp(self):
        self.schema = json.loads(Path("schemas/diagnostic-report.schema.json").read_text(encoding="utf-8"))

    def test_all_rules(self):
        for fp in (None, fingerprint(b"synthetic", True)):
            report = make_report([Diagnostic(rule) for rule in TEMPLATES], fp)
            self.assertTrue(conforms(report, self.schema))

    def test_reject_wrong_shape_and_values(self):
        original = make_report([Diagnostic("JSON_EMPTY")])
        for mutation in ("missing", "extra", "bool_count", "raw_pointer", "raw_message", "bad_fp"):
            report = copy.deepcopy(original)
            if mutation == "missing":
                del report["scope"]
            elif mutation == "extra":
                report["extra"] = "value"
            elif mutation == "bool_count":
                report["summary"]["error_count"] = True
            elif mutation == "raw_pointer":
                report["diagnostics"][0]["json_pointer"] = "/private-key"
            elif mutation == "raw_message":
                report["diagnostics"][0]["message"] = "arbitrary"
            else:
                report["fingerprint"] = {"value": "invalid"}
            self.assertFalse(conforms(report, self.schema))
