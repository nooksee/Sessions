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


class PhaseEvidenceRequired(unittest.TestCase):
    pass


def unsupported_case(phase):
    def test(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), mock.patch.object(ROTATE, "sibling", side_effect=AssertionError("no reads")):
            rc = ROTATE.main(["--phase", str(phase)])
        result = json.loads(out.getvalue())
        self.assertEqual(rc, 2)
        self.assertEqual(result["status"], "refused")
        self.assertEqual(result["reason"], "explicit-synthetic-evidence-required")
        self.assertEqual(result["completed"], [])
        self.assertEqual(result["writes"], 0)
        self.assertTrue(result["needs"])
    return test


for number in range(6, 10):
    setattr(PhaseEvidenceRequired, "test_phase_" + str(number) + "_refuses_without_input_reads", unsupported_case(number))


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


class InstallPhases(unittest.TestCase):
    save = RotateTests.save
    sha = RotateTests.sha
    ref = RotateTests.ref
    make_mind = RotateTests.make_mind
    snapshot = RotateTests.snapshot
    write_body = BuildPhases.write_body
    bind_plan = BuildPhases.bind_plan

    def setUp(self):
        BuildPhases.setUp(self)
        self.pristine = "fixtures/pristine.fixture"
        self.process_path = "fixtures/process.json"
        self.operation_path = "fixtures/operation.json"
        self.go_path = "fixtures/go.json"
        self.load_path = "fixtures/load.json"
        self.accept_path = "fixtures/accept.json"
        self.append_path = "fixtures/append.fixture"
        self.wake_path = "fixtures/wake.json"
        spare = {"type": "custom-title", "sessionId": DESTINATION, "cwd": str(self.room),
                 "customTitle": self.spare_row["label"]}
        self.save(self.pristine, json.dumps(spare) + "\n", text=True)
        self.process = {"schema": "rotate-process/1", "observable": True, "holders": [], "session_records": []}
        self.save(self.process_path, self.process)
        self.go = {"schema": "rotate-go/1", "key": KEY, "writer": WRITER,
                   "container": DESTINATION, "room": str(self.room),
                   "size": (self.room / self.pristine).stat().st_size, "custody_sha256": self.sha(self.pristine),
                   "after_phase": 6, "at": "2026-11-05T12:06:00Z", "word": "go",
                   "rollback": "restore-pristine-and-hold"}
        self.append = [
            {"type": "user", "sessionId": DESTINATION, "cwd": str(self.room),
             "uuid": "0000f001-0000-4000-8000-00000000f001", "parentUuid": self.rows[-1]["uuid"],
             "timestamp": "2026-11-05T12:06:40Z", "message": {"role": "user", "content": "Hello, fixture reader."}},
            {"type": "assistant", "sessionId": DESTINATION, "cwd": str(self.room),
             "uuid": "0000f002-0000-4000-8000-00000000f002", "parentUuid": "0000f001-0000-4000-8000-00000000f001",
             "timestamp": "2026-11-05T12:07:00Z", "message": {"role": "assistant", "model": self.row["model"],
                 "content": "The synthetic room is ready. I am Fixture Reader.",
                 "usage": {"input_tokens": 18000, "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0}}},
        ]
        self.wake = {**self.row, "session_id": DESTINATION, "tokens": 18000, "percent": 1.8,
                     "reading_at": "2026-11-05T12:07:00Z", "measured_at": "2026-11-05T12:07:00Z", "age_seconds": 0}
        self.load = {"schema": "rotate-load/1", "loaded": True, "key": KEY, "container": DESTINATION,
                     "served_at": "2026-11-05T12:06:30Z", "mind_confirmed": True,
                     "readback": {"key": KEY, "person": "Fixture Reader", "room": str(self.room)}}
        self.accept = {"schema": "rotate-acceptance/1", "key": KEY, "container": DESTINATION,
                       "word": "recognize", "at": "2026-11-05T12:08:00Z"}
        self.save("fixtures/binding.json", {"schema": "rotate-binding/1", "key": KEY, "session_id": SID,
                                           "root": str(self.room), "provider": "claude"})
        self.save("fixtures/launcher.json", {"schema": "rotate-launcher/1", "key": KEY, "hold": False})
        self.operation = {"schema": "rotate-operation/1", "key": KEY, "writer": WRITER,
                          "binding": self.record["binding"], "build_sha256": self.sha(self.plan_path),
                          "custody_at": "2026-11-05T12:05:00Z", "rotation": 1, "deviations": 0,
                          "donor_preference": "removed", "pristine": self.ref(self.pristine),
                          "donor_store": self.ref(self.donor), "binding_preimage": self.ref("fixtures/binding.json"),
                          "launcher": self.ref("fixtures/launcher.json")}
        self.bind_operation()

    def bind_operation(self):
        self.save(self.go_path, self.go)
        self.save(self.append_path, "".join(json.dumps(r) + "\n" for r in self.append), text=True)
        self.save(self.wake_path, self.wake)
        self.load.update(append=self.ref(self.append_path), gauge=self.ref(self.wake_path))
        self.save(self.load_path, self.load)
        self.save(self.accept_path, self.accept)
        self.save(self.process_path, self.process)
        self.operation.update(process_model=self.ref(self.process_path), go=self.ref(self.go_path),
                              load=self.ref(self.load_path), acceptance=self.ref(self.accept_path))
        self.save(self.operation_path, self.operation)

    def args(self, phase=6):
        return BuildPhases.args(self, phase) + ["--operation-plan", self.operation_path]

    def invoke(self, phase=6):
        out = io.StringIO()
        def command(argv, **kwargs):
            self.assertEqual(argv[:3], ["/bin/bash", str(TOOL.parents[3] / "ops/bin/template"), "receipt"])
            self.assertTrue(Path(kwargs["cwd"]).is_relative_to(self.room))
            self.assertEqual(kwargs["env"], {"PATH": "/usr/bin:/bin", "LC_ALL": "C"})
            return REAL_RUN(argv, **kwargs)
        with contextlib.redirect_stdout(out), mock.patch("subprocess.run", side_effect=command):
            rc = ROTATE.main(self.args(phase))
        self.assertNotIn(SECRET, out.getvalue())
        self.assertNotIn(SID, out.getvalue())
        return rc, json.loads(out.getvalue())

    def refused(self, phase=7, reason=None):
        before = self.snapshot()
        rc, result = self.invoke(phase)
        self.assertEqual(rc, 2, result)
        self.assertEqual(result["status"], "refused", result)
        if reason:
            self.assertEqual(result["reason"], reason, result)
        self.assertEqual(before, self.snapshot())
        self.assertNotIn("build", result)
        return result

    def test_six_stops_with_two_directly_verified_copies_and_hold(self):
        (self.room / self.go_path).unlink()
        (self.room / self.load_path).unlink()
        before = self.snapshot()
        rc, result = self.invoke(6)
        self.assertEqual(rc, 0, result)
        self.assertEqual(result["completed"], list(range(7)))
        self.assertEqual(result["next_phase"], 7)
        self.assertTrue(result["rehearsal"]["hold"])
        self.assertEqual(result["rehearsal"]["custody_rows_per_tier"], 8)
        self.assertFalse(result["rehearsal"]["physical_custody_proved"])
        self.assertEqual(before, self.snapshot())

    def test_seven_stops_after_verified_join_without_load(self):
        (self.room / self.load_path).unlink()
        before = self.snapshot()
        rc, result = self.invoke(7)
        self.assertEqual(rc, 0, result)
        self.assertEqual(result["completed"], list(range(8)))
        self.assertEqual(len(result["rehearsal"]["agreements"]), 6)
        self.assertTrue(all(result["rehearsal"]["agreements"].values()))
        self.assertTrue(result["rehearsal"]["hold"])
        self.assertEqual(before, self.snapshot())

    def test_eight_records_actual_fixture_usage_and_explicit_acceptance(self):
        before = self.snapshot()
        rc, result = self.invoke(8)
        self.assertEqual(rc, 0, result)
        self.assertEqual(result["completed"], list(range(9)))
        self.assertEqual(result["rehearsal"]["wake"]["tokens"], 18000)
        self.assertIs(result["rehearsal"]["wake"]["native_load_proved"], False)
        self.assertFalse(result["rehearsal"]["hold"])
        self.assertTrue(result["rehearsal"]["fixture_accepted"])
        self.assertFalse(result["native_load_proved"])
        self.assertFalse(result["operator_accepted"])
        self.assertEqual(before, self.snapshot())

    def test_nine_uses_actual_receipt_template_and_removes_only_copy(self):
        before = self.snapshot()
        actual = ROTATE.private_write
        receipts = []
        def inspect(path, raw, *rest):
            if path.suffix == ".md":
                receipts.append(raw)
            return actual(path, raw, *rest)
        with mock.patch.object(ROTATE, "private_write", side_effect=inspect):
            rc, result = self.invoke(9)
        self.assertEqual(rc, 0, result)
        self.assertEqual(result["completed"], list(range(10)))
        self.assertIsNone(result["next_phase"])
        self.assertEqual(result["needs"], [])
        self.assertTrue(result["rehearsal"]["donor_store_removed"])
        self.assertEqual(len(receipts), 1)
        text = receipts[0].decode()
        self.assertIn("not production authority", text)
        for title in ("Tier", "Donor", "Destination", "Window cut and reason", "Static gates", "Custody",
                      "Mind leaf", "Install", "Wake estimate against the measured wake", "Deviations", "Acceptance", "Rollback"):
            self.assertIn("## " + title, text)
        for item in ("18000/1000000", "20000 estimated", self.leaf_sha, "2026-11-05T12:08:00Z", "Synthetic"):
            self.assertIn(item, text)
        self.assertNotIn("{{", text)
        self.assertEqual(before, self.snapshot())

    def test_no_real_holder_reader_in_later_slices(self):
        with mock.patch.object(ROTATE, "no_fixture_holders", side_effect=AssertionError("no host process reads")):
            self.assertEqual(self.invoke(9)[0], 0)

    def test_held_body_stages_new_but_never_switches_registry(self):
        self.process["holders"] = [self.pristine]
        self.bind_operation()
        actual = ROTATE.private_write
        new_files = []
        def inspect(path, raw, *rest):
            if path.suffix == ".NEW":
                new_files.append((path, raw))
            return actual(path, raw, *rest)
        with mock.patch.object(ROTATE, "private_write", side_effect=inspect), mock.patch.object(
                ROTATE, "six_agreements", side_effect=AssertionError("no join")):
            rc, result = self.invoke(7)
        self.assertEqual(rc, 0, result)
        self.assertEqual(len(new_files), 1)
        self.assertTrue(new_files[0][0].is_relative_to(self.room))
        self.assertEqual(result["completed"], list(range(7)))
        self.assertEqual(result["next_phase"], 7)
        self.assertTrue(result["rehearsal"]["hold"])

    def test_held_body_cannot_run_ahead_to_acceptance(self):
        self.process["session_records"] = [self.pristine]
        self.bind_operation()
        result = self.refused(8, "operator-new-swap-pending")
        self.assertTrue(result["rehearsal"]["rollback"])

    def test_holder_path_aliases_preserve_the_new_fallback_before_any_swap(self):
        for field in ("holders", "session_records"):
            for alias in ("./fixtures/pristine.fixture", "fixtures/./pristine.fixture",
                          "fixtures//pristine.fixture"):
                with self.subTest(field=field, alias=alias):
                    self.process.update(holders=[], session_records=[])
                    self.process[field] = [alias]
                    self.bind_operation()
                    actual = ROTATE.private_write
                    staged = []
                    def inspect(path, raw, *rest):
                        if path.suffix == ".NEW":
                            staged.append(path)
                        return actual(path, raw, *rest)
                    with mock.patch.object(ROTATE, "private_write", side_effect=inspect), mock.patch.object(
                            ROTATE, "six_agreements", side_effect=AssertionError("held fixture must not join")) as join:
                        rc, result = self.invoke(7)
                    self.assertEqual((join.call_count, len(staged)), (0, 1))
                    self.assertEqual(rc, 0, result)
                    self.assertEqual(result["completed"], list(range(7)))
                    self.assertEqual(result["next_phase"], 7)
                    self.assertEqual(len(staged), 1)
                    self.assertTrue(staged[0].is_relative_to(self.room))

    def test_rollback_rechecks_tier_two_before_restoring_any_saved_body(self):
        actual_write = ROTATE.private_write
        actual_replace = ROTATE.replace_private
        tier_two = []
        restored = []
        def remember(path, raw, *rest):
            if path.parent.name == "tier-2" and path.name == "destination.fixture":
                tier_two.append(path)
            return actual_write(path, raw, *rest)
        def tamper(*args):
            self.assertEqual(len(tier_two), 1)
            tier_two[0].write_bytes(b"tampered synthetic custody\n")
            raise ROTATE.Refused("force-rollback-after-custody-tamper")
        def inspect(path, raw, *rest):
            restored.append(path.name)
            return actual_replace(path, raw, *rest)
        with mock.patch.object(ROTATE, "private_write", side_effect=remember), mock.patch.object(
                ROTATE, "fixture_go", side_effect=tamper), mock.patch.object(
                ROTATE, "replace_private", side_effect=inspect):
            result = self.refused(7, "force-rollback-after-custody-tamper")
        self.assertIs(result["rehearsal"]["rollback"], False)
        self.assertIn("unknown", result["rehearsal"]["rollback_status"])
        self.assertNotIn("destination.fixture", restored)

    def test_custody_root_privacy_is_rechecked_after_creation(self):
        actual = ROTATE.custody_verify
        def loosen(tiers, files, notice):
            tiers[1].chmod(0o755)
            return actual(tiers, files, notice)
        with mock.patch.object(ROTATE, "custody_verify", side_effect=loosen):
            self.refused(6)

    def test_custody_member_privacy_is_rechecked_after_creation(self):
        actual = ROTATE.custody_verify
        def loosen(tiers, files, notice):
            (tiers[1] / "destination.fixture").chmod(0o644)
            return actual(tiers, files, notice)
        with mock.patch.object(ROTATE, "custody_verify", side_effect=loosen):
            self.refused(6)

    def test_registry_switch_preserves_every_other_resident_row(self):
        actual = ROTATE.six_agreements
        expected = [row for row in self.identities if row["key"] != KEY]
        checked = []
        def inspect(args, notice, paths, plain):
            rows = json.loads(paths["registry"].read_bytes())["identities"]
            self.assertEqual([row for row in rows if row["key"] != KEY], expected)
            checked.append(True)
            return actual(args, notice, paths, plain)
        with mock.patch.object(ROTATE, "six_agreements", side_effect=inspect):
            self.assertEqual(self.invoke(7)[0], 0)
        self.assertEqual(checked, [True])

    def test_append_rechecks_the_six_agreements_after_a_new_wrong_title(self):
        self.append.append({"type": "custom-title", "sessionId": DESTINATION,
                            "cwd": str(self.room), "customTitle": "Wrong fixture title"})
        self.bind_operation()
        self.refused(8, "six-way-body-label")

    def test_eight_does_not_read_close_only_fields_or_write_a_receipt_or_unlink(self):
        for field in ("rotation", "deviations", "donor_preference"):
            del self.operation[field]
        self.bind_operation()
        actual = Path.unlink
        donor_unlinks = []
        def inspect(path, *args, **kwargs):
            if path.name == "donor.fixture" and path.parent.name == "runtime":
                donor_unlinks.append(path)
            return actual(path, *args, **kwargs)
        with mock.patch.object(ROTATE, "fixture_receipt", side_effect=AssertionError("phase 8 must stop")) as receipt, \
                mock.patch.object(Path, "unlink", inspect):
            rc, result = self.invoke(8)
        self.assertEqual((receipt.call_count, len(donor_unlinks)), (0, 0))
        self.assertEqual(rc, 0, result)
        self.assertEqual(result["completed"], list(range(9)))
        receipt.assert_not_called()
        self.assertEqual(donor_unlinks, [])
        self.assertNotIn("receipt", result["rehearsal"])
        self.assertNotIn("donor_store_removed", result["rehearsal"])

    def test_inputs_rechecked_before_close_prevent_receipt_and_donor_unlink(self):
        actual_append = ROTATE.append_proof
        actual_unlink = Path.unlink
        donor_unlinks = []
        def change(*args):
            value = actual_append(*args)
            self.save(self.pristine, "{}\n", text=True)
            return value
        def inspect(path, *args, **kwargs):
            if path.name == "donor.fixture" and path.parent.name == "runtime":
                donor_unlinks.append(path)
            return actual_unlink(path, *args, **kwargs)
        with mock.patch.object(ROTATE, "append_proof", side_effect=change), mock.patch.object(
                ROTATE, "fixture_receipt", wraps=ROTATE.fixture_receipt) as receipt, mock.patch.object(
                Path, "unlink", inspect):
            rc, result = self.invoke(9)
        self.assertEqual(rc, 2, result)
        self.assertEqual(result["reason"], "evidence-changed")
        self.assertEqual((receipt.call_count, len(donor_unlinks)), (0, 0))
        self.assertTrue(result["rehearsal"]["rollback"])
        receipt.assert_not_called()
        self.assertEqual(donor_unlinks, [])

    def test_served_at_equal_to_go_is_an_explicit_allowed_boundary(self):
        self.load["served_at"] = self.go["at"]
        self.bind_operation()
        self.assertEqual(self.invoke(8)[0], 0)

    def test_go_refusal_and_load_failure_restore_all_four_and_keep_hold(self):
        for phase, fail in ((7, "go"), (8, "load"), (8, "accept")):
            with self.subTest(fail=fail):
                self.go["word"] = "no" if fail == "go" else "go"
                self.load["loaded"] = fail != "load"
                self.accept["word"] = "no" if fail == "accept" else "recognize"
                self.bind_operation()
                actual = ROTATE.replace_private
                restored = []
                def capture(path, raw, *rest):
                    value = actual(path, raw, *rest)
                    restored.append((path.name, raw))
                    return value
                with mock.patch.object(ROTATE, "replace_private", side_effect=capture):
                    result = self.refused(phase)
                self.assertTrue(result["rehearsal"]["rollback"])
                self.assertTrue(result["rehearsal"]["hold"])
                for name in ("destination.fixture", "registry.json", "binding.json", "donor.fixture", "launcher.json"):
                    self.assertIn(name, [name for name, _ in restored[-5:]])
                final = dict(restored[-5:])
                self.assertEqual(final["destination.fixture"], (self.room / self.pristine).read_bytes())
                self.assertEqual(final["registry.json"], (self.room / self.registry).read_bytes())
                self.assertEqual(final["binding.json"], (self.room / "fixtures/binding.json").read_bytes())
                self.assertEqual(final["donor.fixture"], (self.room / self.donor).read_bytes())
                self.assertIs(json.loads(final["launcher.json"])["hold"], True)

    def test_each_install_step_failure_runs_bounded_rollback(self):
        for fail_at in range(2, 5):
            with self.subTest(step=fail_at):
                actual = ROTATE.replace_private
                calls = 0
                def fail(path, raw, *rest):
                    nonlocal calls
                    calls += 1
                    if calls == fail_at:
                        raise ROTATE.Refused("synthetic-step-failure")
                    return actual(path, raw, *rest)
                with mock.patch.object(ROTATE, "replace_private", side_effect=fail):
                    result = self.refused(7, "synthetic-step-failure")
                self.assertTrue(result["rehearsal"]["rollback"])

    def test_failure_after_publication_keeps_known_postimage_for_rollback(self):
        actual = ROTATE.replace_private
        calls = 0
        def after_publish(path, raw, *rest):
            nonlocal calls
            calls += 1
            value = actual(path, raw, *rest)
            if calls == 3:
                raise ROTATE.Refused("synthetic-after-publication")
            return value
        with mock.patch.object(ROTATE, "replace_private", side_effect=after_publish):
            result = self.refused(7, "synthetic-after-publication")
        self.assertTrue(result["rehearsal"]["rollback"])

    def test_interrupt_rolls_back_then_removes_own_staging(self):
        before = self.snapshot()
        with mock.patch.object(ROTATE, "six_agreements", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.invoke(7)
        self.assertEqual(before, self.snapshot())

    def test_both_custody_tiers_direct_reads_and_all_members(self):
        actual = ROTATE.custody_verify
        observed = []
        def inspect(tiers, files, notice):
            observed.append((len(tiers), set(files)))
            self.assertEqual(tiers[0].parent, tiers[1].parent)
            self.assertNotEqual(tiers[0], tiers[1])
            for tier in tiers:
                self.assertEqual(stat.S_IMODE(tier.stat().st_mode), 0o700)
            return actual(tiers, files, notice)
        with mock.patch.object(ROTATE, "custody_verify", side_effect=inspect):
            self.assertEqual(self.invoke(9)[0], 0)
        self.assertGreaterEqual(len(observed), 3)
        self.assertEqual(observed[0][0], 2)
        self.assertEqual(observed[0][1], {"donor.fixture", "destination.fixture", "successor.fixture", "capsule.txt",
                                        "gates.json", "registry.json", "binding.json", "launcher.json"})

    def test_registry_staging_and_canonical_postimage_preserve_f1(self):
        actual = ROTATE.private_write
        calls = []
        owner_arguments = []
        owner = (self.room / self.registry).stat()
        def inspect(path, raw, notice, owner_pair=None):
            result = actual(path, raw, notice, owner_pair)
            if path.name.startswith("registry.json"):
                node = path.lstat()
                owner_arguments.append(owner_pair)
                calls.append((node.st_uid, node.st_gid, stat.S_IMODE(node.st_mode), node.st_nlink))
            return result
        with mock.patch.object(ROTATE, "private_write", side_effect=inspect):
            self.assertEqual(self.invoke(8)[0], 0)
        self.assertGreaterEqual(len(calls), 3)
        self.assertEqual(owner_arguments[0], (owner.st_uid, owner.st_gid))
        self.assertTrue(all(v == (owner.st_uid, owner.st_gid, 0o600, 1) for v in calls))

    def test_canonical_registry_owner_rechecked_after_swap_dependency_returns(self):
        actual = ROTATE.replace_private
        lstat = Path.lstat
        armed = False
        def replace(path, *args):
            nonlocal armed
            result = actual(path, *args)
            if path.name == "registry.json":
                armed = True
            return result
        def metadata(path, *args, **kwargs):
            node = lstat(path, *args, **kwargs)
            if armed and path.name == "registry.json" and path.parent.name == "runtime":
                fields = {name: getattr(node, name) for name in (
                    "st_dev", "st_ino", "st_uid", "st_gid", "st_mode", "st_nlink", "st_size", "st_mtime_ns", "st_ctime_ns")}
                fields["st_gid"] += 1
                return types.SimpleNamespace(**fields)
            return node
        with mock.patch.object(ROTATE, "replace_private", side_effect=replace), mock.patch.object(Path, "lstat", metadata):
            self.refused(7, "canonical-registry-owner")

    def test_unsafe_registry_modes_links_and_hardlinks_refuse(self):
        path = self.room / self.registry
        path.chmod(0o664)
        self.refused(6)
        path.chmod(0o600)
        os.link(path, self.room / "registry-second.json")
        self.refused(6)

    def test_process_lists_must_be_observable_and_confined(self):
        for change, reason in (({"observable": False}, "process-model-unobservable"),
                               ({"schema": "other"}, "process-model-schema"),
                               ({"holders": None}, "process-model-lists"),
                               ({"session_records": None}, "process-model-lists"),
                               ({"holders": ["../outside.fixture"]}, "escaped-or-body-path")):
            with self.subTest(change=change):
                self.process = {"schema": "rotate-process/1", "observable": True, "holders": [],
                                "session_records": [], **change}
                self.bind_operation()
                self.refused(6, reason)

    def test_process_holder_on_spare_metadata_refuses_before_staging(self):
        self.process["holders"] = [self.spare]
        self.bind_operation()
        with mock.patch.object(ROTATE.tempfile, "TemporaryDirectory", side_effect=AssertionError("no staging")):
            self.refused(6, "synthetic-destination-held")

    def test_custody_inventory_manifest_and_each_tier_hash_are_checked(self):
        actual = ROTATE.custody_verify
        for tier_index, mode, reason in ((0, "extra", "custody-inventory"), (1, "manifest", "custody-manifest"),
                                         (0, "donor", "custody-file-hash"), (1, "successor", "custody-file-hash")):
            with self.subTest(tier=tier_index, mode=mode):
                def corrupt(tiers, files, notice):
                    tier = tiers[tier_index]
                    if mode == "extra":
                        path = tier / "extra"
                        path.write_bytes(b"invented")
                        path.chmod(0o600)
                    elif mode == "manifest":
                        (tier / "SHA256SUMS").write_bytes(b"wrong manifest\n")
                    else:
                        name = "donor.fixture" if mode == "donor" else "successor.fixture"
                        (tier / name).write_bytes(b"wrong fixture bytes\n")
                    return actual(tiers, files, notice)
                with mock.patch.object(ROTATE, "custody_verify", side_effect=corrupt):
                    self.refused(6, reason)

    def test_each_six_way_agreement_is_independently_enforced(self):
        actual = ROTATE.six_agreements
        for field in ("registry-id", "binding-id", "body-id", "root-cwd", "registry-room", "body-label"):
            with self.subTest(field=field):
                def corrupt(args, notice, paths, plain):
                    if field.startswith("registry"):
                        data = notice.decode(paths["registry"].read_bytes())
                        data["identities"][0]["session_id" if field == "registry-id" else "room"] = WRITER_SID
                        paths["registry"].write_bytes(ROTATE.json_bytes(data))
                    elif field in ("binding-id", "root-cwd"):
                        data = notice.decode(paths["binding"].read_bytes())
                        data["session_id" if field == "binding-id" else "root"] = WRITER_SID
                        paths["binding"].write_bytes(ROTATE.json_bytes(data))
                    else:
                        rows = [notice.decode(line) for line in paths["destination"].read_bytes().splitlines()]
                        if field == "body-id":
                            rows[0]["sessionId"] = WRITER_SID
                        else:
                            rows[-1]["agentName"] = "Another fixture label"
                        paths["destination"].write_bytes(b"".join(ROTATE.json_bytes(r) for r in rows))
                    return actual(args, notice, paths, plain)
                with mock.patch.object(ROTATE, "six_agreements", side_effect=corrupt):
                    self.refused(7, "six-way-" + field)

    def test_unterminated_join_and_ambiguous_registry_refuse(self):
        actual = ROTATE.six_agreements
        for failure in ("termination", "ambiguous"):
            with self.subTest(failure=failure):
                def corrupt(args, notice, paths, plain):
                    if failure == "termination":
                        paths["destination"].write_bytes(paths["destination"].read_bytes().rstrip(b"\n"))
                    else:
                        data = notice.decode(paths["registry"].read_bytes())
                        data["identities"].append(data["identities"][0])
                        paths["registry"].write_bytes(ROTATE.json_bytes(data))
                    return actual(args, notice, paths, plain)
                with mock.patch.object(ROTATE, "six_agreements", side_effect=corrupt):
                    self.refused(7, "join-body-termination" if failure == "termination" else "join-registry-ambiguous")

    def test_join_cwd_is_checked_in_body_independently_of_binding(self):
        actual = ROTATE.six_agreements
        def wrong_cwd(args, notice, paths, plain):
            rows = [notice.decode(line) for line in paths["destination"].read_bytes().splitlines()]
            rows[0]["cwd"] = str(self.base)
            paths["destination"].write_bytes(b"".join(ROTATE.json_bytes(row) for row in rows))
            return actual(args, notice, paths, plain)
        with mock.patch.object(ROTATE, "six_agreements", side_effect=wrong_cwd):
            self.refused(7, "six-way-root-cwd")

    def test_join_blank_row_refuses_strict_json(self):
        actual = ROTATE.six_agreements
        def empty(args, notice, paths, plain):
            paths["destination"].write_bytes(b"\n")
            return actual(args, notice, paths, plain)
        with mock.patch.object(ROTATE, "six_agreements", side_effect=empty):
            self.refused(7, "evidence-or-dependency-refused")

    def test_join_each_label_component_is_required(self):
        actual = ROTATE.six_agreements
        for kind, value in (("custom-title", None), ("agent-name", None), ("custom-title", "Wrong fixture title")):
            with self.subTest(kind=kind, value=value):
                def change(args, notice, paths, plain):
                    rows = [notice.decode(line) for line in paths["destination"].read_bytes().splitlines()]
                    if value is None:
                        rows = [row for row in rows if row.get("type") != kind]
                    else:
                        for row in rows:
                            if row.get("type") == kind:
                                row["customTitle"] = value
                    paths["destination"].write_bytes(b"".join(ROTATE.json_bytes(row) for row in rows))
                    return actual(args, notice, paths, plain)
                with mock.patch.object(ROTATE, "six_agreements", side_effect=change):
                    self.refused(7, "six-way-body-label")

    def test_append_is_terminated_identity_bound_and_hash_bound(self):
        self.append[0]["sessionId"] = SID
        self.bind_operation()
        self.refused(8, "synthetic-body-identity-mismatch")

    def test_append_tools_parents_and_message_uniqueness(self):
        original = copy.deepcopy(self.append)
        for change, reason in (
            ("duplicate", "append-duplicate-message"), ("parent", "append-parent-chain"),
            ("use", "append-unmatched-tools"), ("result", "append-tool-result"), ("use-twice", "append-tool-use")):
            with self.subTest(change=change):
                self.append = copy.deepcopy(original)
                if change == "duplicate":
                    self.append[1]["uuid"] = self.append[0]["uuid"]
                elif change == "parent":
                    self.append[0]["parentUuid"] = WRITER_SID
                else:
                    block = {"type": "tool_result", "tool_use_id": "fixture-call"} if change == "result" else {
                        "type": "tool_use", "id": "fixture-call"}
                    self.append[1]["message"]["content"] = [block, block] if change == "use-twice" else [block]
                self.bind_operation()
                self.refused(8, reason)

    def test_successful_tool_pair_in_fixture_append(self):
        self.append[0]["message"]["content"] = [{"type": "tool_use", "id": "fixture-call"}]
        self.append[1]["message"]["content"] = [{"type": "tool_result", "tool_use_id": "fixture-call"}]
        self.bind_operation()
        self.assertEqual(self.invoke(8)[0], 0)

    def test_append_nonstring_tool_identifier_is_not_a_valid_pair(self):
        self.append[0]["message"]["content"] = [{"type": "tool_use", "id": 17}]
        self.append[1]["message"]["content"] = [{"type": "tool_result", "tool_use_id": 17}]
        self.bind_operation()
        self.refused(8, "append-tool-use")

    def test_empty_append_cannot_imply_mechanical_acceptance(self):
        self.append = self.append[:1]
        self.bind_operation()
        self.refused(8, "append-first-reply-required")

    def test_append_reply_type_and_role_are_each_required(self):
        for field in ("type", "role"):
            with self.subTest(field=field):
                original = copy.deepcopy(self.append)
                if field == "type":
                    self.append[-1]["type"] = "metadata"
                else:
                    self.append[-1]["message"]["role"] = "user"
                self.bind_operation()
                self.refused(8, "append-first-reply-required")
                self.append = original

    def test_wake_is_extracted_not_taken_from_estimate(self):
        self.wake.update(tokens=20000, percent=2.0)
        self.bind_operation()
        self.refused(8, "wake-reading-mismatch")

    def test_wake_model_and_time_are_independently_bound_to_append(self):
        original = dict(self.wake)
        for changes in ({"model": "other-synthetic-model"}, {"reading_at": "2026-11-05T12:07:01Z",
                                                           "measured_at": "2026-11-05T12:07:01Z"}):
            with self.subTest(changes=changes):
                self.wake = {**original, **changes}
                self.bind_operation()
                self.refused(8, "wake-reading-mismatch")

    def test_readback_names_each_target_field_not_only_shape(self):
        original = dict(self.load["readback"])
        for field in ("key", "person", "room"):
            with self.subTest(field=field):
                self.load["readback"] = {**original, field: "wrong-fixture-value"}
                self.bind_operation()
                self.refused(8, "load-readback-mismatch")

    def test_binding_and_launcher_each_target_field_is_bound(self):
        for ref_key, fields, reason in (("binding_preimage", ("schema", "key", "session_id", "root", "provider"),
                                        "binding-preimage-mismatch"),
                                       ("launcher", ("schema", "key", "hold"), "launcher-preimage-mismatch")):
            path = self.operation[ref_key]["path"]
            original = (self.room / path).read_bytes()
            data = json.loads(original)
            for field in fields:
                with self.subTest(ref_key=ref_key, field=field):
                    self.save(path, {**data, field: "wrong-fixture-value"})
                    self.operation[ref_key] = self.ref(path)
                    self.bind_operation()
                    self.refused(6, reason)
            self.save(path, original.decode(), text=True)
            self.operation[ref_key] = self.ref(path)

    def test_post_reading_compaction_is_an_independent_refusal(self):
        real = ROTATE.sibling
        gauge = real("gauge")
        actual = gauge.read_claude
        def compacted(path):
            row = actual(path)
            if path.name == "destination.fixture":
                row["compaction_after"] = True
            return row
        gauge.read_claude = compacted
        with mock.patch.object(ROTATE, "sibling", side_effect=lambda name: gauge if name == "gauge" else real(name)):
            self.refused(8, "wake-reading-mismatch")

    def test_wake_before_serve_and_acceptance_before_wake_refuse(self):
        self.load["served_at"] = "2026-11-05T12:07:01Z"
        self.bind_operation()
        self.refused(8, "wake-reading-predates-load")
        self.load["served_at"] = "2026-11-05T12:06:30Z"
        self.accept["at"] = "2026-11-05T12:06:59Z"
        self.bind_operation()
        self.refused(8, "acceptance-predates-wake")

    def test_absent_donor_restored_only_after_verified_rollback_fixture_go(self):
        actual = ROTATE.six_agreements
        def remove(args, notice, paths, plain):
            paths["donor"].unlink()
            raise ROTATE.Refused("synthetic-donor-absent")
        with mock.patch.object(ROTATE, "six_agreements", side_effect=remove):
            result = self.refused(7, "synthetic-donor-absent")
        self.assertTrue(result["rehearsal"]["rollback"])

    def test_absent_donor_without_validated_rollback_go_is_not_restored(self):
        self.go["word"] = "no"
        self.bind_operation()
        actual = ROTATE.fixture_go
        def absent(*args):
            stage = next(self.room.glob(".rotate-build.*"))
            (stage / "runtime/donor.fixture").unlink()
            return actual(*args)
        with mock.patch.object(ROTATE, "fixture_go", side_effect=absent):
            result = self.refused(7, "replacement-declined")
        self.assertFalse(result["rehearsal"]["rollback"])
        self.assertTrue(result["rehearsal"]["hold"])

    def test_rollback_does_not_overwrite_unrecognized_concurrent_bytes(self):
        def concurrent(args, notice, paths, plain):
            paths["registry"].write_bytes(b"unrecognized concurrent fixture\n")
            raise ROTATE.Refused("synthetic-concurrent-write")
        with mock.patch.object(ROTATE, "six_agreements", side_effect=concurrent):
            result = self.refused(7, "synthetic-concurrent-write")
        self.assertFalse(result["rehearsal"]["rollback"])
        self.assertTrue(result["rehearsal"]["hold"])
        self.assertIn("unknown", result["rehearsal"]["rollback_status"])

    def test_each_phase_six_preimage_has_an_independent_guard(self):
        for reference, field, value, reason in (
            ("pristine", "cwd", "wrong-fixture-room", "pristine-room"),
            ("pristine", "customTitle", "Wrong spare label", "pristine-label"),
            ("binding_preimage", "session_id", WRITER_SID, "binding-preimage-mismatch"),
            ("launcher", "hold", True, "launcher-preimage-mismatch"),
            ("launcher", "hold", 0, "launcher-preimage-mismatch")):
            with self.subTest(reference=reference, field=field, value=value):
                ref = self.operation[reference]
                path = self.room / ref["path"]
                saved = path.read_bytes()
                value_object = json.loads(saved)
                value_object[field] = value
                self.save(ref["path"], json.dumps(value_object) + "\n", text=True)
                self.operation[reference] = self.ref(ref["path"])
                self.bind_operation()
                self.refused(6, reason)
                self.save(ref["path"], saved.decode(), text=True)
                self.operation[reference] = self.ref(ref["path"])

    def test_pristine_fixture_cannot_hide_work_behind_fresh_metadata(self):
        original = (self.room / self.pristine).read_text()
        for row in ({"type": "user", "sessionId": DESTINATION, "message": {"role": "user", "content": "Old fixture work"}},
                    {"type": "unclassified-work", "sessionId": DESTINATION},
                    {"type": "system", "sessionId": DESTINATION, "message": {"content": "Undeclared fixture work"}}):
            self.save(self.pristine, original + json.dumps(row) + "\n", text=True)
            self.operation["pristine"] = self.ref(self.pristine)
            self.bind_operation()
            self.refused(6, "pristine-not-empty")

    def test_donor_store_requires_fixture_extension_and_exact_bytes(self):
        self.save("fixtures/store.json", (self.room / self.donor).read_text(), text=True)
        self.operation["donor_store"] = self.ref("fixtures/store.json")
        self.bind_operation()
        self.refused(6, "donor-store-fixture-required")
        self.save("fixtures/other.fixture", "{}\n", text=True)
        self.operation["donor_store"] = self.ref("fixtures/other.fixture")
        self.bind_operation()
        self.refused(6, "donor-store-mismatch")

    def test_hold_is_read_back_before_custody(self):
        actual = ROTATE.replace_private
        def ignored(path, raw, notice, expected, *rest):
            if path.name == "launcher.json":
                return expected
            return actual(path, raw, notice, expected, *rest)
        with mock.patch.object(ROTATE, "replace_private", side_effect=ignored):
            self.refused(6, "synthetic-hold-unproved")

    def test_serve_release_is_read_back_before_append(self):
        actual = ROTATE.replace_private
        calls = 0
        def ignored_release(path, raw, notice, expected, *rest):
            nonlocal calls
            if path.name == "launcher.json":
                calls += 1
                if calls == 2:
                    return expected
            return actual(path, raw, notice, expected, *rest)
        with mock.patch.object(ROTATE, "replace_private", side_effect=ignored_release):
            self.refused(8, "serve-hold-not-released")

    def test_rollback_hold_is_read_back_and_not_inferred(self):
        actual = ROTATE.replace_private
        calls = 0
        def lost_hold(path, raw, notice, expected, *rest):
            nonlocal calls
            if path.name == "launcher.json":
                calls += 1
                if calls == 3:
                    return expected
            return actual(path, raw, notice, expected, *rest)
        self.load["loaded"] = False
        self.bind_operation()
        with mock.patch.object(ROTATE, "replace_private", side_effect=lost_hold):
            result = self.refused(8, "synthetic-load-failed")
        self.assertFalse(result["rehearsal"]["rollback"])
        self.assertIsNone(result["rehearsal"]["hold"])

    def test_destination_is_rechecked_against_verified_custody(self):
        actual = ROTATE.custody_verify
        calls = 0
        def change(tiers, files, notice):
            nonlocal calls
            value = actual(tiers, files, notice)
            calls += 1
            if calls == 2:
                (tiers[0].parent / "runtime/destination.fixture").write_bytes(b"changed fixture\n")
            return value
        with mock.patch.object(ROTATE, "custody_verify", side_effect=change):
            self.refused(7, "destination-custody-mismatch")

    def test_final_donor_identity_and_bytes_guard_prevents_wrong_unlink(self):
        actual = ROTATE.fixture_receipt
        for change in ("inode", "bytes"):
            with self.subTest(change=change):
                def moved(*args):
                    value = actual(*args)
                    stage = args[2]
                    path = stage / "runtime/donor.fixture"
                    raw = path.read_bytes()
                    if change == "inode":
                        path.unlink()
                        ROTATE.private_write(path, raw, ROTATE.sibling("notice"))
                    else:
                        path.write_bytes(b"changed donor fixture\n")
                    return value
                with mock.patch.object(ROTATE, "fixture_receipt", side_effect=moved):
                    self.refused(9, "donor-disposition-changed")

    def test_donor_hash_is_checked_independently_of_unchanged_metadata(self):
        actual = ROTATE.fixture_receipt
        read = Path.read_bytes
        armed = False
        def receipt(*args):
            nonlocal armed
            result = actual(*args)
            armed = True
            return result
        def changed_read(path):
            if armed and path.name == "donor.fixture" and path.parent.name == "runtime":
                return b"different synthetic bytes with an unchanged metadata model\n"
            return read(path)
        with mock.patch.object(ROTATE, "fixture_receipt", side_effect=receipt), mock.patch.object(Path, "read_bytes", changed_read):
            self.refused(9, "donor-disposition-changed")

    def test_close_unlinks_only_runtime_donor_after_verified_custody(self):
        actual = Path.unlink
        removed = []
        def unlink(path, *args, **kwargs):
            removed.append(path)
            self.assertEqual(path.name, "donor.fixture")
            self.assertEqual(path.parent.name, "runtime")
            self.assertTrue(path.is_relative_to(self.room))
            stage = path.parent.parent
            self.assertEqual(path.read_bytes(), (stage / "tier-2/donor.fixture").read_bytes())
            return actual(path, *args, **kwargs)
        with mock.patch.object(Path, "unlink", unlink):
            self.assertEqual(self.invoke(9)[0], 0)
        self.assertEqual(len(removed), 1)

    def test_receipt_failure_rolls_back_before_donor_disposition(self):
        with mock.patch.object(ROTATE, "fixture_receipt", side_effect=ROTATE.Refused("synthetic-receipt-failed")):
            result = self.refused(9, "synthetic-receipt-failed")
        self.assertTrue(result["rehearsal"]["rollback"])
        self.assertNotIn("donor_store_removed", result["rehearsal"])

    def test_receipt_generator_failure_and_empty_output_are_not_receipts(self):
        actual = self.invoke
        for rc, output in ((1, b"synthetic partial receipt"), (0, b"")):
            with self.subTest(rc=rc):
                out = io.StringIO()
                with contextlib.redirect_stdout(out), mock.patch("subprocess.run", return_value=types.SimpleNamespace(
                        returncode=rc, stdout=output, stderr=b"synthetic refusal")):
                    code = ROTATE.main(self.args(9))
                row = json.loads(out.getvalue())
                self.assertEqual(code, 2, row)
                self.assertEqual(row["reason"], "receipt-template-refused")
                self.assertTrue(row["rehearsal"]["rollback"])

    def test_no_staging_outside_fixture_even_when_output_is_redirected(self):
        actual = ROTATE.tempfile.TemporaryDirectory
        checked = []
        def confined(*args, **kwargs):
            self.assertEqual(Path(kwargs["dir"]), self.room)
            checked.append(True)
            return actual(*args, **kwargs)
        with mock.patch.object(ROTATE.tempfile, "TemporaryDirectory", side_effect=confined):
            rc, result = self.invoke(9)
        self.assertEqual(checked, [True])
        self.assertEqual(rc, 0, result)

    def test_source_destination_bytes_cannot_change_after_custody(self):
        actual = ROTATE.fixture_go
        actual_replace = ROTATE.replace_private
        destination_swaps = []
        pristine_before = (self.room / self.pristine).read_bytes()
        def change(*args):
            value = actual(*args)
            self.save(self.pristine, "{}\n", text=True)
            return value
        def inspect(path, raw, *rest):
            if path.name == "destination.fixture":
                destination_swaps.append(raw)
            return actual_replace(path, raw, *rest)
        with mock.patch.object(ROTATE, "fixture_go", side_effect=change), mock.patch.object(
                ROTATE, "replace_private", side_effect=inspect):
            rc, result = self.invoke(7)
        self.assertEqual(rc, 2)
        self.assertEqual(result["reason"], "evidence-changed")
        self.assertTrue(result["rehearsal"]["rollback"])
        self.assertEqual(destination_swaps, [pristine_before])


class PrivateSwapTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=TOOL.parents[3] / "var/tmp")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.base.chmod(0o700)
        self.notice = ROTATE.sibling("notice")
        self.path = self.base / "registry.json"
        ROTATE.private_write(self.path, b"original fixture\n", self.notice)

    def state(self):
        return ROTATE.node_id(self.path.lstat()), ROTATE.digest(self.path.read_bytes())

    def reason(self, reason, function):
        with self.assertRaisesRegex(ROTATE.Refused, "^" + reason + "$"):
            function()

    def test_exclusive_staging_refuses_existing_node_by_name(self):
        self.reason("staged-target-exists", lambda: ROTATE.private_write(self.path, b"new", self.notice))

    def test_exclusive_staging_refuses_dangling_link_by_name(self):
        path = self.base / "linked-stage"
        path.symlink_to(self.base / "absent")
        self.reason("staged-target-exists", lambda: ROTATE.private_write(path, b"new", self.notice))

    def test_explicit_mode_survives_open_umask(self):
        old = os.umask(0)
        try:
            ROTATE.replace_private(self.path, b"new fixture\n", self.notice, self.state())
            self.assertEqual(stat.S_IMODE(self.path.stat().st_mode), 0o600)
        finally:
            os.umask(old)

    def test_staged_hash_is_read_back(self):
        path = self.base / "stage.json"
        with mock.patch.object(Path, "read_bytes", return_value=b"not the staged bytes"):
            self.reason("staged-hash-mismatch", lambda: ROTATE.private_write(path, b"new", self.notice))

    def test_staged_owner_is_checked_after_explicit_mode_and_owner(self):
        path = self.base / "stage.json"
        with mock.patch.object(os, "fchown", return_value=None):
            self.reason("staged-ownership-mismatch", lambda: ROTATE.private_write(
                path, b"new", self.notice, (os.geteuid() + 1, os.getegid())))

    def test_swap_rejects_stale_inode_fingerprint(self):
        expected = self.state()
        self.path.unlink()
        ROTATE.private_write(self.path, b"original fixture\n", self.notice)
        self.reason("swap-preimage-identity", lambda: ROTATE.replace_private(self.path, b"new", self.notice, expected))

    def test_swap_rejects_hash_with_current_metadata(self):
        expected = (self.state()[0], "f" * 64)
        self.reason("swap-preimage-hash", lambda: ROTATE.replace_private(self.path, b"new", self.notice, expected))

    def test_swap_rechecks_after_staging_before_rename(self):
        expected = self.state()
        actual = ROTATE.private_write
        def race(*args):
            value = actual(*args)
            self.path.write_bytes(b"newer concurrent fixture\n")
            return value
        with mock.patch.object(ROTATE, "private_write", side_effect=race):
            self.reason("swap-preimage-changed", lambda: ROTATE.replace_private(self.path, b"new", self.notice, expected))
        self.assertEqual(self.path.read_bytes(), b"newer concurrent fixture\n")

    def test_swap_proves_published_inode_even_when_bytes_match(self):
        expected = self.state()
        with mock.patch.object(os, "replace", return_value=None):
            self.reason("swap-postimage-identity", lambda: ROTATE.replace_private(
                self.path, b"original fixture\n", self.notice, expected))

    def test_swap_proves_published_hash(self):
        expected = self.state()
        published = []
        actual = os.replace
        def corrupt(source, target):
            actual(source, target)
            target.write_bytes(b"corrupt published fixture\n")
        with mock.patch.object(os, "replace", side_effect=corrupt):
            self.reason("swap-postimage-hash", lambda: ROTATE.replace_private(
                self.path, b"new", self.notice, expected, published.append))
        self.assertEqual(published, [], "A failed postimage must not become rollback authority")

    def test_swap_proves_postimage_ownership_not_only_inode(self):
        expected = self.state()
        published = []
        actual = self.notice.private_node
        target_reads = 0
        def changed_owner(path, *rest):
            nonlocal target_reads
            node = actual(path, *rest)
            if path == self.path:
                target_reads += 1
                if target_reads == 3:
                    fields = {name: getattr(node, name) for name in (
                        "st_dev", "st_ino", "st_uid", "st_gid", "st_mode", "st_nlink", "st_size", "st_mtime_ns", "st_ctime_ns")}
                    fields["st_gid"] += 1
                    return types.SimpleNamespace(**fields)
            return node
        with mock.patch.object(self.notice, "private_node", side_effect=changed_owner):
            self.reason("swap-postimage-ownership", lambda: ROTATE.replace_private(
                self.path, b"new", self.notice, expected, published.append))
        self.assertEqual(published, [], "Unaccepted ownership must not become rollback authority")

    def test_swap_never_follows_a_link_or_accepts_extra_link(self):
        expected = self.state()
        os.link(self.path, self.base / "extra.json")
        with self.assertRaises(Exception):
            ROTATE.replace_private(self.path, b"new", self.notice, expected)
        self.path.unlink()
        self.path.symlink_to(self.base / "extra.json")
        with self.assertRaises(Exception):
            ROTATE.replace_private(self.path, b"new", self.notice, expected)


def bad_fixture_case(attribute, field, value, phase, reason):
    def test(self):
        getattr(self, attribute)[field] = value(self) if callable(value) else value
        self.bind_operation()
        self.refused(phase, reason)
    return test


for name, attribute, field, value, phase, reason in (
    ("operation_schema", "operation", "schema", "other", 6, "operation-plan-mismatch"),
    ("operation_key", "operation", "key", WRITER, 6, "operation-plan-mismatch"),
    ("operation_writer", "operation", "writer", KEY, 6, "operation-plan-mismatch"),
    ("operation_binding", "operation", "binding", "f" * 64, 6, "operation-plan-mismatch"),
    ("operation_build", "operation", "build_sha256", "f" * 64, 6, "operation-plan-mismatch"),
    ("custody_time", "operation", "custody_at", "2026-11-05T12:03:59Z", 6, "custody-predates-build"),
    ("go_schema", "go", "schema", "other", 7, "replacement-go-mismatch"),
    ("go_key", "go", "key", WRITER, 7, "replacement-go-mismatch"),
    ("go_writer", "go", "writer", KEY, 7, "replacement-go-mismatch"),
    ("go_container", "go", "container", WRITER_SID, 7, "replacement-go-mismatch"),
    ("go_room", "go", "room", "unrelated-fixture", 7, "replacement-go-mismatch"),
    ("go_size", "go", "size", 1, 7, "replacement-go-mismatch"),
    ("go_hash", "go", "custody_sha256", "f" * 64, 7, "replacement-go-mismatch"),
    ("go_rollback", "go", "rollback", "none", 7, "replacement-go-mismatch"),
    ("go_early_phase", "go", "after_phase", 0, 7, "replacement-go-mismatch"),
    ("go_early_time", "go", "at", "2026-11-05T12:05:00Z", 7, "replacement-go-predates-custody"),
    ("go_float_size", "go", "size", lambda s: float(s.go["size"]), 7, "replacement-go-types"),
    ("go_float_phase", "go", "after_phase", 6.0, 7, "replacement-go-types"),
    ("load_schema", "load", "schema", "other", 8, "load-schema"),
    ("load_failure", "load", "loaded", False, 8, "synthetic-load-failed"),
    ("load_key", "load", "key", WRITER, 8, "load-target-mismatch"),
    ("load_container", "load", "container", WRITER_SID, 8, "load-target-mismatch"),
    ("load_before_go", "load", "served_at", "2026-11-05T12:05:59Z", 8, "load-predates-go"),
    ("load_readback", "load", "readback", {}, 8, "load-readback-mismatch"),
    ("mind_unconfirmed", "load", "mind_confirmed", False, 8, "mind-confirmation-required"),
    ("accept_schema", "accept", "schema", "other", 8, "operator-fixture-acceptance-required"),
    ("accept_key", "accept", "key", WRITER, 8, "operator-fixture-acceptance-required"),
    ("accept_container", "accept", "container", WRITER_SID, 8, "operator-fixture-acceptance-required"),
    ("accept_word", "accept", "word", "status-only", 8, "operator-fixture-acceptance-required"),
    ("rotation_bool", "operation", "rotation", True, 9, "rotation-number-required"),
    ("rotation_zero", "operation", "rotation", 0, 9, "rotation-number-required"),
    ("deviations_bool", "operation", "deviations", True, 9, "deviations-count-required"),
    ("deviations_negative", "operation", "deviations", -1, 9, "deviations-count-required"),
    ("donor_preference", "operation", "donor_preference", "unspecified", 9, "donor-preference-required"),
):
    setattr(InstallPhases, "test_s3_" + name, bad_fixture_case(attribute, field, value, phase, reason))


if __name__ == "__main__":
    unittest.main()
