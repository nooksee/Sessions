#!/usr/bin/env python3
"""Smoke test for ops/lib/scripts/estimate.py, ported from Scripts/analyze_codex_token_context_pressure.py on 2026-11-01.

The legacy script came without a test suite. This suite proves only that the
ported copy is present and compiles; it runs nothing, reads no body and writes
nothing. Behavior cases: [PLACEHOLDER: behavior cases on synthetic inputs,
owner: the writer the Integrator names for estimate]. Run:

    python3 -I -B tools/test/test_estimate.py
"""
import importlib.util
import py_compile
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

TOOL = Path(__file__).resolve().parents[2] / "ops" / "lib" / "scripts" / "estimate.py"


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
    def test_the_evidence_folder_is_the_rooms(self):
        """tiktoken is stubbed, since the checks run with nothing installed; nothing here counts a token."""
        module = load("estimate_under_test", TOOL, tiktoken=types.ModuleType("tiktoken"))
        self.assertEqual(module.EVIDENCE_DIR, TOOL.resolve().parents[3] / "logs")


if __name__ == "__main__":
    unittest.main()
