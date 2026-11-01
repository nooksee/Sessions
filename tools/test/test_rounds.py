#!/usr/bin/env python3
"""Smoke test for ops/lib/scripts/rounds.sh, ported from Scripts/session_health_rounds.sh on 2026-11-01.

The legacy script came without a test suite. This suite proves only that the
ported copy is present and compiles; it runs nothing, reads no body and writes
nothing. Behavior cases: [PLACEHOLDER: behavior cases on synthetic inputs,
owner: the writer the Session Continuity Manager names for rounds]. Run:

    python3 -I -B tools/test/test_rounds.py
"""
import py_compile
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parents[2] / "ops" / "lib" / "scripts" / "rounds.sh"


class SmokeTest(unittest.TestCase):
    def test_tool_exists(self):
        self.assertTrue(TOOL.is_file(), TOOL)

    def test_tool_compiles(self):
        r = subprocess.run(["bash", "-n", str(TOOL)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
