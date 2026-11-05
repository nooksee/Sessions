#!/usr/bin/env python3
"""Synthetic operator-only notice proofs; no real notifier, body or registry.

Generated with ops/bin/template; implemented by Joe Codex. Run with -I -B.
Fake subprocesses prove submission, never actual display or context delivery.
"""
import contextlib
import fcntl
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

TOOL = Path(__file__).resolve().parents[2] / "ops" / "lib" / "scripts" / "notice.py"
REAL_RUN = subprocess.run


SPEC = importlib.util.spec_from_file_location("notice_tested", TOOL)
NOTICE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(NOTICE)
SID = "0000a111-0000-4000-8000-00000000a111"
NEW_SID = "0000b222-0000-4000-8000-00000000b222"
SECRET = "BODY-CONTENT-NEVER-PRINT-THIS"


class NoticeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.registry = self.base / "registry.json"
        self.state = self.base / "logs" / "notices"
        self.identities = [{"key": "fixture-resident", "provider": "codex", "session_id": SID}]
        self.save_registry()
        self.row = {"schema": "gauge/1", "key": "fixture-resident", "provider": "codex", "session_id": SID,
                    "tokens": 650000, "window": 1000000, "percent": 65.0, "body": "live",
                    "state": "last observed", "reading_at": "2026-11-05T07:00:00Z",
                    "measured_at": "2026-11-05T07:01:00Z", "age_seconds": 60,
                    "window_source": "native token_count", "reason": SECRET, "person": SECRET}
        self.send = mock.patch.object(NOTICE.subprocess, "run", return_value=subprocess.CompletedProcess([], 0)).start()
        self.addCleanup(mock.patch.stopall)

    def save_registry(self):
        self.registry.write_text(json.dumps({"identities": self.identities}), encoding="utf-8")
        self.registry.chmod(0o600)

    def invoke(self, row=None, raw=None, *extra):
        args = ["--key", "fixture-resident", "--registry", str(self.registry),
                "--state-dir", str(self.state), "--notifier", "/synthetic/notifier", *extra]
        payload = raw if raw is not None else json.dumps(self.row if row is None else row).encode()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = NOTICE.main(args, stream=io.BytesIO(payload))
        text = out.getvalue()
        self.assertNotIn(SECRET, text)
        self.assertNotIn(SID, text)
        return rc, json.loads(text)

    def reading(self, tokens, minute=0):
        row = dict(self.row, tokens=tokens, percent=round(100 * tokens / 1000000, 1),
                   reading_at=f"2026-11-05T07:{minute:02d}:00Z",
                   measured_at=f"2026-11-05T07:{minute + 1:02d}:00Z")
        return row

    def assert_refused(self, row=None, raw=None):
        rc, result = self.invoke(row, raw)
        self.assertEqual(rc, 2, result)
        self.assertEqual(result["status"], "unknown")
        self.assertFalse(result["submitted"])
        self.assertFalse(result["resident_context_delivered"])
        return result

    def prepare_state(self):
        self.state.mkdir(parents=True, mode=0o700)

    def test_submission_claim_is_not_display_or_context(self):
        rc, result = self.invoke()
        self.assertEqual(rc, 0)
        self.assertEqual(result["status"], "submitted")
        self.assertTrue(result["submitted"])
        self.assertEqual(result["displayed"], "unproved")
        self.assertFalse(result["resident_context_delivered"])
        self.assertEqual(result["measurement"], "last observed")
        self.assertEqual(result["age_seconds"], 60)

    def test_notifier_argv_is_bounded_without_private_text(self):
        self.invoke()
        args, kwargs = self.send.call_args
        self.assertEqual(len(args[0]), 5)
        self.assertEqual(kwargs["timeout"], 2.0)
        self.assertFalse(kwargs.get("shell", False))
        self.assertNotIn(SECRET, str(args))
        self.assertNotIn(SID, str(args))
        self.assertEqual(kwargs["stderr"], subprocess.DEVNULL)

    def test_dry_run_creates_nothing(self):
        before = sorted(str(p) for p in self.base.rglob("*"))
        rc, result = self.invoke(None, None, "--dry-run")
        self.assertEqual(rc, 0)
        self.assertEqual(result["would"], "due")
        self.send.assert_not_called()
        self.assertEqual(before, sorted(str(p) for p in self.base.rglob("*")))

    def test_shared_pressure_helper_is_actually_used(self):
        real = NOTICE.sibling
        closeout = real("closeout")
        with mock.patch.object(closeout, "pressure_band", return_value=42) as call:
            with mock.patch.object(NOTICE, "sibling", side_effect=lambda name: closeout if name == "closeout" else real(name)):
                rc, result = self.invoke(None, None, "--dry-run")
        self.assertEqual(rc, 0)
        self.assertEqual(result["band"], 42)
        call.assert_called_once_with(650000, 1000000)

    def test_zero_below_equal_and_next_band(self):
        for tokens, band in ((0, None), (649999, None), (650000, 0), (700000, 1)):
            with self.subTest(tokens=tokens):
                rc, result = self.invoke(self.reading(tokens), None, "--dry-run")
                self.assertEqual(rc, 0)
                self.assertEqual(result["band"], band)

    def test_same_band_and_lower_band_are_suppressed(self):
        self.invoke(self.reading(700000))
        for tokens in (720000, 650000):
            rc, result = self.invoke(self.reading(tokens, 2))
            self.assertEqual(rc, 0)
            self.assertEqual(result["status"], "suppressed")
        self.assertEqual(self.send.call_count, 1)

    def test_next_band_submits(self):
        self.invoke()
        rc, result = self.invoke(self.reading(700000, 2))
        self.assertEqual(rc, 0)
        self.assertEqual(result["status"], "submitted")
        self.assertEqual(self.send.call_count, 2)

    def test_below_trigger_rearms(self):
        self.invoke()
        self.invoke(self.reading(100000, 2))
        rc, result = self.invoke(self.reading(650000, 3))
        self.assertEqual(rc, 0)
        self.assertEqual(result["status"], "submitted")
        self.assertEqual(self.send.call_count, 2)

    def test_new_native_body_does_not_inherit_suppression(self):
        self.invoke()
        self.identities[0]["session_id"] = NEW_SID
        self.save_registry()
        rc, result = self.invoke(dict(self.row, session_id=NEW_SID))
        self.assertEqual(rc, 0)
        self.assertTrue(result["submitted"])
        self.assertNotIn(NEW_SID, json.dumps(result))

    def test_failed_notifier_consumes_no_band_and_retries(self):
        self.send.return_value.returncode = 1
        self.assert_refused()
        self.assertFalse((self.state / "fixture-resident.json").exists())
        self.send.return_value.returncode = 0
        rc, result = self.invoke()
        self.assertEqual(rc, 0)
        self.assertTrue(result["submitted"])

    def test_notifier_timeout_and_missing_executable(self):
        for exc in (subprocess.TimeoutExpired("fixture", 2), FileNotFoundError(SECRET)):
            with self.subTest(exception=type(exc).__name__):
                self.send.side_effect = exc
                self.assert_refused()
                self.assertFalse((self.state / "fixture-resident.json").exists())
        self.send.side_effect = None
        self.assertEqual(self.invoke()[0], 0)

    def test_post_submission_persistence_failure_is_honest(self):
        with mock.patch.object(NOTICE.Store, "write", side_effect=OSError(SECRET)):
            rc, result = self.invoke()
        self.assertEqual(rc, 2)
        self.assertTrue(result["submitted"])
        self.assertEqual(result["status"], "unknown")

    def test_malformed_duplicate_nonfinite_and_multiple_rows(self):
        valid = json.dumps(self.row).encode()
        for raw in (b"", b"{", b"[]", b"null", b'\xff', b'{"x":1,"x":2}',
                    b'{"x":NaN}', valid + b"\n" + valid):
            with self.subTest(raw=raw[:20]):
                self.assert_refused(raw=raw)
        self.send.assert_not_called()
        self.assertFalse(self.state.exists())

    def test_oversized_input(self):
        self.assert_refused(raw=b" " * (NOTICE.LIMIT + 1))
        self.send.assert_not_called()

    def test_wrong_schema_or_identity(self):
        for name, value in (("schema", "unknown"), ("key", "another-resident"),
                            ("provider", "claude"), ("session_id", NEW_SID)):
            with self.subTest(field=name):
                self.assert_refused(dict(self.row, **{name: value}))
        self.assertFalse(self.state.exists())

    def test_duplicate_registry_keys_and_native_bindings(self):
        for extra in (dict(self.identities[0], session_id=NEW_SID), dict(self.identities[0], key="another-resident")):
            with self.subTest(extra=extra["key"]):
                self.identities = [self.identities[0], extra]
                self.save_registry()
                self.assert_refused()
        self.send.assert_not_called()

    def test_malformed_registry_and_duplicate_json_keys(self):
        for raw in (b"{}", b'{"identities":[]}', b'{"identities":null}', b'{"identities":[],"identities":[]}'):
            self.registry.write_bytes(raw)
            self.assert_refused()
        self.assertFalse(self.state.exists())

    def test_missing_or_nonprivate_registry(self):
        self.registry.chmod(0o644)
        self.assert_refused()
        self.registry.unlink()
        self.assert_refused()
        self.assertFalse(self.state.exists())

    def test_registry_symlink_rejected(self):
        target = self.base / "real.json"
        self.registry.rename(target)
        self.registry.symlink_to(target)
        self.assert_refused()
        self.send.assert_not_called()

    def test_unknown_archived_and_compacted_measurements(self):
        for state in ("unknown", "compacted", "before compaction", "archived body", "window unknown", "invalid"):
            with self.subTest(state=state):
                self.assert_refused(dict(self.row, state=state))
        self.assert_refused(dict(self.row, body="archived"))
        self.send.assert_not_called()

    def test_invalid_token_window_counters(self):
        for field, value in (("tokens", None), ("tokens", -1), ("tokens", True), ("tokens", 1.5),
                             ("tokens", 1000001), ("window", 0), ("window", True), ("window", 1000)):
            with self.subTest(field=field, value=value):
                self.assert_refused(dict(self.row, **{field: value}))
        self.assertFalse(self.state.exists())

    def test_invalid_time_age_percent_and_window_provenance(self):
        for field, value in (("reading_at", None), ("reading_at", "2026-11-05T07:00:00"),
                             ("measured_at", "nonsense"), ("age_seconds", -1), ("age_seconds", True),
                             ("age_seconds", 50), ("percent", None), ("percent", True),
                             ("percent", 99), ("window_source", None), ("window_source", "")):
            with self.subTest(field=field):
                self.assert_refused(dict(self.row, **{field: value}))

    def test_old_reading_is_not_given_an_invented_freshness_cutoff(self):
        row = dict(self.row, measured_at="2026-11-06T07:00:00Z", age_seconds=86400)
        self.assertEqual(self.invoke(row)[0], 0)

    def test_time_control_characters_cannot_enter_notifier_output(self):
        self.assert_refused(dict(self.row, reading_at="2026-11-05\n07:00:00Z"))
        self.send.assert_not_called()

    def test_unsafe_existing_lock_is_not_repaired(self):
        self.prepare_state()
        lock = self.state / "fixture-resident.lock"
        lock.write_bytes(b"evidence")
        lock.chmod(0o644)
        self.assert_refused()
        self.assertEqual(lock.read_bytes(), b"evidence")
        self.assertEqual(lock.stat().st_mode & 0o777, 0o644)

    def test_unsafe_existing_state_is_not_repaired(self):
        self.invoke()
        self.send.reset_mock()
        state = self.state / "fixture-resident.json"
        before = state.read_bytes()
        state.chmod(0o644)
        self.assert_refused()
        self.assertEqual(state.read_bytes(), before)
        self.assertEqual(state.stat().st_mode & 0o777, 0o644)
        self.send.assert_not_called()

    def test_dry_run_preserves_existing_state_bytes(self):
        self.invoke()
        self.send.reset_mock()
        before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.state.iterdir()}
        self.assertEqual(self.invoke(self.reading(700000, 2), None, "--dry-run")[0], 0)
        after = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.state.iterdir()}
        self.assertEqual(before, after)
        self.send.assert_not_called()

    def test_cli_timeout_is_bounded_with_a_fake_executable(self):
        notifier = self.base / "slow-notifier"
        notifier.write_text("#!/bin/sh\nexec sleep 10\n", encoding="ascii")
        notifier.chmod(0o700)
        result = REAL_RUN([sys.executable, "-I", "-B", str(TOOL), "--key", "fixture-resident",
                           "--registry", str(self.registry), "--state-dir", str(self.state),
                           "--notifier", str(notifier)], input=json.dumps(self.row),
                          text=True, capture_output=True, timeout=5)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(json.loads(result.stdout)["reason"], "notifier-timeout")
        self.assertFalse((self.state / "fixture-resident.json").exists())

    def test_older_reading_cannot_rearm_a_newer_band(self):
        self.invoke(self.reading(650000, 3))
        result = self.assert_refused(self.reading(100000))
        self.assertEqual(result["reason"], "out-of-order-reading")
        self.assertEqual(self.send.call_count, 1)

    def test_private_modes_under_open_umask_and_no_pending_residue(self):
        old = os.umask(0)
        try:
            self.assertEqual(self.invoke()[0], 0)
        finally:
            os.umask(old)
        for node in (self.state, self.state.parent):
            self.assertEqual(node.stat().st_mode & 0o777, 0o700)
        for node in self.state.iterdir():
            self.assertEqual(node.stat().st_mode & 0o777, 0o600)
            self.assertEqual(node.stat().st_nlink, 1)
            self.assertNotIn(SID, node.read_text())
        self.assertEqual(sorted(p.name for p in self.state.iterdir()),
                         ["fixture-resident.json", "fixture-resident.lock"])

    def test_unsafe_directory_is_not_normalized(self):
        self.prepare_state()
        self.state.chmod(0o755)
        self.assert_refused()
        self.assertEqual(self.state.stat().st_mode & 0o777, 0o755)
        self.assertEqual(list(self.state.iterdir()), [])

    def test_symlink_parent_and_final_directory_refused(self):
        target = self.base / "target"
        target.mkdir(mode=0o700)
        self.state.parent.symlink_to(target, target_is_directory=True)
        self.assert_refused()
        self.assertEqual(list(target.iterdir()), [])
        self.state.parent.unlink()
        self.state.parent.mkdir()
        self.state.symlink_to(target, target_is_directory=True)
        self.assert_refused()
        self.assertEqual(list(target.iterdir()), [])

    def test_corrupt_state_is_preserved_before_lock_creation(self):
        self.prepare_state()
        state = self.state / "fixture-resident.json"
        state.write_bytes(b"{broken")
        state.chmod(0o600)
        before = state.read_bytes()
        self.assert_refused()
        self.assertEqual(state.read_bytes(), before)
        self.assertEqual(list(self.state.iterdir()), [state])

    def test_symlink_hardlink_and_special_state_are_rejected(self):
        self.prepare_state()
        path = self.state / "fixture-resident.json"
        outside = self.base / "outside"
        outside.write_bytes(b"untouched")
        outside.chmod(0o600)
        path.symlink_to(outside)
        self.assert_refused()
        path.unlink()
        os.link(outside, path)
        self.assert_refused()
        path.unlink()
        os.mkfifo(path, 0o600)
        self.assert_refused()
        self.assertEqual(outside.read_bytes(), b"untouched")
        self.send.assert_not_called()

    def test_unexplained_pending_is_preserved(self):
        self.prepare_state()
        pending = self.state / ".notice-interrupted"
        pending.write_bytes(b"evidence")
        pending.chmod(0o600)
        self.assert_refused()
        self.assertEqual(pending.read_bytes(), b"evidence")
        self.assertEqual(list(self.state.iterdir()), [pending])

    def test_live_flock_is_nonblocking(self):
        self.prepare_state()
        lock = self.state / "fixture-resident.lock"
        fd = os.open(lock, os.O_RDWR | os.O_CREAT, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            result = self.assert_refused()
            self.assertEqual(result["reason"], "notice-state-busy")
        finally:
            os.close(fd)
        self.assertEqual(self.invoke()[0], 0)

    def test_existing_lock_inode_survives_repeated_runs(self):
        self.invoke()
        lock = self.state / "fixture-resident.lock"
        inode = lock.stat().st_ino
        self.invoke()
        self.assertEqual(inode, lock.stat().st_ino)

    def test_unknown_does_not_change_successful_state(self):
        self.invoke()
        before = (self.state / "fixture-resident.json").read_bytes()
        self.assert_refused(dict(self.row, state="compacted"))
        self.assertEqual((self.state / "fixture-resident.json").read_bytes(), before)

    def test_no_body_path_is_opened(self):
        row = dict(self.row, body="live", ignored_body_path=str(self.base / SECRET))
        original = Path.open

        def guard(path, *args, **kwargs):
            self.assertNotIn(SECRET, str(path))
            return original(path, *args, **kwargs)

        with mock.patch.object(Path, "open", guard):
            self.assertEqual(self.invoke(row)[0], 0)

    def test_cli_help_and_argument_failure_do_not_touch_state(self):
        for args, expected in ((["--help"], 0), (["--key", "fixture-resident", "--unexpected"], 2)):
            result = REAL_RUN([sys.executable, "-I", "-B", str(TOOL), *args],
                              cwd=self.base, input=b"", capture_output=True, timeout=5)
            self.assertEqual(result.returncode, expected, result.stderr)
        self.assertFalse(self.state.exists())

    def test_cli_submits_only_to_synthetic_executable(self):
        notifier = self.base / "notifier"
        notifier.write_text("#!/bin/sh\nexit 0\n", encoding="ascii")
        notifier.chmod(0o700)
        result = REAL_RUN([sys.executable, "-I", "-B", str(TOOL), "--key", "fixture-resident",
                           "--registry", str(self.registry), "--state-dir", str(self.state),
                           "--notifier", str(notifier)], input=json.dumps(self.row),
                          text=True, capture_output=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "submitted")
        self.assertNotIn(SECRET, result.stdout + result.stderr)

if __name__ == "__main__":
    unittest.main()
