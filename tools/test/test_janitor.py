#!/usr/bin/env python3
"""Focused fail-closed tests for the Codex writer-claim janitor."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[2] / "ops" / "lib" / "scripts" / "janitor.py"
SPEC = importlib.util.spec_from_file_location("codex_claim_janitor", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
janitor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(janitor)


class ClaimReadTests(unittest.TestCase):
    @mock.patch.object(janitor.subprocess, "run")
    def test_claims_uses_existing_json_checker(self, run: mock.Mock) -> None:
        findings = [{"thread": "thread-1", "holder_kind": "background-daemon"}]
        run.return_value = SimpleNamespace(stdout=json.dumps({"findings": findings}))

        self.assertEqual(janitor.claims(), findings)
        run.assert_called_once_with(
            [janitor.sys.executable, str(janitor.CHECKER), "--json"],
            capture_output=True,
            text=True,
            timeout=60,
        )


class IdleEvidenceTests(unittest.TestCase):
    def test_body_idle_minutes_reads_exact_rollout_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / "state.sqlite"
            body = root / "body.jsonl"
            body.write_text("{}\n", encoding="utf-8")
            now = 2_000_000_000.0
            os.utime(body, (now - 7_200, now - 7_200))
            with sqlite3.connect(state) as con:
                con.execute("create table threads (id text, rollout_path text)")
                con.execute("insert into threads values (?, ?)", ("thread-1", str(body)))

            with mock.patch.object(janitor, "STATE", state), mock.patch.object(
                janitor.time, "time", return_value=now
            ):
                self.assertEqual(janitor.body_idle_minutes("thread-1"), 120.0)

    def test_unknown_thread_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "state.sqlite"
            with sqlite3.connect(state) as con:
                con.execute("create table threads (id text, rollout_path text)")
            with mock.patch.object(janitor, "STATE", state):
                self.assertIsNone(janitor.body_idle_minutes("missing"))


class MainDecisionTests(unittest.TestCase):
    def run_main(self) -> str:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            janitor.main()
        return out.getvalue()

    @mock.patch.object(janitor, "claims", return_value=[])
    @mock.patch.object(janitor.subprocess, "run")
    def test_no_daemon_claim_makes_no_change(self, run: mock.Mock, _claims: mock.Mock) -> None:
        self.assertIn("nothing to do", self.run_main())
        run.assert_not_called()

    @mock.patch.object(janitor, "body_idle_minutes", return_value=59.0)
    @mock.patch.object(
        janitor,
        "claims",
        return_value=[{"thread": "thread-1", "holder_kind": "background-daemon"}],
    )
    @mock.patch.object(janitor.subprocess, "run")
    def test_recent_body_stands_down(
        self, run: mock.Mock, _claims: mock.Mock, _idle: mock.Mock
    ) -> None:
        self.assertIn("standing down", self.run_main())
        run.assert_not_called()

    @mock.patch.object(janitor.time, "sleep")
    @mock.patch.object(janitor, "body_idle_minutes", return_value=120.0)
    @mock.patch.object(
        janitor,
        "claims",
        side_effect=[
            [{"thread": "thread-1", "holder_kind": "background-daemon"}],
            [],
        ],
    )
    @mock.patch.object(janitor.subprocess, "run")
    def test_idle_daemon_claim_gets_one_verified_restart(
        self,
        run: mock.Mock,
        _claims: mock.Mock,
        _idle: mock.Mock,
        sleep: mock.Mock,
    ) -> None:
        self.assertIn("released", self.run_main())
        run.assert_called_once_with(
            ["systemctl", "--user", "restart", janitor.SERVICE],
            check=True,
            timeout=120,
        )
        sleep.assert_called_once_with(20)


if __name__ == "__main__":
    unittest.main()
