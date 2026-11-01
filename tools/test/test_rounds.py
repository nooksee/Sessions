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


    def test_drift_block_is_the_registered_text(self):
        """The Resident Center drift step (Control's frozen-runtime decision) is present and byte-bound:
        the wrapper's 6537-byte suffix hashes as George's stage C packet (2026-11-01 15:20) states.
        A static check, never a production run of the detector."""
        import hashlib
        tail = TOOL.read_bytes()[-6537:]
        self.assertIn(b"# Resident Center source drift", tail)
        self.assertIn(b"check_resident_center_drift.py", tail)
        self.assertIn(b"DETECTOR FAULT", tail)
        self.assertEqual(hashlib.sha256(tail).hexdigest()[:16], "fa54ccf3e0b5f1d6")

if __name__ == "__main__":
    unittest.main()
