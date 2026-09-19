import unittest
from workflow_auditor.diagnostics import Diagnostic, TEMPLATES
from workflow_auditor.report import make_report, render


class DiagnosticTests(unittest.TestCase):
    def test_fixed_templates(self):
        for rule in TEMPLATES:
            diagnostic = Diagnostic(rule)
            self.assertEqual(diagnostic.to_dict()["message"], TEMPLATES[rule])
            self.assertEqual(set(diagnostic.to_dict()),
                             {"rule_id", "severity", "status", "json_pointer",
                              "message", "safe_parameters"})

    def test_validation(self):
        for kwargs in ({"rule_id": "unknown"},
                       {"rule_id": "JSON_INVALID", "severity": "unknown"},
                       {"rule_id": "JSON_INVALID", "status": "unknown"},
                       {"rule_id": "JSON_INVALID", "json_pointer": "/raw-key"},
                       {"rule_id": "JSON_INVALID", "safe_parameters": {"count": True}}):
            with self.assertRaises(ValueError):
                Diagnostic(**kwargs)

    def test_sort_summary_stability(self):
        items = [Diagnostic("JSON_INVALID", json_pointer="/$k1"),
                 Diagnostic("JSON_EMPTY", status="NOT_CHECKED"),
                 Diagnostic("STRING_FILE_URI", severity="WARNING", json_pointer="/$k0"),
                 Diagnostic("JSON_INVALID", severity="INFO", json_pointer="/$k2")]
        report = make_report(items)
        self.assertEqual(report, make_report(list(reversed(items))))
        self.assertEqual(report["summary"], dict(error_count=2, warning_count=1,
                                               info_count=1, not_checked_count=1))
        for mode in ("text", "json"):
            self.assertEqual(render(report, mode), render(make_report(items), mode))
