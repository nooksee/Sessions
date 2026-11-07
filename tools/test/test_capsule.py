#!/usr/bin/env python3
"""Smoke test for ops/lib/scripts/capsule.py, ported from Scripts/build_codex_succession_capsule.py on 2026-11-01.

The legacy script came without a test suite. This suite proves only that the
ported copy is present and compiles; it runs nothing, reads no body and writes
nothing. Behavior cases: [PLACEHOLDER: behavior cases on synthetic inputs,
owner: the writer the Session Continuity Manager names for capsule]. Run:

    python3 -I -B tools/test/test_capsule.py
"""
import importlib.util
import py_compile
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

TOOL = Path(__file__).resolve().parents[2] / "ops" / "lib" / "scripts" / "capsule.py"


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
    def text(self):
        module = load("capsule_under_test", TOOL)
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(module, "run_git", return_value="synthetic"):
            return module, module.build_capsule(Path(tmp))

    def test_the_working_root_is_the_tools_own_place(self):
        module, text = self.text()
        self.assertEqual(module.ROOT, TOOL.resolve().parents[4])
        self.assertIn(f"The working root for this repo is `{module.ROOT}`.", text)

    def test_the_operator_is_named_by_role(self):
        _, text = self.text()
        self.assertIn("The operator holds final authority.", text)


if __name__ == "__main__":
    unittest.main()
