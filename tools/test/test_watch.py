#!/usr/bin/env python3
"""Smoke test for ops/lib/scripts/watch.py, ported from Scripts/watch_codex_session_size.py on 2026-11-01.

The legacy script came without a test suite. This suite proves only that the
ported copy is present and compiles; it runs nothing, reads no body and writes
nothing. Behavior cases: [PLACEHOLDER: behavior cases on synthetic inputs,
owner: the writer the Integrator names for watch]. Run:

    python3 -I -B tools/test/test_watch.py
"""
import py_compile
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parents[2] / "ops" / "lib" / "scripts" / "watch.py"


class SmokeTest(unittest.TestCase):
    def test_tool_exists(self):
        self.assertTrue(TOOL.is_file(), TOOL)

    def test_tool_compiles(self):
        with tempfile.TemporaryDirectory() as tmp:
            py_compile.compile(str(TOOL), cfile=str(Path(tmp) / "compiled.pyc"), doraise=True)


if __name__ == "__main__":
    unittest.main()
