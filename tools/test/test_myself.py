#!/usr/bin/env python3
"""Focused root-free tests for the resident self-check canary."""

from __future__ import annotations

import contextlib
import dataclasses
import datetime as dt
import hashlib
import importlib.util
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[2] / "ops" / "lib" / "scripts" / "myself.py"
SESSIONS_ROOT = MODULE_PATH.parents[3]
SPEC = importlib.util.spec_from_file_location("check_myself", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
check_myself = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = check_myself
SPEC.loader.exec_module(check_myself)

NOW = dt.datetime(2026, 8, 9, 23, 0, tzinfo=dt.timezone.utc)
CODEX_ID = "0000b1b1-0000-4000-8000-00000000b1b1"
CLAUDE_ID = "0000b2b2-0000-4000-8000-00000000b2b2"


def json_line(payload: dict) -> str:
    return json.dumps(payload, separators=(",", ":")) + "\n"


def digest_tree(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


class Fixture:
    def __init__(self, root: Path, provider: str) -> None:
        self.root = root
        self.provider = provider
        self.session_id = CODEX_ID if provider == "codex" else CLAUDE_ID
        self.key = "fixture-codex" if provider == "codex" else "fixture-claude"
        self.role = "Fixture Analyst"
        self.person = "Cora Codex" if provider == "codex" else "Clara Claude"
        self.display = f"{self.role} ({self.person})"
        self.project = root / "Sessions"
        self.project.mkdir(parents=True)
        self.registry = root / "resident-identities.json"
        self.roster = root / "residents.json"
        self.bindings = root / "host-bindings.json"
        self.resource = root / "resource-state.json"     # the shared status-line record: never read by the leg
        self.window_spec = root / "gauge-window-table.md"
        self.proc_root = root / "proc"
        self.codex_lock_root = root / "codex-writer-locks"
        self.codex_root = root / "codex"
        self.claude_root = root / "claude"
        self.paths = check_myself.CheckPaths(
            registry=self.registry,
            roster=self.roster,
            bindings=self.bindings,
            codex_lock_root=self.codex_lock_root,
            proc_root=self.proc_root,
            window_spec=self.window_spec,
            room=self.project,
        )
        self.write_room_setting()
        self.write_layers()
        self.write_body()

    def write_room_setting(self, payload: object = None) -> None:
        """The room's own project setting, as this room requires it: auto memory off."""
        folder = self.project / ".claude"
        folder.mkdir(exist_ok=True)
        (folder / "settings.json").write_text(json.dumps({"autoMemoryEnabled": False} if payload is None else payload))

    @property
    def body(self) -> Path:
        if self.provider == "codex":
            return (
                self.codex_root
                / "sessions/2026/08/09"
                / f"rollout-2026-08-09T00-00-00-{self.session_id}.jsonl"
            )
        return self.claude_root / "-fixture-Sessions" / f"{self.session_id}.jsonl"

    def write_layers(self) -> None:
        self.registry.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "identities": [
                        {
                            "key": self.key,
                            "provider": self.provider,
                            "session_id": self.session_id,
                            "room": str(self.project),
                            "role": self.role,
                            "person": self.person,
                            "verified": "fixture",
                        }
                    ],
                }
            )
            + "\n",
            encoding="utf-8",
        )
        self.roster.write_text(
            json.dumps(
                {
                    "schema_version": "fixture/v1",
                    "residents": [
                        {
                            "key": self.key,
                            "display_name": self.display,
                            "provider_id": self.provider,
                            "enabled": True,
                        }
                    ],
                }
            )
            + "\n",
            encoding="utf-8",
        )
        self.bindings.write_text(
            json.dumps(
                {
                    "schema_version": "fixture/v1",
                    "providers": {
                        "codex": {"session_root": str(self.codex_root)},
                        "claude": {"session_root": str(self.claude_root)},
                    },
                    "residents": [
                        {
                            "key": self.key,
                            "provider_id": self.provider,
                            "session_id": self.session_id,
                            "project_root": str(self.project),
                        }
                    ],
                }
            )
            + "\n",
            encoding="utf-8",
        )
        self.bindings.chmod(0o600)
        self.resource.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "generated_at": NOW.isoformat(),
                    "provider": "anthropic",
                    "model": {"id": "claude-fixture"},
                    "context": {"window_size": 1000},
                }
            )
            + "\n",
            encoding="utf-8",
        )
        self.write_table()

    def write_table(self, rows: tuple = (("claude-fixture", 1000),)) -> None:
        """A synthetic copy of the gauge's reviewed window table, in the gauge spec's row form."""
        self.window_spec.write_text(
            "# Synthetic window table\n\n"
            + "".join(f"model={model}|window={window}|source=fixture table|observed=2026-08-09\n"
                      for model, window in rows),
            encoding="utf-8",
        )

    def codex_rows(
        self,
        *,
        tokens: int = 120,
        message_count: int = 2,
        shared_timestamp: str | None = None,
        native_compactions: int = 0,
    ) -> list[dict]:
        rows = [
            {
                "timestamp": "2026-08-09T22:00:00Z",
                "type": "session_meta",
                "payload": {"id": self.session_id, "cwd": str(self.project)},
            },
            {
                "timestamp": "2026-08-09T22:00:01Z",
                "type": "compacted",
                "payload": {
                    "message": f"LINEAGE MEMORY. You are `{self.display}`.",
                    "replacement_history": [],
                },
            },
        ]
        for number in range(native_compactions):
            rows.append(
                {
                    "timestamp": f"2026-08-09T22:01:{number:02d}Z",
                    "type": "compacted",
                    "payload": {
                        "message": "",
                        "replacement_history": [],
                        "window_number": number + 1,
                    },
                }
            )
        for number in range(message_count):
            stamp = shared_timestamp or f"2026-08-09T22:02:{number:02d}Z"
            rows.append(
                {
                    "timestamp": stamp,
                    "type": "response_item",
                    "payload": {
                        "type": "message",
                        "role": "user" if number % 2 == 0 else "assistant",
                        "content": [{"type": "input_text", "text": f"message {number}"}],
                    },
                }
            )
        rows.append(
            {
                "timestamp": "2026-08-09T22:03:00Z",
                "type": "event_msg",
                "payload": {
                    "type": "token_count",
                    "info": {
                        "last_token_usage": {"input_tokens": tokens},
                        "model_context_window": 1000,
                    },
                },
            }
        )
        return rows

    def claude_rows(self, *, tokens: int = 120) -> list[dict]:
        return [
            {
                "type": "user",
                "sessionId": self.session_id,
                "cwd": str(self.project),
                "timestamp": "2026-08-09T22:00:00Z",
                "message": {
                    "role": "user",
                    "content": (
                        "<session_clinic_orientation>\n"
                        f"You are {self.person.upper()}, {self.role}, resident "
                        f"of the Sessions project ({self.project}).\n"
                        "</session_clinic_orientation>"
                    ),
                },
            },
            {
                "type": "user",
                "sessionId": self.session_id,
                "cwd": str(self.project),
                "timestamp": "2026-08-09T22:01:00Z",
                "message": {"role": "user", "content": "fixture question"},
            },
            {
                "type": "assistant",
                "sessionId": self.session_id,
                "cwd": str(self.project),
                "timestamp": "2026-08-09T22:02:00Z",
                "message": {
                    "role": "assistant",
                    "model": "claude-fixture",
                    "content": [{"type": "text", "text": "fixture answer"}],
                    "usage": {
                        "input_tokens": 10,
                        "cache_creation_input_tokens": 10,
                        "cache_read_input_tokens": tokens - 20,
                        "output_tokens": 10,
                    },
                },
            },
        ]

    def write_body(self, **kwargs) -> None:
        self.body.parent.mkdir(parents=True, exist_ok=True)
        rows = self.codex_rows(**kwargs) if self.provider == "codex" else self.claude_rows(**kwargs)
        self.body.write_text("".join(json_line(row) for row in rows), encoding="utf-8")

    def fake_claude_parent(self, pid: int = 500, *, identify: bool = True) -> int:
        parent = self.proc_root / str(pid)
        parent.mkdir(parents=True)
        command = b"/home/fixture/.local/bin/claude\0"
        if identify:
            command += b"--resume\0" + self.session_id.encode() + b"\0"
        parent.joinpath("cmdline").write_bytes(command)
        parent.joinpath("environ").write_bytes(b"")
        parent.joinpath("status").write_text("Name:\tclaude\nPPid:\t1\n", encoding="utf-8")
        return pid

    def fake_codex_parent(self, pid: int = 400, *, hold_lock: bool = True) -> int:
        parent = self.proc_root / str(pid)
        parent.mkdir(parents=True, exist_ok=True)
        parent.joinpath("cmdline").write_bytes(
            b"/home/fixture/.local/bin/codex\0app-server\0"
        )
        parent.joinpath("status").write_text("Name:\tcodex\nPPid:\t1\n", encoding="utf-8")
        self.codex_lock_root.mkdir(parents=True, exist_ok=True)
        lock = self.codex_lock_root / f"{self.session_id}.lock"
        lock.touch()
        if hold_lock:
            fd_root = parent / "fd"
            fd_root.mkdir(exist_ok=True)
            descriptor = fd_root / "9"
            if not descriptor.exists() and not descriptor.is_symlink():
                descriptor.symlink_to(lock)
        return pid

    def fake_shell_parent(self, pid: int = 600) -> int:
        parent = self.proc_root / str(pid)
        parent.mkdir(parents=True)
        parent.joinpath("cmdline").write_bytes(b"/bin/bash\0")
        parent.joinpath("status").write_text(
            "Name:\tbash\nPPid:\t1\n",
            encoding="utf-8",
        )
        return pid

    def run(self, *, environ: dict[str, str] | None = None, start_pid: int | None = None):
        if environ is None:
            environ = (
                {"CODEX_THREAD_ID": self.session_id}
                if self.provider == "codex"
                else {}
            )
        if start_pid is None and self.provider == "codex" and "CODEX_THREAD_ID" in environ:
            start_pid = self.fake_codex_parent()
        return check_myself.run_check(
            self.paths,
            environ=environ,
            start_pid=start_pid,
            now=NOW,
        )


class ResidentSelfCheckTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_exact_codex_caller_identification(self) -> None:
        fixture = Fixture(self.root, "codex")
        report = fixture.run()
        output = check_myself.render(report)
        self.assertEqual(0, report.exit_code, output)
        self.assertIn(f"registry_identity={fixture.display}", output)
        self.assertIn("provider=codex", output)
        self.assertIn("result: PASS", output)

    def test_exact_claude_caller_identification_from_native_ancestry(self) -> None:
        fixture = Fixture(self.root, "claude")
        pid = fixture.fake_claude_parent()
        report = fixture.run(environ={}, start_pid=pid)
        output = check_myself.render(report)
        self.assertEqual(0, report.exit_code, output)
        self.assertIn(f"registry_identity={fixture.display}", output)
        self.assertIn(str(fixture.proc_root / str(pid) / "cmdline"), output)
        self.assertIn("provider=claude", output)

    def test_claude_backtick_orientation_remains_supported(self) -> None:
        fixture = Fixture(self.root, "claude")
        rows = fixture.claude_rows()
        rows[0]["message"]["content"] = (
            "<session_clinic_orientation>\n"
            f"You are `{fixture.display}`.\n"
            "</session_clinic_orientation>"
        )
        fixture.body.write_text(
            "".join(json_line(row) for row in rows),
            encoding="utf-8",
        )
        pid = fixture.fake_claude_parent()
        report = fixture.run(environ={}, start_pid=pid)
        self.assertEqual(0, report.exit_code, check_myself.render(report))
        self.assertEqual("pass", report.legs[5].status)
        self.assertIn("canonical display agrees", report.legs[5].detail)

    def test_latest_real_claude_orientation_supersedes_donor_identity(self) -> None:
        fixture = Fixture(self.root, "claude")
        rows = fixture.claude_rows()
        rows.insert(
            0,
            {
                "type": "user",
                "sessionId": fixture.session_id,
                "cwd": str(fixture.project),
                "timestamp": "2026-08-09T21:59:00Z",
                "message": {
                    "role": "user",
                    "content": (
                        "<session_clinic_orientation>\n"
                        "You are CLAUDE DEVENS, resident of the live-usb project.\n"
                        "</session_clinic_orientation>"
                    ),
                },
            },
        )
        fixture.body.write_text(
            "".join(json_line(row) for row in rows),
            encoding="utf-8",
        )
        pid = fixture.fake_claude_parent()
        report = fixture.run(environ={}, start_pid=pid)
        self.assertEqual(0, report.exit_code, check_myself.render(report))
        self.assertEqual("pass", report.legs[5].status)
        self.assertIn("identity_rows_seen=2", report.legs[5].detail)

    def test_unparseable_latest_orientation_does_not_reuse_older_identity(self) -> None:
        fixture = Fixture(self.root, "claude")
        rows = fixture.claude_rows()
        rows.insert(
            1,
            {
                "type": "user",
                "sessionId": fixture.session_id,
                "cwd": str(fixture.project),
                "timestamp": "2026-08-09T22:00:30Z",
                "message": {
                    "role": "user",
                    "content": (
                        "<session_clinic_orientation>\n"
                        "Identity statement unavailable.\n"
                        "</session_clinic_orientation>"
                    ),
                },
            },
        )
        fixture.body.write_text(
            "".join(json_line(row) for row in rows),
            encoding="utf-8",
        )
        pid = fixture.fake_claude_parent()
        report = fixture.run(environ={}, start_pid=pid)
        self.assertEqual(1, report.exit_code)
        self.assertEqual("undetermined", report.legs[5].status)
        self.assertIn("latest", report.legs[5].detail)
        self.assertIn("identity_rows_seen=2", report.legs[5].detail)

    def test_latest_claude_orientation_person_mismatch_is_a_finding(self) -> None:
        fixture = Fixture(self.root, "claude")
        rows = fixture.claude_rows()
        rows[0]["message"]["content"] = (
            "<session_clinic_orientation>\n"
            "You are WRONG PERSON, Fixture Analyst, resident of Sessions.\n"
            "</session_clinic_orientation>"
        )
        fixture.body.write_text(
            "".join(json_line(row) for row in rows),
            encoding="utf-8",
        )
        pid = fixture.fake_claude_parent()
        report = fixture.run(environ={}, start_pid=pid)
        self.assertEqual(1, report.exit_code)
        self.assertEqual("finding", report.legs[5].status)
        self.assertIn("registry_person", report.legs[5].detail)

    def test_claude_provider_name_and_role_orientation_is_correlated(self) -> None:
        fixture = Fixture(self.root, "claude")
        fixture.role = "Integrator"
        fixture.person = "Claude Shannon"
        fixture.display = f"{fixture.role} ({fixture.person})"
        fixture.write_layers()
        rows = fixture.claude_rows()
        rows[0]["message"]["content"] = (
            "<session_clinic_orientation>\n"
            "You are Claude, Integrator II, the resident "
            "session-health specialist in the Sessions room.\n"
            "</session_clinic_orientation>"
        )
        fixture.body.write_text(
            "".join(json_line(row) for row in rows),
            encoding="utf-8",
        )
        pid = fixture.fake_claude_parent()
        report = fixture.run(environ={}, start_pid=pid)
        self.assertEqual(0, report.exit_code, check_myself.render(report))
        self.assertEqual("pass", report.legs[5].status)
        self.assertIn("omits the durable surname", report.legs[5].detail)

    def test_ordinary_sessions_shell_without_provider_ancestry_fails_closed(self) -> None:
        fixture = Fixture(self.root, "codex")
        pid = fixture.fake_shell_parent()
        original_cwd = Path.cwd()
        try:
            os.chdir(SESSIONS_ROOT)
            report = check_myself.run_check(
                fixture.paths,
                environ={},
                start_pid=pid,
                now=NOW,
            )
        finally:
            os.chdir(original_cwd)
        output = check_myself.render(report)
        self.assertEqual(1, report.exit_code)
        self.assertEqual("undetermined", report.legs[0].status)
        self.assertIn("result: FAIL-CLOSED", output)
        self.assertNotIn("registry_identity=", output)
        self.assertIn(str(fixture.proc_root / str(pid) / "cmdline"), output)

    def test_incomplete_coverage_exits_nonzero(self) -> None:
        fixture = Fixture(self.root, "claude")
        fixture.window_spec.unlink()
        pid = fixture.fake_claude_parent()
        report = fixture.run(
            environ={"CLAUDE_CODE_SESSION_ID": fixture.session_id},
            start_pid=pid,
        )
        self.assertEqual(1, report.exit_code)
        self.assertGreater(report.unresolved, 0)
        self.assertIn(str(fixture.window_spec), check_myself.render(report))

    def test_every_material_leg_names_an_exact_surface(self) -> None:
        fixture = Fixture(self.root, "codex")
        report = fixture.run()
        self.assertEqual(check_myself.EXPECTED_LEGS, len(report.legs))
        self.assertTrue(all(leg.surfaces for leg in report.legs))
        output = check_myself.render(report)
        for path in (fixture.registry, fixture.roster, fixture.bindings, fixture.body):
            self.assertIn(str(path.resolve()), output)

    def test_coverage_output_contains_only_measured_counts(self) -> None:
        fixture = Fixture(self.root, "codex")
        output = check_myself.render(fixture.run())
        self.assertIn("findings=0", output)
        self.assertNotIn("included=", output)
        self.assertNotIn("excluded=", output)

    def test_stateless_second_run_reflects_changed_live_state(self) -> None:
        fixture = Fixture(self.root, "codex")
        before = check_myself.render(fixture.run())
        fixture.write_body(tokens=680)
        after = check_myself.render(fixture.run())
        self.assertNotEqual(before, after)
        self.assertIn("pressure=68.0%", after)
        self.assertNotIn("pressure=68.0%", before)

    def test_run_stores_nothing(self) -> None:
        fixture = Fixture(self.root, "codex")
        fixture.fake_codex_parent()
        before = digest_tree(self.root)
        first = check_myself.render(fixture.run())
        second = check_myself.render(fixture.run())
        after = digest_tree(self.root)
        self.assertEqual(first, second)
        self.assertEqual(before, after)

    def test_ambiguous_provider_signals_fail_closed(self) -> None:
        fixture = Fixture(self.root, "codex")
        claude_pid = fixture.fake_claude_parent()
        codex_pid = fixture.fake_codex_parent()
        (fixture.proc_root / str(codex_pid) / "status").write_text(
            f"Name:\tcodex\nPPid:\t{claude_pid}\n",
            encoding="utf-8",
        )
        report = fixture.run(
            environ={
                "CODEX_THREAD_ID": CODEX_ID,
                "CLAUDE_CODE_SESSION_ID": CLAUDE_ID,
            },
            start_pid=codex_pid,
        )
        self.assertEqual(1, report.exit_code)
        self.assertEqual("undetermined", report.legs[0].status)

    def test_spoofed_codex_environment_without_provider_ancestor_fails_closed(self) -> None:
        fixture = Fixture(self.root, "codex")
        report = check_myself.run_check(
            fixture.paths,
            environ={"CODEX_THREAD_ID": fixture.session_id},
            start_pid=None,
            now=NOW,
        )
        self.assertEqual(1, report.exit_code)
        self.assertEqual("undetermined", report.legs[0].status)
        self.assertIn("no matching codex process", report.legs[0].detail)

    def test_codex_environment_with_process_but_without_held_lock_fails_closed(self) -> None:
        fixture = Fixture(self.root, "codex")
        pid = fixture.fake_codex_parent(hold_lock=False)
        report = check_myself.run_check(
            fixture.paths,
            environ={"CODEX_THREAD_ID": fixture.session_id},
            start_pid=pid,
            now=NOW,
        )
        self.assertEqual(1, report.exit_code)
        self.assertEqual("undetermined", report.legs[0].status)
        self.assertIn("not held", report.legs[0].detail)

    def test_claude_environment_without_exact_process_identity_fails_closed(self) -> None:
        fixture = Fixture(self.root, "claude")
        pid = fixture.fake_claude_parent(identify=False)
        report = check_myself.run_check(
            fixture.paths,
            environ={"CLAUDE_CODE_SESSION_ID": fixture.session_id},
            start_pid=pid,
            now=NOW,
        )
        self.assertEqual(1, report.exit_code)
        self.assertEqual("undetermined", report.legs[0].status)
        self.assertIn("no matching exact Claude session", report.legs[0].detail)

    def test_duplicate_native_bodies_fail_closed(self) -> None:
        fixture = Fixture(self.root, "codex")
        duplicate = fixture.body.with_name(f"duplicate-{fixture.session_id}.jsonl")
        shutil.copyfile(fixture.body, duplicate)
        report = fixture.run()
        self.assertEqual(1, report.exit_code)
        self.assertGreaterEqual(report.duplicates, 1)
        self.assertEqual("undetermined", report.legs[4].status)

    def test_missing_binding_root_keeps_body_comparison_undetermined(self) -> None:
        fixture = Fixture(self.root, "codex")
        payload = json.loads(fixture.bindings.read_text(encoding="utf-8"))
        payload["residents"] = []
        fixture.bindings.write_text(json.dumps(payload) + "\n", encoding="utf-8")
        fixture.bindings.chmod(0o600)
        report = fixture.run()
        self.assertEqual(1, report.exit_code)
        self.assertEqual("undetermined", report.legs[4].status)
        self.assertIn("comparison unavailable", report.legs[4].detail)
        self.assertNotIn("metadata agree", report.legs[4].detail)

    def test_rotation_line_is_a_finding(self) -> None:
        fixture = Fixture(self.root, "codex")
        fixture.write_body(tokens=700)
        report = fixture.run()
        self.assertEqual(1, report.exit_code)
        self.assertEqual("finding", report.legs[6].status)
        self.assertIn("rotation_line=70.0%", report.legs[6].detail)

    def test_twenty_message_timestamp_cluster_is_a_finding(self) -> None:
        fixture = Fixture(self.root, "codex")
        fixture.write_body(
            message_count=20,
            shared_timestamp="2026-08-09T22:02:00Z",
        )
        report = fixture.run()
        self.assertEqual(1, report.exit_code)
        self.assertEqual("finding", report.legs[8].status)
        self.assertIn("clusters=1", report.legs[8].detail)

    def test_nineteen_message_timestamp_cluster_is_clear(self) -> None:
        fixture = Fixture(self.root, "codex")
        fixture.write_body(
            message_count=19,
            shared_timestamp="2026-08-09T22:02:00Z",
        )
        report = fixture.run()
        self.assertEqual(0, report.exit_code, check_myself.render(report))
        self.assertEqual("pass", report.legs[8].status)

    def test_native_compaction_excludes_synthetic_capsule(self) -> None:
        fixture = Fixture(self.root, "codex")
        fixture.write_body(native_compactions=1)
        report = fixture.run()
        self.assertEqual(0, report.exit_code, check_myself.render(report))
        self.assertIn("native_compactions=1", report.legs[7].detail)

    def test_body_identity_mismatch_is_a_finding(self) -> None:
        fixture = Fixture(self.root, "codex")
        rows = fixture.codex_rows()
        rows[1]["payload"]["message"] = (
            "LINEAGE MEMORY. You are `Wrong Role (Wrong Person)`."
        )
        fixture.body.write_text("".join(json_line(row) for row in rows), encoding="utf-8")
        report = fixture.run()
        self.assertEqual(1, report.exit_code)
        self.assertEqual("finding", report.legs[5].status)

    def test_malformed_body_row_is_not_counted_as_pass(self) -> None:
        fixture = Fixture(self.root, "codex")
        with fixture.body.open("a", encoding="utf-8") as handle:
            handle.write("{malformed\n")
        report = fixture.run()
        self.assertEqual(1, report.exit_code)
        self.assertEqual("finding", report.legs[7].status)
        self.assertGreater(len(report.source_failures), 0)

    def test_private_binding_mode_is_enforced(self) -> None:
        fixture = Fixture(self.root, "codex")
        fixture.bindings.chmod(0o644)
        report = fixture.run()
        self.assertEqual(1, report.exit_code)
        self.assertEqual("finding", report.legs[3].status)

    def test_arguments_are_rejected(self) -> None:
        saved = sys.argv
        stream = io.StringIO()
        try:
            sys.argv = [str(MODULE_PATH), "--guess"]
            with contextlib.redirect_stderr(stream):
                result = check_myself.main()
        finally:
            sys.argv = saved
        self.assertEqual(2, result)
        self.assertIn("accepts no arguments", stream.getvalue())



def _hold(fixture: Fixture, *, value: object = "held", drop_launcher_rows: bool) -> None:
    """Mark the fixture resident as held from the launcher (the operator, 2026-10-23)."""
    registry = json.loads(fixture.registry.read_text())
    registry["identities"][0]["launcher"] = value
    fixture.registry.write_text(json.dumps(registry))
    if drop_launcher_rows:
        for path in (fixture.roster, fixture.bindings):
            data = json.loads(path.read_text())
            data["residents"] = []
            path.write_text(json.dumps(data))
        fixture.bindings.chmod(0o600)


class HeldResidentTests(unittest.TestCase):
    """A registry-only claude or codex resident held from the launcher."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _run(self, provider: str, **hold: object) -> tuple[object, str]:
        root = self.root / f"{provider}-{len(list(self.root.iterdir()))}"
        root.mkdir()
        fixture = Fixture(root, provider)
        _hold(fixture, **hold)
        if provider == "claude":
            report = fixture.run(environ={}, start_pid=fixture.fake_claude_parent())
        else:
            report = fixture.run()
        return report, check_myself.render(report)

    def _leg(self, report: object, name: str) -> object:
        legs = [leg for leg in report.legs if leg.name == name]
        self.assertEqual(1, len(legs), name)
        return legs[0]

    def test_held_and_absent_from_launcher_passes(self) -> None:
        for provider in ("claude", "codex"):
            with self.subTest(provider=provider):
                report, output = self._run(provider, drop_launcher_rows=True)
                self.assertEqual(0, report.exit_code, output)
                self.assertIn("result: PASS", output)
                for name in ("launcher roster", "host bindings"):
                    leg = self._leg(report, name)
                    self.assertEqual("pass", leg.status, output)
                    self.assertIn("held from the launcher", leg.detail)
                    self.assertIn("absent as required", leg.detail)

    def test_held_but_present_in_launcher_is_a_finding(self) -> None:
        for provider in ("claude", "codex"):
            with self.subTest(provider=provider):
                report, output = self._run(provider, drop_launcher_rows=False)
                self.assertNotEqual(0, report.exit_code, output)
                for name in ("launcher roster", "host bindings"):
                    leg = self._leg(report, name)
                    self.assertEqual("finding", leg.status, output)
                    self.assertIn("present although the registry holds it from the launcher",
                                  leg.detail)

    def test_held_session_bound_under_another_key_is_a_finding(self) -> None:
        # Copilot review of PR #112: a bindings row under another key that
        # carries the held session is reported too.
        for provider in ("claude", "codex"):
            with self.subTest(provider=provider):
                root = self.root / f"alias-{provider}"
                root.mkdir()
                fixture = Fixture(root, provider)
                _hold(fixture, drop_launcher_rows=True)
                data = json.loads(fixture.bindings.read_text())
                data["residents"] = [{"key": "someone-else", "session_id": fixture.session_id}]
                fixture.bindings.write_text(json.dumps(data))
                fixture.bindings.chmod(0o600)
                report = (fixture.run(environ={}, start_pid=fixture.fake_claude_parent())
                          if provider == "claude" else fixture.run())
                output = check_myself.render(report)
                leg = self._leg(report, "host bindings")
                self.assertEqual("finding", leg.status, output)
                self.assertIn("held session is bound under launcher key someone-else", leg.detail)
                self.assertNotEqual(0, report.exit_code, output)

    def _held_fixture(self, provider: str, tag: str) -> Fixture:
        root = self.root / f"{tag}-{provider}-{len(list(self.root.iterdir()))}"
        root.mkdir()
        fixture = Fixture(root, provider)
        _hold(fixture, drop_launcher_rows=True)
        return fixture

    def _run_fixture(self, fixture: Fixture) -> tuple[object, str]:
        report = (fixture.run(environ={}, start_pid=fixture.fake_claude_parent())
                  if fixture.provider == "claude" else fixture.run())
        return report, check_myself.render(report)

    def test_held_still_requires_private_bindings_mode(self) -> None:
        # Copilot review of PR #112, pinned per Claudio's condition 5: only
        # 0600 passes; holding changes row expectations, not file privacy.
        for provider in ("claude", "codex"):
            for mode in (0o400, 0o640, 0o644, 0o660, 0o700, 0o606, 0o600):
                with self.subTest(provider=provider, mode=oct(mode)):
                    fixture = self._held_fixture(provider, "mode")
                    fixture.bindings.chmod(mode)
                    report, output = self._run_fixture(fixture)
                    leg = self._leg(report, "host bindings")
                    if mode == 0o600:
                        self.assertEqual("pass", leg.status, output)
                    else:
                        self.assertEqual("finding", leg.status, output)
                        self.assertIn(f"private binding mode={oct(mode)}", leg.detail)
                        self.assertNotEqual(0, report.exit_code, output)

    def test_held_mode_follows_a_symlink_like_the_unheld_leg(self) -> None:
        # The unheld leg reads the mode through stat(), which follows a link;
        # the held leg must judge the same file the same way.
        for target_mode, status in ((0o600, "pass"), (0o644, "finding")):
            with self.subTest(target_mode=oct(target_mode)):
                fixture = self._held_fixture("codex", "link")
                real = fixture.bindings.with_name("real-bindings.json")
                fixture.bindings.rename(real)
                real.chmod(target_mode)
                fixture.bindings.symlink_to(real)
                report, output = self._run_fixture(fixture)
                self.assertEqual(status, self._leg(report, "host bindings").status, output)

    def test_held_alias_rules(self) -> None:
        # Pinned per Claudio's condition 5: the held resident's own key is
        # presence, not an alias; another key counts only with the same
        # session; aliases are listed in sorted order.
        fixture = self._held_fixture("codex", "own")
        data = json.loads(fixture.bindings.read_text())
        data["residents"] = [{"key": fixture.key, "session_id": fixture.session_id}]
        fixture.bindings.write_text(json.dumps(data))
        fixture.bindings.chmod(0o600)
        report, output = self._run_fixture(fixture)
        leg = self._leg(report, "host bindings")
        self.assertIn("present although the registry holds it from the launcher", leg.detail)
        self.assertNotIn("bound under launcher key", leg.detail)

        fixture = self._held_fixture("codex", "other")
        data = json.loads(fixture.bindings.read_text())
        data["residents"] = [{"key": "someone-else", "session_id": "different-session"}]
        fixture.bindings.write_text(json.dumps(data))
        fixture.bindings.chmod(0o600)
        report, output = self._run_fixture(fixture)
        self.assertEqual("pass", self._leg(report, "host bindings").status, output)

        fixture = self._held_fixture("codex", "order")
        data = json.loads(fixture.bindings.read_text())
        data["residents"] = [{"key": "zeta", "session_id": fixture.session_id},
                             {"key": "alpha", "session_id": fixture.session_id}]
        fixture.bindings.write_text(json.dumps(data))
        fixture.bindings.chmod(0o600)
        report, output = self._run_fixture(fixture)
        self.assertIn("held session is bound under launcher key alpha, zeta (",
                      self._leg(report, "host bindings").detail)

    def test_held_malformed_collection_is_not_absence(self) -> None:
        # Copilot review of PR #112: a missing or malformed collection is not
        # verified absence for a held resident.
        cases = {
            "no residents field": {},
            "residents not a list": {"residents": {"key": "x"}},
            "unreadable entry": {"residents": ["not an object"]},
            "readable row beside an unreadable one": {
                "residents": [{"key": "someone-else", "session_id": "other"}, "not an object"]},
            "top-level payload not an object": [],
        }
        for which in ("roster", "bindings"):
            for label, payload in cases.items():
              for provider in ("claude", "codex"):
                with self.subTest(which=which, case=label, provider=provider):
                    root = self.root / f"bad-{which}-{len(list(self.root.iterdir()))}"
                    root.mkdir()
                    fixture = Fixture(root, provider)
                    _hold(fixture, drop_launcher_rows=True)
                    path = fixture.roster if which == "roster" else fixture.bindings
                    original = json.loads(path.read_text())
                    if which == "bindings" and isinstance(payload, dict):
                        # Keep the provider configuration; break only the collection.
                        payload = {**{k: v for k, v in original.items() if k != "residents"},
                                   **payload}
                    path.write_text(json.dumps(payload))
                    if which == "bindings":
                        path.chmod(0o600)
                    report, _ = self._run_fixture(fixture)
                    output = check_myself.render(report)
                    name = "launcher roster" if which == "roster" else "host bindings"
                    leg = self._leg(report, name)
                    self.assertEqual("undetermined", leg.status, output)
                    self.assertIn("absence cannot be verified", leg.detail)
                    self.assertNotEqual(0, report.exit_code, output)

    def test_unknown_launcher_value_is_a_finding(self) -> None:
        for value in ("served", "Held", "", None, True):
            with self.subTest(value=value):
                report, output = self._run("codex", value=value, drop_launcher_rows=False)
                self.assertNotEqual(0, report.exit_code, output)
                leg = self._leg(report, "launcher roster")
                self.assertEqual("finding", leg.status, output)
                self.assertIn(f"registry launcher value {value!r} is not 'held'", leg.detail)


class SharedGaugePressureTests(unittest.TestCase):
    """The eleven synthetic reader cases, with actual caller/registry legs."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        gauge_path = MODULE_PATH.with_name("gauge.py")
        spec = importlib.util.spec_from_file_location("myself_parity_gauge", gauge_path)
        self.gauge = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.gauge)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _fixture(self, provider):
        fixture = Fixture(self.root, provider)
        fixture.write_table((("claude-fixture", 1_000_000),))
        if provider == "codex":
            rows = [row for row in fixture.codex_rows() if row["type"] != "event_msg"]
            rows.append({"timestamp": "2026-08-09T22:10:00Z", "type": "turn_context",
                         "payload": {"model": "synthetic-codex"}})
        else:
            rows = [row for row in fixture.claude_rows() if row["type"] != "assistant"]
        rows.append(self._usage(provider, 300_000))
        fixture.body.write_text("".join(json_line(row) for row in rows))
        return fixture

    @staticmethod
    def _usage(provider, tokens, stamp="2026-08-09T22:20:00Z", window=1_000_000, side=False):
        if provider == "codex":
            return {"timestamp": stamp, "type": "event_msg", "payload": {"type": "token_count",
                "info": {"last_token_usage": {"input_tokens": tokens}, "model_context_window": window}}}
        return {"type": "assistant", "isSidechain": side, "timestamp": stamp,
                "message": {"id": "synthetic-" + stamp, "model": "claude-fixture",
                    "usage": {"input_tokens": tokens, "cache_read_input_tokens": 0,
                              "cache_creation_input_tokens": 0, "output_tokens": 1}}}

    @staticmethod
    def _boundary(provider, side=False):
        if provider == "codex":
            return {"timestamp": "2026-08-09T22:30:00Z", "type": "compacted",
                    "payload": {"message": "", "window_number": 2}}
        return {"timestamp": "2026-08-09T22:30:00Z", "type": "system",
                "subtype": "compact_boundary", "isSidechain": side}

    @staticmethod
    def _append(fixture, row, terminated=True):
        with fixture.body.open("a") as handle:
            handle.write(json.dumps(row, separators=(",", ":")) + ("\n" if terminated else ""))

    def _read(self, fixture):
        if fixture.provider == "claude":
            if not hasattr(fixture, "synthetic_parent"):
                fixture.synthetic_parent = fixture.fake_claude_parent()
            report = fixture.run(environ={}, start_pid=fixture.synthetic_parent)
        else:
            report = fixture.run()
        legs = {leg.name: leg for leg in report.legs}
        for name in ("caller identity", "identity registry"):
            self.assertEqual("pass", legs[name].status, check_myself.render(report))
        measured = self.gauge.measure(
            {"key": fixture.key, "person": fixture.person, "provider": fixture.provider,
             "session_id": fixture.session_id}, NOW,
            {"claude-fixture": {"window": 1_000_000, "source": "synthetic", "observed": "2026-08-09"}},
            None, fixture.claude_root, [fixture.codex_root / "sessions"],
            [self.root / "absent-archive"], self.root / "absent-copilot")
        return report, legs["context pressure"], measured

    def _known(self, fixture, tokens):
        report, leg, measured = self._read(fixture)
        self.assertEqual("last observed", measured["state"])
        self.assertEqual(tokens, measured["tokens"])
        self.assertEqual("pass", leg.status, check_myself.render(report))
        self.assertIn(f"tokens={tokens}; window=1000000; pressure={measured['percent']:.1f}%", leg.detail)
        self.assertEqual(0, report.exit_code, check_myself.render(report))

    def _unknown(self, fixture, state):
        report, leg, measured = self._read(fixture)
        self.assertEqual(state, measured["state"])
        self.assertIsNone(measured["percent"])
        self.assertEqual("undetermined", leg.status, check_myself.render(report))
        self.assertNotIn("pressure=", leg.detail)
        self.assertNotEqual(0, report.exit_code)

    def test_codex_ordinary_reading(self):
        self._known(self._fixture("codex"), 300_000)

    def test_codex_compaction_invalidates_old_pressure(self):
        fixture = self._fixture("codex")
        self._append(fixture, self._boundary("codex"))
        self._unknown(fixture, "before compaction")

    def test_codex_fresh_reading_after_compaction(self):
        fixture = self._fixture("codex")
        self._append(fixture, self._boundary("codex"))
        self._append(fixture, self._usage("codex", 200_000, "2026-08-09T22:40:00Z"))
        self._known(fixture, 200_000)

    def test_codex_new_unknown_window_never_reuses_old_reading(self):
        fixture = self._fixture("codex")
        self._append(fixture, self._usage("codex", 400_000, "2026-08-09T22:30:00Z", window=None))
        self._unknown(fixture, "window unknown")

    def test_codex_unterminated_row_is_not_a_reading(self):
        fixture = self._fixture("codex")
        self._append(fixture, self._usage("codex", 800_000, "2026-08-09T22:30:00Z"), terminated=False)
        self._known(fixture, 300_000)

    def test_claude_ordinary_reading(self):
        self._known(self._fixture("claude"), 300_000)

    def test_claude_sidechain_usage_is_not_resident_pressure(self):
        fixture = self._fixture("claude")
        self._append(fixture, self._usage("claude", 900_000, "2026-08-09T22:30:00Z", side=True))
        self._known(fixture, 300_000)

    def test_claude_zero_usage_never_supersedes_real_reading(self):
        fixture = self._fixture("claude")
        self._append(fixture, self._usage("claude", 0, "2026-08-09T22:30:00Z"))
        self._known(fixture, 300_000)

    def test_claude_compaction_invalidates_old_pressure(self):
        fixture = self._fixture("claude")
        self._append(fixture, self._boundary("claude"))
        self._unknown(fixture, "before compaction")

    def test_claude_sidechain_compaction_does_not_invalidate_main(self):
        fixture = self._fixture("claude")
        self._append(fixture, self._boundary("claude", side=True))
        self._known(fixture, 300_000)

    def test_claude_fresh_reading_after_compaction(self):
        fixture = self._fixture("claude")
        self._append(fixture, self._boundary("claude"))
        self._append(fixture, self._usage("claude", 200_000, "2026-08-09T22:40:00Z"))
        self._known(fixture, 200_000)

    def test_missing_gauge_fails_closed_without_losing_other_legs(self):
        fixture = self._fixture("codex")
        before = fixture.body.read_bytes()
        with mock.patch.object(check_myself, "GAUGE_PATH", self.root / "absent-gauge.py"):
            report, leg, _ = self._read(fixture)
        self.assertEqual("undetermined", leg.status)
        self.assertIn("FileNotFoundError", leg.detail)
        self.assertEqual(check_myself.EXPECTED_LEGS, len(report.legs))
        self.assertEqual("pass", next(x for x in report.legs if x.name == "body metrics").status)
        self.assertNotEqual(0, report.exit_code)
        self.assertEqual(before, fixture.body.read_bytes())

    def test_gauge_load_error_is_unknown_not_an_old_reader_fallback(self):
        fixture = self._fixture("claude")
        with mock.patch.object(check_myself, "_load_gauge", side_effect=OSError("synthetic fault")):
            report, leg, _ = self._read(fixture)
        self.assertEqual("undetermined", leg.status)
        self.assertIn("OSError", leg.detail)
        self.assertNotIn("pressure=", leg.detail)
        self.assertNotEqual(0, report.exit_code)

    def test_codex_tokens_exceeding_window_are_undetermined(self):
        fixture = self._fixture("codex")
        self._append(fixture, self._usage("codex", 1_000_001, "2026-08-09T22:30:00Z"))
        self._unknown(fixture, "invalid")

    def test_repeated_run_refreshes_usage_and_compaction_state(self):
        fixture = self._fixture("codex")
        self._known(fixture, 300_000)
        self._append(fixture, self._boundary("codex"))
        self._unknown(fixture, "before compaction")
        self._append(fixture, self._usage("codex", 200_000, "2026-08-09T22:40:00Z"))
        self._known(fixture, 200_000)

    def test_claude_missing_model_cannot_match_missing_capability_model(self):
        fixture = self._fixture("claude")
        row = self._usage("claude", 400_000, "2026-08-09T22:30:00Z")
        row["message"].pop("model")
        self._append(fixture, row)
        resource = json.loads(fixture.resource.read_text())
        resource["model"].pop("id")
        fixture.resource.write_text(json.dumps(resource))
        report, leg, measured = self._read(fixture)
        self.assertEqual("window unknown", measured["state"])
        self.assertEqual("undetermined", leg.status)
        self.assertIn("no verified model", leg.detail)
        self.assertNotEqual(0, report.exit_code)


class WindowTableTests(unittest.TestCase):
    """W3: the Claude window comes from the gauge's reviewed table for the caller's own model, through
    gauge.resolve_window; strict unknown otherwise; the shared status-line record is never used."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def leg(self, fixture):
        if not hasattr(fixture, "synthetic_parent"):
            fixture.synthetic_parent = fixture.fake_claude_parent()
        report = fixture.run(environ={}, start_pid=fixture.synthetic_parent)
        return report, {leg.name: leg for leg in report.legs}["context pressure"]

    def test_a_model_in_the_table_resolves_with_provenance(self) -> None:
        fixture = Fixture(self.root, "claude")
        report, leg = self.leg(fixture)
        self.assertEqual("pass", leg.status, check_myself.render(report))
        self.assertIn("window=1000;", leg.detail)
        self.assertIn("model=claude-fixture; tokens_source=caller-native-body", leg.detail)
        self.assertIn("window_source=gauge spec table: fixture table, observed 2026-08-09", leg.detail)
        self.assertIn(str(fixture.window_spec), leg.surfaces)
        self.assertNotIn(str(fixture.resource), check_myself.render(report))
        self.assertEqual(0, report.exit_code)

    def test_a_model_absent_from_the_table_is_undetermined(self) -> None:
        fixture = Fixture(self.root, "claude")
        fixture.write_table((("claude-other", 1000),))
        report, leg = self.leg(fixture)
        self.assertEqual("undetermined", leg.status)
        self.assertIn("no reviewed window for claude-fixture", leg.detail)
        self.assertIn("the shared status-line record is not used", leg.detail)
        self.assertNotEqual(0, report.exit_code)

    def test_the_shared_record_is_never_used(self) -> None:
        fixture = Fixture(self.root, "claude")
        for model, window in (("claude-other", 5), ("claude-fixture", 7)):
            with self.subTest(record=model):
                payload = json.loads(fixture.resource.read_text(encoding="utf-8"))
                payload["model"]["id"], payload["context"]["window_size"] = model, window
                fixture.resource.write_text(json.dumps(payload) + "\n", encoding="utf-8")
                report, leg = self.leg(fixture)
                self.assertEqual("pass", leg.status, check_myself.render(report))
                self.assertIn("window=1000;", leg.detail)                # the table's, not the record's
        fixture.resource.unlink()
        self.assertEqual("pass", self.leg(fixture)[1].status)
        fixture.write_table((("claude-other", 1000),))
        payload = {"generated_at": NOW.isoformat(), "model": {"id": "claude-fixture"}, "context": {"window_size": 1000}}
        fixture.resource.write_text(json.dumps(payload) + "\n", encoding="utf-8")
        self.assertEqual("undetermined", self.leg(fixture)[1].status)   # no fallback to a matching record

    def test_a_pre_compaction_reading_stays_unknown(self) -> None:
        fixture = Fixture(self.root, "claude")
        with fixture.body.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"timestamp": "2026-08-09T22:30:00Z", "type": "system",
                                     "subtype": "compact_boundary", "isSidechain": False}) + "\n")
        report, leg = self.leg(fixture)
        self.assertEqual("undetermined", leg.status)
        self.assertIn("before compaction", leg.detail)

    def test_an_unreadable_table_is_undetermined(self) -> None:
        fixture = Fixture(self.root, "claude")
        cases = {"absent": lambda: fixture.window_spec.unlink(),
                 "not UTF-8": lambda: fixture.window_spec.write_bytes(b"model=claude-fixture|window=1000|\xff\n"),
                 "no rows": lambda: fixture.window_spec.write_text("# no rows\n", encoding="utf-8"),
                 "a folder": lambda: (fixture.window_spec.unlink(), fixture.window_spec.mkdir())}
        for name, breaker in cases.items():
            with self.subTest(case=name):
                if fixture.window_spec.is_dir():
                    fixture.window_spec.rmdir()
                fixture.write_table()
                breaker()
                report, leg = self.leg(fixture)
                self.assertEqual("undetermined", leg.status, name)
                self.assertIn("unreadable or has no rows", leg.detail)

    def test_a_gauge_that_cannot_load_is_undetermined(self) -> None:
        fixture = Fixture(self.root, "claude")
        report = fixture.run(environ={}, start_pid=fixture.fake_claude_parent())
        self.assertEqual(0, report.exit_code)
        with mock.patch.object(check_myself, "_load_gauge", side_effect=ImportError("synthetic")):
            window, detail, path = check_myself._claude_window(
                check_myself.BodyAnalysis(path=fixture.body, provider="claude", size=0), fixture.window_spec)
        self.assertEqual((window, path), (None, fixture.window_spec))
        self.assertIn("window table is unavailable: ImportError", detail)


class AutoMemoryTests(unittest.TestCase):
    """The auto memory leg: this room's Claude residents wake from their own mind and handoff, so a launch here must
    run with the provider's auto memory off. Read from the launch's own process, then the room's settings."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.fx = Fixture(self.root, "claude")
        self.pid = self.fx.fake_claude_parent()
        self.project_file = self.fx.project / ".claude" / "settings.json"
        self.local_file = self.fx.project / ".claude" / "settings.local.json"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def launch(self, *arguments: str, environ: bytes = b"") -> None:
        folder = self.fx.proc_root / str(self.pid)
        words = [b"/home/fixture/.local/bin/claude", *(a.encode() for a in arguments), b"--resume", self.fx.session_id.encode()]
        folder.joinpath("cmdline").write_bytes(b"\0".join(words) + b"\0")
        folder.joinpath("environ").write_bytes(environ)

    def leg(self):
        report = self.fx.run(environ={}, start_pid=self.pid)
        legs = [leg for leg in report.legs if leg.name == "auto memory"]
        self.assertEqual(1, len(legs))
        self.assertEqual(check_myself.EXPECTED_LEGS, len(report.legs))
        return legs[0]

    def assert_leg(self, status: str, *words: str) -> None:
        leg = self.leg()
        self.assertEqual(status, leg.status, leg.detail)
        for word in words:
            self.assertIn(word, leg.detail)

    def test_the_room_setting_off_is_a_pass_and_the_whole_check_passes(self) -> None:
        self.launch()
        self.assert_leg("pass", "off by .claude/settings.json")
        report = self.fx.run(environ={}, start_pid=self.pid)
        self.assertEqual(0, report.exit_code, check_myself.render(report))

    def test_no_setting_is_a_finding_and_fails_the_check(self) -> None:
        self.project_file.unlink()
        self.launch()
        self.assert_leg("finding", "nothing turns auto memory off")
        self.assertEqual(1, self.fx.run(environ={}, start_pid=self.pid).exit_code)
        self.fx.write_room_setting({"permissions": {}})
        self.assert_leg("finding", "nothing turns auto memory off")

    def test_the_setting_on_or_not_a_boolean_is_a_finding(self) -> None:
        self.launch()
        for value, words in ((True, "is on by .claude/settings.json"), ("false", "not true or false"),
                             (0, "not true or false"), (None, "not true or false")):
            with self.subTest(value=value):
                self.fx.write_room_setting({"autoMemoryEnabled": value})
                self.assert_leg("finding", words)

    def test_local_settings_win_over_the_project_file(self) -> None:
        self.launch()
        self.local_file.write_text(json.dumps({"autoMemoryEnabled": True}))
        self.assert_leg("finding", "on by .claude/settings.local.json")
        self.local_file.write_text(json.dumps({"other": 1}))
        self.assert_leg("pass", "off by .claude/settings.json")
        self.project_file.unlink()
        self.local_file.write_text(json.dumps({"autoMemoryEnabled": False}))
        self.assert_leg("pass", "off by .claude/settings.local.json")

    def test_the_launch_switch_turns_it_off_and_is_read_by_its_value(self) -> None:
        self.project_file.unlink()
        for value, status in ((b"", "finding"), (b"0", "finding"), (b"false", "finding"), (b"FALSE", "finding"),
                              (b"1", "pass"), (b"true", "pass"), (b"yes", "pass"), (b"\xff", "pass")):
            with self.subTest(value=value):
                self.launch(environ=b"A=b\0CLAUDE_CODE_DISABLE_AUTO_MEMORY=" + value + b"\0C=d\0")
                self.assertEqual(status, self.leg().status)
        self.launch(environ=b"XCLAUDE_CODE_DISABLE_AUTO_MEMORY=1\0")
        self.assertEqual("finding", self.leg().status)

    def test_a_settings_argument_wins_over_the_room_files(self) -> None:
        on = self.root / "on.json"
        on.write_text(json.dumps({"autoMemoryEnabled": True}))
        for form in (("--settings", str(on)), (f"--settings={on}",), ("--settings", '{"autoMemoryEnabled": true}')):
            with self.subTest(form=form[0][:12]):
                self.launch(*form)
                self.assert_leg("finding", "on by a --settings argument of the launch")
        off = self.root / "off.json"
        off.write_text(json.dumps({"autoMemoryEnabled": False}))
        self.project_file.unlink()
        self.launch("--settings", str(off))
        self.assert_leg("pass", "off by a --settings argument")
        self.launch("--settings", str(self.root / "absent.json"))
        self.assert_leg("finding", "nothing turns auto memory off")

    def test_what_cannot_be_read_is_undetermined_and_never_a_pass(self) -> None:
        self.launch()
        self.project_file.write_text("{not json")
        self.assert_leg("undetermined", ".claude/settings.json cannot be read")
        self.project_file.write_text("[]")
        self.assert_leg("undetermined", "cannot be read")
        self.project_file.write_text(json.dumps({"autoMemoryEnabled": False, "pad": "x" * 70000}))
        self.assert_leg("undetermined", "cannot be read")
        self.fx.write_room_setting()
        moved = self.root / "elsewhere.json"
        self.project_file.rename(moved)
        self.project_file.symlink_to(moved)
        self.assert_leg("undetermined", "cannot be read")
        self.project_file.unlink()
        self.fx.write_room_setting()
        (self.fx.proc_root / str(self.pid) / "environ").unlink()
        self.assert_leg("undetermined", "environment cannot be read")

    def test_a_codex_caller_and_a_row_of_another_room_are_not_judged(self) -> None:
        self.project_file.unlink()
        self.launch()
        rows = json.loads(self.fx.registry.read_text())
        rows["identities"][0]["room"] = str(self.root / "another-room")
        self.fx.registry.write_text(json.dumps(rows))
        self.assert_leg("pass", "another room")
        codex = Fixture(self.root / "codex-case", "codex")
        report = codex.run()
        leg = next(leg for leg in report.legs if leg.name == "auto memory")
        self.assertEqual("pass", leg.status)
        self.assertIn("not a Claude row", leg.detail)
        self.assertEqual(0, report.exit_code, check_myself.render(report))

    def test_a_row_of_this_room_written_through_a_link_is_this_room(self) -> None:
        self.project_file.unlink()
        self.launch()
        link = self.root / "link-to-room"
        link.symlink_to(self.fx.project)
        rows = json.loads(self.fx.registry.read_text())
        rows["identities"][0]["room"] = str(link)
        self.fx.registry.write_text(json.dumps(rows))
        self.assert_leg("finding", "nothing turns auto memory off")

    def test_no_identity_no_room_or_no_launch_is_undetermined(self) -> None:
        self.launch()
        rows = json.loads(self.fx.registry.read_text())
        rows["identities"][0]["room"] = ""
        self.fx.registry.write_text(json.dumps(rows))
        self.assert_leg("undetermined", "names no room")
        rows["identities"][0]["room"] = str(self.fx.project)
        self.fx.registry.write_text(json.dumps(rows))
        paths = dataclasses.replace(self.fx.paths, room=None)
        report = check_myself.run_check(paths, environ={}, start_pid=self.pid, now=NOW)
        self.assertEqual("undetermined", next(leg for leg in report.legs if leg.name == "auto memory").status)
        with mock.patch.object(check_myself, "_launch_process", return_value=None):
            self.assert_leg("undetermined", "names this session")
        self.fx.registry.write_text(json.dumps({"identities": []}))
        self.assert_leg("undetermined", "unavailable")

    def test_the_leg_prints_no_session_and_no_argument_and_writes_nothing(self) -> None:
        self.launch("--settings", "/secret/settings/path")
        before = digest_tree(self.root)
        leg = self.leg()
        rendered = leg.detail + " ".join(leg.surfaces)
        self.assertNotIn("/secret/settings/path", rendered)
        self.assertNotIn(self.fx.session_id, leg.detail)
        self.assertEqual(before, digest_tree(self.root))

    def test_the_live_paths_name_this_room(self) -> None:
        self.assertEqual(SESSIONS_ROOT, check_myself.CheckPaths.live().room)


class OrientationAfterIdeNoticesTests(unittest.TestCase):
    """A row counts only when the tag begins it, after any leading IDE notices. Every row here is synthetic."""

    OPENED = "<ide_opened_file>The user opened the file /home/example/a.py in the IDE.</ide_opened_file>"
    SELECTED = "<ide_selection>The user selected lines 1 to 2 from /home/example/a.py:\nfirst\nsecond\n</ide_selection>"
    TAG = "<session_clinic_orientation>"
    CLOSE = "</session_clinic_orientation>"

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def leg(self, content_of):
        """The body identity leg, with the fixture's orientation row replaced by what content_of makes of the good row."""
        fixture = Fixture(Path(tempfile.mkdtemp(dir=self.root)), "claude")
        rows = fixture.claude_rows()
        good = f"{self.TAG}\nYou are `{fixture.display}`.\n{self.CLOSE}"
        rows[0]["message"]["content"] = content_of(good, fixture)
        fixture.body.write_text("".join(json_line(row) for row in rows), encoding="utf-8")
        return fixture.run(environ={}, start_pid=fixture.fake_claude_parent()).legs[5]

    def counted(self, content_of) -> None:
        leg = self.leg(content_of)
        self.assertEqual("pass", leg.status, leg.detail)
        self.assertIn("identity_rows_seen=1", leg.detail)

    def not_counted(self, content_of) -> None:
        leg = self.leg(content_of)
        self.assertEqual("undetermined", leg.status, leg.detail)
        self.assertIn("identity_rows_seen=0", leg.detail)

    def test_a_tagged_row_after_each_notice_counts(self) -> None:
        for label, before in (("opened", self.OPENED), ("selected", self.SELECTED), ("both", self.OPENED + self.SELECTED),
                              ("selected then opened, with lines", self.SELECTED + "\n\n" + self.OPENED + "\n"),
                              ("leading white space", "\n  " + self.OPENED + " ")):
            with self.subTest(label):
                self.counted(lambda good, f: before + good)

    def test_the_older_plain_form_after_a_notice_counts(self) -> None:
        self.counted(lambda good, f: self.OPENED + f"{self.TAG}\nYou are {f.person.upper()}, {f.role}, resident.\n{self.CLOSE}")

    def test_a_notice_with_no_tag_does_not_count(self) -> None:
        for before in (self.OPENED, self.SELECTED, self.OPENED + "fixture question"):
            with self.subTest(before):
                self.not_counted(lambda good, f: before)

    def test_a_tag_after_other_leading_text_does_not_count(self) -> None:
        self.not_counted(lambda good, f: "fixture text " + good)
        self.not_counted(lambda good, f: self.OPENED + "fixture text " + good)

    def test_a_tag_inside_a_wrapper_does_not_count(self) -> None:
        wrap = '<cross-session-message from="fixture">%s</cross-session-message>'
        self.not_counted(lambda good, f: wrap % good)
        self.not_counted(lambda good, f: self.OPENED + wrap % good)
        self.not_counted(lambda good, f: wrap % "fixture text" + good)

    def test_a_tag_in_a_tool_result_does_not_count(self) -> None:
        self.not_counted(lambda good, f: [{"type": "tool_result", "content": good}])
        self.not_counted(lambda good, f: [{"type": "tool_result", "content": self.OPENED + good}])
        self.not_counted(lambda good, f: "<tool_result>" + good + "</tool_result>")

    def test_a_tag_quoted_later_does_not_count(self) -> None:
        self.not_counted(lambda good, f: "the tag reads " + good + " in this message")
        self.not_counted(lambda good, f: self.SELECTED + "the tag reads " + good)

    def test_a_tag_inside_a_notice_does_not_count(self) -> None:
        self.not_counted(lambda good, f: f"<ide_selection>{good}</ide_selection>")
        self.not_counted(lambda good, f: f"<ide_selection>{good}</ide_selection>fixture question")
        self.not_counted(lambda good, f: f"<ide_opened_file>{good}</ide_opened_file>")

    def test_a_selection_quoting_a_closing_tag_and_the_tag_does_not_count(self) -> None:
        self.not_counted(lambda good, f: f"<ide_selection>a</ide_selection>{good} b</ide_selection> question")
        self.not_counted(lambda good, f: f"<ide_selection>a</ide_selection>{good} b</ide_opened_file> question")

    def test_another_notice_name_or_a_broken_notice_does_not_count(self) -> None:
        for before in ("<ide_diagnostics>x</ide_diagnostics>", "<ide_opened_file>no closing tag ", "<ide_opened_file>x</ide_selection>",
                       "<ide_selection>a</ide_selection> text </ide_selection>", "<IDE_OPENED_FILE>x</IDE_OPENED_FILE>"):
            with self.subTest(before):
                self.not_counted(lambda good, f: before + good)

    def test_a_row_with_no_notice_counts_as_it_always_did(self) -> None:
        self.counted(lambda good, f: good)
        self.counted(lambda good, f: "\n  " + good)
        self.counted(lambda good, f: good + " it quotes </ide_selection> later")
        self.counted(lambda good, f: good + self.OPENED)

    def test_the_identity_comes_from_the_tag_not_the_notice(self) -> None:
        wrong = "<ide_selection>You are `Wrong Role (Wrong Person)`.\nYou are Wrong Person, Wrong Role.\n</ide_selection>"
        self.counted(lambda good, f: wrong + good)
        leg = self.leg(lambda good, f: f"<ide_selection>{good.replace(self.TAG, '').replace(self.CLOSE, '')}</ide_selection>{self.TAG}\nIdentity statement unavailable.\n{self.CLOSE}")
        self.assertEqual("undetermined", leg.status, leg.detail)
        self.assertIn("identity_rows_seen=1", leg.detail)
        self.assertIn("latest_identity_line=1", leg.detail)

    def test_the_claim_function_applies_the_same_rule(self) -> None:
        wrong = "<ide_selection>\nYou are Wrong Person, Wrong Role.\n</ide_selection>"
        claim = check_myself._orientation_claim(f"{wrong}{self.TAG}\nYou are Right Person, Right Role.\n{self.CLOSE}", 7)
        self.assertEqual(("Right Person", "Right Role", 7), (claim.person, claim.role, claim.line_number))
        self.assertIsNone(check_myself._orientation_claim(f"fixture text {self.TAG}\nYou are Right Person.\n{self.CLOSE}", 7))
        self.assertIsNone(check_myself._orientation_claim(["not text"], 7))

    def test_the_latest_row_stands_and_every_counted_row_counts(self) -> None:
        fixture = Fixture(Path(tempfile.mkdtemp(dir=self.root)), "claude")
        rows = fixture.claude_rows()
        good = f"{self.TAG}\nYou are `{fixture.display}`.\n{self.CLOSE}"
        rows[0]["message"]["content"] = f"{self.TAG}\nYou are `Wrong Role (Wrong Person)`.\n{self.CLOSE}"
        rows[1]["message"]["content"] = self.OPENED + good
        fixture.body.write_text("".join(json_line(row) for row in rows), encoding="utf-8")
        leg = fixture.run(environ={}, start_pid=fixture.fake_claude_parent()).legs[5]
        self.assertEqual("pass", leg.status, leg.detail)
        self.assertIn("identity_rows_seen=2", leg.detail)


class CopilotCallerSignal(unittest.TestCase):
    """A Copilot seat is known by its own session variable, a Copilot process above the caller, and that
    session's in-use lock naming the process. Every identifier and path here is invented."""

    SESSION = "0000c0f1-0000-4000-8000-00000000c0f1"

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.proc = self.root / "proc"
        self.state = self.root / "session-state"
        self.locks = self.root / "codex-locks"
        self.locks.mkdir()
        self.process(9001, 1, ["/usr/bin/node", "/invented/github-copilot-cli/node_modules/copilot/index.js", "--acp"])
        self.process(9002, 9001, ["/bin/bash", "-c", "an invented command"])
        (self.state / self.SESSION).mkdir(parents=True)
        (self.state / self.SESSION / "inuse.9001.lock").write_text("9001\n", encoding="utf-8")

    def process(self, pid: int, parent: int, argv: list[str]) -> None:
        folder = self.proc / str(pid)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "cmdline").write_bytes(b"\0".join(a.encode() for a in argv) + b"\0")
        (folder / "status").write_text(f"Name:\tinvented\nPPid:\t{parent}\n", encoding="utf-8")

    def resolve(self, environ=None, start=9002):
        return check_myself.resolve_caller(
            {"COPILOT_AGENT_SESSION_ID": self.SESSION} if environ is None else environ,
            self.proc, start, self.locks, self.state)

    def test_a_held_copilot_session_resolves(self) -> None:
        caller, _, errors = self.resolve()
        self.assertEqual([], errors)
        self.assertEqual(("copilot", self.SESSION), (caller.provider, caller.session_id))

    def test_the_variable_alone_is_not_enough(self) -> None:
        caller, _, errors = self.resolve(start=None)
        self.assertIsNone(caller)
        self.assertTrue(any("no matching copilot process" in e for e in errors))

    def test_a_session_not_held_by_an_ancestor_fails_closed(self) -> None:
        (self.state / self.SESSION / "inuse.9001.lock").rename(self.state / self.SESSION / "inuse.7777.lock")
        caller, _, errors = self.resolve()
        self.assertIsNone(caller)
        self.assertTrue(any("not held by a caller-ancestor Copilot process" in e for e in errors))

    def test_a_missing_state_folder_fails_closed(self) -> None:
        other = "0000c0f2-0000-4000-8000-00000000c0f2"
        caller, _, errors = self.resolve({"COPILOT_AGENT_SESSION_ID": other})
        self.assertIsNone(caller)
        self.assertTrue(any("state folder is absent" in e for e in errors))

    def test_a_path_that_merely_mentions_copilot_is_not_a_copilot_process(self) -> None:
        self.process(9001, 1, ["/usr/bin/node", "/invented/notes-about-copilot/tool.js"])
        caller, _, errors = self.resolve()
        self.assertIsNone(caller)
        self.assertTrue(any("no matching copilot process" in e for e in errors))

    def test_a_resume_argument_without_the_variable_resolves_nobody(self) -> None:
        # The review finding on #82: a process-derived Copilot signal must not bypass the lock.
        self.process(9001, 1, ["/usr/bin/node", "/invented/github-copilot-cli/index.js", "--resume", self.SESSION])
        (self.state / self.SESSION / "inuse.9001.lock").unlink()
        for environ in ({}, {"COPILOT_AGENT_SESSION_ID": self.SESSION}):
            with self.subTest(environ=sorted(environ)):
                caller, _, errors = self.resolve(environ)
                self.assertIsNone(caller)
                self.assertTrue(errors)

    def test_a_resume_argument_cannot_name_another_session(self) -> None:
        other = "0000c0f4-0000-4000-8000-00000000c0f4"
        self.process(9001, 1, ["/usr/bin/node", "/invented/github-copilot-cli/index.js", "--resume", other])
        caller, _, errors = self.resolve()
        self.assertEqual([], errors)
        self.assertEqual(self.SESSION, caller.session_id)

    def test_a_symlinked_state_folder_fails_closed(self) -> None:
        real = self.state / self.SESSION
        moved = self.root / "elsewhere"
        real.rename(moved)
        real.symlink_to(moved, target_is_directory=True)
        caller, _, errors = self.resolve()
        self.assertIsNone(caller)
        self.assertTrue(any("state folder is absent" in e for e in errors))

    def test_a_malformed_variable_fails_closed(self) -> None:
        caller, _, errors = self.resolve({"COPILOT_AGENT_SESSION_ID": "not-an-identifier"})
        self.assertIsNone(caller)
        self.assertTrue(any("not a native UUID" in e for e in errors))

    def test_a_second_provider_signal_disagrees(self) -> None:
        caller, _, errors = self.resolve({"COPILOT_AGENT_SESSION_ID": self.SESSION,
                                          "CLAUDE_CODE_SESSION_ID": "0000c0f3-0000-4000-8000-00000000c0f3"})
        self.assertTrue(caller is None or caller.provider == "copilot")
        self.assertTrue(any("claude process" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
