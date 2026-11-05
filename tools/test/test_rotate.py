#!/usr/bin/env python3
"""Synthetic rotation phase gates. No native body, provider or live record.

Generated with ops/bin/template; implemented by Joe Codex. Run with -I -B
under umask 0002, 0022 and 0077. Fixture minds contain invented entries only.
"""
import contextlib
import datetime as dt
import hashlib
import importlib.util
import io
import json
import os
import stat
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

TOOL = Path(__file__).resolve().parents[2] / "ops" / "lib" / "scripts" / "rotate.py"
SPEC = importlib.util.spec_from_file_location("rotate_tested", TOOL)
ROTATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ROTATE)
REAL_RUN = subprocess.run
SID = "0000d611-0000-4000-8000-00000000d611"
WRITER_SID = "0000d622-0000-4000-8000-00000000d622"
DESTINATION = "0000d633-0000-4000-8000-00000000d633"
KEY, WRITER = "fixture-resident", "fixture-writer"
SECRET = "SYNTHETIC-CONTENT-MUST-NOT-LEAVE-EVIDENCE"


class RotateTests(unittest.TestCase):
    def setUp(self):
        scratch = TOOL.parents[3] / "var" / "tmp"
        self.tmp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.room = self.base / "room"
        self.room.mkdir(mode=0o700)
        self.registry = "ops/etc/resident-identities.json"
        self.gauge = "logs/gauge.json"
        self.state = "logs/closeout/state.json"
        self.closed = "storage/active/closing.json"
        self.save(".rotate-synthetic.json", {"schema": "rotate-synthetic/1", "synthetic": True})
        self.identities = [
            {"key": KEY, "person": "Fixture Reader", "role": "Role", "room": str(self.room),
             "provider": "claude", "session_id": SID},
            {"key": WRITER, "person": "Fixture Writer", "role": "Role", "room": str(self.room),
             "provider": "codex", "session_id": WRITER_SID},
        ]
        self.save(self.registry, {"identities": self.identities})
        self.row = {"schema": "gauge/1", "key": KEY, "provider": "claude", "session_id": SID,
                    "tokens": 700000, "window": 1000000, "percent": 70.0, "body": "live",
                    "state": "last observed", "reading_at": "2026-11-05T12:00:00Z",
                    "measured_at": "2026-11-05T12:01:00Z", "age_seconds": 60,
                    "window_source": "synthetic reviewed fixture", "reason": SECRET}
        self.save(self.gauge, self.row)
        self.card = {SID: {"key": KEY, "band": 1, "unknown": 0}}
        self.save(self.state, self.card)
        self.save("storage/handoff/fixture.md", SECRET + "\n", text=True)
        self.make_mind()
        self.record = {"schema": "rotate-closing/1", "key": KEY, "writer": WRITER, "tier": "B",
                       "binding": hashlib.sha256(json.dumps([KEY, "claude", SID], separators=(",", ":")).encode()).hexdigest(),
                       "gauge_sha256": self.sha(self.gauge), "closeout_sha256": self.sha(self.state),
                       "destination_sha256": hashlib.sha256(DESTINATION.encode()).hexdigest(),
                       "closed_at": "2026-11-05T12:02:00Z", "handoff": self.ref("storage/handoff/fixture.md"),
                       "mind": {"proposed": 0, "decision": "none-proposed", "leaf_sha256": self.leaf_sha}}
        self.save(self.closed, self.record)

    def save(self, rel, value, text=False):
        path = self.room / rel
        current = self.room
        for part in path.relative_to(self.room).parts[:-1]:
            current /= part
            current.mkdir(mode=0o700, exist_ok=True)
        path.write_text(value if text else json.dumps(value), encoding="utf-8")
        path.chmod(0o600)
        return path

    def sha(self, rel):
        return hashlib.sha256((self.room / rel).read_bytes()).hexdigest()

    def ref(self, rel):
        return {"path": rel, "sha256": self.sha(rel)}

    def make_mind(self, now=None):
        mind = ROTATE.sibling("mind")
        changes = self.save("changes.json", {"add": [
            {"layer": "lesson", "text": "Check the exact target before choosing a recovery action.",
             "event": "A synthetic rehearsal", "date": "2026-11-05", "source": "docs/fixture.md",
             "applies_when": "A target has changed", "not_when": "There is no pending operation"}]})
        args = types.SimpleNamespace(room=self.room, key=KEY, registry=self.room / self.registry,
                                     changes=str(changes), by=WRITER)
        prepared = mind.prepare(args, now or dt.datetime(2026, 11, 5, 11, 0, tzinfo=dt.timezone.utc),
                                "yes, write this invented fixture entry")
        raw = prepared[0].encode()
        self.leaf_sha = hashlib.sha256(raw).hexdigest()
        self.leaf = "archives/MIND-" + KEY + "-2026-11-05-" + self.leaf_sha[:8] + ".md"
        self.save(self.leaf, prepared[0], text=True)
        self.save("MIND.md", mind.pointer_text({KEY: (self.leaf, self.leaf_sha)}), text=True)

    def args(self, phase=0):
        return ["--room", str(self.room), "--key", KEY, "--writer", WRITER, "--phase", str(phase),
                "--destination", DESTINATION,
                "--gauge-row", self.gauge, "--closeout-state", self.state, "--closing-record", self.closed]

    def invoke(self, phase=0, extra=()):
        out = io.StringIO()
        # Any subprocess from the tool is a test failure, including provider,
        # notifier, launcher, Git, shell or custody commands.
        with contextlib.redirect_stdout(out), mock.patch("subprocess.run", side_effect=AssertionError("no commands")) as commands:
            rc = ROTATE.main(self.args(phase) + list(extra))
        commands.assert_not_called()
        text = out.getvalue()
        self.assertNotIn(SECRET, text)
        self.assertNotIn(SID, text)
        return rc, json.loads(text)

    def snapshot(self):
        result = {}
        for p in self.room.rglob("*"):
            node = p.lstat()
            content = os.readlink(p) if p.is_symlink() else (
                hashlib.sha256(p.read_bytes()).hexdigest() if stat.S_ISREG(node.st_mode) else None)
            result[str(p.relative_to(self.room))] = (stat.S_IMODE(node.st_mode), node.st_ino, node.st_mtime_ns, content)
        return result

    def refused(self, phase=0, extra=(), reason=None):
        before = self.snapshot()
        rc, result = self.invoke(phase, extra)
        self.assertEqual(rc, 2, result)
        self.assertEqual(result["status"], "refused", result)
        self.assertEqual(result["writes"], 0)
        if reason:
            self.assertEqual(result["reason"], reason, result)
        self.assertEqual(before, self.snapshot())
        return result

    def test_phase_zero_stops_before_closing_or_mind(self):
        (self.room / self.closed).unlink()
        (self.room / "MIND.md").unlink()
        before = self.snapshot()
        rc, result = self.invoke()
        self.assertEqual(rc, 0)
        self.assertEqual(result["completed"], [0])
        self.assertEqual(result["next_phase"], 1)
        self.assertEqual(result["status"], "stop")
        self.assertFalse(result["native_load_proved"])
        self.assertFalse(result["operator_accepted"])
        self.assertEqual(before, self.snapshot())

    def test_phase_one_checks_handoff_without_reading_mind(self):
        (self.room / "MIND.md").unlink()
        rc, result = self.invoke(1)
        self.assertEqual(rc, 0, result)
        self.assertEqual(result["completed"], [0, 1])
        self.assertEqual(result["next_phase"], 2)

    def test_phase_two_calls_actual_mind_show_ref_and_stops(self):
        before = self.snapshot()
        rc, result = self.invoke(2)
        self.assertEqual(rc, 0, result)
        self.assertEqual(result["completed"], [0, 1, 2])
        self.assertEqual(result["next_phase"], 3)
        self.assertEqual(result["mind"], {"leaf": self.leaf, "sha256": self.leaf_sha})
        self.assertEqual(before, self.snapshot())

    def test_repeated_checks_do_not_persist_or_advance(self):
        before = self.snapshot()
        for phase in (0, 1, 2, 2, 0):
            rc, result = self.invoke(phase)
            self.assertEqual(rc, 0, result)
            self.assertEqual(result["phase"], phase)
        self.assertEqual(before, self.snapshot())

    def test_interrupted_gate_leaves_nothing_and_retry_rechecks(self):
        before = self.snapshot()
        with mock.patch.object(ROTATE, "mind_ready", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.invoke(2)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(self.invoke(2)[0], 0)

    def test_below_due_even_when_rounded_percent_is_seventy(self):
        self.row.update(tokens=699999, percent=70.0)
        self.save(self.gauge, self.row)
        self.refused(reason="rotation-line-not-reached")

    def test_snapshot_age_and_provenance_are_not_claimed_fresh(self):
        rc, result = self.invoke()
        self.assertEqual(rc, 0)
        self.assertEqual(result["measurement"]["age_seconds"], 60)
        self.assertIn("no fresh telemetry", result["provenance"])
        self.assertIn("not independently proved", result["closeout_proof"])

    def test_shared_measurement_and_pressure_path_is_used(self):
        notice = ROTATE.sibling("notice")
        original = notice.measurement
        with mock.patch.object(notice, "measurement", wraps=original) as measure:
            sibling = ROTATE.sibling
            with mock.patch.object(ROTATE, "sibling", side_effect=lambda name: notice if name == "notice" else sibling(name)):
                self.assertEqual(self.invoke()[0], 0)
            measure.assert_called_once()

    def test_unusable_measurements_refuse(self):
        original = dict(self.row)
        for change in ({"state": "compacted"}, {"body": "archived"}, {"tokens": True},
                       {"window": 0}, {"tokens": 1000001}, {"percent": 1.0},
                       {"age_seconds": -1}, {"window_source": ""}, {"key": WRITER}):
            with self.subTest(change=change):
                self.save(self.gauge, {**original, **change})
                self.refused()

    def test_duplicate_or_multiple_gauge_json_refuses(self):
        for raw in ('{"schema":"gauge/1","schema":"gauge/1"}', '{}\n{}', '{', 'NaN'):
            with self.subTest(raw=raw):
                self.save(self.gauge, raw, text=True)
                self.refused()

    def test_ambiguous_registry_refuses(self):
        self.save(self.registry, {"identities": self.identities + [self.identities[0]]})
        self.refused()

    def test_actual_binding_namespace_is_not_admitted(self):
        self.identities[0]["session_id"] = "1000" + SID[4:]
        self.save(self.registry, {"identities": self.identities})
        self.refused(reason="synthetic-identities-required")

    def test_missing_or_wrong_writer_refuses(self):
        self.refused(extra=("--writer", "missing-writer"))
        self.refused(extra=("--writer", KEY), reason="self-rotation-refused")

    def test_wrong_registered_room_refuses(self):
        self.identities[0]["room"] = str(self.base)
        self.save(self.registry, {"identities": self.identities})
        self.refused(reason="resident-room-or-writer-mismatch")

    def test_destination_is_declared_not_adopted_or_opened(self):
        for destination in (SID, WRITER_SID, "not-a-spare", "1000" + DESTINATION[4:]):
            with self.subTest(destination=destination):
                self.refused(extra=("--destination", destination), reason="synthetic-unregistered-destination-required")
        result = self.invoke()[1]
        self.assertEqual(result["destination_sha256"], hashlib.sha256(DESTINATION.encode()).hexdigest())
        self.assertIn("unimplemented", result["destination_proof"])

    def test_pending_closeout_state_blocks_without_cleanup(self):
        self.save("logs/closeout/.state.partial", "incomplete", text=True)
        self.refused(reason="pending-closeout-state")

    def test_closeout_state_requires_exact_session_key_and_band(self):
        for value in ({}, {WRITER_SID: self.card[SID]}, {SID: {"key": WRITER, "band": 1, "unknown": 0}},
                      {SID: {"key": KEY, "band": True, "unknown": 0}},
                      {SID: {"key": KEY, "band": 2, "unknown": 0}},
                      {SID: {"key": KEY, "band": 1, "unknown": 1}}):
            with self.subTest(value=value):
                self.save(self.state, value)
                self.refused(reason="closeout-state-unproved")

    def test_missing_or_changed_handoff_refuses(self):
        self.save("storage/handoff/fixture.md", "changed", text=True)
        self.refused(1, reason="evidence-hash-mismatch")

    def test_closing_record_binds_inputs_writer_and_body(self):
        original = dict(self.record)
        for key in ("schema", "key", "writer", "binding", "gauge_sha256", "closeout_sha256", "destination_sha256", "tier"):
            with self.subTest(key=key):
                self.save(self.closed, {**original, key: "wrong"})
                self.refused(1, reason="closing-record-mismatch")

    def test_closeout_must_not_predate_the_usage_reading(self):
        self.record["closed_at"] = "2026-11-05T11:59:00Z"
        self.save(self.closed, self.record)
        self.refused(1, reason="closing-record-predates-reading")

    def test_unresolved_mind_proposals_refuse(self):
        for count, decision in ((4, "approved-and-written"), (True, "none-proposed"),
                                (1, "pending"), (1, "none-proposed"), (0, "approved-and-written")):
            with self.subTest(count=count, decision=decision):
                self.record["mind"].update(proposed=count, decision=decision)
                self.save(self.closed, self.record)
                self.refused(1, reason="mind-disposition-unproved")

    def test_approved_entries_require_retained_approval_evidence(self):
        self.record["mind"].update(proposed=1, decision="approved-and-written")
        self.save(self.closed, self.record)
        self.refused(1)
        self.save("storage/active/approval.md", "Synthetic approval for this invented entry.\n", text=True)
        self.record["mind"]["approval"] = self.ref("storage/active/approval.md")
        self.save(self.closed, self.record)
        self.refused(2, reason="new-mind-write-unproved")
        self.make_mind(dt.datetime(2026, 11, 5, 12, 1, 30, tzinfo=dt.timezone.utc))
        self.record["mind"]["leaf_sha256"] = self.leaf_sha
        self.save(self.closed, self.record)
        self.assertEqual(self.invoke(2)[0], 0)
        self.record["mind"]["proposed"] = 3
        self.save(self.closed, self.record)
        self.refused(2, reason="new-mind-entry-count-mismatch")

    def test_missing_mind_is_not_waived(self):
        (self.room / "MIND.md").unlink()
        self.refused(2)

    def test_mind_check_failure_is_not_waived(self):
        self.save(self.leaf, "not a mind\n", text=True)
        self.refused(2, reason="mind-show-ref-refused")

    def test_closing_mind_must_be_the_checked_mind(self):
        self.record["mind"]["leaf_sha256"] = "0" * 64
        self.save(self.closed, self.record)
        result = self.refused(2, reason="closing-mind-mismatch")
        self.assertNotIn("mind", result)

    def test_unparseable_mind_ref_does_not_pass(self):
        real = ROTATE.sibling
        fake = types.SimpleNamespace(main=lambda args: (print(SECRET), 0)[1])
        with mock.patch.object(ROTATE, "sibling", side_effect=lambda name: fake if name == "mind" else real(name)):
            self.refused(2, reason="invalid-mind-reference")

    def test_late_input_change_is_caught(self):
        original = ROTATE.mind_ready
        def change(*args):
            result = original(*args)
            self.save(self.gauge, {**self.row, "tokens": 710000, "percent": 71.0})
            return result
        with mock.patch.object(ROTATE, "mind_ready", side_effect=change):
            rc, result = self.invoke(2)
        self.assertEqual(rc, 2)
        self.assertEqual(result["reason"], "evidence-changed")
        self.assertNotIn("mind", result)

    def test_late_pending_state_is_caught(self):
        original = ROTATE.mind_ready
        def change(*args):
            result = original(*args)
            self.save("logs/closeout/.state.partial", "pending", text=True)
            return result
        with mock.patch.object(ROTATE, "mind_ready", side_effect=change):
            rc, result = self.invoke(2)
        self.assertEqual(rc, 2)
        self.assertEqual(result["reason"], "pending-closeout-state")

    def test_synthetic_marker_is_required(self):
        (self.room / ".rotate-synthetic.json").unlink()
        self.refused()

    def test_numeric_marker_does_not_masquerade_as_true(self):
        self.save(".rotate-synthetic.json", {"schema": "rotate-synthetic/1", "synthetic": 1})
        self.refused(reason="synthetic-room-required")

    def test_nonprivate_file_and_directory_refuse_without_normalizing(self):
        (self.room / self.gauge).chmod(0o664)
        self.refused()
        (self.room / self.gauge).chmod(0o600)
        self.room.chmod(0o775)
        self.refused()

    def test_absolute_traversal_and_body_paths_refuse_before_read(self):
        for path in (str(self.base / "outside.json"), "../outside.json", "logs/body.jsonl"):
            with self.subTest(path=path):
                self.refused(extra=("--gauge-row", path), reason="escaped-or-body-path")

    def test_symlinked_file_and_parent_refuse(self):
        outside = self.base / "outside.json"
        outside.write_text(SECRET)
        target = self.room / self.gauge
        target.unlink()
        target.symlink_to(outside)
        self.refused()
        target.unlink()
        self.save(self.gauge, self.row)
        (self.room / "linked").symlink_to(self.base, target_is_directory=True)
        self.refused(extra=("--gauge-row", "linked/outside.json"))

    def test_hardlink_and_fifo_refuse(self):
        os.link(self.room / self.gauge, self.room / "second-link")
        self.refused()
        (self.room / "second-link").unlink()
        (self.room / self.gauge).unlink()
        os.mkfifo(self.room / self.gauge, 0o600)
        self.refused()

    def test_linked_mind_leaf_is_rejected_before_show(self):
        target = self.room / self.leaf
        copy = self.base / "external-leaf"
        copy.write_bytes(target.read_bytes())
        copy.chmod(0o600)
        target.unlink()
        target.symlink_to(copy)
        self.refused(2)

    def test_oversized_snapshot_refuses(self):
        self.save(self.gauge, " " * (ROTATE.SMALL + 1), text=True)
        self.refused(reason="oversized-evidence")

    def test_cli_default_dry_run_and_read_only_help(self):
        before = self.snapshot()
        result = REAL_RUN([sys.executable, "-I", "-B", str(TOOL), *self.args()], capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertTrue(json.loads(result.stdout)["dry_run"])
        help_result = REAL_RUN([sys.executable, "-I", "-B", str(TOOL), "--help"], capture_output=True, text=True, timeout=15)
        self.assertEqual(help_result.returncode, 0)
        self.assertEqual(before, self.snapshot())

    def test_apply_or_implicit_live_room_is_impossible(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as error:
                ROTATE.main(["--apply"])
        self.assertEqual(error.exception.code, 2)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(ROTATE.main([]), 2)
        self.assertEqual(json.loads(out.getvalue())["reason"], "explicit-synthetic-evidence-required")


class UnsupportedPhases(unittest.TestCase):
    pass


def unsupported_case(phase):
    def test(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), mock.patch.object(ROTATE, "sibling", side_effect=AssertionError("no reads")):
            rc = ROTATE.main(["--phase", str(phase)])
        result = json.loads(out.getvalue())
        self.assertEqual(rc, 2)
        self.assertEqual(result["status"], "unsupported")
        self.assertEqual(result["completed"], [])
        self.assertEqual(result["writes"], 0)
        self.assertTrue(result["needs"])
    return test


for number in range(3, 10):
    setattr(UnsupportedPhases, "test_phase_" + str(number) + "_refuses_without_input_reads", unsupported_case(number))


if __name__ == "__main__":
    unittest.main()
