import json
import os
import subprocess
import sys
import unittest
from tests.security.test_no_sensitive_echo import invoke


class CliTests(unittest.TestCase):
    def test_valid_and_deterministic(self):
        for mode in ("text", "json"):
            args = ["audit", "tests/fixtures/valid_generic.json", "--output-format", mode]
            first = invoke(args)
            self.assertEqual(first[0], 0)
            self.assertEqual(first, invoke(args))
            self.assertEqual(first[2], "")
            self.assertNotIn("INTERNAL_ERROR", first[1])

    def test_content_error(self):
        code, out, err = invoke(["audit", "tests/fixtures/duplicate_key.json",
                                 "--output-format", "json"])
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(out)["diagnostics"][0]["rule_id"], "JSON_DUPLICATE_KEY")
        self.assertEqual(err, "")

    def test_boundary_and_usage(self):
        for args in (["audit", "tests/fixtures/absent.json"], [], ["audit"],
                     ["audit", "tests", "--max-depth", "0"]):
            self.assertEqual(invoke(args)[0], 2)

    def test_fingerprint(self):
        args = ["audit", "tests/fixtures/valid_generic.json", "--output-format", "json"]
        self.assertIsNone(json.loads(invoke(args)[1])["fingerprint"])
        fp = json.loads(invoke(args + ["--fingerprint"])[1])["fingerprint"]
        self.assertTrue(fp["user_opt_in"])
        self.assertRegex(fp["value"], "^[0-9a-f]{64}$")

    def test_entrypoint(self):
        completed = subprocess.run(
            [sys.executable, "-S", "-m", "workflow_auditor", "audit",
             "tests/fixtures/valid_generic.json"], capture_output=True, text=True,
            check=False, env=os.environ.copy())
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(completed.stderr, "")
        self.assertIn("input: input-1", completed.stdout)
