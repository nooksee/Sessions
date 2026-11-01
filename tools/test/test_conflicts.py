#!/usr/bin/env python3
"""Focused tests for exact Codex thread-writer holder classification."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[2] / "ops" / "lib" / "scripts" / "conflicts.py"
SPEC = importlib.util.spec_from_file_location("writer_conflicts", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
conflicts = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(conflicts)


class HolderClassificationTests(unittest.TestCase):
    def test_editor_bridge(self) -> None:
        self.assertEqual(
            conflicts.classify_holder(
                "/home/nos4r2/.cache/JetBrains/PyCharm/acp-agents/codex-acp",
                "codex-acp",
            ),
            "editor-bridge",
        )

    def test_remote_daemon(self) -> None:
        self.assertEqual(
            conflicts.classify_holder(
                "/home/nos4r2/.codex/packages/standalone/current/codex",
                "codex app-server --remote-control --listen unix://",
            ),
            "background-daemon",
        )

    def test_visible_resume_console(self) -> None:
        self.assertEqual(
            conflicts.classify_holder(
                "/home/nos4r2/.codex/packages/standalone/current/codex",
                "codex resume 00000000-0000-0000-0000-000000000000",
            ),
            "terminal-cli",
        )

    def test_ordinary_terminal_cli(self) -> None:
        self.assertEqual(
            conflicts.classify_holder(
                "/home/nos4r2/.local/bin/codex",
                "codex",
            ),
            "terminal-cli",
        )

    def test_unrelated_process(self) -> None:
        self.assertEqual(
            conflicts.classify_holder("/usr/bin/python3", "python3 worker.py"),
            "unknown",
        )


if __name__ == "__main__":
    unittest.main()
