import copy
import hashlib
import json
import unittest
from pathlib import Path
from unittest.mock import patch
from workflow_auditor.diagnostics import Diagnostic
from workflow_auditor.report import make_report, render
from tests.security.test_no_sensitive_echo import invoke
from tests.contract.test_report_schema import conforms
from tests.unit.test_workflow_v1 import fixture

SENTINEL = "SENSITIVE_SENTINEL_DO_NOT_ECHO_48291"


def run_value(value, format="workflow-v1", extra=(), output="json"):
    data = json.dumps(value).encode()
    with patch("workflow_auditor.cli.read_input", return_value=data):
        return invoke(["audit", "synthetic.json", "--format", format,
                       "--output-format", output, *extra])


class SaveFormatContractTests(unittest.TestCase):
    def test_format_scope_and_schema(self):
        schema = json.loads(Path("schemas/diagnostic-report.schema.json").read_text())
        for format, value, scope in (
            ("workflow-v1", fixture(), "comfyui-workflow-v1"),
            ("workflow-v0.4", fixture(True), "comfyui-workflow-v0.4"),
            ("generic-json", {}, "generic-json-security-core")):
            for selection in (format, "auto") if format != "generic-json" else (format,):
                code, out, err = run_value(value, selection)
                report = json.loads(out)
                self.assertEqual((code, err, report["format"], report["scope"]),
                                 (0, "", format, scope))
                self.assertTrue(conforms(report, schema))

    def test_detection_failures_do_not_call_adapters(self):
        ambiguous = fixture()
        ambiguous["last_node_id"] = 20
        for value, format, rule in (({}, "unknown", "FMT_UNKNOWN"),
                                     (ambiguous, "ambiguous", "FMT_AMBIGUOUS")):
            with patch("workflow_auditor.cli.workflow_v1.validate") as v1, patch(
                    "workflow_auditor.cli.workflow_v04.validate") as v04:
                code, out, err = run_value(value, "auto")
                v1.assert_not_called()
                v04.assert_not_called()
            report = json.loads(out)
            self.assertEqual((code, err, report["format"], report["scope"]),
                             (1, "", format, "format-detection"))
            self.assertEqual([d["rule_id"] for d in report["diagnostics"]], [rule])

    def test_explicit_bypasses_detection_and_rejects_mismatch(self):
        with patch("workflow_auditor.cli.detect_format", side_effect=AssertionError):
            self.assertEqual(run_value(fixture())[0], 0)
            self.assertEqual(run_value(fixture(True), "workflow-v1")[0], 1)
            self.assertEqual(run_value(fixture(), "workflow-v0.4")[0], 1)

    def test_generic_default_unchanged(self):
        args = ["audit", "tests/fixtures/valid_generic.json", "--output-format", "json"]
        self.assertEqual(invoke(args), invoke(args + ["--format", "generic-json"]))
        report = json.loads(invoke(args)[1])
        self.assertEqual(report["scope"], "generic-json-security-core")
        self.assertIsNone(report["fingerprint"])

    def test_fingerprint(self):
        data = fixture()
        self.assertIsNone(json.loads(run_value(data)[1])["fingerprint"])
        report = json.loads(run_value(data, extra=("--fingerprint",))[1])
        self.assertEqual(report["fingerprint"], {
            "algorithm": "sha256", "user_opt_in": True,
            "value": hashlib.sha256(json.dumps(data).encode()).hexdigest()})

    def test_usage_limits_and_paths_safe(self):
        for flag, values in (("--max-nodes", ("0", "-1", "100001", "true", SENTINEL)),
                             ("--max-links", ("0", "-1", "500001", "false", SENTINEL)),
                             ("--format", (SENTINEL, "workflow-api"))):
            for value in values:
                code, out, err = invoke(["audit", SENTINEL, flag, value])
                self.assertEqual(code, 2)
                self.assertTrue(SENTINEL not in out + err, "Sensitive output check failed.")
                self.assertNotIn("Traceback", out + err)

    def test_limits_content_and_warning_exit(self):
        self.assertEqual(run_value(fixture(), extra=("--max-nodes", "1"))[0], 1)
        value = fixture()
        value["links"] *= 2
        self.assertEqual(run_value(value, extra=("--max-links", "1"))[0], 1)
        value = fixture(True)
        value["version"] = 2
        self.assertEqual(run_value(value, "workflow-v0.4")[0], 0)

    def test_not_checked_summary_and_stability(self):
        value = fixture()
        value["links"][0]["origin_slot"] = "0"
        report = json.loads(run_value(value)[1])
        self.assertEqual(report["summary"]["not_checked_count"], 2)
        self.assertEqual(report["summary"]["error_count"], 0)
        for output in ("json", "text"):
            self.assertEqual(run_value(value, output=output), run_value(value, output=output))
        items = [Diagnostic("LINK_BACKREF_NOT_CHECKED", severity="INFO", status=s,
                            json_pointer="/links/1") for s in ("NOT_CHECKED", "CHECKED")]
        for output in ("json", "text"):
            self.assertEqual(render(make_report(items), output),
                             render(make_report(list(reversed(items))), output))

    def test_original_values_never_echo(self):
        for legacy, format in ((False, "workflow-v1"), (True, "workflow-v0.4")):
            value = fixture(legacy)
            for node in value["nodes"]:
                node.update(id=SENTINEL, type=SENTINEL, properties={SENTINEL: SENTINEL},
                            widgets_values=[SENTINEL])
            if legacy:
                value["links"][0] = [SENTINEL, SENTINEL, SENTINEL, SENTINEL, SENTINEL, SENTINEL]
            else:
                value["links"][0] = dict.fromkeys(value["links"][0], SENTINEL)
            for output in ("text", "json"):
                code, out, err = run_value(value, format, output=output)
                self.assertEqual(code, 1)
                for forbidden in (SENTINEL, "synthetic.json", str(Path.cwd()), "Traceback"):
                    self.assertTrue(forbidden not in out + err, "Sensitive output check failed.")

    def test_numeric_ids_and_synthetic_types_never_echo(self):
        value = fixture()
        value["nodes"][0]["id"] = 827364591
        value["nodes"][1]["id"] = "synthetic-id-private"
        value["links"][0].update(id=918273645, origin_id=827364591,
                                  target_id="synthetic-id-private")
        for output in ("text", "json"):
            code, out, err = run_value(value, output=output)
            self.assertEqual(code, 1)
            for forbidden in ("827364591", "918273645", "synthetic-id-private",
                              "SyntheticSource", "SyntheticSink", "SyntheticTransform"):
                self.assertTrue(forbidden not in out + err, "Sensitive output check failed.")

    def test_internal_exception_safe(self):
        with patch("workflow_auditor.cli.workflow_v1.validate", side_effect=OSError(SENTINEL)):
            code, out, err = run_value(fixture())
        self.assertEqual(code, 3)
        self.assertTrue(SENTINEL not in out + err, "Sensitive output check failed.")
        self.assertNotIn("Traceback", out + err)
        self.assertIn("INTERNAL_ERROR", out)

    def test_bad_json_keeps_content_exit(self):
        with patch("workflow_auditor.cli.read_input", return_value=b'{"x":1,"x":2}'):
            code, out, err = invoke(["audit", "synthetic.json", "--format", "workflow-v1"])
        self.assertEqual(code, 1)
        self.assertIn("JSON_DUPLICATE_KEY", out)
