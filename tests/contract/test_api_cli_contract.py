import copy
import hashlib
import json
import unittest
from pathlib import Path
from unittest.mock import patch
from workflow_auditor.diagnostics import Diagnostic
from workflow_auditor.report import make_report, render
from tests.contract.test_report_schema import conforms
from tests.contract.test_save_format_cli_contract import run_value
from tests.security.test_no_sensitive_echo import invoke
from tests.unit.test_api_format import RULE_CASES, node, valid

SENTINEL = "SENSITIVE_SENTINEL_DO_NOT_ECHO_48291"


class ApiRuleContractTests(unittest.TestCase):
    pass


def rule_contract(rule, case):
    def test(self):
        value, pointer, severity, status = case
        schema = json.loads(Path("schemas/diagnostic-report.schema.json").read_text(encoding="utf-8"))
        for output in ("json", "text"):
            code, out, err = run_value(value, "api", output=output)
            self.assertEqual((code, err), (int(severity == "ERROR"), ""))
            self.assertIn(rule, out)
            self.assertIn(pointer, out)
            self.assertEqual((code, out, err), run_value(value, "api", output=output))
            clean = run_value(valid(), "api", output=output)
            self.assertEqual(clean[0], 0)
            self.assertNotIn(rule, clean[1])
            for forbidden in ("SyntheticSource", "SyntheticSink", "SyntheticTransform", "synthetic.json", str(Path.cwd()), "Traceback", SENTINEL):
                self.assertTrue(forbidden not in out + err, "Private output detected.")
            if output == "json":
                report = json.loads(out)
                self.assertTrue(conforms(report, schema))
                self.assertEqual((report["format"], report["scope"]), ("api", "comfyui-api-format"))
                self.assertEqual(report["summary"]["not_checked_count"], int(status == "NOT_CHECKED"))
                self.assertEqual(report["diagnostics"][0]["json_pointer"], pointer)
            # Repeat each rule with private labels in all applicable input positions.
            private_value = copy.deepcopy(value)
            if private_value:
                old_id, private_node = next(iter(private_value.items()))
                new_id = SENTINEL if rule == "API_NODE_ID_INVALID" else "827364591"
                private_value = {new_id: private_node}
                if isinstance(private_node, dict):
                    private_node["extra"] = SENTINEL
                    if isinstance(private_node.get("class_type"), str) and private_node["class_type"]:
                        private_node["class_type"] = SENTINEL
                    inputs = private_node.get("inputs")
                    if isinstance(inputs, dict):
                        private_node["inputs"] = {SENTINEL + str(i): item for i, item in enumerate(inputs.values())}
                        for item in private_node["inputs"].values():
                            if isinstance(item, list) and item:
                                item[0] = new_id if item[0] == old_id else "938475610"
                private_code, private_out, private_err = run_value(private_value, "api", output=output)
                self.assertEqual(private_code, code)
                self.assertIn(rule, private_out)
                self.assertIn(pointer, private_out)
                for forbidden in (SENTINEL, "827364591", "938475610"):
                    self.assertTrue(forbidden not in private_out + private_err, "Private rule output detected.")
    return test


for _rule, _case in RULE_CASES.items():
    setattr(ApiRuleContractTests, "test_" + _rule.lower(), rule_contract(_rule, _case))


class ApiCliTests(unittest.TestCase):
    def test_explicit_and_auto(self):
        for selection in ("api", "auto"):
            code, out, err = run_value(valid(), selection)
            report = json.loads(out)
            self.assertEqual((code, err, report["format"], report["scope"]),
                             (0, "", "api", "comfyui-api-format"))

    def test_explicit_bypasses_detection(self):
        with patch("workflow_auditor.cli.detect_format", side_effect=AssertionError):
            self.assertEqual(run_value(valid(), "api")[0], 0)

    def test_default_generic_unchanged(self):
        with patch("workflow_auditor.cli.read_input", return_value=json.dumps(valid()).encode()):
            args = ["audit", "synthetic.json", "--output-format", "json"]
            self.assertEqual(invoke(args), invoke(args + ["--format", "generic-json"]))
            self.assertEqual(json.loads(invoke(args)[1])["format"], "generic-json")

    def test_empty_auto_unknown(self):
        self.assertEqual(run_value({}, "api")[0], 0)
        code, out, err = run_value({}, "auto")
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(out)["format"], "unknown")
        self.assertIn("FMT_UNKNOWN", out)

    def test_fingerprint(self):
        self.assertIsNone(json.loads(run_value(valid(), "api")[1])["fingerprint"])
        report = json.loads(run_value(valid(), "api", extra=("--fingerprint",))[1])
        self.assertEqual(report["fingerprint"], {"algorithm": "sha256", "user_opt_in": True,
                         "value": hashlib.sha256(json.dumps(valid()).encode()).hexdigest()})

    def test_duplicate_key_and_nonfinite(self):
        for data, rule in ((b'{"1":{},"1":{}}', "JSON_DUPLICATE_KEY"),
                           (b'{"1":{"inputs":{"x":NaN}}}', "JSON_NON_FINITE_NUMBER")):
            with patch("workflow_auditor.cli.read_input", return_value=data):
                code, out, err = invoke(["audit", "synthetic.json", "--format", "api"])
            self.assertEqual(code, 1)
            self.assertIn(rule, out)

    def test_limits_cli(self):
        for flag, values in (("--max-nodes", ("true", "0", "-1", "100001")),
                             ("--max-links", ("false", "0", "-1", "500001"))):
            for value in values:
                self.assertEqual(run_value(valid(), "api", extra=(flag, value))[0], 2)
        self.assertEqual(run_value(valid(), "api", extra=("--max-nodes", "1"))[0], 1)
        value = {"1": node({"a": ["1", 0], "b": ["99", 0]})}
        self.assertEqual(run_value(value, "api", extra=("--max-links", "1"))[0], 1)

    def test_safe_original_values_all_locations(self):
        value = {"827364591": {"class_type": SENTINEL, "inputs": {SENTINEL: ["827364591", False]},
                               "_meta": {"title": SENTINEL}, "extra": SENTINEL},
                 SENTINEL: {"class_type": "SyntheticSink", "inputs": {}}}
        for output in ("json", "text"):
            code, out, err = run_value(value, "api", output=output)
            self.assertEqual(code, 1)
            for forbidden in (SENTINEL, "827364591", "SyntheticSink", "synthetic.json", str(Path.cwd()), "Traceback"):
                self.assertTrue(forbidden not in out + err, "SENTINEL_ECHO_CHECK = FAIL")
            self.assertIn("/api_nodes/0/inputs/$k0", out)
            self.assertIn("/api_nodes/1", out)

    def test_internal_exception(self):
        for output in ("text", "json"):
            with patch("workflow_auditor.cli.api_format.validate", side_effect=OSError(SENTINEL + str(Path.cwd()))):
                code, out, err = run_value(valid(), "api", output=output)
            self.assertEqual(code, 3)
            self.assertIn("INTERNAL_ERROR", out)
            for forbidden in (SENTINEL, str(Path.cwd()), "Traceback"):
                self.assertTrue(forbidden not in out + err, "Private exception detected.")

    def test_sorting(self):
        diagnostics = [Diagnostic("API_META_INVALID", severity="WARNING", json_pointer="/api_nodes/1/_meta"),
                       Diagnostic("API_INPUTS_MISSING", json_pointer="/api_nodes/0/inputs")]
        for output in ("json", "text"):
            self.assertEqual(render(make_report(diagnostics, format="api"), output),
                             render(make_report(list(reversed(diagnostics)), format="api"), output))

    def test_no_embedded_file_or_network_reads(self):
        value = {"1": node({"resource": "../synthetic-resource", "address": "https" + ":" + "//synthetic.invalid"})}
        with patch("builtins.open", side_effect=AssertionError), patch("socket.socket", side_effect=AssertionError):
            code, out, err = run_value(value, "api")
        self.assertEqual((code, err), (0, ""))
        self.assertIn("STRING_PATH_TRAVERSAL", out)
        self.assertNotIn("synthetic-resource", out)
        self.assertNotIn("synthetic.invalid", out)
