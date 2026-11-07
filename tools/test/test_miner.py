#!/usr/bin/env python3
"""Smoke test for ops/lib/scripts/miner.py, ported from Scripts/mine_codex_logs_compaction_events.py on 2026-11-01.

The legacy script came without a test suite. This suite proves only that the
ported copy is present and compiles; it runs nothing, reads no body and writes
nothing. Behavior cases: [PLACEHOLDER: behavior cases on synthetic inputs,
owner: the writer the Session Continuity Manager names for miner]. Run:

    python3 -I -B tools/test/test_miner.py
"""
import importlib.util
import os
import py_compile
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

TOOL = Path(__file__).resolve().parents[2] / "ops" / "lib" / "scripts" / "miner.py"


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
    def test_the_default_database_is_under_this_users_home(self):
        with mock.patch.dict(os.environ, {"HOME": "/home/example"}):
            module = load("miner_under_test", TOOL)
        self.assertEqual(module.DEFAULT_DB, Path("/home/example/.codex/logs_2.sqlite"))


if __name__ == "__main__":
    unittest.main()
