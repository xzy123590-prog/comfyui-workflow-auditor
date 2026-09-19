import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from workflow_auditor.cli import main


SENTINEL = "SENSITIVE_SENTINEL_DO_NOT_ECHO_48291"


def invoke(args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(args)
    return code, out.getvalue(), err.getvalue()


class NoEchoTests(unittest.TestCase):
    def test_values_keys_paths_and_errors(self):
        with tempfile.TemporaryDirectory(dir="tests") as folder:
            path = Path(folder) / (SENTINEL + ".json")
            payloads = [
                json.dumps({SENTINEL: "../" + SENTINEL}).encode(),
                ('{"' + SENTINEL + '":1,"' + SENTINEL + '":2}').encode(),
                ('{"' + SENTINEL + '":').encode(), b"\xff",
            ]
            for payload in payloads:
                path.write_bytes(payload)
                for mode in ("text", "json"):
                    code, out, err = invoke(["audit", str(path), "--output-format", mode])
                    combined = out + err
                    self.assertTrue(SENTINEL not in combined, "SENTINEL_ECHO_CHECK = FAIL")
                    self.assertTrue(str(path) not in combined, "Path echo detected.")
                    self.assertTrue(str(path.absolute()) not in combined, "Path echo detected.")
                    self.assertEqual(err, "")

    def test_usage(self):
        for args in (["audit", SENTINEL, "--unknown-" + SENTINEL],
                     ["audit", SENTINEL, "--max-bytes", SENTINEL],
                     ["audit", SENTINEL, "--output-format", SENTINEL],
                     [SENTINEL]):
            code, out, err = invoke(args)
            self.assertEqual(code, 2)
            self.assertTrue(SENTINEL not in out + err, "SENTINEL_ECHO_CHECK = FAIL")

    def test_internal_error(self):
        with patch("workflow_auditor.cli.read_input", side_effect=RuntimeError(SENTINEL)):
            code, out, err = invoke(["audit", "synthetic.json"])
        self.assertEqual(code, 3)
        self.assertIn("INTERNAL_ERROR", out)
        self.assertTrue(SENTINEL not in out + err, "SENTINEL_ECHO_CHECK = FAIL")
        self.assertNotIn("Traceback", out + err)

    def test_render_failure(self):
        with patch("workflow_auditor.cli.render", side_effect=RuntimeError(SENTINEL)):
            code, out, err = invoke(["audit", "tests/fixtures/valid_generic.json"])
        self.assertEqual(code, 3)
        self.assertTrue(SENTINEL not in out + err, "SENTINEL_ECHO_CHECK = FAIL")
