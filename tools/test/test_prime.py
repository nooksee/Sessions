#!/usr/bin/env python3
"""Smoke test for ops/lib/scripts/prime.py, ported from Scripts/build_prime_session_candidate_packet.py on 2026-11-01.

The legacy script came without a test suite. This suite proves only that the
ported copy is present and compiles; it runs nothing, reads no body and writes
nothing. Behavior cases: [PLACEHOLDER: behavior cases on synthetic inputs,
owner: the writer the Session Continuity Manager names for prime]. Run:

    python3 -I -B tools/test/test_prime.py
"""
import importlib.util
import py_compile
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

TOOL = Path(__file__).resolve().parents[2] / "ops" / "lib" / "scripts" / "prime.py"


def load(name, path, **stubs):
    """A private copy of the module, so that a value read at import is read under this test's environment."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, {name: module, **stubs}):
        spec.loader.exec_module(module)
    return module


class SmokeTest(unittest.TestCase):
    def test_tool_exists(self):
        self.assertTrue(TOOL.is_file(), TOOL)

    def test_tool_compiles(self):
        with tempfile.TemporaryDirectory() as tmp:
            py_compile.compile(str(TOOL), cfile=str(Path(tmp) / "compiled.pyc"), doraise=True)


class TheHostNames(unittest.TestCase):
    def test_the_live_usb_marker_names_the_tools_own_place(self):
        module = load("prime_under_test", TOOL)
        self.assertEqual(module.ROOT, TOOL.resolve().parents[4])
        self.assertIn(f"Mount and verify `{module.ROOT}` before acting.", module.LIVE_USB_MARKER)


if __name__ == "__main__":
    unittest.main()
