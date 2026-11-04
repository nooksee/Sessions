#!/usr/bin/env python3
"""Focused root-free tests for the resident self-check canary."""

from __future__ import annotations

import contextlib
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
CODEX_ID = "0000bd76-0000-4000-8000-00000000bd76"
CLAUDE_ID = "0000b454-0000-4000-8000-00000000b454"


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
        self.resource = root / "resource-state.json"
        self.proc_root = root / "proc"
        self.codex_lock_root = root / "codex-writer-locks"
        self.codex_root = root / "codex"
        self.claude_root = root / "claude"
        self.paths = check_myself.CheckPaths(
            registry=self.registry,
            roster=self.roster,
            bindings=self.bindings,
            resource_state=self.resource,
            codex_lock_root=self.codex_lock_root,
            proc_root=self.proc_root,
        )
        self.write_layers()
        self.write_body()

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
        fixture.role = "Session Continuity Manager"
        fixture.person = "Claude Shannon"
        fixture.display = f"{fixture.role} ({fixture.person})"
        fixture.write_layers()
        rows = fixture.claude_rows()
        rows[0]["message"]["content"] = (
            "<session_clinic_orientation>\n"
            "You are Claude, Session Continuity Manager II, the resident "
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
        fixture.resource.unlink()
        pid = fixture.fake_claude_parent()
        report = fixture.run(
            environ={"CLAUDE_CODE_SESSION_ID": fixture.session_id},
            start_pid=pid,
        )
        self.assertEqual(1, report.exit_code)
        self.assertGreater(report.unresolved, 0)
        self.assertIn(str(fixture.resource), check_myself.render(report))

    def test_older_matching_claude_capability_record_resolves_with_age(self) -> None:
        fixture = Fixture(self.root, "claude")
        payload = json.loads(fixture.resource.read_text(encoding="utf-8"))
        payload["generated_at"] = (NOW - dt.timedelta(hours=18)).isoformat()
        fixture.resource.write_text(json.dumps(payload) + "\n", encoding="utf-8")
        pid = fixture.fake_claude_parent()
        report = fixture.run(environ={}, start_pid=pid)
        self.assertEqual(0, report.exit_code, check_myself.render(report))
        self.assertEqual("pass", report.legs[6].status)
        self.assertIn("capability_record_age_seconds=64800", report.legs[6].detail)
        self.assertIn(
            "capability_record_class=older-model-capability-evidence",
            report.legs[6].detail,
        )

    def test_future_dated_claude_capability_record_fails_closed(self) -> None:
        fixture = Fixture(self.root, "claude")
        payload = json.loads(fixture.resource.read_text(encoding="utf-8"))
        payload["generated_at"] = (NOW + dt.timedelta(minutes=10)).isoformat()
        fixture.resource.write_text(json.dumps(payload) + "\n", encoding="utf-8")
        pid = fixture.fake_claude_parent()
        report = fixture.run(environ={}, start_pid=pid)
        self.assertEqual(1, report.exit_code)
        self.assertEqual("undetermined", report.legs[6].status)
        self.assertIn("future-dated", report.legs[6].detail)

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
    """Mark the fixture resident as held from the launcher (Kevin, 2026-10-23)."""
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
        resource = json.loads(fixture.resource.read_text())
        resource["context"]["window_size"] = 1_000_000
        fixture.resource.write_text(json.dumps(resource))
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


if __name__ == "__main__":
    unittest.main()
