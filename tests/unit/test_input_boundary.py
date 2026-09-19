import os
import stat
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from workflow_auditor.diagnostics import Rejected
from workflow_auditor.input_boundary import read_input, validate_path, is_link_or_reparse
from workflow_auditor.limits import MAX_BYTES


class BoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir="tests")
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "input.json"
        self.path.write_bytes(b"{}")

    def reject(self, path, rule, **kwargs):
        with self.assertRaises(Rejected) as context:
            read_input(str(path), **kwargs)
        self.assertEqual(context.exception.diagnostic.rule_id, rule)

    def test_valid(self):
        self.assertEqual(read_input(str(self.path)), b"{}")

    def test_missing(self):
        self.reject(self.path.with_name("absent.json"), "INPUT_NOT_FOUND")

    def test_directory(self):
        self.reject(self.temp.name, "INPUT_NOT_REGULAR_FILE")

    def test_unc(self):
        self.reject("\\\\" + "synthetic" + "\\share\\input.json", "INPUT_UNC_PATH")
        self.reject("//" + "synthetic/share/input.json", "INPUT_UNC_PATH")

    def test_device(self):
        for prefix in ("\\\\?\\", "\\\\.\\", "\\??\\"):
            self.reject(prefix + "synthetic", "INPUT_DEVICE_PATH")

    def test_size(self):
        self.reject(self.path, "INPUT_TOO_LARGE", max_bytes=1)
        self.assertEqual(read_input(str(self.path), 2), b"{}")

    def test_bool_and_limits(self):
        for value in (True, False, 0, -1, MAX_BYTES + 1, "2"):
            with self.assertRaises(ValueError):
                read_input(str(self.path), value)

    def test_link_attributes(self):
        self.assertTrue(is_link_or_reparse(SimpleNamespace(st_mode=stat.S_IFLNK)))
        self.assertTrue(is_link_or_reparse(SimpleNamespace(
            st_mode=stat.S_IFREG, st_file_attributes=0x400)))
        self.assertFalse(is_link_or_reparse(SimpleNamespace(
            st_mode=stat.S_IFREG, st_file_attributes=0)))
        with patch("workflow_auditor.input_boundary.os.fstat",
                   return_value=SimpleNamespace(st_mode=stat.S_IFLNK)):
            self.reject(self.path, "INPUT_LINK_OR_REPARSE_POINT")

    def test_non_regular_handle(self):
        with patch("workflow_auditor.input_boundary.os.fstat",
                   return_value=SimpleNamespace(st_mode=stat.S_IFIFO)):
            self.reject(self.path, "INPUT_NOT_REGULAR_FILE")

    def test_permission_error(self):
        with patch("workflow_auditor.input_boundary.os.fstat", side_effect=PermissionError):
            self.reject(self.path, "INPUT_NOT_REGULAR_FILE")

    def test_growth_bounded(self):
        with patch("workflow_auditor.input_boundary.os.read", return_value=b"xxx"):
            self.reject(self.path, "INPUT_TOO_LARGE", max_bytes=2)

    def test_no_embedded_reads(self):
        payload = b'{"path":"relative-unused.json"}'
        self.path.write_bytes(payload)
        self.assertEqual(read_input(str(self.path)), payload)

    def test_invalid_path(self):
        for value in ("", "\0", "../input.json"):
            self.reject(value, "INPUT_NOT_REGULAR_FILE")

    @unittest.skipUnless(os.name == "nt", "Windows device syntax")
    def test_reserved_devices(self):
        for value in ("NUL", "CON.txt", "COM1", "x:relative", "item.json:stream"):
            self.reject(value, "INPUT_DEVICE_PATH")
