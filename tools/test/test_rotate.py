#!/usr/bin/env python3
"""Synthetic rotation phase gates. No native body, provider or live record.

Generated with ops/bin/template; implemented by Joe Codex. Run with -I -B
under umask 0002, 0022 and 0077. Fixture minds contain invented entries only.
"""
import contextlib
import copy
import datetime as dt
import hashlib
import importlib.util
import io
import json
import os
import re
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


for number in range(6, 10):
    setattr(UnsupportedPhases, "test_phase_" + str(number) + "_refuses_without_input_reads", unsupported_case(number))


class BuildPhases(unittest.TestCase):
    save = RotateTests.save
    sha = RotateTests.sha
    ref = RotateTests.ref
    make_mind = RotateTests.make_mind
    invoke = RotateTests.invoke
    snapshot = RotateTests.snapshot

    def setUp(self):
        RotateTests.setUp(self)
        self.gate = ROTATE.sibling("gate")
        process_model = self.base / "process-model"
        process_model.mkdir(mode=0o700)
        self.gate.PROC = process_model
        real_sibling = ROTATE.sibling
        patcher = mock.patch.object(ROTATE, "sibling", side_effect=lambda name: self.gate if name == "gate" else real_sibling(name))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.spare = "fixtures/spare.json"
        self.donor = "fixtures/donor.fixture"
        self.estimate_path = "fixtures/estimate.json"
        self.plan_path = "fixtures/build.json"
        self.row["model"] = "synthetic-model"
        self.save(self.gauge, self.row)
        self.record["gauge_sha256"] = self.sha(self.gauge)
        self.save(self.closed, self.record)
        self.spare_row = {"schema": "rotate-spare/1", "provider": "claude", "session_id": DESTINATION,
                          "room": str(self.room), "cwd": str(self.room), "owner": None, "fresh": True,
                          "work_rows": 0, "created_at": "2026-11-05T12:03:00Z",
                          "label": "Role (Fixture Reader) - spare body, do not open"}
        self.save(self.spare, self.spare_row)
        self.rows = []
        for i, (kind, text) in enumerate((("user", "Old synthetic work."), ("system", ""),
                                          ("user", "The retained synthetic summary."),
                                          ("user", "Close out now"), ("assistant", "Procedure is parked."),
                                          ("user", "Which fixture bracket carries the load?"),
                                          ("assistant", "The lower fixture bracket carries the load."))):
            uid = "0000e" + str(i).zfill(3) + "-0000-4000-8000-00000000e" + str(i).zfill(3)
            previous = None if not self.rows else self.rows[-1]["uuid"]
            r = {"type": kind, "sessionId": SID, "uuid": uid, "parentUuid": previous,
                 "cwd": str(self.room), "timestamp": "2026-11-05T11:59:" + str(i).zfill(2) + "Z"}
            if kind != "system":
                r["message"] = {"role": kind, "content": text}
            if i == 1:
                r.update(subtype="compact_boundary", parentUuid=None)
            if i == 2:
                r["isCompactSummary"] = True
            if i == 3:
                r["isMeta"] = True
            if i == 6:
                r["timestamp"] = self.row["reading_at"]
                r["message"].update(model=self.row["model"], id="synthetic-call",
                                     usage={"input_tokens": self.row["tokens"], "cache_read_input_tokens": 0,
                                            "cache_creation_input_tokens": 0})
            self.rows.append(r)
        self.write_body()
        self.save("fixtures/reason.md", "Keep the substantive bracket question and its reply after the summary.\n", text=True)
        self.save("fixtures/transition.md", "Earlier procedure is in the closing handoff. No work is in flight.\n", text=True)
        self.estimate = {"schema": "rotate-estimate/1", "tokens": 20000, "window": self.row["window"],
                         "method": "Invented fixture estimate; no native model call."}
        self.plan = {"schema": "rotate-build/1", "key": KEY, "writer": WRITER, "built_at": "2026-11-05T12:04:00Z",
                     "binding": self.record["binding"], "cut": {"user_row": 5, "exchange_row": 5,
                     "reason": self.ref("fixtures/reason.md")}, "transition": self.ref("fixtures/transition.md")}
        self.bind_plan()

    def args(self, phase=0):
        return RotateTests.args(self, phase) + ["--build-plan", self.plan_path]

    def write_body(self):
        return self.save(self.donor, "".join(json.dumps(r) + "\n" for r in self.rows), text=True)

    def bind_plan(self):
        self.plan["closing_sha256"] = self.sha(self.closed)
        self.plan["destination"] = self.ref(self.spare)
        self.plan["donor"] = self.ref(self.donor)
        self.estimate["donor_sha256"] = self.sha(self.donor)
        self.estimate["cut_row"] = self.plan["cut"]["user_row"]
        self.save(self.estimate_path, self.estimate)
        self.plan["cut"]["estimate"] = self.ref(self.estimate_path)
        self.save(self.plan_path, self.plan)

    def refused(self, phase=3, reason=None):
        before = self.snapshot()
        rc, result = self.invoke(phase)
        self.assertEqual(rc, 2, result)
        self.assertEqual(result["status"], "refused", result)
        if reason:
            self.assertEqual(result["reason"], reason, result)
        self.assertEqual(before, self.snapshot())
        self.assertNotIn("build", result)
        return result

    def tampered_gate(self, change, reason):
        real = ROTATE.static_gates
        def tamper(raw, rows, *rest):
            changed = change(rows)
            if changed is None:
                changed = b"".join(json.dumps(r, separators=(",", ":")).encode() + b"\n" for r in rows)
            return real(changed, rows, *rest)
        with mock.patch.object(ROTATE, "static_gates", side_effect=tamper):
            return self.refused(5, reason)

    def test_destination_stops_without_reading_donor(self):
        (self.room / self.donor).unlink()
        before = self.snapshot()
        rc, result = self.invoke(3)
        self.assertEqual(rc, 0, result)
        self.assertEqual(result["completed"], [0, 1, 2, 3])
        self.assertEqual(result["next_phase"], 4)
        self.assertEqual(result["writes"], 0)
        self.assertEqual(before, self.snapshot())

    def test_window_runs_actual_gauge_and_stops(self):
        before = self.snapshot()
        rc, result = self.invoke(4)
        self.assertEqual(rc, 0, result)
        self.assertEqual(result["completed"], list(range(5)))
        self.assertEqual(result["window"]["start"], 5)
        self.assertEqual(result["writes"], 0)
        self.assertIn("not a native wake", result["window"]["estimate"]["provenance"])
        self.assertEqual(before, self.snapshot())

    def test_build_runs_existing_builder_and_every_static_gate(self):
        before = self.snapshot()
        rc, result = self.invoke(5)
        self.assertEqual(rc, 0, result)
        self.assertEqual(result["completed"], list(range(6)))
        self.assertEqual(result["next_phase"], 6)
        self.assertGreater(result["writes"], 0)
        self.assertTrue(result["temporary_artifacts_removed"])
        self.assertTrue(all(result["build"]["gates"].values()))
        self.assertGreaterEqual(len(result["build"]["gates"]), 15)
        self.assertFalse(result["build"]["artifacts_retained"])
        self.assertFalse(result["native_load_proved"])
        self.assertEqual(before, self.snapshot())

    def test_foreign_stale_or_wrong_spare_refuses(self):
        original = dict(self.spare_row)
        for change in ({"room": str(self.base)}, {"cwd": str(self.base)}, {"owner": WRITER},
                       {"label": "Role (Fixture Writer) - spare body, do not open"},
                       {"session_id": WRITER_SID}, {"provider": "codex"}):
            with self.subTest(change=change):
                self.save(self.spare, {**original, **change})
                self.bind_plan()
                self.refused(reason="synthetic-spare-mismatch")

    def test_freshness_requires_zero_actual_metadata_work_rows(self):
        for change in ({"fresh": False}, {"fresh": 1}, {"work_rows": 1}, {"work_rows": False}):
            with self.subTest(change=change):
                self.save(self.spare, {**self.spare_row, **change})
                self.bind_plan()
                self.refused(reason="synthetic-spare-not-fresh")

    def test_missing_owner_is_unknown_not_unowned(self):
        self.spare_row.pop("owner")
        self.save(self.spare, self.spare_row)
        self.bind_plan()
        self.refused(reason="synthetic-spare-mismatch")

    def test_spare_creation_must_follow_closeout(self):
        self.spare_row["created_at"] = "2026-11-05T11:00:00Z"
        self.save(self.spare, self.spare_row)
        self.bind_plan()
        self.refused(reason="synthetic-spare-predates-closeout")

    def test_build_time_is_bound_after_spare_creation(self):
        self.plan["built_at"] = "2026-11-05T12:02:59Z"
        self.bind_plan()
        self.refused(reason="synthetic-build-predates-spare")

    def test_open_fixture_destination_is_a_real_holder(self):
        # Inspect only this test process. Other host processes are not part
        # of the synthetic process model or a claimed fleet-holder proof.
        own = Path("/") / "proc" / str(os.getpid())
        self.gate.PROC = types.SimpleNamespace(iterdir=lambda: iter([own]))
        with (self.room / self.spare).open("rb"):
            self.refused(reason="synthetic-destination-held")

    def test_holder_read_failure_is_not_an_empty_holder_list(self):
        class Denied:
            name = "123"
            def stat(self):
                return types.SimpleNamespace(st_uid=os.geteuid())
            def __truediv__(self, _):
                return self
            def iterdir(self):
                raise PermissionError("synthetic process cannot be inspected")
        self.gate.PROC = types.SimpleNamespace(iterdir=lambda: iter([Denied()]))
        self.refused(reason="fixture-holder-evidence-unavailable")

    def test_wrong_plan_binding_refuses(self):
        self.plan["binding"] = "f" * 64
        self.save(self.plan_path, self.plan)
        self.refused(reason="build-plan-mismatch")

    def test_pending_interrupted_build_is_preserved_and_blocks(self):
        self.save(".rotate-build.leftover/partial", "invented interrupted artifact\n", text=True)
        self.refused(reason="pending-synthetic-build")

    def test_provider_build_gap_is_not_silently_bridged(self):
        self.row["provider"] = "codex"
        self.identities[0]["provider"] = "codex"
        self.save(self.registry, {"identities": self.identities})
        self.save(self.gauge, self.row)
        self.spare_row["provider"] = "codex"
        self.save(self.spare, self.spare_row)
        self.record["binding"] = hashlib.sha256(json.dumps([KEY, "codex", SID], separators=(",", ":")).encode()).hexdigest()
        self.record["gauge_sha256"] = self.sha(self.gauge)
        self.save(self.closed, self.record)
        self.plan["binding"] = self.record["binding"]
        self.bind_plan()
        self.refused(4, "provider-window-build-unsupported")

    def test_body_must_have_explicit_fixture_extension(self):
        p = self.save("fixtures/donor.json", "{}\n", text=True)
        self.plan["donor"] = self.ref(str(p.relative_to(self.room)))
        self.save(self.plan_path, self.plan)
        self.refused(4, "synthetic-body-extension-required")

    def test_unterminated_fixture_is_not_tolerated_as_damaged_rows(self):
        p = self.room / self.donor
        p.write_bytes(p.read_bytes().rstrip(b"\n"))
        self.bind_plan()
        self.refused(4, "synthetic-body-not-terminated")

    def test_fixture_row_limit_is_bounded_before_identity_walk(self):
        self.save(self.donor, "{}\n" * 4097, text=True)
        self.bind_plan()
        self.refused(4, "synthetic-body-row-bound")

    def test_private_body_modes_and_linked_parents_refuse(self):
        path = self.room / self.donor
        path.chmod(0o664)
        self.refused(4)
        path.chmod(0o600)
        self.save("elsewhere/body.fixture", "{}\n", text=True)
        (self.room / "linked-bodies").symlink_to(self.room / "elsewhere", target_is_directory=True)
        self.plan["donor"] = {"path": "linked-bodies/body.fixture", "sha256": "f" * 64}
        self.save(self.plan_path, self.plan)
        self.refused(4)

    def test_nonfixture_or_wrong_identity_fields_refuse(self):
        self.rows[3]["message"]["content"] = "1000" + SID[4:]
        self.write_body()
        self.bind_plan()
        self.refused(4, "nonfixture-body-identifier")
        self.rows[3]["message"]["content"] = "Synthetic procedure."
        self.rows[2]["session_id"] = WRITER_SID
        self.write_body()
        self.bind_plan()
        self.refused(4, "synthetic-body-identity-mismatch")

    def test_nonfixture_message_correlation_identifier_refuses(self):
        self.rows[2]["uuid"] = "not-a-message-identifier"
        self.write_body()
        self.bind_plan()
        self.refused(4, "nonfixture-message-identifier")

    def test_native_usage_must_match_the_phase_zero_reading(self):
        self.rows[-1]["message"]["usage"]["input_tokens"] -= 1
        self.write_body()
        self.bind_plan()
        self.refused(4, "donor-usage-mismatch")

    def test_boundary_and_exact_summary_required(self):
        self.rows[1].pop("subtype")
        self.write_body()
        self.bind_plan()
        self.refused(4, "synthetic-boundary-required")
        self.rows[1]["subtype"] = "compact_boundary"
        self.rows[2].pop("isCompactSummary")
        self.write_body()
        self.bind_plan()
        self.refused(4, "exact-compaction-summary-required")

    def test_cut_requires_explicit_integer_operator_rows(self):
        self.plan["cut"]["user_row"] = True
        self.bind_plan()
        self.refused(4, "cut-indices-required")

    def test_procedure_injection_and_assistant_are_not_operator_cuts(self):
        for row in (3, 4):
            with self.subTest(row=row):
                self.plan["cut"]["user_row"] = row
                self.plan["cut"]["exchange_row"] = row
                self.bind_plan()
                self.refused(4, "genuine-user-cut-required")

    def test_beyond_procedure_exchange_requires_an_assistant_reply(self):
        self.rows[-1]["isMeta"] = True
        self.write_body()
        self.bind_plan()
        self.refused(4, "substantive-exchange-required")

    def test_bound_wake_estimate_is_not_a_new_measurement(self):
        self.estimate["tokens"] = 200001
        self.bind_plan()
        self.refused(4, "wake-estimate-unproved-or-over-budget")

    def test_boundary_root_and_summary_parent_evidence_required(self):
        self.rows[1]["parentUuid"] = self.rows[0]["uuid"]
        self.write_body()
        self.bind_plan()
        self.refused(4, "boundary-not-root")
        self.rows[1]["parentUuid"] = None
        self.rows[2].pop("uuid")
        self.write_body()
        self.bind_plan()
        self.refused(4, "window-parent-evidence-required")

    def test_transition_is_text_not_a_file_path(self):
        self.save("fixtures/transition.md", "archives/MIND-fixture.md", text=True)
        self.plan["transition"] = self.ref("fixtures/transition.md")
        self.bind_plan()
        self.refused(5, "transition-text-required")

    def test_media_externalizer_runs_on_both_supported_shapes(self):
        data = "QUJD" * 100
        self.rows[5]["message"]["content"] = [{"type": "text", "text": "Which fixture bracket carries the load?"}]
        self.rows[6]["message"]["content"] = [{"type": "text", "text": "The lower bracket."},
            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": data}}]
        self.rows[6]["toolUseResult"] = {"type": "image", "file": {"filePath": "synthetic.png", "base64": data, "originalSize": 300}}
        self.write_body()
        self.bind_plan()
        before = self.snapshot()
        rc, result = self.invoke(5)
        self.assertEqual(rc, 0, result)
        self.assertEqual(result["build"]["media_blocks"], 2)
        self.assertEqual(result["build"]["media_files"], 1)
        self.assertEqual(before, self.snapshot())

    def test_invalid_or_unsupported_inline_media_fails_closed(self):
        self.rows[-1]["message"]["content"] = [{"type": "image", "source": {"data": "small-payload"}}]
        self.write_body()
        self.bind_plan()
        self.refused(5, "static-inline-media")

    def test_static_termination_and_parse_are_measured(self):
        self.tampered_gate(lambda rows: b"{}", "static-terminated")
        self.tampered_gate(lambda rows: b"{}\n", "static-parse")

    def test_static_identity_and_donor_residue(self):
        self.tampered_gate(lambda rows: rows[0].update(sessionId=WRITER_SID), "static-identities")

    def test_static_dangling_parent_and_duplicate_message_id(self):
        self.tampered_gate(lambda rows: rows[2].update(parentUuid=DESTINATION), "static-parent-chain")
        self.tampered_gate(lambda rows: rows[2].update(uuid=rows[1]["uuid"]), "static-unique-message-ids")

    def test_static_head_is_boundary(self):
        self.tampered_gate(lambda rows: rows[0].update(subtype="ordinary"), "static-boundary-head")

    def test_static_missing_and_duplicated_orientation(self):
        self.tampered_gate(lambda rows: rows.pop(-3) and None, "static-orientation-count")
        def duplicate(rows):
            extra = dict(rows[-3])
            extra["uuid"] = DESTINATION
            rows.insert(-2, extra)
        self.tampered_gate(duplicate, "static-orientation-count")

    def test_static_capsule_text_and_working_directory(self):
        self.tampered_gate(lambda rows: rows[-3]["message"].update(content="<session_clinic_orientation>\nnot the capsule"), "static-orientation-text")
        self.tampered_gate(lambda rows: rows[-3].update(cwd=str(self.base)), "static-working-directory")

    def test_new_orientation_uses_bound_build_time_not_legacy_literal(self):
        self.tampered_gate(lambda rows: rows[-3].update(timestamp="2026-07-30T15:30:00Z"), "static-orientation-time")

    def test_static_destination_must_be_named_in_the_capsule(self):
        actual = ROTATE.capsule_text
        def unnamed(*args):
            return actual(*args).replace(DESTINATION, "unnamed synthetic container")
        with mock.patch.object(ROTATE, "capsule_text", side_effect=unnamed):
            self.refused(5, "static-destination-named")

    def test_static_residue_gate_is_separate_from_identity_set(self):
        real = ROTATE.sibling
        successor = real("successor")
        actual_count = successor.count_residue
        calls = 0
        def residue(rows, donor):
            nonlocal calls
            calls += 1
            return actual_count(rows, donor) if calls == 1 else (1, 0)
        successor.count_residue = residue
        with mock.patch.object(ROTATE, "sibling", side_effect=lambda name: successor if name == "successor" else real(name)):
            self.refused(5, "static-donor-structural-residue")

    def test_static_plain_label_is_last(self):
        self.tampered_gate(lambda rows: rows[-1].update(agentName="Other fixture"), "static-plain-label-last")

    def test_static_unmatched_tool_use_and_tool_result(self):
        self.tampered_gate(lambda rows: rows[3]["message"].update(content=[{"type": "tool_use", "id": "fixture-call"}]), "static-tool-pairs")
        self.tampered_gate(lambda rows: rows[3]["message"].update(content=[{"type": "tool_result", "tool_use_id": "fixture-call"}]), "static-tool-result-matched")

    def test_static_duplicate_tool_use_is_not_a_pair(self):
        self.tampered_gate(lambda rows: rows[3]["message"].update(content=[{"type": "tool_use", "id": "fixture-call"},
            {"type": "tool_use", "id": "fixture-call"}]), "static-tool-use-unique")

    def test_static_window_and_spoken_text_are_carried(self):
        self.tampered_gate(lambda rows: rows.insert(-2, {"type": "metadata", "sessionId": DESTINATION}), "static-carried-window")
        self.tampered_gate(lambda rows: rows[2]["message"].update(content="Changed synthetic prose."), "static-carried-text")

    def test_orientation_privacy_screen_is_actual(self):
        self.save("fixtures/transition.md", "Invented fixture: biopsy.\n", text=True)
        self.plan["transition"] = self.ref("fixtures/transition.md")
        self.bind_plan()
        self.refused(5, "static-orientation-privacy")

    def media_fixture(self):
        self.rows[-1]["message"]["content"] = [{"type": "text", "text": "Synthetic answer."},
            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "QUJD" * 100}}]
        self.write_body()
        self.bind_plan()

    def test_externalized_file_fixity_is_checked(self):
        self.media_fixture()
        actual = ROTATE.static_gates
        def corrupt(raw, rows, args, evidence, capsule, media_dir, externalizer, window):
            next(media_dir.iterdir()).write_bytes(b"different invented bytes")
            return actual(raw, rows, args, evidence, capsule, media_dir, externalizer, window)
        with mock.patch.object(ROTATE, "static_gates", side_effect=corrupt):
            self.refused(5, "static-media-pointer")

    def test_media_pointer_must_name_the_actual_file(self):
        self.media_fixture()
        def tamper(rows):
            block = rows[3]["message"]["content"][-1]
            block["text"] = "[media externalized synthetic: preserved at missing-fixture.png]"
        self.tampered_gate(tamper, "static-media-pointer-links")

    def test_media_blocks_without_producer_files_refuse(self):
        actual = ROTATE.static_gates
        def absent(raw, rows, args, evidence, capsule, media_dir, externalizer, window):
            externalizer.blocks = 1
            return actual(raw, rows, args, evidence, capsule, media_dir, externalizer, window)
        with mock.patch.object(ROTATE, "static_gates", side_effect=absent):
            self.refused(5, "static-media-pointer-count")

    def test_successor_prose_is_not_reidentified(self):
        self.rows[5]["message"]["content"] += " Invented history mentions " + SID + "."
        self.write_body()
        self.bind_plan()
        actual = ROTATE.static_gates
        def inspect(raw, rows, *rest):
            self.assertIn(SID, rows[2]["message"]["content"])
            self.assertNotIn(DESTINATION, rows[2]["message"]["content"])
            return actual(raw, rows, *rest)
        with mock.patch.object(ROTATE, "static_gates", side_effect=inspect):
            self.assertEqual(self.invoke(5)[0], 0)

    def test_exception_and_interruption_leave_no_artifact_adoption(self):
        before = self.snapshot()
        with mock.patch.object(ROTATE, "static_gates", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.invoke(5)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(self.invoke(5)[0], 0)

    def test_repeated_builds_never_advance_or_retain_artifacts(self):
        before = self.snapshot()
        for phase in (3, 4, 5, 5, 3):
            rc, result = self.invoke(phase)
            self.assertEqual(rc, 0, result)
            self.assertEqual(result["next_phase"], phase + 1)
        self.assertEqual(before, self.snapshot())

    def test_late_new_holder_prevents_build(self):
        with mock.patch.object(ROTATE, "no_fixture_holders", side_effect=(None, ROTATE.Refused("synthetic-destination-held"))):
            self.refused(5, "synthetic-destination-held")

    def test_c1_capsule_mind_is_verbatim_actual_show_ref_leaf(self):
        mind = ROTATE.sibling("mind")
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            rc = mind.main(["--room", str(self.room), "--registry", str(self.room / self.registry),
                            "show", KEY, "--ref"])
        self.assertEqual(rc, 0)
        ref = re.fullmatch(r"leaf=(archives/MIND-[a-z0-9-]+\.md)\|sha256=([0-9a-f]{64})\n", out.getvalue())
        self.assertIsNotNone(ref)
        leaf = (self.room / ref.group(1)).read_bytes()
        self.assertEqual(hashlib.sha256(leaf).hexdigest(), ref.group(2))
        actual = ROTATE.static_gates
        observed = []
        def inspect(raw, rows, args, evidence, capsule, *rest):
            before, marker, after = capsule.partition("\n\nMind\n")
            mind_text, transition, tail = after.partition("\nTransition\n")
            self.assertTrue(before.startswith("Registry\n"))
            self.assertTrue(marker and transition)
            self.assertEqual(mind_text.encode("utf-8"), leaf)
            self.assertTrue(tail)
            observed.append(ref.group(2))
            return actual(raw, rows, args, evidence, capsule, *rest)
        with mock.patch.object(ROTATE, "static_gates", side_effect=inspect):
            self.assertEqual(self.invoke(5)[0], 0)
        self.assertEqual(observed, [ref.group(2)])

    def test_c1_capsule_first_turn_and_four_part_order(self):
        actual = ROTATE.static_gates
        seen = []
        def inspect(raw, rows, args, evidence, capsule, *rest):
            positions = [capsule.index(part) for part in ("Registry\n", "\n\nMind\n", "\nTransition\n", "\nFirst turn\n")]
            self.assertEqual(positions, sorted(positions))
            self.assertEqual(capsule.partition("\nFirst turn\n")[2],
                             "The room's status in a few lines, then speak as yourself.\n")
            seen.append(True)
            return actual(raw, rows, args, evidence, capsule, *rest)
        with mock.patch.object(ROTATE, "static_gates", side_effect=inspect):
            self.assertEqual(self.invoke(5)[0], 0)
        self.assertEqual(seen, [True])

    def test_c1_staging_is_created_inside_the_synthetic_room(self):
        actual = tempfile.TemporaryDirectory
        seen = []
        def private_stage(*args, **kwargs):
            # Refuse the mutant before it can create anything outside the
            # authorized fixture, not merely after observing its writes.
            self.assertEqual(kwargs.get("dir"), self.room)
            stage = actual(*args, **kwargs)
            self.assertEqual(Path(stage.name).parent, self.room)
            self.assertTrue(Path(stage.name).name.startswith(".rotate-build."))
            seen.append(Path(stage.name))
            return stage
        before = self.snapshot()
        with mock.patch.object(ROTATE.tempfile, "TemporaryDirectory", side_effect=private_stage):
            self.assertEqual(self.invoke(5)[0], 0)
        self.assertEqual(len(seen), 1)
        self.assertFalse(seen[0].exists())
        self.assertEqual(before, self.snapshot())

    def test_c1_cut_reason_is_required_hash_bound_and_recorded(self):
        reason = dict(self.plan["cut"]["reason"])
        self.plan["cut"]["reason"] = {**reason, "sha256": "0" * 64}
        self.save(self.plan_path, self.plan)
        self.refused(4, "evidence-hash-mismatch")
        self.plan["cut"].pop("reason")
        self.save(self.plan_path, self.plan)
        self.refused(4, "invalid-evidence-reference")
        self.plan["cut"]["reason"] = reason
        self.save(self.plan_path, self.plan)
        rc, result = self.invoke(4)
        self.assertEqual(rc, 0, result)
        self.assertEqual(result["window"]["reason_sha256"], self.sha(reason["path"]))

    def test_c1_window_uses_the_last_of_two_boundaries(self):
        self.rows[0].update(type="system", subtype="compact_boundary", parentUuid=None)
        self.rows[0].pop("message")
        self.write_body()
        self.bind_plan()
        rc, result = self.invoke(4)
        self.assertEqual(rc, 0, result)
        self.assertEqual(result["window"]["boundary"], 1)
        self.assertEqual(result["window"]["summary"], 2)

    def test_c1_two_summaries_are_not_exactly_one(self):
        self.rows[3]["isCompactSummary"] = True
        self.write_body()
        self.bind_plan()
        self.refused(4, "exact-compaction-summary-required")

    def test_c1_estimate_schema_is_checked_independently(self):
        self.estimate["schema"] = "rotate-estimate/99"
        self.save(self.estimate_path, self.estimate)
        self.plan["cut"]["estimate"] = self.ref(self.estimate_path)
        self.save(self.plan_path, self.plan)
        self.refused(4, "wake-estimate-unproved-or-over-budget")

    def test_c1_estimate_binds_the_exact_donor_hash(self):
        self.estimate["donor_sha256"] = "0" * 64
        self.save(self.estimate_path, self.estimate)
        self.plan["cut"]["estimate"] = self.ref(self.estimate_path)
        self.save(self.plan_path, self.plan)
        self.refused(4, "wake-estimate-unproved-or-over-budget")

    def test_c1_estimate_binds_the_selected_cut(self):
        self.estimate["cut_row"] = 4
        self.save(self.estimate_path, self.estimate)
        self.plan["cut"]["estimate"] = self.ref(self.estimate_path)
        self.save(self.plan_path, self.plan)
        self.refused(4, "wake-estimate-unproved-or-over-budget")

    def test_c1_estimate_window_matches_the_reading(self):
        self.estimate["window"] -= 1
        self.save(self.estimate_path, self.estimate)
        self.plan["cut"]["estimate"] = self.ref(self.estimate_path)
        self.save(self.plan_path, self.plan)
        self.refused(4, "wake-estimate-unproved-or-over-budget")

    def test_c1_estimate_method_cannot_be_blank(self):
        self.estimate["method"] = " \t "
        self.save(self.estimate_path, self.estimate)
        self.plan["cut"]["estimate"] = self.ref(self.estimate_path)
        self.save(self.plan_path, self.plan)
        self.refused(4, "wake-estimate-unproved-or-over-budget")

    def test_c1_metadata_user_row_is_not_a_prompt(self):
        self.rows[5]["isMeta"] = True
        self.write_body()
        self.bind_plan()
        self.refused(4, "genuine-user-cut-required")

    def test_c1_sidechain_user_row_is_not_a_prompt(self):
        self.rows[5]["isSidechain"] = True
        self.write_body()
        self.bind_plan()
        self.refused(4, "genuine-user-cut-required")

    def test_c1_summary_user_row_is_not_a_prompt(self):
        self.rows[5]["isCompactSummary"] = True
        self.write_body()
        self.bind_plan()
        self.refused(4, "genuine-user-cut-required")

    def test_c1_nonempty_tool_result_is_not_a_prompt(self):
        self.rows[5]["message"]["content"] = [{"type": "tool_result", "tool_use_id": "fixture-call",
            "text": "A nonempty invented result must not masquerade as a user prompt."}]
        self.write_body()
        self.bind_plan()
        self.refused(4, "genuine-user-cut-required")

    def test_c1_empty_user_content_is_not_a_prompt(self):
        self.rows[5]["message"]["content"] = " \t "
        self.write_body()
        self.bind_plan()
        self.refused(4, "genuine-user-cut-required")

    def test_c1_injected_user_content_is_not_a_prompt(self):
        self.rows[5]["message"]["content"] = "<system-reminder>Invented injected procedure.</system-reminder>"
        self.write_body()
        self.bind_plan()
        self.refused(4, "genuine-user-cut-required")

    def test_c1_cut_start_must_itself_be_a_user_prompt(self):
        self.plan["cut"].update(user_row=4, exchange_row=5)
        self.bind_plan()
        self.refused(4, "genuine-user-cut-required")

    def test_c1_exchange_row_must_itself_be_a_user_prompt(self):
        extra = copy.deepcopy(self.rows[-1])
        extra.update(uuid=DESTINATION, parentUuid=self.rows[-1]["uuid"], timestamp="2026-11-05T12:00:01Z")
        extra["message"].pop("usage")
        extra["message"]["content"] = "Another invented assistant reply."
        self.rows.append(extra)
        self.write_body()
        self.plan["cut"].update(user_row=5, exchange_row=6)
        self.bind_plan()
        self.refused(4, "genuine-user-cut-required")

    def test_c1_exchange_cannot_precede_the_selected_cut(self):
        self.rows[3].pop("isMeta")
        self.rows[3]["message"]["content"] = "An earlier invented project question."
        self.write_body()
        self.plan["cut"].update(user_row=5, exchange_row=3)
        self.bind_plan()
        self.refused(4, "genuine-user-cut-required")

    def test_c1_build_plan_binds_the_closing_record_hash(self):
        self.plan["closing_sha256"] = "0" * 64
        self.save(self.plan_path, self.plan)
        self.refused(3, "build-plan-mismatch")

    def test_c1_every_row_needs_the_exact_session_identity(self):
        self.rows[0].pop("sessionId")
        self.write_body()
        self.bind_plan()
        self.refused(4, "synthetic-body-identity-mismatch")

    def test_c1_late_failure_never_leaks_a_completed_build_object(self):
        actual = ROTATE.build_preview
        changed = []
        def late_change(*args):
            preview = actual(*args)
            self.assertTrue(preview["gates"])
            self.save(self.gauge, {**self.row, "tokens": 710000, "percent": 71.0})
            changed.append(self.snapshot())
            return preview
        with mock.patch.object(ROTATE, "build_preview", side_effect=late_change):
            rc, result = self.invoke(5)
        self.assertEqual(rc, 2, result)
        self.assertEqual(result["reason"], "evidence-changed")
        self.assertNotIn("build", result)
        self.assertEqual(len(changed), 1)
        self.assertEqual(self.snapshot(), changed[0])


if __name__ == "__main__":
    unittest.main()
