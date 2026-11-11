#!/usr/bin/env python3
"""Synthetic rotation phase gates. No native body, provider or live record.

Generated with ops/bin/template; implemented by Joe Codex. Run with -I -B
under umask 0002, 0022 and 0077. Fixture minds contain invented leaves only.
"""
import contextlib
import copy
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
import time
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
                       "mind": {"index_sha256": self.index_sha}}
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

    def add_leaf(self, title, now="2026-11-05T11:00:00Z", agent=KEY):
        """One invented leaf, written by the mind tool itself, so its index and ledger are real."""
        body = self.base / "leaf-body.md"
        body.write_text("Check the exact target before choosing a recovery action.\n", encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            rc = ROTATE.sibling("mind").main(["--room", str(self.room), "--registry", str(self.room / self.registry),
                                              "--now", now, "add", "--agent", agent, "--title", title,
                                              "--body", str(body)])
        self.assertEqual(rc, 0)
        self.index_sha = self.sha("MIND.md")

    def make_mind(self):
        self.add_leaf("Check the target before recovery")
        self.leaf = "archives/mind/MIND-2026-11-05-001.md"
        self.leaf_sha = self.sha(self.leaf)

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

    def test_phase_two_calls_actual_mind_check_and_stops(self):
        before = self.snapshot()
        rc, result = self.invoke(2)
        self.assertEqual(rc, 0, result)
        self.assertEqual(result["completed"], [0, 1, 2])
        self.assertEqual(result["next_phase"], 3)
        self.assertEqual(result["mind"], {"index_sha256": self.index_sha, "own_leaves": 1})
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

    def test_closing_record_must_name_the_index_it_closed_with(self):
        for mind in (None, {}, {"index_sha256": "abc"}, {"index_sha256": 7},
                     {"index_sha256": self.index_sha, "proposed": 0},
                     {"proposed": 0, "decision": "none-proposed", "leaf_sha256": self.index_sha}):
            with self.subTest(mind=mind):
                self.record["mind"] = mind
                self.save(self.closed, self.record)
                self.refused(1, reason="mind-index-unproved")

    def test_a_room_with_no_mind_closes_with_null(self):
        for rel in ("MIND.md", "logs/mind/ledger.jsonl", self.leaf):
            (self.room / rel).unlink()
        self.record["mind"] = {"index_sha256": None}
        self.save(self.closed, self.record)
        rc, result = self.invoke(2)
        self.assertEqual(rc, 0, result)
        self.assertEqual(result["mind"], {"index_sha256": None, "own_leaves": 0})

    def test_a_leaf_written_after_closing_is_caught(self):
        self.add_leaf("A second invented idea", now="2026-11-05T12:03:00Z")
        self.refused(2, reason="closing-mind-mismatch")
        self.record["mind"]["index_sha256"] = self.index_sha
        self.save(self.closed, self.record)
        rc, result = self.invoke(2)
        self.assertEqual(rc, 0, result)
        self.assertEqual(result["mind"]["own_leaves"], 2)

    def test_missing_mind_is_not_waived(self):
        (self.room / "MIND.md").unlink()
        self.refused(2)

    def test_mind_check_failure_is_not_waived(self):
        self.save(self.leaf, "not a mind\n", text=True)
        self.refused(2, reason="mind-check-refused")

    def test_a_retired_format_index_is_not_waived(self):
        self.save("MIND.md", "resident=" + KEY + "|leaf=archives/MIND-x.md|sha256=" + "0" * 64 + "\n", text=True)
        self.refused(2, reason="mind-check-refused")

    def test_closing_mind_must_be_the_checked_mind(self):
        self.record["mind"]["index_sha256"] = "0" * 64
        self.save(self.closed, self.record)
        result = self.refused(2, reason="closing-mind-mismatch")
        self.assertNotIn("mind", result)

    def test_mind_check_failures_are_honored_and_not_echoed(self):
        real = ROTATE.sibling
        mind = real("mind")
        fake = types.SimpleNamespace(parse_index=mind.parse_index, read_registry=mind.read_registry,
                                     verify=lambda room, reg: ([("FAIL", "leaf", SECRET)], ["leaf: " + SECRET]))
        with mock.patch.object(ROTATE, "sibling", side_effect=lambda name: fake if name == "mind" else real(name)):
            result = self.refused(2, reason="mind-check-refused")
        self.assertNotIn(SECRET, json.dumps(result))

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
    add_leaf = RotateTests.add_leaf
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
        self.save("fixtures/transition.md", "archives/mind/fixture.md", text=True)
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

    def test_c1_capsule_mind_is_the_residents_own_index_lines(self):
        self.add_leaf("An idea of the writer's", agent=WRITER, now="2026-11-05T11:30:00Z")
        self.record["mind"]["index_sha256"] = self.index_sha
        self.save(self.closed, self.record)
        self.bind_plan()
        mind = ROTATE.sibling("mind")
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            rc = mind.main(["--room", str(self.room), "--registry", str(self.room / self.registry),
                            "show", "--agent", KEY])
        self.assertEqual(rc, 0)
        own = out.getvalue()
        self.assertEqual(own.count("\n"), 1)
        leaf_body = (self.room / self.leaf).read_text(encoding="utf-8").split("---\n\n", 1)[1]
        actual = ROTATE.static_gates
        observed = []
        def inspect(raw, rows, args, evidence, capsule, *rest):
            before, marker, after = capsule.partition("\n\nMind\n")
            mind_text, transition, tail = after.partition("\nTransition\n")
            self.assertTrue(before.startswith("Registry\n"))
            self.assertTrue(marker and transition)
            self.assertEqual(mind_text, own + ROTATE.MIND_HINT)
            self.assertNotIn(leaf_body.strip(), capsule)
            self.assertNotIn(WRITER + " \u2014", capsule)
            self.assertTrue(tail)
            observed.append(own)
            return actual(raw, rows, args, evidence, capsule, *rest)
        with mock.patch.object(ROTATE, "static_gates", side_effect=inspect):
            self.assertEqual(self.invoke(5)[0], 0)
        self.assertEqual(observed, [own])

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
    add_leaf = RotateTests.add_leaf
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
                      "Mind index", "Install", "Wake estimate against the measured wake", "Deviations", "Acceptance", "Rollback"):
            self.assertIn("## " + title, text)
        for item in ("18000/1000000", "20000 estimated", self.index_sha, "2026-11-05T12:08:00Z", "Synthetic"):
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


class ClaudeAdapterTests(unittest.TestCase):
    save = RotateTests.save
    sha = RotateTests.sha
    ref = RotateTests.ref
    make_mind = RotateTests.make_mind
    add_leaf = RotateTests.add_leaf
    snapshot = RotateTests.snapshot
    invoke = RotateTests.invoke
    refused = BuildPhases.refused
    write_body = BuildPhases.write_body
    bind_plan = BuildPhases.bind_plan

    def setUp(self):
        BuildPhases.setUp(self)
        self.adapter_path = "fixtures/adapter.json"
        self.process_path = "fixtures/adapter-process.json"
        self.pristine = "fixtures/adapter-pristine.fixture"
        self.compaction_path = "fixtures/compaction.json"
        self.after_path = "fixtures/after-gauge.json"
        self.save(self.process_path, {"schema": "rotate-process/1", "observable": True,
                                      "holders": [], "session_records": []})
        uid = "0000f101-0000-4000-8000-00000000f101"
        self.pristine_rows = [
            {"type": "custom-title", "customTitle": self.spare_row["label"]},
            {"type": "user", "uuid": uid, "parentUuid": None,
             "timestamp": "2026-11-05T12:03:01Z",
             "message": {"role": "user", "content": ROTATE.FIRST_PROMPT}},
            {"type": "assistant", "uuid": "0000f102-0000-4000-8000-00000000f102",
             "parentUuid": uid, "timestamp": "2026-11-05T12:03:02Z",
             "message": {"role": "assistant", "content": "READY"}},
        ]
        for r in self.pristine_rows:
            r.update(sessionId=DESTINATION, cwd=str(self.room))
        self.save_pristine()
        self.after = {**self.row, "tokens": 18000, "percent": 1.8,
                      "reading_at": "2026-11-05T12:01:00Z", "measured_at": "2026-11-05T12:01:01Z",
                      "age_seconds": 1}
        self.save(self.after_path, self.after)
        self.compaction = {"schema": "rotate-compaction-fixture/1", "actor": "operator",
                           "method": "supported-interface", "at": "2026-11-05T12:00:10Z",
                           "before_gauge_sha256": self.sha(self.gauge), "after_gauge": self.ref(self.after_path)}
        self.rows[1]["timestamp"] = self.compaction["at"]
        self.rows[2]["timestamp"] = "2026-11-05T12:00:11Z"
        self.rows[5]["timestamp"] = "2026-11-05T12:00:30Z"
        self.rows[6]["timestamp"] = self.after["reading_at"]
        self.rows[6]["message"]["usage"]["input_tokens"] = self.after["tokens"]
        self.write_body()
        self.bind_plan()
        self.save(self.compaction_path, self.compaction)
        self.adapter = {"schema": "rotate-claude-adapter/1", "kind": "registered-fixture",
                        "key": KEY, "writer": WRITER, "binding": self.record["binding"],
                        "gauge_sha256": self.sha(self.gauge), "closeout_sha256": self.sha(self.state),
                        "destination_sha256": hashlib.sha256(DESTINATION.encode()).hexdigest(),
                        "provider_version": "invented-cli-version", "process_model": self.ref(self.process_path),
                        "pristine": self.ref(self.pristine),
                        "destination_metadata": self.ref(self.spare), "compaction": self.ref(self.compaction_path)}
        self.save_adapter()

    def args(self, phase=0):
        return BuildPhases.args(self, phase) + ["--adapter", "claude", "--adapter-plan", self.adapter_path]

    def save_adapter(self):
        self.save(self.adapter_path, self.adapter)

    def save_pristine(self):
        self.save(self.pristine, "".join(json.dumps(r) + "\n" for r in self.pristine_rows), text=True)

    def bind_compaction(self):
        self.save(self.after_path, self.after)
        self.compaction["after_gauge"] = self.ref(self.after_path)
        self.save(self.compaction_path, self.compaction)
        self.adapter["compaction"] = self.ref(self.compaction_path)
        self.save_adapter()

    def bad_pristine(self, change, reason):
        change(self.pristine_rows)
        self.save_pristine()
        self.adapter["pristine"] = self.ref(self.pristine)
        self.save_adapter()
        self.refused(3, reason)

    def test_each_preparation_phase_stops_and_preserves_inputs(self):
        for phase in range(6):
            with self.subTest(phase=phase):
                before = self.snapshot()
                rc, result = self.invoke(phase)
                self.assertEqual(rc, 0, result)
                self.assertEqual(result["completed"], list(range(phase + 1)))
                self.assertFalse(result["adapter"]["native_actions_implemented"])
                self.assertFalse(result["native_load_proved"])
                self.assertEqual(self.snapshot(), before)
        self.assertEqual(result["build"]["media_files"], 0)
        self.assertTrue(all(result["build"]["gates"].values()))

    def test_later_inputs_absent_are_not_read_at_earlier_stops(self):
        for name, phase in ((self.pristine, 2), (self.compaction_path, 3)):
            with self.subTest(name=name):
                path = self.room / name
                raw = path.read_bytes()
                path.unlink()
                rc, result = self.invoke(phase)
                self.assertEqual(rc, 0, result)
                path.write_bytes(raw)
                path.chmod(0o600)

    def test_missing_adapter_plan_refuses(self):
        (self.room / self.adapter_path).unlink()
        self.refused(0)

    def test_version_requires_a_bounded_nonblank_string(self):
        for value in (None, 123, "", "  ", "x" * 65):
            with self.subTest(value=value):
                self.adapter["provider_version"] = value
                self.save_adapter()
                self.refused(0, "claude-provider-version-required")

    def test_codex_row_never_uses_the_claude_contract(self):
        with self.assertRaisesRegex(ROTATE.Refused, "claude-adapter-provider-required"):
            ROTATE.claude_contract(types.SimpleNamespace(), None, {"provider": "codex"}, None, None)

    def test_any_holder_blocks_preparation_without_proc_read(self):
        self.save(self.process_path, {"schema": "rotate-process/1", "observable": True,
                                      "holders": [self.pristine], "session_records": []})
        self.adapter["process_model"] = self.ref(self.process_path)
        self.save_adapter()
        with mock.patch.object(ROTATE, "no_fixture_holders", side_effect=AssertionError("no host proc")):
            self.refused(0, "claude-writers-not-closed")

    def test_nonobservable_process_model_refuses(self):
        self.save(self.process_path, {"schema": "rotate-process/1", "observable": False,
                                      "holders": [], "session_records": []})
        self.adapter["process_model"] = self.ref(self.process_path)
        self.save_adapter()
        self.refused(0, "process-model-unobservable")

    def test_pristine_hash_is_checked(self):
        self.save(self.pristine, "changed\n", text=True)
        self.refused(3, "evidence-hash-mismatch")

    def test_destination_metadata_is_the_same_bound_preimage(self):
        self.adapter["destination_metadata"] = self.ref(self.process_path)
        self.save_adapter()
        self.refused(3, "claude-destination-metadata-mismatch")

    def test_first_exchange_has_exactly_three_rows(self):
        self.bad_pristine(lambda rows: rows.append(copy.deepcopy(rows[-1])), "claude-first-exchange-required")

    def test_first_exchange_has_the_exact_room(self):
        self.bad_pristine(lambda rows: rows[1].update(cwd="invented-other-room"), "claude-first-exchange-room")

    def test_first_exchange_has_the_spare_label(self):
        self.bad_pristine(lambda rows: rows[0].update(customTitle="Other fixture"), "claude-first-exchange-label")

    def test_first_prompt_is_inert_and_plain(self):
        self.bad_pristine(lambda rows: rows[1]["message"].update(content="Run a tool"), "claude-first-prompt-not-inert")

    def test_first_reply_is_inert_and_plain(self):
        self.bad_pristine(lambda rows: rows[2]["message"].update(content="Not ready"), "claude-first-reply-not-inert")

    def test_first_prompt_requires_an_identifier(self):
        self.bad_pristine(lambda rows: rows[1].pop("uuid"), "claude-first-prompt-chain")

    def test_first_prompt_has_no_parent(self):
        self.bad_pristine(lambda rows: rows[1].update(parentUuid=SID), "claude-first-prompt-chain")

    def test_first_reply_requires_an_identifier(self):
        self.bad_pristine(lambda rows: rows[2].pop("uuid"), "claude-first-reply-chain")

    def test_first_reply_has_a_distinct_identifier(self):
        self.bad_pristine(lambda rows: rows[2].update(uuid=rows[1]["uuid"]), "claude-first-reply-chain")

    def test_first_reply_points_to_the_first_prompt(self):
        self.bad_pristine(lambda rows: rows[2].update(parentUuid=None), "claude-first-reply-chain")

    def test_first_exchange_cannot_predate_creation(self):
        self.bad_pristine(lambda rows: rows[1].update(timestamp="2026-11-05T12:02:59Z"), "claude-first-exchange-time")

    def test_first_reply_cannot_predate_its_prompt(self):
        self.bad_pristine(lambda rows: rows[2].update(timestamp="2026-11-05T12:03:00Z"), "claude-first-exchange-time")

    def test_first_reply_cannot_follow_the_build_clock(self):
        self.bad_pristine(lambda rows: rows[2].update(timestamp="2026-11-05T12:04:01Z"), "claude-first-exchange-time")

    def test_compaction_after_the_initial_due_reading_is_allowed(self):
        rc, result = self.invoke(4)
        self.assertEqual(rc, 0, result)
        self.assertEqual(result["measurement"]["tokens"], 700000)
        self.assertEqual(result["window"]["summary"], 2)
        self.assertNotEqual(self.after["tokens"], self.row["tokens"])

    def test_compaction_must_follow_the_phase_zero_reading(self):
        self.compaction["at"] = self.row["reading_at"]
        self.bind_compaction()
        self.refused(4, "claude-compaction-outside-closing-seam")

    def test_compaction_must_precede_quiescence(self):
        self.compaction["at"] = self.record["closed_at"]
        self.bind_compaction()
        self.refused(4, "claude-compaction-outside-closing-seam")

    def test_post_compaction_window_is_the_same_measured_model_window(self):
        self.after["window"] *= 2
        self.after["percent"] /= 2
        self.bind_compaction()
        self.refused(4, "claude-post-compaction-window")

    def test_post_compaction_provider_is_checked_independently(self):
        real_window = ROTATE.claude_window
        def changed_provider(args, evidence, *rest):
            real_measurement = evidence.notice.measurement
            def changed(*values):
                row, band, binding = real_measurement(*values)
                return {**row, "provider": "codex"}, band, binding
            with mock.patch.object(evidence.notice, "measurement", side_effect=changed):
                return real_window(args, evidence, *rest)
        with mock.patch.object(ROTATE, "claude_window", side_effect=changed_provider):
            self.refused(4, "claude-post-compaction-provider")

    def test_post_compaction_reading_cannot_precede_compaction(self):
        self.after["reading_at"] = self.row["reading_at"]
        self.after["measured_at"] = self.after["reading_at"]
        self.after["age_seconds"] = 0
        self.bind_compaction()
        self.refused(4, "claude-post-compaction-reading-time")

    def test_post_compaction_reading_cannot_follow_quiescence(self):
        self.after["reading_at"] = "2026-11-05T12:02:01Z"
        self.after["measured_at"] = self.after["reading_at"]
        self.after["age_seconds"] = 0
        self.bind_compaction()
        self.refused(4, "claude-post-compaction-reading-time")

    def test_actual_boundary_binds_the_compaction_time(self):
        self.rows[1]["timestamp"] = "2026-11-05T12:00:09Z"
        self.write_body()
        self.bind_plan()
        self.refused(4, "claude-compaction-boundary-time")

    def test_summary_cannot_predate_compaction(self):
        self.rows[2]["timestamp"] = "2026-11-05T12:00:09Z"
        self.write_body()
        self.bind_plan()
        self.refused(4, "claude-summary-time")

    def test_summary_cannot_follow_the_selected_prompt(self):
        self.rows[2]["timestamp"] = "2026-11-05T12:00:31Z"
        self.write_body()
        self.bind_plan()
        self.refused(4, "claude-summary-time")

    def test_late_adapter_input_change_prevents_build(self):
        real = ROTATE.claude_window
        def change(*args):
            result = real(*args)
            self.adapter["provider_version"] = "changed"
            self.save_adapter()
            return result
        before = self.snapshot()
        with mock.patch.object(ROTATE, "claude_window", side_effect=change):
            rc, result = self.invoke(5)
        self.assertEqual(rc, 2, result)
        self.assertEqual(result["reason"], "evidence-changed")
        self.assertNotIn("build", result)
        after = self.snapshot()
        # The deliberately concurrent input edit survives; nothing else changes.
        before.pop(self.adapter_path)
        after.pop(self.adapter_path)
        self.assertEqual(before, after)
        self.assertEqual(json.loads((self.room / self.adapter_path).read_text())["provider_version"], "changed")

    def test_every_native_action_refuses_before_any_evidence_read(self):
        actions = {"disposable-exercise": "named-disposable-exercise-go-required",
                   "compact": "operator-compaction-only", "rotation": "named-resident-rotation-go-required",
                   "hold": "named-native-hold-go-required", "custody": "named-native-custody-go-required",
                   "install": "post-custody-replacement-go-required", "load": "named-native-load-go-required",
                   "rollback": "named-native-rollback-go-required", "donor-disposition": "named-donor-disposition-go-required"}
        for action, reason in actions.items():
            with self.subTest(action=action), mock.patch.object(ROTATE, "Evidence", side_effect=AssertionError("no read")):
                rc, result = self.invoke(0, ("--native-action", action))
                self.assertEqual(rc, 2)
                self.assertEqual(result["reason"], reason + "-native-unimplemented")
                self.assertEqual(result["writes"], 0)

    def test_codex_adapter_refuses_before_any_evidence_read(self):
        with mock.patch.object(ROTATE, "Evidence", side_effect=AssertionError("no read")):
            rc, result = self.invoke(0, ("--adapter", "codex"))
        self.assertEqual(rc, 2)
        self.assertEqual(result["reason"], "codex-summary-active-window-and-loader-proof-required")

    def test_native_phases_refuse_before_staging_or_evidence_read(self):
        reasons = {6: "named-native-custody-go-required", 7: "post-custody-replacement-go-required",
                   8: "named-native-load-go-required", 9: "named-donor-disposition-go-required"}
        for phase, reason in reasons.items():
            with self.subTest(phase=phase), mock.patch.object(ROTATE, "Evidence", side_effect=AssertionError("no read")):
                self.refused(phase, reason + "-native-unimplemented")


def bad_adapter_field(attribute, field, phase, reason):
    def test(self):
        getattr(self, attribute)[field] = "wrong-fixture-value"
        if attribute == "adapter":
            self.save_adapter()
        else:
            self.bind_compaction()
        self.refused(phase, reason)
    return test


for field in ("schema", "kind", "key", "writer", "binding", "gauge_sha256", "closeout_sha256", "destination_sha256"):
    setattr(ClaudeAdapterTests, "test_header_" + field,
            bad_adapter_field("adapter", field, 0, "claude-adapter-" + field.replace("_", "-") + "-mismatch"))
for attribute, fields, phase, prefix in (
    ("compaction", ("schema", "actor", "method", "before_gauge_sha256"), 4, "claude-compaction-"),
):
    for field in fields:
        setattr(ClaudeAdapterTests, "test_" + attribute + "_" + field,
                bad_adapter_field(attribute, field, phase, prefix + field + "-mismatch"))


class NativeDisposableTests(unittest.TestCase):
    """Forward-contract fixtures only; the parent runs these behind masked2.

    The Git exposure reader is an explicit synthetic dependency. Its refusing
    result is tested below; no real Git command, provider or process is run.
    Physical devices are also modeled, not inferred from the host fixture disk.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=TOOL.parents[3] / "var/tmp")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.base.chmod(0o700)
        # Separate parents let strict custody-ancestor tests overlap exactly
        # one selected path, rather than concealing an omitted path check.
        self.room, self.project, self.store = [self.base / (p + "-parent") / p
                                               for p in ("room", "project", "store")]
        self.records_dir = self.base / "records"
        self.operation = "fixture-native"
        self.case = self.room / "storage/active" / self.operation
        self.roots = [self.base / "custody-one", self.base / "custody-two"]
        for path in [self.room, self.project, self.store, self.records_dir, *self.roots]:
            self.mkdir(path)
        self.mkdir(self.case)
        self.registry_path = self.room / "ops/etc/resident-identities.json"
        self.registry = {"identities": [
            {"key": WRITER, "person": "Fixture Writer", "role": "Assistant",
             "room": str(self.room), "provider": "codex", "session_id": WRITER_SID},
            {"key": "fixture-auditor", "person": "Fixture Auditor", "role": "Auditor",
             "room": str(self.room), "provider": "claude",
             "session_id": "0000f644-0000-4000-8000-00000000f644"}]}
        self.put(self.registry_path, self.registry)
        self.donor = self.store / (SID + ".jsonl")
        self.destination = self.store / (DESTINATION + ".jsonl")
        self.stage = self.store / (DESTINATION + ".jsonl.NEW")
        self.donor_rows = [
            self.row("system", 1, None, subtype="compact_boundary"),
            self.row("user", 2, 1, "An invented summary.", isCompactSummary=True),
            self.row("user", 3, 2, "Which invented bracket supports the shelf?"),
            self.row("assistant", 4, 3, "The lower invented bracket supports it.")]
        self.put_rows(self.donor, self.donor_rows)
        self.pristine_rows = [
            {"type": "custom-title", "customTitle": "Fixture - spare body, do not open",
             "sessionId": DESTINATION},
            self.row("user", 11, None, ROTATE.FIRST_PROMPT, sid=DESTINATION),
            self.row("assistant", 12, 11, "READY", sid=DESTINATION)]
        self.pristine_rows[2]["message"]["id"] = "invented-ready-message"   # a real reply always names its message
        self.put_rows(self.destination, self.pristine_rows)
        self.put(self.store / "unrelated.bin", b"Invented unrelated baseline bytes.\n")
        self.candidate_path = self.case / "candidate.jsonl"
        candidate = copy.deepcopy(self.donor_rows)
        for row in candidate:
            row["sessionId"] = DESTINATION
        candidate += [self.row("user", 5, 4,
                              "<session_clinic_orientation>\nInvented capsule only.\n</session_clinic_orientation>",
                              sid=DESTINATION),
                      {"type": "custom-title", "customTitle": "Fixture Resident", "sessionId": DESTINATION},
                      {"type": "agent-name", "agentName": "Fixture Resident", "sessionId": DESTINATION}]
        self.put_rows(self.candidate_path, candidate)
        self.capsule = self.case / "capsule.txt"
        self.window = self.case / "window.json"
        self.gates_path = self.case / "gates.json"
        self.put(self.capsule, b"Invented capsule only.\n")
        self.put(self.window, {"schema": "fixture-window/1", "summary": "Invented summary."})
        self.gates = {"schema": "rotate-native-gates/1", "phase": 5,
                      "donor_sha256": self.sha(self.donor), "pristine_sha256": self.sha(self.destination),
                      "candidate_sha256": self.sha(self.candidate_path),
                      "gates": dict.fromkeys(("trigger", "closeout", "operator_compaction", "window", "static", "media"), True)}
        self.put(self.gates_path, self.gates)
        self.plan = {"schema": "rotate-disposable/1", "operation": self.operation, "provider": "claude",
                     "provider_version": "invented-cli-version", "writer": WRITER, "room": str(self.room),
                     "registry": self.ref(self.registry_path), "project": str(self.project), "store": str(self.store),
                     "records_dir": str(self.records_dir), "synthetic_root": str(self.base),
                     "donor": {**self.ref(self.donor), "session_id": SID},
                     "destination": {**self.ref(self.destination), "session_id": DESTINATION},
                     "candidate": self.ref(self.candidate_path),
                     "artifacts": [{"name": name, **self.ref(path)} for name, path in
                                   (("capsule", self.capsule), ("gates", self.gates_path), ("window", self.window))],
                     "custody_roots": list(map(str, self.roots)), "date": "20261109"}
        self.plan_path, self.go_path, self.proof_path = [self.case / p for p in ("plan.json", "go.json", "proof.json")]
        self.put(self.plan_path, self.plan)
        self.state_home = self.room / "logs/rotate" / self.operation
        self.state_path = self.state_home / "state.json"
        self.custody = ROTATE.sibling("custody")
        self.mind = ROTATE.sibling("mind")
        self.pristine_bytes = self.destination.read_bytes()
        self.donor_bytes = self.donor.read_bytes()
        self.original_store = self.inventory(self.store)
        self.custody_result = None
        self.instrument_serial = 0

    def mkdir(self, path):
        pending = []
        while not path.exists():
            pending.append(path)
            path = path.parent
        for path in reversed(pending):
            path.mkdir(mode=0o700)

    def put(self, path, value):
        self.mkdir(path.parent)
        path.write_bytes(value if isinstance(value, bytes) else json.dumps(value, sort_keys=True).encode("ascii"))
        path.chmod(0o600)

    @staticmethod
    def sha(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def ref(self, path):
        return {"path": str(path), "sha256": self.sha(path)}

    def row(self, kind, number, parent, content=None, sid=SID, **extra):
        uid = lambda n: "0000%04x-0000-4000-8000-00000000%04x" % (n, n)
        result = {"type": kind, "uuid": uid(number), "parentUuid": None if parent is None else uid(parent),
                  "sessionId": sid, "cwd": str(self.project), "timestamp": "2026-11-09T12:00:00Z"}
        if content is not None:
            result["message"] = {"role": kind, "content": content}
        return {**result, **extra}

    def put_rows(self, path, rows):
        self.put(path, b"".join(json.dumps(r, sort_keys=True).encode("ascii") + b"\n" for r in rows))

    def snapshot(self, path):
        if not path.exists():
            return {"type": "absent"}
        st = path.lstat()
        return {"type": "file", "dev": st.st_dev, "ino": st.st_ino, "size": st.st_size,
                "sha256": self.sha(path), "mode": stat.S_IMODE(st.st_mode), "uid": st.st_uid,
                "gid": st.st_gid, "mtime_ns": st.st_mtime_ns, "ctime_ns": st.st_ctime_ns, "nlink": st.st_nlink}

    @staticmethod
    def inventory(root):
        result = {}
        for path in sorted(root.rglob("*")):
            st = path.lstat()
            kind = "link" if path.is_symlink() else "file" if stat.S_ISREG(st.st_mode) else "directory"
            value = os.readlink(path) if kind == "link" else (
                hashlib.sha256(path.read_bytes()).hexdigest() if kind == "file" else None)
            result[str(path.relative_to(root))] = (kind, st.st_size, value,
                                                  stat.S_IMODE(st.st_mode), st.st_uid, st.st_gid)
        return result

    def prepare(self, action, go_change=None, proof_change=None, reuse_go=False):
        if self.state_path.exists():
            state = json.loads(self.state_path.read_bytes())
            if state["phase"] in ("rollback-restored", "rolled-back"):
                delay = 2.05 - (time.time_ns() - state["restored_at_ns"]) / 1e9
                if delay > 0:
                    time.sleep(delay)
        now = dt.datetime.now(dt.timezone.utc)
        plan_sha = self.sha(self.plan_path)
        go = {"schema": "rotate-native-go/1", "operation": self.operation, "plan_sha256": plan_sha,
              "writer": WRITER, "action": action, "at": now.isoformat()}
        if action == "install":
            go.update(pristine_sha256=hashlib.sha256(self.pristine_bytes).hexdigest(),
                      candidate_sha256=self.sha(self.candidate_path),
                      custody_manifest_sha256=self.custody_result["custody_manifest_sha256"],
                      inverse="restore-pristine-and-stop")
        if action == "rollback":
            go["destination_sha256"] = self.sha(self.destination)
        if go_change:
            go_change(go)
        if not reuse_go:
            self.put(self.go_path, go)
        project = self.project.stat()
        observations = [{"at": (now - dt.timedelta(seconds=seconds)).isoformat(),
                         "donor": self.snapshot(self.donor), "destination": self.snapshot(self.destination),
                         "project": {"dev": project.st_dev, "ino": project.st_ino},
                         "same_user_observable": True, "holders": 0, "session_records": 0,
                         "argument_holders": 0, "locks": 0, "unreadable": 0, "foreign_processes": 0}
                        for seconds in (2, 1)]
        proof = {"schema": "rotate-native-proof/1", "operation": self.operation,
                 "plan_sha256": plan_sha, "action": action, "quiescence": observations}
        if action == "install":
            review = {"schema": "rotate-custody-audit/1", "operation": self.operation,
                      "plan_sha256": plan_sha, "manifest_sha256": self.custody_result["custody_manifest_sha256"],
                      "auditor": "fixture-auditor", "verdict": "PASS"}
            review_path = self.case / "audit.json"
            self.put(review_path, review)
            proof["custody_audit"] = {**{k: review[k] for k in ("manifest_sha256", "auditor", "verdict")},
                                      "review": self.ref(review_path)}
        proof["instruments"] = self.instrument_bindings(action, proof)
        if proof_change:
            proof_change(proof)
        self.put(self.proof_path, proof)
        return ["--adapter", "claude", "--native-apply", "--native-action", action,
                "--native-plan", str(self.plan_path), "--native-plan-sha256", plan_sha,
                "--native-go", str(self.go_path), "--native-go-sha256", self.sha(self.go_path),
                "--native-proof", str(self.proof_path), "--native-proof-sha256", self.sha(self.proof_path)]

    def instrument_bindings(self, action, proof):
        """Invented observer records; real reader-format join is a separate probe.

        Keep fixture construction independent of the production packet builder
        so a missing/wrong production key cannot manufacture its own oracle.
        """
        state = json.loads(self.state_path.read_bytes()) if self.state_path.exists() else None
        objects = {"donor": str(self.donor), "destination": str(self.destination), "candidate": str(self.candidate_path),
                   **{item["name"]: item["path"] for item in self.plan["artifacts"]}}
        def bind(name, result):
            self.instrument_serial += 1
            filename = "fixture-%d.json" % self.instrument_serial
            pk = {"evidence": str(self.case), "record_name": filename, "synthetic_root": str(self.base)}
            if name == "I1":
                pk.update(targets={name: str(path) for name, path in (("donor", self.donor), ("destination", self.destination))
                                   if path.exists()},
                          project=str(self.project), session_ids=[SID, DESTINATION],
                          records_dir=str(self.records_dir), interval_s=1)
            elif name == "I2":
                pk.update(objects=objects, project=str(self.store))
            elif name in ("I3B", "I3A"):
                pk.update(preimage=state["i2"]["record"]["path"], destination=str(self.destination),
                          staged=str(self.stage), candidate_sha256=self.sha(self.candidate_path), destination_token="destination")
                if name == "I3A":
                    pk["before"] = state["i3b"]["record"]["path"]
            elif name == "I4":
                pk.update(postimage=state["i4_postimage"]["path"], destination=str(self.destination),
                          destination_sid=DESTINATION, donor_sid=SID)
            else:
                retained = state.get("retained_append")
                pk.update(preimages=state["i2"]["record"]["path"], items=objects, donor="donor", project=str(self.store),
                          custody=[] if retained is None else [{"path": str(root / "sessions-fixture-writer-20261109" / retained["name"]),
                                                                "sha256": retained["sha256"]} for root in self.roots],
                          holders=proof["instruments"]["I1"][-1]["record"]["path"])
            record_path = self.case / filename
            packet_path = self.case / (filename + ".packet.json")
            self.put(record_path, result)
            self.put(packet_path, pk)
            return {"packet": self.ref(packet_path), "record": self.ref(record_path)}
        clear = {"held": [], "own_unreadable": 0, "foreign_unreadable": 0}
        bindings = {"I1": [bind("I1", clear), bind("I1", clear)]}
        for binding, observation in zip(bindings["I1"], proof["quiescence"]):
            stamp = dt.datetime.fromisoformat(observation["at"]).timestamp()
            os.utime(binding["record"]["path"], (stamp, stamp))
        proof["instruments"] = bindings
        if action == "disposable-exercise":
            listing = {path.name: ["file", stat.S_IMODE(path.stat().st_mode), path.stat().st_size]
                       for path in self.store.iterdir() if path.is_file()}
            bindings["I2"] = bind("I2", {"objects": {name: self.snapshot(Path(path)) for name, path in objects.items()},
                                         "listing": listing, "project": [self.store.stat().st_dev, self.store.stat().st_ino]})
        if state and action == "install":
            if state["phase"] == "install-prepared":
                bindings["I3B"] = bind("I3B", {"staged": state["staged"]})
            elif state["phase"] == "install-renamed":
                bindings["I3A"] = bind("I3A", {"postimage": self.snapshot(self.destination)})
        if state and action == "load":
            tail = self.destination.read_bytes()[state["installed"]["size"]:]
            rows = [json.loads(line) for line in tail.splitlines()]
            kinds = {}
            for row in rows:
                key = str(row.get("type"))
                kinds[key] = kinds.get(key, 0) + 1
            bindings["I4"] = bind("I4", {"appended": len(rows), "by_type": kinds})
        if state and action == "rollback" and state["phase"] in ("rollback-restored", "rolled-back"):
            bindings["I5"] = bind("I5", {"differences": [], "notes": []})
        return bindings

    def invoke(self, action="disposable-exercise", edit_args=None, exposure=False, same_disk=False, **prepare):
        args = self.prepare(action, **prepare)
        if edit_args:
            edit_args(args)
        self.before = self.inventory(self.base)
        real_sibling = ROTATE.sibling
        def sibling(name):
            return self.custody if name == "custody" else self.mind if name == "mind" else real_sibling(name)
        stdout, stderr = io.StringIO(), io.StringIO()
        commands = []
        with contextlib.ExitStack() as stack:
            stack.enter_context(contextlib.redirect_stdout(stdout))
            stack.enter_context(contextlib.redirect_stderr(stderr))
            stack.enter_context(mock.patch.object(ROTATE, "sibling", side_effect=sibling))
            self.exposure_reader = stack.enter_context(mock.patch.object(self.mind, "git_exposed", return_value=exposure))
            stack.enter_context(mock.patch.object(self.custody, "root_device", side_effect=lambda p: 101 + self.roots.index(Path(p))))
            stack.enter_context(mock.patch.object(self.custody, "disks", side_effect=lambda dev:
                frozenset({"fixture-disk" if same_disk else "fixture-disk-" + str(dev)})))
            for name in ("run", "Popen", "call", "check_call", "check_output"):
                commands.append(stack.enter_context(mock.patch.object(subprocess, name, side_effect=AssertionError("no commands"))))
            rc = ROTATE.main(args)
        for command in commands:
            command.assert_not_called()
        self.after = self.inventory(self.base)
        text = stdout.getvalue()
        for private in (SID, DESTINATION, str(self.base), SECRET):
            self.assertNotIn(private, text + stderr.getvalue())
        result = json.loads(text)
        self.assertEqual(result["schema"], "rotate-native/1")
        self.assertIs(result["operator_accepted"], False)
        return rc, result

    def refused(self, action="disposable-exercise", **kwargs):
        before = self.inventory(self.store)
        rc, result = self.invoke(action, **kwargs)
        self.assertEqual(rc, 2, result)
        self.assertEqual(result["status"], "refused", result)
        self.assertRegex(result["reason"], r"^[a-z0-9][a-z0-9-]{0,159}$")
        self.assertEqual(self.inventory(self.store), before)
        return result

    def stop(self, action, phase, **kwargs):
        rc, result = self.invoke(action, **kwargs)
        self.assertEqual(rc, 0, result)
        self.assertEqual(result["status"], "stop", result)
        self.assertEqual(result["phase"], phase)
        for field in ("resident_mind", "notebook", "launcher_join"):
            self.assertEqual(result[field], "NOT APPLICABLE")
        self.assertIs(result["provider_started"], False)
        self.assertIs(result["compaction_triggered"], False)
        return result

    def preserve(self):
        self.stop("disposable-exercise", "admitted")
        self.custody_result = self.stop("custody", "custodied")

    def install(self):
        self.stop("install", "install-prepared")
        self.assertEqual(self.destination.read_bytes(), self.pristine_bytes)
        self.assertTrue(self.stage.exists())
        self.stop("install", "install-renamed", reuse_go=True)
        self.stop("install", "installed", reuse_go=True)

    def inverse(self, **kwargs):
        missing_donor = not self.donor.exists()
        self.stop("rollback", "rollback-donor-pending" if missing_donor else "rollback-restored", **kwargs)
        if missing_donor:
            self.stop("rollback", "rollback-restored", reuse_go=True, **kwargs)
        self.stop("rollback", "rolled-back", reuse_go=True, **kwargs)

    def test_admission_records_private_state_without_rewriting_bodies(self):
        self.stop("disposable-exercise", "admitted")
        self.assertEqual(self.inventory(self.store), self.original_store)
        self.assertEqual(self.donor.read_bytes(), self.donor_bytes)
        self.assertEqual(stat.S_IMODE(self.state_home.stat().st_mode), 0o700)
        for path in self.state_home.iterdir():
            if path.is_file():
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        self.assertGreater(self.exposure_reader.call_count, 0)

    def test_missing_go_refuses_without_creating_state(self):
        def edit(args):
            index = args.index("--native-go")
            del args[index:index + 2]
        self.refused(edit_args=edit)
        self.assertFalse(self.state_home.exists())
        self.assertEqual(self.before, self.after)

    def test_bad_go_hash_refuses_without_creating_state(self):
        self.refused(edit_args=lambda a: a.__setitem__(a.index("--native-go-sha256") + 1, "0" * 64))
        self.assertFalse(self.state_home.exists())
        self.assertEqual(self.before, self.after)

    def test_bad_plan_hash_refuses_without_creating_state(self):
        self.refused(edit_args=lambda a: a.__setitem__(a.index("--native-plan-sha256") + 1, "0" * 64))
        self.assertFalse(self.state_home.exists())
        self.assertEqual(self.before, self.after)

    def test_missing_native_apply_refuses_without_state(self):
        self.refused(edit_args=lambda a: a.remove("--native-apply"))
        self.assertFalse(self.state_home.exists())

    def test_explicit_dry_run_refuses_even_with_apply(self):
        self.refused(edit_args=lambda a: a.append("--dry-run"))
        self.assertFalse(self.state_home.exists())

    def test_git_exposure_reader_refusal_is_enforced(self):
        self.refused(exposure=True)
        self.assertGreater(self.exposure_reader.call_count, 0)

    def test_plan_schema_provider_and_version_are_checked(self):
        for field, value in (("schema", "wrong/1"), ("provider", "codex"),
                             ("provider_version", ""), ("provider_version", "x" * 65)):
            with self.subTest(field=field, value=value):
                plan = copy.deepcopy(self.plan)
                plan[field] = value
                self.put(self.plan_path, plan)
                self.refused()

    def test_go_binds_action_operation_writer_and_plan(self):
        for field in ("schema", "action", "operation", "writer", "plan_sha256"):
            with self.subTest(field=field):
                self.refused(go_change=lambda go, key=field: go.__setitem__(key, "wrong"))

    def test_registered_target_is_not_disposable(self):
        self.registry["identities"][0]["session_id"] = SID
        self.put(self.registry_path, self.registry)
        self.plan["registry"] = self.ref(self.registry_path)
        self.put(self.plan_path, self.plan)
        self.refused()

    def test_ambiguous_registry_writer_refuses(self):
        self.registry["identities"].append(copy.deepcopy(self.registry["identities"][0]))
        self.put(self.registry_path, self.registry)
        self.plan["registry"] = self.ref(self.registry_path)
        self.put(self.plan_path, self.plan)
        self.refused()

    def test_nonprivate_registry_refuses(self):
        self.registry_path.chmod(0o664)
        self.refused()

    def test_hardlinked_candidate_refuses(self):
        os.link(self.candidate_path, self.case / "candidate-link")
        self.refused()

    def test_changed_closed_donor_hash_refuses(self):
        self.put(self.donor, self.donor_bytes + b"\n")
        self.refused()

    def test_changed_candidate_hash_refuses(self):
        self.put(self.candidate_path, self.candidate_path.read_bytes() + b"\n")
        self.refused()

    def test_existing_new_is_preserved_and_blocks_admission(self):
        self.put(self.stage, b"Unknown interrupted stage.\n")
        self.refused()
        self.assertEqual(self.stage.read_bytes(), b"Unknown interrupted stage.\n")

    def test_quiescence_requires_two_fresh_distinct_readings(self):
        for change in (lambda p: p.__setitem__("quiescence", p["quiescence"][:1]),
                       lambda p: p["quiescence"][1].__setitem__("at", p["quiescence"][0]["at"]),
                       lambda p: p["quiescence"][0].__setitem__("at", "2020-01-01T00:00:00Z")):
            with self.subTest(change=change):
                self.refused(proof_change=change)

    def test_each_process_evidence_guard_refuses_independently(self):
        for field in ("holders", "session_records", "argument_holders", "locks", "unreadable", "foreign_processes"):
            with self.subTest(field=field):
                self.refused(proof_change=lambda p, key=field: p["quiescence"][0].__setitem__(key, 1))

    def test_unobservable_process_evidence_refuses(self):
        self.refused(proof_change=lambda p: p["quiescence"][0].__setitem__("same_user_observable", False))

    def test_each_preparation_gate_must_be_true(self):
        for field in self.gates["gates"]:
            with self.subTest(field=field):
                gates = copy.deepcopy(self.gates)
                gates["gates"][field] = False
                self.put(self.gates_path, gates)
                plan = copy.deepcopy(self.plan)
                next(a for a in plan["artifacts"] if a["name"] == "gates").update(self.ref(self.gates_path))
                self.put(self.plan_path, plan)
                self.refused()

    def test_admission_repeat_is_idempotent(self):
        self.stop("disposable-exercise", "admitted")
        before = self.inventory(self.state_home)
        self.stop("disposable-exercise", "admitted")
        after = self.inventory(self.state_home)
        # A repeat exports a fresh pair of exclusive observer output names;
        # admission, preimages and lock remain unchanged.
        for key in ("state.json", "preimages.json", "operation.lock"):
            self.assertEqual(after[key], before[key])

    def test_custody_install_rollback_restore_whole_store_inventory(self):
        self.preserve()
        self.install()
        self.assertEqual(self.destination.read_bytes(), self.candidate_path.read_bytes())
        self.assertEqual(self.donor.read_bytes(), self.donor_bytes)
        self.inverse()
        self.assertEqual(self.inventory(self.store), self.original_store)
        self.assertFalse(self.stage.exists())
        self.assertEqual(self.donor.read_bytes(), self.donor_bytes)

    def test_install_requires_independent_registered_auditor(self):
        self.preserve()
        for name in ("", WRITER, "not-registered"):
            with self.subTest(name=name):
                self.refused("install", proof_change=lambda p, name=name: p["custody_audit"].__setitem__("auditor", name))

    def test_changed_pristine_after_custody_refuses_install(self):
        self.preserve()
        self.put(self.destination, self.pristine_bytes + b"\n")
        self.refused("install")

    def test_unknown_destination_bytes_are_not_overwritten_by_rollback(self):
        self.preserve()
        self.install()
        self.put(self.destination, b"Unknown newer destination bytes.\n")
        self.refused("rollback")
        self.assertEqual(self.destination.read_bytes(), b"Unknown newer destination bytes.\n")

    def test_after_rename_before_journal_save_resumes_same_go(self):
        self.preserve()
        self.stop("install", "install-prepared")
        save = ROTATE.NativeOperation.save
        def interrupted(operation):
            if operation.state["phase"] == "install-renamed":
                raise OSError("Invented interruption before committed state.")
            return save(operation)
        with mock.patch.object(ROTATE.NativeOperation, "save", new=interrupted):
            rc, result = self.invoke("install", reuse_go=True)
        self.assertEqual(rc, 2, result)
        self.assertEqual(self.destination.read_bytes(), self.candidate_path.read_bytes())
        self.assertEqual(json.loads(self.state_path.read_text())["phase"], "install-prepared")
        self.stop("install", "install-renamed", reuse_go=True)
        self.stop("install", "installed", reuse_go=True)
        self.inverse()
        self.assertEqual(self.inventory(self.store), self.original_store)

    def change_instrument(self, proof, name, transform, packet=False, index=None):
        binding = proof["instruments"][name]
        if index is not None:
            binding = binding[index]
        key = "packet" if packet else "record"
        path = Path(binding[key]["path"])
        record = json.loads(path.read_bytes())
        transform(record)
        self.put(path, record)
        binding[key] = self.ref(path)

    def test_initial_packet_export_does_not_admit_or_touch_store(self):
        self.stop("disposable-exercise", "awaiting-instruments", edit_args=lambda a: a.append("--native-export-instruments"),
                  proof_change=lambda p: p.pop("instruments"))
        self.assertFalse(self.state_home.exists())
        self.assertEqual(self.inventory(self.store), self.original_store)
        index = json.loads((self.case / "instrument-packets.json").read_bytes())
        self.assertEqual(set(index), {"I1", "I2"})
        self.assertEqual(len(index["I1"]), 2)
        packets = {name: json.loads(Path((ref[0] if isinstance(ref, list) else ref)["path"]).read_bytes())
                   for name, ref in index.items()}
        pair = [json.loads(Path(ref["path"]).read_bytes()) for ref in index["I1"]]
        self.assertNotEqual(pair[0]["record_name"], pair[1]["record_name"])
        self.assertEqual(packets["I1"]["project"], str(self.project))
        self.assertEqual(packets["I2"]["project"], str(self.store))

    def test_missing_actual_i1_records_refuses(self):
        result = self.refused(proof_change=lambda p: p.pop("instruments"))
        self.assertEqual(result["reason"], "native-two-i1-records-required")

    def test_reexport_never_reuses_exclusive_observer_output_names(self):
        kwargs = {"edit_args": lambda a: a.append("--native-export-instruments"),
                  "proof_change": lambda p: p.pop("instruments")}
        self.stop("disposable-exercise", "awaiting-instruments", **kwargs)
        index = json.loads((self.case / "instrument-packets.json").read_bytes())
        old = json.loads(Path(index["I1"][0]["path"]).read_bytes())
        old_record = self.case / old["record_name"]
        self.put(old_record, b"Invented retained old observation.\n")
        self.stop("disposable-exercise", "awaiting-instruments", **kwargs)
        index = json.loads((self.case / "instrument-packets.json").read_bytes())
        new = json.loads(Path(index["I1"][0]["path"]).read_bytes())
        self.assertNotEqual(old["record_name"], new["record_name"])
        self.assertEqual(old_record.read_bytes(), b"Invented retained old observation.\n")

    def test_i1_record_holders_and_unreadable_counts_are_enforced(self):
        for field, value in (("held", [["invented holder", 1]]), ("own_unreadable", 1), ("foreign_unreadable", 1)):
            with self.subTest(field=field):
                result = self.refused(proof_change=lambda p, k=field, v=value:
                    self.change_instrument(p, "I1", lambda r: r.__setitem__(k, v), index=0))
                self.assertEqual(result["reason"], "native-i1-not-clear")

    def test_i1_false_is_not_integer_zero(self):
        result = self.refused(proof_change=lambda p:
            self.change_instrument(p, "I1", lambda r: r.__setitem__("own_unreadable", False), index=0))
        self.assertEqual(result["reason"], "native-i1-count-type")

    def test_reusing_one_i1_inode_is_not_two_readings(self):
        result = self.refused(proof_change=lambda p: p["instruments"]["I1"].__setitem__(1, p["instruments"]["I1"][0]))
        self.assertEqual(result["reason"], "native-distinct-i1-records-required")

    def test_old_i1_record_refuses_despite_fresh_wrapper(self):
        def age(proof):
            path = Path(proof["instruments"]["I1"][0]["record"]["path"])
            os.utime(path, (1, 1))
        self.assertEqual(self.refused(proof_change=age)["reason"], "native-i1-record-stale")

    def test_i1_file_times_must_show_the_actual_interval(self):
        def same_time(proof):
            left, right = proof["instruments"]["I1"]
            stamp = Path(left["record"]["path"]).stat().st_mtime_ns
            os.utime(right["record"]["path"], ns=(stamp, stamp))
        self.assertEqual(self.refused(proof_change=same_time)["reason"], "native-i1-record-interval")

    def test_i2_actual_objects_not_internal_checkpoint_are_required(self):
        result = self.refused(proof_change=lambda p:
            self.change_instrument(p, "I2", lambda r: r["objects"]["donor"].__setitem__("sha256", "0" * 64)))
        self.assertEqual(result["reason"], "native-i2-objects")

    def test_i2_listing_and_store_identity_are_checked_separately(self):
        for edit in (lambda r: r.__setitem__("listing", {}), lambda r: r.__setitem__("project", [0, 0])):
            with self.subTest(edit=edit):
                result = self.refused(proof_change=lambda p: self.change_instrument(p, "I2", edit))
                self.assertEqual(result["reason"], "native-i2-store-listing")

    def test_reader_packet_wrong_working_folder_refuses(self):
        result = self.refused(proof_change=lambda p: self.change_instrument(
            p, "I1", lambda r: r.__setitem__("project", str(self.store)), packet=True, index=0))
        self.assertEqual(result["reason"], "native-instrument-packet-mismatch")

    def test_install_first_call_stops_with_original_target_and_real_stage(self):
        self.preserve()
        self.stop("install", "install-prepared")
        self.assertEqual(self.destination.read_bytes(), self.pristine_bytes)
        self.assertEqual(self.stage.read_bytes(), self.candidate_path.read_bytes())
        exports = json.loads((self.state_home / "instrument-packets.json").read_bytes())
        pk = json.loads(Path(exports["I3B"]["path"]).read_bytes())
        self.assertEqual(pk["destination_token"], "destination")
        self.assertEqual(pk["staged"], str(self.stage))

    def test_missing_i3b_leaves_candidate_staged_not_installed(self):
        self.preserve()
        self.stop("install", "install-prepared")
        result = self.refused("install", reuse_go=True, proof_change=lambda p: p["instruments"].pop("I3B"))
        self.assertEqual(result["reason"], "native-instrument-reference-required")
        self.assertTrue(self.stage.exists())

    def test_i3b_must_observe_the_exact_staged_inode(self):
        self.preserve()
        self.stop("install", "install-prepared")
        result = self.refused("install", reuse_go=True, proof_change=lambda p: self.change_instrument(
            p, "I3B", lambda r: r["staged"].__setitem__("ino", 0)))
        self.assertEqual(result["reason"], "native-i3b-staged-inode")

    def test_i3b_missing_destination_token_refuses(self):
        self.preserve()
        self.stop("install", "install-prepared")
        result = self.refused("install", reuse_go=True, proof_change=lambda p: self.change_instrument(
            p, "I3B", lambda r: r.pop("destination_token"), packet=True))
        self.assertEqual(result["reason"], "native-instrument-packet-mismatch")

    def test_i3a_wrong_postimage_does_not_claim_installed(self):
        self.preserve()
        self.stop("install", "install-prepared")
        self.stop("install", "install-renamed", reuse_go=True)
        result = self.refused("install", reuse_go=True, proof_change=lambda p: self.change_instrument(
            p, "I3A", lambda r: r["postimage"].__setitem__("sha256", "0" * 64)))
        self.assertEqual(result["reason"], "native-i3a-postimage")
        self.assertEqual(json.loads(self.state_path.read_bytes())["phase"], "install-renamed")

    def test_export_recovers_saved_stage_without_rerunning_install(self):
        self.preserve()
        publish = ROTATE.NativeOperation.publish_instruments
        def fail_after_stage(operation):
            if operation.state["phase"] == "install-prepared":
                raise OSError("Invented interruption before packet publication.")
            return publish(operation)
        with mock.patch.object(ROTATE.NativeOperation, "publish_instruments", new=fail_after_stage):
            rc, result = self.invoke("install")
        self.assertEqual(rc, 2, result)
        before = self.inventory(self.store)
        self.stop("install", "install-prepared", reuse_go=True,
                  edit_args=lambda a: a.append("--native-export-instruments"),
                  proof_change=lambda p: p.pop("instruments"))
        self.assertEqual(self.inventory(self.store), before)
        index = json.loads((self.state_home / "instrument-packets.json").read_bytes())
        self.assertIn("I3B", index)
        packet = json.loads(Path(index["I3B"]["path"]).read_bytes())
        self.assertEqual(packet["staged"], str(self.stage))

    def test_pre_restore_i1_cannot_close_inverse_even_with_current_snapshots(self):
        self.preserve()
        self.install()
        self.stop("rollback", "rollback-restored")
        state = json.loads(self.state_path.read_bytes())
        def predates(proof):
            for index, binding in enumerate(proof["instruments"]["I1"]):
                stamp = state["restored_at_ns"] - (2 - index) * 1_000_000_000
                os.utime(binding["record"]["path"], ns=(stamp, stamp))
        result = self.refused("rollback", reuse_go=True, proof_change=predates)
        self.assertEqual(result["reason"], "native-i1-before-restore")

    def test_published_inverse_reader_uses_the_new_second_i1_output(self):
        self.preserve()
        self.install()
        self.stop("rollback", "rollback-restored")
        index = json.loads((self.state_home / "instrument-packets.json").read_bytes())
        second = json.loads(Path(index["I1"][1]["path"]).read_bytes())
        inverse = json.loads(Path(index["I5"]["path"]).read_bytes())
        self.assertEqual(inverse["holders"], str(self.case / second["record_name"]))
        self.assertFalse(Path(inverse["holders"]).exists())

    def append_reply(self):
        row = self.row("assistant", 101, 5, [{"type": "text", "text": "Invented appended reply."}], sid=DESTINATION)
        row["message"].update(id="invented-call", model="claude-sonnet-4-5-20250929",
                              usage={"input_tokens": 123, "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0})
        self.put(self.destination, self.destination.read_bytes() + json.dumps(row).encode() + b"\n")
        return self.destination.read_bytes()

    def gauge_proof(self, proof):
        proof["first_gauge"] = ROTATE.sibling("gauge").read_claude(self.destination)

    def test_load_reads_append_and_actual_i4_then_custodies_it_before_restore(self):
        self.preserve()
        self.install()
        appended = self.append_reply()
        self.stop("load", "loaded", proof_change=self.gauge_proof)
        state = json.loads(self.state_path.read_bytes())
        flat = json.loads(Path(state["i4_postimage"]["path"]).read_bytes())
        self.assertIn("uuids", flat)
        self.assertNotIn("postimage", flat)
        self.inverse(proof_change=lambda p: p.__setitem__("appended_sha256", hashlib.sha256(appended).hexdigest()))
        state = json.loads(self.state_path.read_bytes())
        for root in self.roots:
            kept = root / "sessions-fixture-writer-20261109" / state["retained_append"]["name"]
            self.assertEqual(kept.read_bytes(), appended)
        self.assertEqual(self.inventory(self.store), self.original_store)

    def test_i4_not_a_clean_append_refuses_without_marking_loaded(self):
        self.preserve()
        self.install()
        self.append_reply()
        def bad(proof):
            self.gauge_proof(proof)
            self.change_instrument(proof, "I4", lambda r: r.__setitem__("appended", 0))
        result = self.refused("load", proof_change=bad)
        self.assertEqual(result["reason"], "native-i4-clean-append-required")
        self.assertEqual(json.loads(self.state_path.read_bytes())["phase"], "installed")

    def test_inverse_waits_for_external_i5(self):
        self.preserve()
        self.install()
        self.stop("rollback", "rollback-restored")
        result = self.refused("rollback", reuse_go=True, proof_change=lambda p: p["instruments"].pop("I5"))
        self.assertEqual(result["reason"], "native-instrument-reference-required")
        self.assertEqual(self.inventory(self.store), self.original_store)

    def test_inverse_i5_difference_refuses_final_acceptance(self):
        self.preserve()
        self.install()
        self.stop("rollback", "rollback-restored")
        result = self.refused("rollback", reuse_go=True, proof_change=lambda p: self.change_instrument(
            p, "I5", lambda r: r.__setitem__("differences", ["invented difference"])))
        self.assertEqual(result["reason"], "native-i5-inverse-not-clear")

    def test_missing_donor_restore_requires_its_explicit_go(self):
        self.preserve()
        self.install()
        self.donor.unlink()
        self.refused("rollback")
        self.assertFalse(self.donor.exists())
        self.inverse(go_change=lambda g: g.__setitem__("restore_absent_donor", True))
        self.assertEqual(self.donor.read_bytes(), self.donor_bytes)
        self.assertEqual(self.inventory(self.store), self.original_store)

    def test_two_partitions_on_one_physical_disk_are_not_two_copies(self):
        self.refused(same_disk=True)
        self.assertFalse(self.state_path.exists())

    def test_well_formed_changed_donor_is_stopped_by_closed_hash_guard(self):
        rows = copy.deepcopy(self.donor_rows)
        rows[2]["message"]["content"] = "A different invented question."
        self.put_rows(self.donor, rows)
        result = self.refused()
        self.assertEqual(result["reason"], "native-closed-target-hash")


    def guard_plan(self, edit, reason):
        """Alter only a supplied record after the independent fixture is built.

        Hash-bind the changed plan and its go/proof, so the tested predicate,
        rather than an unrelated stale digest, must reject the input.
        """
        def revise(args):
            p = copy.deepcopy(self.plan)
            edit(p)
            self.put(self.plan_path, p)
            plan_sha = self.sha(self.plan_path)
            args[args.index("--native-plan-sha256") + 1] = plan_sha
            for path, flag in ((self.go_path, "--native-go-sha256"),
                               (self.proof_path, "--native-proof-sha256")):
                value = json.loads(path.read_bytes())
                value["plan_sha256"] = plan_sha
                self.put(path, value)
                args[args.index(flag) + 1] = self.sha(path)
            self.guard_store_before = self.inventory(self.store)
        rc, result = self.invoke(edit_args=revise)
        self.assertEqual(rc, 2, result)
        self.assertEqual(result["status"], "refused")
        self.assertEqual(result["reason"], reason)
        self.assertEqual(self.inventory(self.store), self.guard_store_before)
        self.assertFalse(self.state_path.exists())

    def guard_registry(self, edit, reason):
        def revise(p):
            registry = copy.deepcopy(self.registry)
            edit(registry)
            self.put(self.registry_path, registry)
            p["registry"] = self.ref(self.registry_path)
        self.guard_plan(revise, reason)

    def test_guard_operation_type(self):
        def change(p):
            p["operation"] = 12
        self.guard_plan(change, "native-operation-name")

    def test_guard_operation_spelling(self):
        def change(p):
            p["operation"] = "../outside"
        self.guard_plan(change, "native-operation-name")

    def test_guard_writer_type(self):
        def change(p):
            p["writer"] = 12
        self.guard_plan(change, "native-writer-key")

    def test_guard_writer_spelling(self):
        def change(p):
            p["writer"] = "Bad Writer!"
        self.guard_plan(change, "native-writer-key")

    def test_guard_project_not_store(self):
        def change(p):
            p["project"] = str(self.store)
        self.guard_plan(change, "native-private-disposable-project-required")

    def test_guard_project_not_room(self):
        def change(p):
            p["project"] = str(self.room)
        self.guard_plan(change, "native-private-disposable-project-required")

    def test_guard_store_not_room(self):
        def change(p):
            p["store"] = str(self.room)
        self.guard_plan(change, "native-private-disposable-project-required")

    def test_guard_registry_shape(self):
        def change(p):
            p["registry"] = []
        self.guard_plan(change, "native-canonical-registry-required")

    def test_guard_registry_canonical_home(self):
        def change(p):
            p["registry"] = self.ref(self.capsule)
        self.guard_plan(change, "native-canonical-registry-required")

    def test_guard_donor_shape(self):
        def change(p):
            p["donor"] = []
        self.guard_plan(change, "native-target-required")

    def test_guard_donor_identity_type(self):
        def change(p):
            p["donor"]["session_id"] = 12
        self.guard_plan(change, "native-target-identity")

    def test_guard_donor_identity_shape(self):
        def change(p):
            p["donor"]["session_id"] = "not-an-identifier"
        self.guard_plan(change, "native-target-identity")

    def test_guard_donor_store_parent(self):
        def change(p):
            p["donor"]["path"] = str(self.case / self.donor.name)
        self.guard_plan(change, "native-target-store-mapping")

    def test_guard_donor_store_filename(self):
        def change(p):
            p["donor"]["path"] = str(self.store / 'wrong.jsonl')
        self.guard_plan(change, "native-target-store-mapping")

    def test_guard_donor_digest_type(self):
        def change(p):
            p["donor"]["sha256"] = 12
        self.guard_plan(change, "native-target-digest")

    def test_guard_donor_digest_shape(self):
        def change(p):
            p["donor"]["sha256"] = "not-a-digest"
        self.guard_plan(change, "native-target-digest")

    def test_guard_distinct_targets(self):
        def change(p):
            p["destination"] = copy.deepcopy(p['donor'])
        self.guard_plan(change, "native-two-distinct-containers-required")

    def test_guard_candidate_home(self):
        def change(p):
            p["candidate"] = self.ref(self.donor)
        self.guard_plan(change, "native-candidate-evidence-home")

    def test_guard_artifacts_shape(self):
        def change(p):
            p["artifacts"] = {"one": 1, "two": 2, "three": 3}
        self.guard_plan(change, "native-artifact-list")

    def test_guard_artifacts_count(self):
        def change(p):
            p["artifacts"] = p['artifacts'][:2]
        self.guard_plan(change, "native-artifact-list")

    def test_guard_artifact_shape(self):
        def change(p):
            p["artifacts"][0] = []
        self.guard_plan(change, "native-artifact-object")

    def test_guard_artifact_name_type(self):
        def change(p):
            p["artifacts"][0]["name"] = 12
        self.guard_plan(change, "native-artifact-name")

    def test_guard_artifact_name_shape(self):
        def change(p):
            p["artifacts"][0]["name"] = "Bad Name!"
        self.guard_plan(change, "native-artifact-name")

    def test_guard_artifact_name_unique(self):
        def change(p):
            p["artifacts"][1]["name"] = "capsule"
        self.guard_plan(change, "native-artifact-name")

    def test_guard_artifact_reserved_name(self):
        def change(p):
            p["artifacts"][0]["name"] = "candidate"
        self.guard_plan(change, "native-artifact-name")

    def test_guard_artifact_home(self):
        def change(p):
            p["artifacts"][0]["path"] = str(self.donor)
            p["artifacts"][0]["sha256"] = self.sha(self.donor)
        self.guard_plan(change, "native-artifact-evidence-home")

    def test_guard_artifact_required_names(self):
        def change(p):
            p["artifacts"][0]["name"] = "other"
        self.guard_plan(change, "native-required-staged-objects")

    def test_guard_custody_roots_shape(self):
        def change(p):
            p["custody_roots"] = {"one": 1, "two": 2}
        self.guard_plan(change, "native-custody-roots")

    def test_guard_custody_roots_count(self):
        def change(p):
            p["custody_roots"] = p['custody_roots'][:1]
        self.guard_plan(change, "native-custody-roots")

    def test_guard_rows_type(self):
        def change(r):
            r["identities"] = {"invented": []}
        self.guard_registry(change, "native-registry-rows")

    def test_guard_rows_empty(self):
        def change(r):
            r["identities"] = []
        self.guard_registry(change, "native-registry-rows")

    def test_guard_row_type(self):
        def change(r):
            r["identities"][1] = []
        self.guard_registry(change, "native-registry-row")

    def test_guard_key_type(self):
        def change(r):
            r["identities"][1]["key"] = 12
        self.guard_registry(change, "native-registry-identity")

    def test_guard_key_shape(self):
        def change(r):
            r["identities"][1]["key"] = "Bad Key!"
        self.guard_registry(change, "native-registry-identity")

    def test_guard_provider(self):
        def change(r):
            r["identities"][1]["provider"] = "other"
        self.guard_registry(change, "native-registry-identity")

    def test_guard_sid_type(self):
        def change(r):
            r["identities"][1]["session_id"] = 12
        self.guard_registry(change, "native-registry-identity")

    def test_guard_sid_shape(self):
        def change(r):
            r["identities"][1]["session_id"] = "invalid identity with spaces"
        self.guard_registry(change, "native-registry-identity")

    def test_guard_project_already_resident(self):
        def change(r):
            r["identities"][1]["room"] = str(self.project)
        self.guard_registry(change, "native-project-already-resident")

    def test_guard_registered_writer_missing(self):
        def change(r):
            r["identities"][0]["key"] = "other-writer"
        self.guard_registry(change, "native-registered-writer-required")

    def test_guard_registered_writer_room(self):
        def change(r):
            r["identities"][0]["room"] = str(self.project / "other")
        self.guard_registry(change, "native-registered-writer-required")


    def test_guard_future_go_time(self):
        result = self.refused(go_change=lambda g: g.__setitem__(
            "at", (dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=5)).isoformat()))
        self.assertEqual(result["reason"], "native-go-time")

    def test_guard_expired_go_time(self):
        result = self.refused(go_change=lambda g: g.__setitem__(
            "at", (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=2)).isoformat()))
        self.assertEqual(result["reason"], "native-go-time")

    def test_guard_quiescence_observation_type(self):
        result = self.refused(proof_change=lambda p: p["quiescence"].__setitem__(0, []))
        self.assertEqual(result["reason"], "native-quiescence-object")

    def test_guard_quiescence_target_snapshot(self):
        result = self.refused(proof_change=lambda p: p["quiescence"][0]["donor"].__setitem__("ino", -1))
        self.assertEqual(result["reason"], "native-quiescence-target-changed")

    def test_guard_quiescence_project_identity(self):
        result = self.refused(proof_change=lambda p: p["quiescence"][0]["project"].__setitem__("ino", -1))
        self.assertEqual(result["reason"], "native-quiescence-project")

    def test_guard_proof_envelope_fields(self):
        for field in ("schema", "operation", "plan_sha256", "action"):
            with self.subTest(field=field):
                result = self.refused(proof_change=lambda p, f=field: p.__setitem__(f, "wrong"))
                self.assertEqual(result["reason"], "native-proof-binding")

    def test_guard_i2_exact_shape(self):
        result = self.refused(proof_change=lambda p: self.change_instrument(
            p, "I2", lambda r: r.__setitem__("unknown", 0)))
        self.assertEqual(result["reason"], "native-i2-shape")


    def test_guard_missing_plan_argument(self):
        # The CLI without a plan takes the fixture refusal path. Exercise the
        # operation constructor directly to check its independent guard.
        args = ROTATE.build_parser().parse_args(self.prepare("disposable-exercise"))
        args.native_plan = None
        before = self.inventory(self.base)
        with self.assertRaisesRegex(ROTATE.Refused, "^native-hash-bound-plan-required$"):
            ROTATE.NativeOperation(args)
        self.assertEqual(self.inventory(self.base), before)

    def test_guard_missing_plan_hash_argument(self):
        def edit(args):
            index = args.index("--native-plan-sha256")
            del args[index:index + 2]
        result = self.refused(edit_args=edit)
        self.assertEqual(result["reason"], "native-hash-bound-plan-required")

    def guard_moved_record(self, flag, path, reason):
        moved = self.base / (path.name + ".moved")
        self.put(moved, path.read_bytes())
        def edit(args):
            # prepare() finishes generating the go/proof before this move.
            self.put(moved, path.read_bytes())
            args[args.index(flag) + 1] = str(moved)
        result = self.refused(edit_args=edit)
        self.assertEqual(result["reason"], reason)
        self.assertFalse(self.state_path.exists())

    def test_guard_plan_evidence_home(self):
        self.guard_moved_record("--native-plan", self.plan_path, "native-operation-evidence-home")

    def test_guard_go_evidence_home(self):
        self.put(self.go_path, {})
        self.guard_moved_record("--native-go", self.go_path, "native-go-proof-evidence-home")

    def test_guard_proof_evidence_home(self):
        self.put(self.proof_path, {})
        self.guard_moved_record("--native-proof", self.proof_path, "native-go-proof-evidence-home")

    def test_guard_custody_overlaps_room(self):
        def change(p):
            self.roots[0] = self.room
            p["custody_roots"] = list(map(str, self.roots))
        self.guard_plan(change, "native-custody-overlap")

    def quantifier_overlap(self, selected, direction, position):
        target = getattr(self, selected)
        root = target.parent if direction == "ancestor" else target / "custody-child"
        self.mkdir(root)
        self.assertNotEqual(root, target)
        self.assertEqual(root.is_relative_to(target), direction == "descendant")
        self.assertEqual(target.is_relative_to(root), direction == "ancestor")
        for other in ("room", "project", "store"):
            if other != selected:
                unrelated = getattr(self, other)
                self.assertFalse(root.is_relative_to(unrelated) or unrelated.is_relative_to(root))
        def change(plan):
            self.roots[position] = root
            plan["custody_roots"] = list(map(str, self.roots))
        self.guard_plan(change, "native-custody-overlap")
        self.assertEqual(self.before, self.after)
        self.assertFalse(self.state_home.exists())

    def quantifier_registered_target(self, provider, target):
        sid = SID if target == "donor" else DESTINATION
        def change(registry):
            registry["identities"].append({
                "key": "fixture-bound-target", "person": "Invented Registered Target",
                "role": "Resident", "provider": provider, "session_id": sid,
                "room": str(self.room)})
        self.guard_registry(change, "native-target-is-resident")
        self.assertEqual(self.before, self.after)
        self.assertFalse(self.state_home.exists())

    def quantifier_allowed_pristine_envelope(self, kind):
        rows = copy.deepcopy(self.pristine_rows)
        rows.append({"type": kind, "sessionId": DESTINATION})
        self.put_rows(self.destination, rows)
        self.pristine_bytes = self.destination.read_bytes()
        self.plan["destination"].update(self.ref(self.destination))
        self.gates["pristine_sha256"] = self.sha(self.destination)
        self.put(self.gates_path, self.gates)
        next(item for item in self.plan["artifacts"] if item["name"] == "gates").update(self.ref(self.gates_path))
        self.put(self.plan_path, self.plan)
        before = self.inventory(self.store)
        self.stop("disposable-exercise", "admitted")
        self.assertEqual(self.inventory(self.store), before)
        self.assertEqual(self.destination.read_bytes(), self.pristine_bytes)

    def test_quantifier_custody_any_to_all_under_uniform_guard_fault(self):
        """Local branch contract, not a reachable unsafe-input counterexample.

        any/all are equivalent for the nonempty uniform booleans enforced
        immediately before this branch. Inject precisely that guard's fault
        to expose partial presence; every other check still executes.
        A partial existing item must never enter the add-new-member branch.
        The ordinary partial-presence refusal has its own unmodified test.
        """
        self.preserve()
        copies = [root / "sessions-fixture-writer-20261109" / (self.operation + "-donor")
                  for root in self.roots]
        copies[1].unlink()
        kept = copies[0].read_bytes()
        real_require = ROTATE.require
        observed = []
        def require(condition, reason):
            if reason == "native-partial-custody-item":
                observed.append(condition)
                return
            return real_require(condition, reason)
        with mock.patch.object(ROTATE, "require", side_effect=require), \
                mock.patch.object(self.custody, "cmd_add", return_value=2) as add, \
                mock.patch.object(ROTATE, "native_read", wraps=ROTATE.native_read) as read:
            self.refused("custody")
            add.assert_not_called()
            # The original branch re-verifies the existing member. An
            # all-mutant instead takes the missing-item branch and refuses
            # before that read, even though both outer calls refuse.
            self.assertIn(copies[0], [call.args[0] for call in read.call_args_list])
        self.assertEqual(observed, [False])
        self.assertEqual(copies[0].read_bytes(), kept)
        self.assertFalse(copies[1].exists())
        self.assertEqual(self.before, self.after)

    def test_guard_instrument_output_path(self):
        def change(proof):
            binding = proof["instruments"]["I2"]
            wrong = self.case / "different-result.json"
            self.put(wrong, Path(binding["record"]["path"]).read_bytes())
            binding["record"] = self.ref(wrong)
        result = self.refused(proof_change=change)
        self.assertEqual(result["reason"], "native-instrument-output-path")

    def test_guard_instrument_ref_type(self):
        def change(proof):
            proof["instruments"]["I2"]["packet"] = []
        result = self.refused(proof_change=change)
        self.assertEqual(result["reason"], "native-instrument-evidence-home")

    def test_guard_instrument_ref_home(self):
        def change(proof):
            binding = proof["instruments"]["I2"]
            wrong = self.base / "outside-packet.json"
            self.put(wrong, Path(binding["packet"]["path"]).read_bytes())
            binding["packet"] = self.ref(wrong)
        result = self.refused(proof_change=change)
        self.assertEqual(result["reason"], "native-instrument-evidence-home")


    def guard_native_body(self, which, change, reason):
        path = self.destination if which == "destination" else self.candidate_path
        def edit(p):
            rows = [json.loads(line) for line in path.read_bytes().splitlines()]
            change(rows)
            self.put_rows(path, rows)
            p[which]["sha256"] = self.sha(path)
            # Bind fresh snapshots after an intentional fixture change; do not
            # let quiescence hide the body-shape predicate under test.
            proof = json.loads(self.proof_path.read_bytes())
            for observation in proof["quiescence"]:
                observation["destination"] = self.snapshot(self.destination)
            self.put(self.proof_path, proof)
        self.guard_plan(edit, reason)

    def test_guard_pristine_dialogue_sequence(self):
        self.guard_native_body("destination", lambda rows: rows.append(
            self.row("assistant", 13, 12, "Extra invented reply.", sid=DESTINATION)),
            "native-pristine-first-exchange")

    def test_guard_pristine_user_prompt(self):
        self.guard_native_body("destination", lambda rows: rows[1]["message"].__setitem__("content", "Other prompt."),
                               "native-pristine-inert-exchange")

    def test_guard_pristine_assistant_reply(self):
        self.guard_native_body("destination", lambda rows: rows[2]["message"].__setitem__("content", "Other reply."),
                               "native-pristine-inert-exchange")

    def test_guard_pristine_envelope(self):
        self.guard_native_body("destination", lambda rows: rows.append({"type": "unknown", "sessionId": DESTINATION}),
                               "native-pristine-unknown-envelope")

    def test_guard_candidate_boundary_type(self):
        self.guard_native_body("candidate", lambda rows: rows[0].__setitem__("type", "user"),
                               "native-candidate-boundary")

    def test_guard_candidate_boundary_subtype(self):
        self.guard_native_body("candidate", lambda rows: rows[0].__setitem__("subtype", "unknown"),
                               "native-candidate-boundary")

    def guard_native_gates(self, change, reason):
        def edit(p):
            gates = copy.deepcopy(self.gates)
            change(gates)
            self.put(self.gates_path, gates)
            for item in p["artifacts"]:
                if item["name"] == "gates":
                    item["sha256"] = self.sha(self.gates_path)
        self.guard_plan(edit, reason)

    def test_guard_preparation_schema(self):
        self.guard_native_gates(lambda g: g.__setitem__("schema", "wrong"), "native-preparation-gates-required")

    def test_guard_preparation_phase(self):
        self.guard_native_gates(lambda g: g.__setitem__("phase", 4), "native-preparation-gates-required")

    def test_guard_preparation_object_bindings(self):
        for field in ("donor_sha256", "pristine_sha256", "candidate_sha256"):
            with self.subTest(field=field):
                self.guard_native_gates(lambda g, f=field: g.__setitem__(f, "0" * 64),
                                        "native-preparation-binding")


    # Insertion-only methods for NativeDisposableTests. No setUp override.
    # Author proposals: not executed by the worker.

    def survivor_expect_exact_refusal(self, reason, action="disposable-exercise", **kwargs):
        before_store = self.inventory(self.store)
        before_project = self.inventory(self.project)
        before_custody = [self.inventory(root) for root in self.roots]
        before_state = self.state_path.read_bytes() if self.state_path.exists() else None
        preimages = self.state_home / "preimages.json"
        before_preimages = preimages.read_bytes() if preimages.exists() else None
        rc, result = self.invoke(action, **kwargs)
        self.assertEqual(rc, 2, result)
        self.assertEqual(result["status"], "refused", result)
        self.assertEqual(result["reason"], reason, result)
        self.assertEqual(self.inventory(self.store), before_store)
        self.assertEqual(self.inventory(self.project), before_project)
        self.assertEqual([self.inventory(root) for root in self.roots], before_custody)
        self.assertEqual(self.state_path.read_bytes() if self.state_path.exists() else None, before_state)
        self.assertEqual(preimages.read_bytes() if preimages.exists() else None, before_preimages)
        self.assertIs(result["operator_accepted"], False)
        return result

    def survivor_bind_registry(self):
        self.put(self.registry_path, self.registry)
        self.plan["registry"] = self.ref(self.registry_path)
        self.put(self.plan_path, self.plan)

    def survivor_bind_gates(self, checks):
        gates = copy.deepcopy(self.gates)
        gates["gates"] = checks
        self.put(self.gates_path, gates)
        next(item for item in self.plan["artifacts"] if item["name"] == "gates").update(self.ref(self.gates_path))
        self.put(self.plan_path, self.plan)

    def survivor_replace_observer_record(self, proof, name, value, index=None):
        binding = proof["instruments"][name]
        if index is not None:
            binding = binding[index]
        path = Path(binding["record"]["path"])
        self.put(path, value)
        binding["record"] = self.ref(path)
        if name == "I1":
            stamp = dt.datetime.fromisoformat(proof["quiescence"][index]["at"]).timestamp()
            os.utime(path, (stamp, stamp))

    def survivor_bind_review_auditor(self, proof, auditor):
        audit = proof["custody_audit"]
        audit["auditor"] = auditor
        path = Path(audit["review"]["path"])
        review = json.loads(path.read_bytes())
        review["auditor"] = auditor
        self.put(path, review)
        audit["review"] = self.ref(path)

    def test_survivor_native_0037_missing_go_has_the_early_boundary_reason(self):
        def omit(args):
            index = args.index("--native-go")
            del args[index:index + 2]
        self.survivor_expect_exact_refusal("native-named-go-required", edit_args=omit)
        self.assertFalse(self.state_home.exists())
        self.assertEqual(self.before, self.after)

    def test_survivor_native_0038_missing_go_digest_is_checked_separately(self):
        def omit(args):
            index = args.index("--native-go-sha256")
            del args[index:index + 2]
        self.survivor_expect_exact_refusal("native-named-go-required", edit_args=omit)
        self.assertFalse(self.state_home.exists())
        self.assertEqual(self.before, self.after)

    def test_survivor_native_0047_version_type_is_not_only_its_length(self):
        self.plan["provider_version"] = 7
        self.put(self.plan_path, self.plan)
        self.survivor_expect_exact_refusal("native-provider-version")

    def test_survivor_native_0067_duplicate_key_with_distinct_binding(self):
        duplicate = copy.deepcopy(self.registry["identities"][1])
        duplicate["session_id"] = "0000f688-0000-4000-8000-00000000f688"
        self.registry["identities"].append(duplicate)
        self.survivor_bind_registry()
        self.survivor_expect_exact_refusal("native-ambiguous-registry")

    def test_survivor_native_0068_duplicate_binding_with_distinct_key(self):
        duplicate = copy.deepcopy(self.registry["identities"][1])
        duplicate["key"] = "fixture-second-auditor"
        self.registry["identities"].append(duplicate)
        self.survivor_bind_registry()
        self.survivor_expect_exact_refusal("native-ambiguous-registry")

    def test_survivor_native_0081_extra_container_is_not_a_missing_donor(self):
        sid = "0000f699-0000-4000-8000-00000000f699"
        self.put_rows(self.store / (sid + ".jsonl"), [self.row("user", 199, None, "Invented third body.", sid=sid)])
        self.survivor_expect_exact_refusal("native-exact-two-containers-required")
        self.assertFalse(self.state_home.exists())

    def test_survivor_native_0104_changed_opaque_artifact_reaches_its_digest_guard(self):
        self.put(self.capsule, self.capsule.read_bytes() + b"Invented changed artifact.\n")
        self.survivor_expect_exact_refusal("native-reference-hash")
        self.assertFalse(self.state_home.exists())

    def test_survivor_native_0110_binding_has_no_extra_valid_reference(self):
        def extra(proof):
            binding = proof["instruments"]["I2"]
            binding["extra"] = copy.deepcopy(binding["record"])
        self.survivor_expect_exact_refusal("native-instrument-reference-required", proof_change=extra)

    def test_survivor_native_0118_two_item_mapping_is_not_an_observation_list(self):
        def mapping(proof):
            left, right = proof["quiescence"]
            proof["quiescence"] = {"left": left, "right": right}
        self.survivor_expect_exact_refusal("native-two-quiescence-readings", proof_change=mapping)

    def test_survivor_native_0119_third_observation_cannot_be_silently_zip_truncated(self):
        def third(proof):
            proof["quiescence"].append(copy.deepcopy(proof["quiescence"][-1]))
        self.survivor_expect_exact_refusal("native-two-quiescence-readings", proof_change=third)

    def test_survivor_native_0121_two_item_mapping_is_not_an_i1_list(self):
        def mapping(proof):
            left, right = proof["instruments"]["I1"]
            proof["instruments"]["I1"] = {"left": left, "right": right}
        self.survivor_expect_exact_refusal("native-two-i1-records-required", proof_change=mapping)

    def test_survivor_native_0122_third_i1_binding_cannot_be_silently_zip_truncated(self):
        def third(proof):
            bindings = proof["instruments"]["I1"]
            bindings.append(copy.deepcopy(bindings[-1]))
        self.survivor_expect_exact_refusal("native-two-i1-records-required", proof_change=third)

    def test_survivor_native_0128_false_is_not_an_integer_process_count(self):
        for field in ("holders", "session_records", "argument_holders", "locks", "unreadable", "foreign_processes"):
            with self.subTest(field=field):
                self.survivor_expect_exact_refusal(
                    "native-quiescence-" + field.replace("_", "-"),
                    proof_change=lambda p, key=field: p["quiescence"][0].__setitem__(key, False))

    def test_survivor_native_0132_foreign_boolean_has_its_own_type_guard(self):
        def foreign_false(proof):
            self.survivor_replace_observer_record(
                proof, "I1", {"held": [], "own_unreadable": 0, "foreign_unreadable": False}, index=0)
        self.survivor_expect_exact_refusal("native-i1-count-type", proof_change=foreign_false)

    def test_survivor_native_0163_gate_names_in_a_list_are_not_a_gate_mapping(self):
        self.survivor_bind_gates(list(self.gates["gates"]))
        self.survivor_expect_exact_refusal("native-preparation-incomplete")

    def test_survivor_native_0164_true_gates_cannot_omit_one_required_name(self):
        checks = dict(self.gates["gates"])
        del checks["media"]
        self.survivor_bind_gates(checks)
        self.survivor_expect_exact_refusal("native-preparation-incomplete")

    def test_survivor_native_0185_null_audit_has_the_typed_contract_reason(self):
        self.preserve()
        self.survivor_expect_exact_refusal("native-independent-custody-audit-required", "install",
                                          proof_change=lambda p: p.__setitem__("custody_audit", None))

    def test_survivor_native_0186_outer_audit_manifest_must_match(self):
        self.preserve()
        self.survivor_expect_exact_refusal("native-independent-custody-audit-required", "install",
            proof_change=lambda p: p["custody_audit"].__setitem__("manifest_sha256", "0" * 64))

    def test_survivor_native_0187_consistent_review_cannot_name_an_unregistered_auditor(self):
        self.preserve()
        self.survivor_expect_exact_refusal("native-independent-custody-audit-required", "install",
            proof_change=lambda p: self.survivor_bind_review_auditor(p, "fixture-unregistered-auditor"))

    def test_survivor_native_0188_registered_auditor_cannot_review_own_write(self):
        self.registry["identities"][0]["role"] = "Auditor"
        self.survivor_bind_registry()
        self.preserve()
        self.survivor_expect_exact_refusal("native-independent-custody-audit-required", "install",
            proof_change=lambda p: self.survivor_bind_review_auditor(p, WRITER))

    def test_survivor_native_0189_outer_hold_verdict_is_not_a_pass(self):
        self.preserve()
        self.survivor_expect_exact_refusal("native-independent-custody-audit-required", "install",
            proof_change=lambda p: p["custody_audit"].__setitem__("verdict", "HOLD"))

    def test_survivor_native_0231_valid_append_on_replaced_inode_is_not_owned(self):
        self.preserve()
        self.install()
        appended = self.append_reply()
        replacement = self.case / "replacement-destination.jsonl"
        self.put(replacement, appended)
        os.replace(replacement, self.destination)
        self.survivor_expect_exact_refusal("native-rollback-unknown-destination", "rollback",
            proof_change=lambda p: p.__setitem__("appended_sha256", hashlib.sha256(appended).hexdigest()))

    def test_survivor_native_0232_matching_append_digest_does_not_authorize_a_changed_prefix(self):
        self.preserve()
        self.install()
        appended = self.append_reply()
        changed = b"[" + appended[1:]
        self.put(self.destination, changed)
        self.survivor_expect_exact_refusal("native-rollback-unknown-destination", "rollback",
            proof_change=lambda p: p.__setitem__("appended_sha256", hashlib.sha256(changed).hexdigest()))

    def test_survivor_native_0238_null_i5_has_the_typed_contract_reason(self):
        self.preserve()
        self.install()
        self.stop("rollback", "rollback-restored")
        # The strict JSON reader already rejects a top-level null. Isolate the
        # downstream defensive contract with an explicit decoder fault; this
        # is not an unsafe JSON-admission claim.
        original = ROTATE.NativeOperation.instrument
        def decoder_fault(operation, name, binding=None):
            if name == "I5":
                return None, binding
            return original(operation, name, binding)
        with mock.patch.object(ROTATE.NativeOperation, "instrument", new=decoder_fault):
            self.survivor_expect_exact_refusal("native-i5-inverse-not-clear", "rollback", reuse_go=True)

    def test_survivor_native_0239_i5_with_an_extra_field_is_not_the_exact_contract(self):
        self.preserve()
        self.install()
        self.stop("rollback", "rollback-restored")
        self.survivor_expect_exact_refusal("native-i5-inverse-not-clear", "rollback", reuse_go=True,
            proof_change=lambda p: self.survivor_replace_observer_record(
                p, "I5", {"differences": [], "notes": [], "unexpected": True}))

    def test_survivor_native_0241_i5_notes_need_their_own_list_type(self):
        self.preserve()
        self.install()
        self.stop("rollback", "rollback-restored")
        self.survivor_expect_exact_refusal("native-i5-inverse-not-clear", "rollback", reuse_go=True,
            proof_change=lambda p: self.survivor_replace_observer_record(p, "I5", {"differences": [], "notes": {}}))


    # Insert these methods into NativeDisposableTests. No new class or setUp.
    # Author-side proposals only: this worker has not executed these methods.

    def _lifecycle_expect_reason(self, reason, action="disposable-exercise", **kwargs):
        before = self.inventory(self.store)
        result = self.refused(action, **kwargs)
        self.assertEqual(result["reason"], reason, result)
        self.assertEqual(self.inventory(self.store), before)
        return result

    def _lifecycle_refresh_fixture_refs(self, *, gates_bindings=True):
        # Rebind only invented fixture bytes; keep the negative under test intact.
        for name, path in (("donor", self.donor), ("destination", self.destination)):
            self.plan[name].update(self.ref(path))
        self.plan["candidate"] = self.ref(self.candidate_path)
        if gates_bindings:
            self.gates.update(donor_sha256=self.sha(self.donor),
                              pristine_sha256=self.sha(self.destination),
                              candidate_sha256=self.sha(self.candidate_path))
        self.put(self.gates_path, self.gates)
        for item in self.plan["artifacts"]:
            item.update(self.ref(Path(item["path"])))
        self.put(self.plan_path, self.plan)

    def test_lifecycle_install_go_targets_are_independently_bound(self):
        # native-0179, 0180, 0181, 0182.
        self.preserve()
        for field in ("pristine_sha256", "candidate_sha256", "custody_manifest_sha256", "inverse"):
            with self.subTest(field=field):
                self._lifecycle_expect_reason("native-install-go-targets", "install",
                    go_change=lambda go, field=field: go.__setitem__(field, "wrong"))

    def test_lifecycle_install_go_must_postdate_custody(self):
        # native-0183. Equal timestamps are not post-custody authority.
        self.preserve()
        state = json.loads(self.state_path.read_bytes())
        self._lifecycle_expect_reason("native-install-go-before-custody", "install",
            go_change=lambda go: go.__setitem__("at", state["custody_at"]))

    def test_lifecycle_audit_review_must_remain_inside_the_case(self):
        # native-0190. The review remains valid, private and hash-bound.
        self.preserve()
        def outside(proof):
            review = proof["custody_audit"]["review"]
            path = self.base / "outside-review.json"
            self.put(path, Path(review["path"]).read_bytes())
            proof["custody_audit"]["review"] = self.ref(path)
        self._lifecycle_expect_reason("native-custody-audit-evidence-home", "install",
                                      proof_change=outside)

    def test_lifecycle_audit_review_fields_are_bound(self):
        # native-0191: the report inventories this all(...) as one atomic row.
        self.preserve()
        for field in ("schema", "operation", "plan_sha256", "manifest_sha256", "auditor", "verdict"):
            with self.subTest(field=field):
                def alter(proof, field=field):
                    reference = proof["custody_audit"]["review"]
                    path = Path(reference["path"])
                    review = json.loads(path.read_bytes())
                    review[field] = "wrong"
                    self.put(path, review)
                    proof["custody_audit"]["review"] = self.ref(path)
                self._lifecycle_expect_reason("native-custody-audit-review-binding", "install",
                                              proof_change=alter)

    def test_lifecycle_install_resume_rejects_a_new_go_digest(self):
        # native-0195. The fresh invocation intentionally does not reuse the go.
        self.preserve()
        self.stop("install", "install-prepared")
        self._lifecycle_expect_reason("native-install-resume-go-changed", "install")

    def test_lifecycle_install_rejects_changed_recorded_stage(self):
        # native-0199. The changed stage is preserved, never silently rebuilt.
        self.preserve()
        self.stop("install", "install-prepared")
        self.put(self.stage, b"Invented changed staged bytes.\n")
        self._lifecycle_expect_reason("native-stage-changed", "install", reuse_go=True)

    def test_lifecycle_export_rejects_changed_recorded_stage(self):
        # native-0251. Export must not turn a changed stage into a new baseline.
        self.preserve()
        self.stop("install", "install-prepared")
        self.put(self.stage, b"Invented changed staged bytes.\n")
        self._lifecycle_expect_reason("native-stage-changed", "install", reuse_go=True,
            edit_args=lambda args: args.append("--native-export-instruments"))

    def test_lifecycle_checkpoint_envelope_fields_are_checked(self):
        # native-0246: this all(...) is one atomic report row.
        self.stop("disposable-exercise", "admitted")
        original = json.loads(self.state_path.read_bytes())
        for field in ("schema", "operation", "plan_sha256"):
            with self.subTest(field=field):
                changed = copy.deepcopy(original)
                changed[field] = "wrong"
                self.put(self.state_path, changed)
                self._lifecycle_expect_reason("native-checkpoint-binding", "custody")
        self.put(self.state_path, original)

    def test_lifecycle_checkpoint_preimage_digest_is_checked(self):
        # native-0247. The actual preimage file is kept intact.
        self.stop("disposable-exercise", "admitted")
        state = json.loads(self.state_path.read_bytes())
        state["preimages_sha256"] = "0" * 64
        self.put(self.state_path, state)
        self._lifecycle_expect_reason("native-preimages-changed", "custody")

    def test_lifecycle_nonadmission_action_cannot_create_a_checkpoint(self):
        # native-0248. No checkpoint or preimages exist yet.
        self._lifecycle_expect_reason("native-admission-required", "custody")

    def test_lifecycle_orphan_preimages_are_not_replaced(self):
        # native-0249. A failed admission's retained preimages are not absence.
        path = self.state_home / "preimages.json"
        self.put(path, {"invented": "retained interrupted admission"})
        before = path.read_bytes()
        self._lifecycle_expect_reason("native-admission-required")
        self.assertEqual(path.read_bytes(), before)

    def test_lifecycle_existing_empty_state_home_cannot_export_as_admitted(self):
        # native-0250. Existing directory, but no state or preimages file.
        self.mkdir(self.state_home)
        self._lifecycle_expect_reason("native-admission-required",
            edit_args=lambda args: args.append("--native-export-instruments"))

    def test_lifecycle_initial_export_requires_admission_action(self):
        # native-0242. Constructor inputs and the synthetic proof are otherwise valid.
        self._lifecycle_expect_reason("native-initial-export-action", "custody",
            edit_args=lambda args: args.append("--native-export-instruments"))


    # Append to NativeDisposableTests after the selected earlier lifecycle methods.
    # Requires the existing _lifecycle_expect_reason helper. No subclass/setUp.
    # These are unexecuted author-side proposals, not mutation results.

    def test_remaining_custody_member_bytes_are_reverified(self):
        # native-0173. Both manifests continue to agree; only copied bytes drift.
        self.preserve()
        alias = self.operation + "-donor"
        for root in self.roots:
            copied = root / "sessions-fixture-writer-20261109" / alias
            self.put(copied, copied.read_bytes() + b"Invented custody drift.\n")
        self._lifecycle_expect_reason("native-custody-member-hash", "custody")

    def test_remaining_custody_manifest_binds_the_actual_member(self):
        # native-0174. Alter the same valid digest field on both open manifests.
        # Discover the manifest by its exact member row, not an assumed filename.
        self.preserve()
        alias = self.operation + "-donor"
        expected = self.sha(self.donor)
        for root in self.roots:
            batch = root / "sessions-fixture-writer-20261109"
            changed = []
            for path in batch.iterdir():
                if not path.is_file():
                    continue
                raw = path.read_bytes()
                lines = raw.splitlines(keepends=True)
                matches = [i for i, line in enumerate(lines)
                           if line.decode("ascii").rstrip("\r\n").split("  ")[:2] == [expected, alias]]
                if matches:
                    self.assertEqual(len(matches), 1)
                    index = matches[0]
                    lines[index] = b"0" * 64 + lines[index][64:]
                    self.put(path, b"".join(lines))
                    changed.append(path)
            self.assertEqual(len(changed), 1)
            self.assertEqual(self.sha(batch / alias), expected)
        self._lifecycle_expect_reason("native-custody-member-manifest", "custody")

    def test_remaining_load_rejects_a_replacement_inode(self):
        # native-0207. Valid appended bytes are retained on a different inode.
        self.preserve()
        self.install()
        raw = self.append_reply()
        replacement = self.store / "invented-replacement.fixture"
        self.put(replacement, raw)
        os.replace(replacement, self.destination)
        self._lifecycle_expect_reason("native-load-inode-changed", "load",
                                      proof_change=self.gauge_proof)

    def test_remaining_load_requires_bytes_beyond_the_install(self):
        # native-0208. The installed body and its inode are otherwise untouched.
        self.preserve()
        self.install()
        self._lifecycle_expect_reason("native-load-prefix-changed", "load")

    def test_remaining_load_requires_the_exact_installed_prefix(self):
        # native-0209. Keep JSON, byte length, inode and appended chain valid.
        self.preserve()
        self.install()
        raw = self.append_reply()
        marker = b"Invented capsule only."
        index = raw.index(marker)
        changed = raw[:index] + b"X" + raw[index + 1:]
        self.assertEqual(len(changed), len(raw))
        self.put(self.destination, changed)
        self._lifecycle_expect_reason("native-load-prefix-changed", "load",
                                      proof_change=self.gauge_proof)

    def test_remaining_load_validates_gauge_output_before_acceptance(self):
        # native-0211, 0212, 0213. Only the reader's returned data is modeled;
        # NativeOperation.load and all require calls remain real and unpatched.
        self.preserve()
        self.install()
        self.append_reply()
        gauge = ROTATE.sibling("gauge")
        original = gauge.read_claude(self.destination)
        real_sibling = ROTATE.sibling
        for field, value in (("tokens", True), ("tokens", 0), ("compaction_after", True)):
            with self.subTest(field=field, value=value):
                reading = copy.deepcopy(original)
                reading[field] = value
                # sibling() creates a new module each time. Bind this exact
                # synthetic reader into the path the operation really calls.
                with mock.patch.object(ROTATE, "sibling", side_effect=lambda name:
                        gauge if name == "gauge" else real_sibling(name)), \
                        mock.patch.object(gauge, "read_claude", return_value=reading):
                    self._lifecycle_expect_reason("native-load-first-gauge-unproved", "load",
                                                  proof_change=self.gauge_proof)

    def test_load_refuses_a_reading_carried_in_the_installed_prefix(self):
        # Review finding on #79: an append with no usable usage must not borrow the prefix's reading.
        self.preserve()
        self.install()
        row = self.row("assistant", 101, 5, [{"type": "text", "text": "Invented appended reply."}], sid=DESTINATION)
        row["message"].update(id="invented-call", model="claude-sonnet-4-5-20250929",
                              usage={"input_tokens": 0, "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0})
        self.put(self.destination, self.destination.read_bytes() + json.dumps(row).encode() + b"\n")
        gauge = ROTATE.sibling("gauge")
        carried = {"tokens": 123, "model": "claude-sonnet-4-5-20250929", "reading_at": "2026-11-09T00:00:00Z",
                   "call": "invented-carried-call", "compaction_after": None}
        real_sibling = ROTATE.sibling
        def supplied(proof):
            proof["first_gauge"] = dict(carried)
        with mock.patch.object(ROTATE, "sibling", side_effect=lambda name:
                gauge if name == "gauge" else real_sibling(name)), \
                mock.patch.object(gauge, "read_claude", return_value=dict(carried)):
            self._lifecycle_expect_reason("native-load-gauge-not-appended", "load", proof_change=supplied)

    def test_remaining_load_requires_a_gauge_proof_object(self):
        # native-0214. Real synthetic append and gauge; wrong supplied shape only.
        self.preserve()
        self.install()
        self.append_reply()
        self._lifecycle_expect_reason("native-load-gauge-mismatch", "load",
            proof_change=lambda proof: proof.__setitem__("first_gauge", []))

    def test_remaining_load_binds_each_supplied_gauge_field(self):
        # native-0215 is one atomic all(...) inventory row.
        self.preserve()
        self.install()
        self.append_reply()
        for field in ("tokens", "model", "reading_at", "call"):
            with self.subTest(field=field):
                def mismatch(proof, field=field):
                    self.gauge_proof(proof)
                    proof["first_gauge"][field] = "invented-mismatch"
                self._lifecycle_expect_reason("native-load-gauge-mismatch", "load",
                                              proof_change=mismatch)

    def test_remaining_pending_state_blocks_before_the_action(self):
        # native-0244. A forwarding spy retains every real preserve guard.
        # It distinguishes early refusal from the same reason in save().
        self.stop("disposable-exercise", "admitted")
        pending = self.state_home / ".state.NEW"
        self.put(pending, b"Invented interrupted state write.\n")
        old_state = self.state_path.read_bytes()
        real_preserve = ROTATE.NativeOperation.preserve
        with mock.patch.object(ROTATE.NativeOperation, "preserve", autospec=True,
                               side_effect=real_preserve) as action:
            self._lifecycle_expect_reason("native-pending-state-write", "custody")
            action.assert_not_called()
        self.assertEqual(self.state_path.read_bytes(), old_state)
        self.assertEqual(pending.read_bytes(), b"Invented interrupted state write.\n")

    def test_remaining_pending_packets_block_before_the_action(self):
        # native-0245. Without the early gate, publication could refuse too late.
        self.stop("disposable-exercise", "admitted")
        pending = self.state_home / ".packets.NEW"
        self.put(pending, b"Invented interrupted packet export.\n")
        old_state = self.state_path.read_bytes()
        real_preserve = ROTATE.NativeOperation.preserve
        with mock.patch.object(ROTATE.NativeOperation, "preserve", autospec=True,
                               side_effect=real_preserve) as action:
            self._lifecycle_expect_reason("native-pending-packet-export", "custody")
            action.assert_not_called()
        self.assertEqual(self.state_path.read_bytes(), old_state)
        self.assertEqual(pending.read_bytes(), b"Invented interrupted packet export.\n")

    def test_remaining_rollback_go_names_the_current_destination(self):
        # native-0227. Refusal precedes any restore or append-custody act.
        self.preserve()
        self.install()
        self._lifecycle_expect_reason("native-rollback-go-postimage", "rollback",
            go_change=lambda go: go.__setitem__("destination_sha256", "0" * 64))

    def test_remaining_rollback_resume_requires_the_original_go(self):
        # native-0226. The first permitted restore is setup, not the attempted act.
        self.preserve()
        self.install()
        self.stop("rollback", "rollback-restored")
        self._lifecycle_expect_reason("native-rollback-resume-go-changed", "rollback")

    def test_remaining_custody_rejects_an_installed_phase(self):
        # native-0175. Explicit malformed checkpoint-phase fixture only.
        self.stop("disposable-exercise", "admitted")
        state = json.loads(self.state_path.read_bytes())
        state["phase"] = "installed"
        self.put(self.state_path, state)
        self._lifecycle_expect_reason("native-custody-phase", "custody")

    def test_remaining_install_requires_a_custodied_phase(self):
        # native-0178. Supply normal-shaped go fields without inventing custody.
        self.stop("disposable-exercise", "admitted")
        self.custody_result = {"custody_manifest_sha256": "0" * 64}
        self._lifecycle_expect_reason("native-install-phase", "install")

    def test_remaining_load_requires_an_installed_phase(self):
        # native-0206. Preserve real install evidence; make only its phase invalid.
        self.preserve()
        self.install()
        state = json.loads(self.state_path.read_bytes())
        state["phase"] = "admitted"
        self.put(self.state_path, state)
        self._lifecycle_expect_reason("native-load-phase", "load")

    def test_remaining_rollback_rejects_a_merely_admitted_phase(self):
        # native-0225. No custody was taken, so no inverse is available.
        self.stop("disposable-exercise", "admitted")
        self._lifecycle_expect_reason("native-rollback-phase", "rollback")


    def test_guard_artifacts_upper_count(self):
        self.guard_plan(lambda p: p.__setitem__("artifacts", p["artifacts"] * 22), "native-artifact-list")

    def test_guard_custody_roots_upper_count(self):
        self.guard_plan(lambda p: p.__setitem__("custody_roots", [str(self.roots[0])] * 5), "native-custody-roots")

    def test_guard_quiescence_cannot_come_from_the_future(self):
        result = self.refused(proof_change=lambda p: p["quiescence"][0].__setitem__(
            "at", (dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=1)).isoformat()))
        self.assertEqual(result["reason"], "native-quiescence-stale")

    def test_guard_i1_record_cannot_come_from_the_future(self):
        def change(proof):
            future = time.time() + 60
            os.utime(proof["instruments"]["I1"][0]["record"]["path"], (future, future))
        result = self.refused(proof_change=change)
        self.assertEqual(result["reason"], "native-i1-record-stale")


    # Insert into NativeDisposableTests. Uses _lifecycle_expect_reason.
    # Unexecuted author-side proposals; no subclass, setUp or target-guard mocks.

    def test_inventory_extra_nonjsonl_store_name_blocks_readmission(self):
        # native-0145. The exact-two JSONL admission condition remains satisfied.
        self.stop("disposable-exercise", "admitted")
        self.put(self.store / "invented-unrelated.txt", b"Invented extra file.\n")
        self._lifecycle_expect_reason("native-store-listing-changed")

    def test_inventory_changed_existing_store_entry_blocks_readmission(self):
        # native-0146. Names and both JSONL bodies remain unchanged.
        self.stop("disposable-exercise", "admitted")
        self.put(self.store / "unrelated.bin", b"Invented changed baseline bytes.\n")
        self._lifecycle_expect_reason("native-store-entry-changed")

    def test_inventory_new_private_project_file_blocks_readmission(self):
        # native-0147. No store object or store name changes.
        self.stop("disposable-exercise", "admitted")
        self.put(self.project / "invented-project.txt", b"Invented project change.\n")
        self._lifecycle_expect_reason("native-project-listing-changed")

    def test_inventory_custodied_operation_cannot_be_readmitted(self):
        # native-0149. Real preserve setup, not a fabricated state phase.
        self.preserve()
        self._lifecycle_expect_reason("native-operation-already-admitted")

    def test_inventory_changed_pristine_blocks_admission_repeat(self):
        # native-0150. Fresh observations cannot replace the saved pristine.
        self.stop("disposable-exercise", "admitted")
        rows = copy.deepcopy(self.pristine_rows)
        rows[2]["timestamp"] = "2026-11-09T12:00:01Z"
        self.put_rows(self.destination, rows)
        self._lifecycle_expect_reason("native-pristine-changed")

    def test_inventory_partial_custody_member_is_not_completed_implicitly(self):
        # native-0170. Only an owned synthetic custody copy is removed in setup.
        self.preserve()
        alias = self.operation + "-donor"
        retained = self.roots[1] / "sessions-fixture-writer-20261109" / alias
        kept = retained.read_bytes()
        missing = self.roots[0] / "sessions-fixture-writer-20261109" / alias
        missing.unlink()
        self._lifecycle_expect_reason("native-partial-custody-item", "custody")
        self.assertFalse(missing.exists())
        self.assertEqual(retained.read_bytes(), kept)

    def test_inventory_missing_custody_member_requires_explicit_add(self):
        # native-0171. Re-verification does not recreate missing owned copies.
        self.preserve()
        copies = [root / "sessions-fixture-writer-20261109" / (self.operation + "-donor")
                  for root in self.roots]
        for path in copies:
            path.unlink()
        self._lifecycle_expect_reason("native-custody-item-missing", "custody")
        for path in copies:
            self.assertFalse(path.exists())

    def test_inventory_custody_add_failure_is_not_success(self):
        # native-0172. Model only the dependency's exit status, not any require.
        self.stop("disposable-exercise", "admitted")
        with mock.patch.object(self.custody, "cmd_add", return_value=2) as add:
            self._lifecycle_expect_reason("native-custody-add-refused", "custody")
            add.assert_called_once()

    def test_inventory_changed_pristine_blocks_custody_repeat(self):
        # native-0176. Earlier admission and preservation actually completed.
        self.preserve()
        rows = copy.deepcopy(self.pristine_rows)
        rows[2]["timestamp"] = "2026-11-09T12:00:01Z"
        self.put_rows(self.destination, rows)
        self._lifecycle_expect_reason("native-pristine-changed", "custody")

    def _inventory_expect_manifest_digest_reread(self, action):
        # Forward every read to the real reader; observe all custody members.
        # No snapshot, custody, digest or require predicate is replaced.
        expected = {
            root / "sessions-fixture-writer-20261109" / (self.operation + "-" + name)
            for root in self.roots
            for name in ("donor", "destination", "candidate", "preimages",
                         *(item["name"] for item in self.plan["artifacts"]))}
        seen = set()
        real_read = ROTATE.native_read
        def read(path, *args, **kwargs):
            result = real_read(path, *args, **kwargs)
            seen.add(Path(path))
            return result
        with mock.patch.object(ROTATE, "native_read", side_effect=read):
            self._lifecycle_expect_reason("native-custody-manifest-changed", action)
        self.assertTrue(expected <= seen, "not every required custody member was read")
        self.assertEqual(self.destination.read_bytes(), self.pristine_bytes)
        self.assertFalse(self.stage.exists())

    def test_inventory_custody_reverification_checks_checkpoint_manifest_digest(self):
        # native-0177. Change only the state value, not real copies or manifests.
        self.preserve()
        state = json.loads(self.state_path.read_bytes())
        state["custody_manifest_sha256"] = "0" * 64
        self.put(self.state_path, state)
        self._inventory_expect_manifest_digest_reread("custody")

    def test_inventory_install_rereads_copies_despite_matching_go_and_audit(self):
        # native-0184. Fixture go and outer/inner audit follow the changed state
        # digest, so no earlier authority guard can conceal the actual reread.
        self.preserve()
        state = json.loads(self.state_path.read_bytes())
        state["custody_manifest_sha256"] = "0" * 64
        self.put(self.state_path, state)
        self.custody_result = {**self.custody_result, "custody_manifest_sha256": "0" * 64}
        self._inventory_expect_manifest_digest_reread("install")


    def test_guard_reinstall_rejects_an_appended_postimage(self):
        self.preserve()
        self.install()
        self.append_reply()
        self._lifecycle_expect_reason("native-installed-postimage-changed", "install", reuse_go=True)

    def test_guard_after_rename_requires_the_recorded_postimage(self):
        self.preserve()
        self.stop("install", "install-prepared")
        self.stop("install", "install-renamed", reuse_go=True)
        self.append_reply()
        self._lifecycle_expect_reason("native-installed-postimage-changed", "install", reuse_go=True)

    def test_guard_prepared_install_requires_the_same_pristine(self):
        self.preserve()
        self.stop("install", "install-prepared")
        rows = copy.deepcopy(self.pristine_rows)
        rows[2]["timestamp"] = "2026-11-09T12:00:01Z"
        self.put_rows(self.destination, rows)
        self._lifecycle_expect_reason("native-install-preimage-changed", "install", reuse_go=True)

    def test_guard_lost_stage_is_not_proof_of_rename(self):
        self.preserve()
        self.stop("install", "install-prepared")
        self.stage.unlink()
        self._lifecycle_expect_reason("native-install-rename-witness-required", "install", reuse_go=True)

    def test_guard_user_only_append_is_not_an_assistant_wake(self):
        self.preserve()
        self.install()
        row = self.row("user", 101, 5, "An invented prompt without a reply.", sid=DESTINATION)
        self.put(self.destination, self.destination.read_bytes() + json.dumps(row).encode("ascii") + b"\n")
        self._lifecycle_expect_reason("native-load-no-assistant-append", "load")

    def test_guard_rollback_keeps_a_changed_recorded_stage(self):
        self.preserve()
        self.stop("install", "install-prepared")
        self.put(self.stage, b"Invented unexpected staging bytes.\n")
        self._lifecycle_expect_reason("native-rollback-unknown-stage", "rollback")

    def test_guard_rollback_keeps_stage_when_pristine_has_changed(self):
        self.preserve()
        self.stop("install", "install-prepared")
        rows = copy.deepcopy(self.pristine_rows)
        rows[2]["timestamp"] = "2026-11-09T12:00:01Z"
        self.put_rows(self.destination, rows)
        self._lifecycle_expect_reason("native-rollback-unknown-stage", "rollback")

    def test_guard_rollback_append_needs_its_own_digest_evidence(self):
        self.preserve()
        self.install()
        self.append_reply()
        self._lifecycle_expect_reason("native-rollback-append-evidence-required", "rollback")

    def test_guard_rollback_identical_bytes_do_not_authorize_a_replaced_inode(self):
        self.preserve()
        self.install()
        replacement = self.case / "invented-identical-replacement.fixture"
        self.put(replacement, self.destination.read_bytes())
        os.replace(replacement, self.destination)
        self._lifecycle_expect_reason("native-rollback-installed-identity-changed", "rollback")

    def test_guard_rollback_before_install_requires_original_pristine(self):
        self.preserve()
        rows = copy.deepcopy(self.pristine_rows)
        rows[2]["timestamp"] = "2026-11-09T12:00:01Z"
        self.put_rows(self.destination, rows)
        self._lifecycle_expect_reason("native-rollback-pristine-changed", "rollback")


    def _guard_direct_operation(self, action="disposable-exercise", **prepare):
        """Construct the real operation on invented inputs, without run/acts."""
        args = ROTATE.build_parser().parse_args(self.prepare(action, **prepare))
        real_sibling = ROTATE.sibling
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(ROTATE, "sibling", side_effect=lambda name:
                self.mind if name == "mind" else self.custody if name == "custody" else real_sibling(name)))
            stack.enter_context(mock.patch.object(self.mind, "git_exposed", return_value=False))
            stack.enter_context(mock.patch.object(self.custody, "root_device",
                side_effect=lambda p: 101 + self.roots.index(Path(p))))
            stack.enter_context(mock.patch.object(self.custody, "disks",
                side_effect=lambda dev: frozenset({"fixture-disk-" + str(dev)})))
            operation = ROTATE.NativeOperation(args)
        if self.state_path.exists():
            operation.state = json.loads(self.state_path.read_bytes())
            operation.preimages = json.loads((self.state_home / "preimages.json").read_bytes())
        return operation

    def test_guard_export_collision_preserves_the_old_packet(self):
        # Pin only export entropy, not the packet equality predicate.
        with mock.patch.object(ROTATE.os, "urandom", return_value=b"a" * 8):
            self.stop("disposable-exercise", "awaiting-instruments",
                      edit_args=lambda a: a.append("--native-export-instruments"))
            index = json.loads((self.case / "instrument-packets.json").read_bytes())
            path = Path(index["I1"][0]["path"])
            self.put(path, b"Invented retained collision.\n")
            self._lifecycle_expect_reason("native-instrument-export-changed",
                edit_args=lambda a: a.append("--native-export-instruments"))
        self.assertEqual(path.read_bytes(), b"Invented retained collision.\n")

    def test_guard_export_pending_index_is_not_overwritten(self):
        self.put(self.case / ".packets.NEW", b"Invented interrupted export.\n")
        self._lifecycle_expect_reason("native-pending-packet-export",
            edit_args=lambda a: a.append("--native-export-instruments"))
        self.assertEqual((self.case / ".packets.NEW").read_bytes(), b"Invented interrupted export.\n")

    def test_guard_export_rechecks_pending_index_before_replacement(self):
        self.stop("disposable-exercise", "awaiting-instruments",
                  edit_args=lambda a: a.append("--native-export-instruments"))
        pending = self.case / ".packets.NEW"
        real_exists = ROTATE.os.path.lexists
        calls = []
        def race(path):
            if Path(path) == pending:
                calls.append(path)
                if len(calls) == 2:
                    self.put(pending, b"Invented concurrent export.\n")
            return real_exists(path)
        with mock.patch.object(ROTATE.os.path, "lexists", side_effect=race):
            self._lifecycle_expect_reason("native-pending-packet-export",
                edit_args=lambda a: a.append("--native-export-instruments"))
        self.assertEqual(len(calls), 2)
        self.assertEqual(pending.read_bytes(), b"Invented concurrent export.\n")

    def test_guard_save_preserves_an_interrupted_state_file(self):
        operation = self._guard_direct_operation()
        self.mkdir(operation.directory)
        operation.state = {"schema": "invented-state"}
        path = operation.directory / ".state.NEW"
        self.put(path, b"Invented interrupted state.\n")
        before = self.inventory(self.base)
        with self.assertRaisesRegex(ROTATE.Refused, "^native-pending-state-write$"):
            operation.save()
        self.assertEqual(self.inventory(self.base), before)

    def _guard_go_ages_at_act(self, seconds):
        operation = self._guard_direct_operation()
        operation.go["at"] = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=seconds)).isoformat()
        # Exercise the refresh method after admission, not the constructor's
        # independent age check. Hash readers are observed, not bypassed.
        before = self.inventory(self.base)
        with mock.patch.object(operation, "root_identities") as roots, \
                mock.patch.object(operation, "quiescence") as quiet:
            with self.assertRaisesRegex(ROTATE.Refused, "^native-go-expired-at-act$"):
                operation.refresh_at_act()
            roots.assert_not_called()
            quiet.assert_not_called()
        self.assertEqual(self.inventory(self.base), before)

    def test_guard_go_future_at_act(self):
        self._guard_go_ages_at_act(-3600)

    def test_guard_go_expired_at_act(self):
        self._guard_go_ages_at_act(7200)

    def test_guard_donor_residue_is_checked_after_row_validation(self):
        # Typed reader fault isolates the second, independent structural
        # residue scan; normal donor fields already fail native_rows.
        real_rows = ROTATE.native_rows
        def rows(raw, *args, **kwargs):
            result = real_rows(raw, *args, **kwargs)
            if raw == self.candidate_path.read_bytes():
                values, ids, assistant = result
                values = copy.deepcopy(values)
                values[0]["invented_nested"] = {"sessionId": SID}
                return values, ids, assistant
            return result
        with mock.patch.object(ROTATE, "native_rows", side_effect=rows):
            self._lifecycle_expect_reason("native-candidate-donor-residue")

    def test_guard_unknown_stage_is_rechecked_after_listing(self):
        self.preserve()
        real_listing = ROTATE.NativeOperation.listing
        def race(operation, *args, **kwargs):
            result = real_listing(operation, *args, **kwargs)
            if operation.action == "install" and operation.state["phase"] == "custodied":
                self.put(operation.stage, b"Invented concurrent stage.\n")
            return result
        with mock.patch.object(ROTATE.NativeOperation, "listing", new=race):
            rc, result = self.invoke("install")
        self.assertEqual(rc, 2, result)
        self.assertEqual(result["reason"], "native-unknown-stage")
        self.assertEqual(self.stage.read_bytes(), b"Invented concurrent stage.\n")
        self.assertEqual(self.destination.read_bytes(), self.pristine_bytes)

    def test_guard_i4_derived_binding_collision_is_not_reused(self):
        self.preserve()
        self.stop("install", "install-prepared")
        self.stop("install", "install-renamed", reuse_go=True)
        state = json.loads(self.state_path.read_bytes())
        _, ids, _ = ROTATE.native_rows(self.candidate_path.read_bytes(), DESTINATION, self.project)
        raw = ROTATE.json_bytes({**state["installed"], "uuids": sorted(ids)})
        path = self.case / ("i4-binding-" + hashlib.sha256(raw).hexdigest()[:16] + ".json")
        self.put(path, b"Invented retained binding collision.\n")
        self.survivor_expect_exact_refusal("native-i4-binding-changed", "install", reuse_go=True)

    def _guard_rename_readback_fault(self, field, value, reason):
        self.preserve()
        self.stop("install", "install-prepared")
        real_current = ROTATE.NativeOperation.current
        def fault(operation, name):
            result = real_current(operation, name)
            if name == "destination" and not operation.stage.exists():
                return {**result, field: value}
            return result
        with mock.patch.object(ROTATE.NativeOperation, "current", new=fault):
            rc, result = self.invoke("install", reuse_go=True)
        self.assertEqual(rc, 2, result)
        self.assertEqual(result["reason"], reason)
        self.assertEqual(self.destination.read_bytes(), self.candidate_path.read_bytes())
        self.assertEqual(json.loads(self.state_path.read_bytes())["phase"], "install-prepared")

    def test_guard_rename_content_readback(self):
        self._guard_rename_readback_fault("sha256", "0" * 64, "native-install-unknown-postimage")

    def test_guard_rename_identity_readback(self):
        self._guard_rename_readback_fault("ino", 0, "native-install-unknown-postimage")

    def test_guard_candidate_digest_rechecked_after_rename(self):
        self.preserve()
        self.stop("install", "install-prepared")
        real_instrument = ROTATE.NativeOperation.instrument
        def race(operation, name, binding=None):
            result = real_instrument(operation, name, binding)
            if name == "I3B" and not operation.stage.exists():
                # Fault only after the post-rename I3B packet is validated;
                # before that point its independent candidate pin refuses.
                operation.candidate += b"Invented late memory fault.\n"
            return result
        with mock.patch.object(ROTATE.NativeOperation, "instrument", new=race):
            rc, result = self.invoke("install", reuse_go=True)
        self.assertEqual(rc, 2, result)
        self.assertEqual(result["reason"], "native-installed-candidate-hash")
        self.assertEqual(self.destination.read_bytes(), self.candidate_path.read_bytes())

    def test_guard_rollback_stage_requires_prepared_phase(self):
        self.preserve()
        self.stop("install", "install-prepared")
        state = json.loads(self.state_path.read_bytes())
        state["phase"] = "custodied"
        self.put(self.state_path, state)
        self._lifecycle_expect_reason("native-rollback-unknown-stage", "rollback")

    def test_guard_each_preparation_gate_rejects_truthy_nonboolean(self):
        for field in self.gates["gates"]:
            for value in (1, "yes", [True]):
                with self.subTest(field=field, value=value):
                    checks = dict(self.gates["gates"])
                    checks[field] = value
                    self.survivor_bind_gates(checks)
                    self._lifecycle_expect_reason("native-preparation-incomplete")

    def test_guard_destination_cannot_match_a_later_registry_row(self):
        row = copy.deepcopy(self.registry["identities"][-1])
        row.update(key="fixture-other", provider="codex", session_id=DESTINATION,
                   room=str(self.base / "another-room"))
        self.registry["identities"].append(row)
        self.survivor_bind_registry()
        self._lifecycle_expect_reason("native-target-is-resident")

    def test_guard_absent_donor_requires_go_at_restore_seam(self):
        self.preserve()
        self.install()
        operation = self._guard_direct_operation("rollback")
        operation.state.update(phase="rollback-prepared", rollback_go_sha256=operation.go_sha,
            rollback_initial={name: operation.current(name) for name in operation.targets},
            restores={"donor": {}})
        # A stale restore record is not authority. Keep every filesystem
        # object unchanged and isolate only this defensive checkpoint seam.
        before = self.inventory(self.store)
        with mock.patch.object(operation, "quiescence"), \
                mock.patch.object(operation, "custody_members"), \
                mock.patch.object(operation, "restore_target") as restore:
            with self.assertRaisesRegex(ROTATE.Refused, "^native-donor-restore-go-required$"):
                operation.rollback()
            restore.assert_called_once_with("destination")
        self.assertEqual(self.inventory(self.store), before)

    def test_guard_inverse_final_destination_is_not_assumed(self):
        self.preserve()
        self.install()
        operation = self._guard_direct_operation("rollback")
        operation.state.update(phase="rollback-prepared", rollback_go_sha256=operation.go_sha,
            rollback_initial={name: operation.current(name) for name in operation.targets})
        before = self.inventory(self.store)
        # Deliberately no-op inverse models an interrupted/defective restore;
        # the final independent inventory guard must reject it.
        with mock.patch.object(operation, "quiescence"), \
                mock.patch.object(operation, "custody_members"), \
                mock.patch.object(operation, "restore_target"):
            with self.assertRaisesRegex(ROTATE.Refused, "^native-rollback-inventory-mismatch$"):
                operation.rollback()
        self.assertEqual(self.inventory(self.store), before)

    def test_guard_opened_lock_identity_must_match_its_path(self):
        real_node = ROTATE.sibling("notice").private_node
        real_sibling = ROTATE.sibling
        notice = real_sibling("notice")
        def fault(path, *args, **kwargs):
            result = real_node(path, *args, **kwargs)
            if Path(path) == self.state_home / "operation.lock":
                fields = list(result)
                fields[1] = 0
                return os.stat_result(fields)
            return result
        def sibling(name):
            return notice if name == "notice" else real_sibling(name)
        with mock.patch.object(notice, "private_node", side_effect=fault), \
                mock.patch.object(ROTATE, "sibling", side_effect=sibling):
            self._lifecycle_expect_reason("native-operation-lock-replaced")
        self.assertFalse(self.state_path.exists())


    # Insert into NativeDisposableTests; reuse the parent-provided
    # _guard_direct_operation and existing imports. Author proposal only:
    # no worker execution, syntax check, or mutation catch is claimed.
    # Destination rollback-prepared checkpoints are explicit unit fixtures;
    # donor cases enter rollback-donor-pending through the real rollback path.
    # No current/read/snapshot/digest/require result is replaced. Exact local
    # refusals can distinguish a mutant from a later defensive refusal; that
    # distinction alone is not evidence of unsafe admission.

    @contextlib.contextmanager
    def _restore_guard_case(self, name="destination"):
        self.preserve()
        self.install()
        prepare = {}
        if name == "donor":
            self.donor.unlink()  # Invented donor only; verified custody remains.
            prepare = {"go_change": lambda go: go.update(restore_absent_donor=True),
                       "reuse_go": True}
            self.stop("rollback", "rollback-donor-pending",
                      go_change=prepare["go_change"])
        real_sibling = ROTATE.sibling
        commands = []
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(ROTATE, "sibling", side_effect=lambda key:
                self.mind if key == "mind" else self.custody if key == "custody" else real_sibling(key)))
            stack.enter_context(mock.patch.object(self.mind, "git_exposed", return_value=False))
            for command in ("run", "Popen", "call", "check_call", "check_output"):
                commands.append(stack.enter_context(mock.patch.object(
                    subprocess, command, side_effect=AssertionError("no commands"))))
            operation = self._guard_direct_operation("rollback", **prepare)
            if name == "destination":
                operation.state.update(
                    phase="rollback-prepared", rollback_go_sha256=operation.go_sha,
                    rollback_initial={key: operation.current(key) for key in operation.targets},
                    restores={})
                operation.save()
            try:
                yield operation
            finally:
                for command in commands:
                    command.assert_not_called()

    def _restore_guard_tree(self):
        # Compare exact bytes, links, inode identity, ownership, permissions,
        # link count, size and modification/change times, including directories.
        # Access times are excluded because real reads can update them.
        result = {}
        for path in (self.base, *sorted(self.base.rglob("*"))):
            node = path.lstat()
            payload = (os.readlink(path) if stat.S_ISLNK(node.st_mode) else
                       path.read_bytes() if stat.S_ISREG(node.st_mode) else None)
            result[str(path.relative_to(self.base))] = (
                node.st_dev, node.st_ino, node.st_mode, node.st_uid, node.st_gid,
                node.st_nlink, node.st_size, node.st_mtime_ns, node.st_ctime_ns, payload)
        return result

    def _restore_guard_stage(self, operation, name="destination"):
        # Explicit crash-resume fixture, persisted by the real checkpoint
        # writer. The stage and custody bytes are real, not snapshot stand-ins.
        path = operation.targets[name]
        stage = path.with_name(path.name + ".NEW")
        self.assertFalse(os.path.lexists(stage))
        original = operation.preimages[name]
        raw, _ = ROTATE.native_read(
            operation.roots[0] / operation.batch / (operation.operation + "-" + name))
        self.assertEqual(hashlib.sha256(raw).hexdigest(), original["sha256"])
        operation.write(stage, raw, (original["uid"], original["gid"]))
        operation.state["restores"][name] = {"staged": ROTATE.native_snapshot(stage)}
        operation.save()
        return stage

    def _restore_guard_refusal(self, operation, reason, name="destination"):
        before_tree = self._restore_guard_tree()
        before_state = copy.deepcopy(operation.state)
        with mock.patch.object(operation, "write", wraps=operation.write) as write, \
                mock.patch.object(operation, "save", wraps=operation.save) as save, \
                mock.patch.object(operation, "refresh_at_act", wraps=operation.refresh_at_act) as refresh:
            with self.assertRaises(ROTATE.Refused) as caught:
                operation.restore_target(name)
            self.assertEqual(str(caught.exception), reason)
            write.assert_not_called()
            save.assert_not_called()
            refresh.assert_not_called()
        self.assertEqual(operation.state, before_state)
        self.assertEqual(self._restore_guard_tree(), before_tree)

    def _restore_guard_success(self, operation, name="destination"):
        before_tree = self._restore_guard_tree()
        expected_state = copy.deepcopy(operation.state)
        self.assertIsNone(operation.restore_target(name))
        path = operation.targets[name]
        stage = path.with_name(path.name + ".NEW")
        self.assertFalse(os.path.lexists(stage))
        restored = ROTATE.native_snapshot(path)
        record = operation.state["restores"][name]
        for field in ("type", "size", "sha256", "mode", "uid", "gid", "nlink"):
            self.assertEqual(restored[field], operation.preimages[name][field], field)
        self.assertEqual((restored["dev"], restored["ino"]),
                         (record["staged"]["dev"], record["staged"]["ino"]))
        self.assertEqual(record["installed"], restored)
        # Both controls start with a saved stage; only its installed field
        # may be added, in memory and in the real checkpoint on disk.
        expected_state["restores"][name]["installed"] = restored
        self.assertEqual(operation.state, expected_state)
        self.assertEqual(json.loads(operation.state_path.read_bytes()), expected_state)
        allowed = {str(p.relative_to(self.base)) for p in (
            path, stage, operation.store, operation.directory, operation.state_path)}
        after_tree = self._restore_guard_tree()
        self.assertEqual({k: v for k, v in before_tree.items() if k not in allowed},
                         {k: v for k, v in after_tree.items() if k not in allowed})

    def test_restore_guard_native_0217_initial_target_changed(self):
        with self._restore_guard_case() as operation:
            self.put(self.destination, b"Invented concurrent destination bytes.\n")
            self.assertNotEqual(operation.current("destination"),
                                operation.state["rollback_initial"]["destination"])
            self._restore_guard_refusal(operation, "native-restore-preimage-changed")

    def test_restore_guard_native_0218_unrecorded_stage_kinds(self):
        with self._restore_guard_case() as operation:
            stage = self.destination.with_name(self.destination.name + ".NEW")
            for kind in ("file", "directory", "dangling-link"):
                with self.subTest(kind=kind):
                    if kind == "file":
                        self.put(stage, b"Invented unknown staged bytes.\n")
                    elif kind == "directory":
                        stage.mkdir(mode=0o700)
                    else:
                        stage.symlink_to(self.case / "invented-missing-link-target")
                    self.assertTrue(os.path.lexists(stage))
                    self._restore_guard_refusal(operation, "native-restore-unknown-stage")
                    # Remove only the object just made by this subcase.
                    if kind == "directory":
                        stage.rmdir()
                    else:
                        stage.unlink()

    def test_restore_guard_native_0219_custody_bytes_changed(self):
        with self._restore_guard_case() as operation:
            custody = operation.roots[0] / operation.batch / (operation.operation + "-destination")
            self.put(custody, b"Invented changed custody bytes after verification.\n")
            self.assertNotEqual(self.sha(custody), operation.preimages["destination"]["sha256"])
            self._restore_guard_refusal(operation, "native-restore-custody-changed")

    def test_restore_guard_native_0220_completed_restore_changed(self):
        with self._restore_guard_case() as operation:
            # Establish the installed record with the real fresh restore,
            # including its real authority refresh, write, rename and saves.
            operation.restore_target("destination")
            self.assertEqual(self.destination.read_bytes(), self.pristine_bytes)
            self.assertIn("installed", operation.state["restores"]["destination"])
            self.put(self.destination, self.pristine_bytes + b"Invented later change.\n")
            self._restore_guard_refusal(operation, "native-restored-postimage-changed")

    def test_restore_guard_native_0221_recorded_stage_changed(self):
        with self._restore_guard_case() as operation:
            stage = self._restore_guard_stage(operation)
            recorded = operation.state["restores"]["destination"]["staged"]
            self.put(stage, stage.read_bytes() + b"Invented staged corruption.\n")
            actual = ROTATE.native_snapshot(stage)
            self.assertEqual((actual["dev"], actual["ino"]), (recorded["dev"], recorded["ino"]))
            self.assertNotEqual(actual["sha256"], recorded["sha256"])
            self._restore_guard_refusal(operation, "native-restore-stage-changed")

    def test_restore_guard_native_0222_absent_donor_reappeared(self):
        with self._restore_guard_case("donor") as operation:
            stage = self._restore_guard_stage(operation, "donor")
            self.assertEqual(operation.state["rollback_initial"]["donor"], {"type": "absent"})
            self.put(self.donor, b"Invented independently recreated donor.\n")
            # A valid, unchanged saved stage leaves only the target clause
            # false. Removing it may still encounter the later I1 refusal.
            self.assertEqual(ROTATE.native_snapshot(stage),
                             operation.state["restores"]["donor"]["staged"])
            self._restore_guard_refusal(operation, "native-restore-target-changed", "donor")

    def test_restore_guard_native_0223_same_inode_has_changed_content(self):
        with self._restore_guard_case() as operation:
            stage = self._restore_guard_stage(operation)
            recorded = operation.state["restores"]["destination"]["staged"]
            # Real rename followed by an interrupted-checkpoint resume and
            # real in-place corruption. The inode clause stays independently true.
            os.replace(stage, self.destination)
            self.put(self.destination, self.destination.read_bytes() + b"Invented post-rename corruption.\n")
            actual = ROTATE.native_snapshot(self.destination)
            self.assertEqual((actual["dev"], actual["ino"]), (recorded["dev"], recorded["ino"]))
            self.assertNotEqual(actual["sha256"], recorded["sha256"])
            self._restore_guard_refusal(operation, "native-restore-unknown-postimage")

    def test_restore_guard_native_0224_identical_bytes_have_another_inode(self):
        with self._restore_guard_case() as operation:
            stage = self._restore_guard_stage(operation)
            recorded = operation.state["restores"]["destination"]["staged"]
            os.replace(stage, self.destination)
            replacement = self.case / "invented-restore-identical-replacement.fixture"
            # Allocate while the staged inode still exists, preventing inode
            # reuse from turning this into an accidental equality case.
            self.put(replacement, self.destination.read_bytes())
            os.replace(replacement, self.destination)
            actual = ROTATE.native_snapshot(self.destination)
            for field in ("type", "size", "sha256", "mode", "uid", "gid", "nlink"):
                self.assertEqual(actual[field], recorded[field], field)
            self.assertNotEqual((actual["dev"], actual["ino"]), (recorded["dev"], recorded["ino"]))
            self._restore_guard_refusal(operation, "native-restore-unknown-postimage")

    def test_restore_guard_clean_staged_resume(self):
        with self._restore_guard_case() as operation:
            self._restore_guard_stage(operation)
            self._restore_guard_success(operation)

    def test_restore_guard_clean_renamed_donor_resume(self):
        with self._restore_guard_case("donor") as operation:
            stage = self._restore_guard_stage(operation, "donor")
            os.replace(stage, self.donor)
            self._restore_guard_success(operation, "donor")

def quantifier_overlap_case(selected, direction, position):
    def test(self):
        self.quantifier_overlap(selected, direction, position)
    return test


for selected in ("room", "project", "store"):
    for direction in ("ancestor", "descendant"):
        for position in (0, 1):
            setattr(NativeDisposableTests,
                    "test_quantifier_overlap_%s_%s_root_%d" % (selected, direction, position),
                    quantifier_overlap_case(selected, direction, position))


def quantifier_registered_target_case(provider, target):
    def test(self):
        self.quantifier_registered_target(provider, target)
    return test


for provider in ("claude", "codex", "copilot"):
    for target in ("donor", "destination"):
        setattr(NativeDisposableTests, "test_quantifier_registered_%s_%s" % (provider, target),
                quantifier_registered_target_case(provider, target))


def quantifier_pristine_case(kind):
    def test(self):
        self.quantifier_allowed_pristine_envelope(kind)
    return test


for kind in ("file-history-snapshot", "queue-operation"):
    setattr(NativeDisposableTests, "test_quantifier_pristine_allowed_" + kind.replace("-", "_"),
            quantifier_pristine_case(kind))


class NativeReaderTests(unittest.TestCase):
    """Synthetic filesystem and JSONL predicates; no operation or provider API.

    Race fixtures change only this test's private scratch. Dependency faults
    isolate overlapping predicates without granting access to another path.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=TOOL.parents[3] / "var/tmp")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.base.chmod(0o700)
        self.project = self.base / "project"
        self.project.mkdir(mode=0o700)
        self.source = self.base / "closed.fixture"
        self.write(self.source, b"invented closed bytes\n")
        self.notice = ROTATE.sibling("notice")
        self.errors = (ROTATE.Refused, ValueError, OSError)
        if hasattr(self.notice, "Refused"):
            self.errors += (self.notice.Refused,)
        def sibling(name):
            if name != "notice":
                raise AssertionError("Reader tests require only the notice parser/privacy API")
            return self.notice
        patcher = mock.patch.object(ROTATE, "sibling", side_effect=sibling)
        patcher.start()
        self.addCleanup(patcher.stop)

    @staticmethod
    def write(path, raw):
        path.write_bytes(raw)
        path.chmod(0o600)

    @staticmethod
    def uid(number):
        return "0000%04x-0000-4000-8000-00000000%04x" % (number, number)

    def rows(self):
        return [
            {"type": "user", "sessionId": SID, "cwd": str(self.project),
             "uuid": self.uid(0xc101), "parentUuid": None,
             "message": {"role": "user", "content": [{"type": "text", "text": "An invented question."}]}},
            {"type": "assistant", "sessionId": SID, "cwd": str(self.project),
             "uuid": self.uid(0xc102), "parentUuid": self.uid(0xc101),
             "message": {"role": "assistant", "content": [{"type": "text", "text": "An invented answer."}]}}]

    @staticmethod
    def raw(rows):
        return b"".join(json.dumps(row, sort_keys=True).encode("ascii") + b"\n" for row in rows)

    def parse(self, rows, prefix_ids=()):
        return ROTATE.native_rows(self.raw(rows), SID, self.project, prefix_ids)

    def refuses(self, call, reason=None):
        with self.assertRaises(self.errors) as caught:
            call()
        if reason is not None:
            self.assertEqual(str(caught.exception), reason)
        return caught.exception

    @contextlib.contextmanager
    def read_seam(self, read=None, closed=None):
        fdopen = os.fdopen
        @contextlib.contextmanager
        def wrapped(fd, mode):
            with fdopen(fd, mode) as handle:
                def consume(size):
                    return handle.read(size) if read is None else read(handle, size)
                yield types.SimpleNamespace(fileno=handle.fileno, read=consume)
            if closed is not None:
                closed()
        with mock.patch.object(ROTATE.os, "fdopen", new=wrapped):
            yield

    def test_path_accepts_an_existing_private_absolute_file(self):
        self.assertEqual(ROTATE.native_path(str(self.source)), self.source)

    def test_path_requires_a_string(self):
        self.refuses(lambda: ROTATE.native_path(123), "native-path-required")

    def test_path_rejects_empty_text_at_the_input_guard(self):
        self.refuses(lambda: ROTATE.native_path(""), "native-path-required")

    def test_path_rejects_nul_at_the_input_guard(self):
        self.refuses(lambda: ROTATE.native_path(str(self.source) + "\x00"), "native-path-required")

    def test_path_relative_clause_is_independent_of_resolve(self):
        # Resolve equality is neutralized; no relative path is ever opened.
        with mock.patch.object(Path, "resolve", autospec=True, side_effect=lambda path: path), \
                mock.patch.object(self.notice, "parent_chain") as parents:
            self.refuses(lambda: ROTATE.native_path("invented-relative.fixture"),
                         "native-plain-absolute-path-required")
        parents.assert_not_called()

    def test_path_parent_component_clause_is_independent_of_resolve(self):
        raw = str(self.project / ".." / "closed.fixture")
        with mock.patch.object(Path, "resolve", autospec=True, side_effect=lambda path: path), \
                mock.patch.object(self.notice, "parent_chain") as parents:
            self.refuses(lambda: ROTATE.native_path(raw), "native-plain-absolute-path-required")
        parents.assert_not_called()

    def test_path_rejects_a_final_symlink(self):
        link = self.base / "linked.fixture"
        link.symlink_to(self.source)
        self.refuses(lambda: ROTATE.native_path(str(link)), "native-plain-absolute-path-required")

    def test_path_rejects_a_linked_ancestor(self):
        link = self.base / "linked-project"
        link.symlink_to(self.project, target_is_directory=True)
        self.write(self.project / "child.fixture", b"Invented child.\n")
        self.refuses(lambda: ROTATE.native_path(str(link / "child.fixture")),
                     "native-plain-absolute-path-required")

    def test_path_invokes_the_ancestor_guard_before_return(self):
        with mock.patch.object(self.notice, "parent_chain", side_effect=ROTATE.Refused("invented-ancestor-refusal")) as parents:
            self.refuses(lambda: ROTATE.native_path(str(self.source)), "invented-ancestor-refusal")
        parents.assert_called_once_with(self.source.parent)

    def test_read_returns_exact_private_bytes_and_preimage_stat(self):
        expected = self.source.read_bytes()
        before = self.source.lstat()
        raw, node = ROTATE.native_read(self.source)
        self.assertEqual(raw, expected)
        self.assertEqual((node.st_dev, node.st_ino, node.st_size, node.st_mode),
                         (before.st_dev, before.st_ino, before.st_size, before.st_mode))
        self.assertEqual(self.source.read_bytes(), expected)

    def test_read_rejects_a_missing_file(self):
        self.refuses(lambda: ROTATE.native_read(self.base / "missing.fixture"))

    def test_read_rejects_group_readable_mode(self):
        self.source.chmod(0o640)
        self.refuses(lambda: ROTATE.native_read(self.source))

    def test_read_rejects_group_writable_mode(self):
        self.source.chmod(0o620)
        self.refuses(lambda: ROTATE.native_read(self.source))

    def test_read_rejects_world_readable_mode(self):
        self.source.chmod(0o604)
        self.refuses(lambda: ROTATE.native_read(self.source))

    def test_read_rejects_a_directory(self):
        self.refuses(lambda: ROTATE.native_read(self.project))

    def test_read_rejects_a_fifo_without_opening_it(self):
        fifo = self.base / "invented.fifo"
        os.mkfifo(fifo, 0o600)
        with mock.patch.object(ROTATE.os, "open", side_effect=AssertionError("A FIFO must not be opened")) as opened:
            self.refuses(lambda: ROTATE.native_read(fifo))
        opened.assert_not_called()

    def test_read_rejects_hardlinks(self):
        os.link(self.source, self.base / "second-name.fixture")
        self.refuses(lambda: ROTATE.native_read(self.source))

    def test_read_rejects_oversized_stat_before_open(self):
        with mock.patch.object(ROTATE.os, "open", side_effect=AssertionError("Oversized input must not be opened")) as opened:
            self.refuses(lambda: ROTATE.native_read(self.source, limit=1), "native-file-too-large")
        opened.assert_not_called()

    def test_read_allows_the_exact_limit(self):
        raw = self.source.read_bytes()
        self.assertEqual(ROTATE.native_read(self.source, limit=len(raw))[0], raw)

    def test_read_uses_nofollow_and_nonblock(self):
        opened = os.open
        with mock.patch.object(ROTATE.os, "open", wraps=opened) as observed:
            ROTATE.native_read(self.source)
        calls = [call for call in observed.call_args_list if Path(call.args[0]) == self.source]
        self.assertEqual(len(calls), 1)
        flags = calls[0].args[1]
        self.assertTrue(flags & os.O_NOFOLLOW)
        self.assertTrue(flags & os.O_NONBLOCK)
        self.assertEqual(flags & os.O_ACCMODE, os.O_RDONLY)

    def test_read_detects_replacement_between_stat_and_open(self):
        replacement = self.base / "replacement.fixture"
        self.write(replacement, self.source.read_bytes())
        opened = os.open
        def replace_then_open(path, flags, *args, **kwargs):
            if Path(path) == self.source:
                os.replace(replacement, self.source)
            return opened(path, flags, *args, **kwargs)
        with mock.patch.object(ROTATE.os, "open", side_effect=replace_then_open):
            self.refuses(lambda: ROTATE.native_read(self.source), "native-open-identity-changed")

    def test_read_detects_in_place_change_while_handle_is_open(self):
        original = self.source.read_bytes()
        def change_after_read(handle, size):
            raw = handle.read(size)
            self.source.write_bytes(original + b"Invented concurrent append.\n")
            return raw
        with self.read_seam(read=change_after_read):
            self.refuses(lambda: ROTATE.native_read(self.source), "native-read-identity-changed")

    def test_read_detects_path_replacement_after_handle_closes(self):
        replacement = self.base / "replacement.fixture"
        self.write(replacement, self.source.read_bytes())
        with self.read_seam(closed=lambda: os.replace(replacement, self.source)):
            self.refuses(lambda: ROTATE.native_read(self.source), "native-read-preimage-changed")

    def test_read_checks_returned_length_independently_of_stat(self):
        original = self.source.read_bytes()
        with self.read_seam(read=lambda handle, size: handle.read(size) + b"!"):
            self.refuses(lambda: ROTATE.native_read(self.source, len(original)), "native-read-preimage-changed")

    def test_snapshot_file_reports_all_contract_fields(self):
        node = self.source.lstat()
        expected = {"type": "file", "dev": node.st_dev, "ino": node.st_ino, "size": node.st_size,
                    "sha256": hashlib.sha256(self.source.read_bytes()).hexdigest(),
                    "mode": 0o600, "uid": node.st_uid, "gid": node.st_gid,
                    "mtime_ns": node.st_mtime_ns, "ctime_ns": node.st_ctime_ns, "nlink": 1}
        self.assertEqual(ROTATE.native_snapshot(self.source), expected)

    def test_snapshot_directory_has_no_content_digest(self):
        node = self.project.lstat()
        snap = ROTATE.native_snapshot(self.project)
        self.assertEqual(snap["type"], "directory")
        self.assertIsNone(snap["sha256"])
        self.assertEqual((snap["dev"], snap["ino"], snap["mode"], snap["uid"], snap["gid"]),
                         (node.st_dev, node.st_ino, 0o700, node.st_uid, node.st_gid))

    def test_snapshot_directory_requires_private_mode(self):
        self.project.chmod(0o750)
        self.refuses(lambda: ROTATE.native_snapshot(self.project))

    def test_snapshot_rejects_a_final_link(self):
        link = self.base / "snapshot-link"
        link.symlink_to(self.source)
        self.refuses(lambda: ROTATE.native_snapshot(link))

    def test_snapshot_has_its_own_type_guard_after_privacy_check(self):
        fifo = self.base / "snapshot.fifo"
        os.mkfifo(fifo, 0o600)
        with mock.patch.object(self.notice, "private_node", return_value=fifo.lstat()):
            self.refuses(lambda: ROTATE.native_snapshot(fifo), "native-inventory-type")

    def test_inventory_is_an_immediate_sorted_listing(self):
        child = self.project / "child"
        child.mkdir(mode=0o700)
        self.write(child / "nested.fixture", b"Invented nested bytes.\n")
        self.write(self.project / "first.fixture", b"Invented direct bytes.\n")
        result = ROTATE.native_inventory(self.project)
        self.assertEqual(list(result), ["child", "first.fixture"])
        self.assertEqual(result["child"]["type"], "directory")
        self.assertEqual(result["first.fixture"]["sha256"],
                         hashlib.sha256(b"Invented direct bytes.\n").hexdigest())
        self.assertNotIn("nested.fixture", result)

    def test_inventory_rejects_nonprivate_root_before_children(self):
        self.project.chmod(0o750)
        with mock.patch.object(ROTATE, "native_snapshot") as snapshots:
            self.refuses(lambda: ROTATE.native_inventory(self.project))
        snapshots.assert_not_called()

    def test_inventory_rejects_child_link_before_snapshot(self):
        link = self.project / "link"
        link.symlink_to(self.source)
        with mock.patch.object(ROTATE, "native_snapshot", return_value={}) as snapshots:
            self.refuses(lambda: ROTATE.native_inventory(self.project), "native-inventory-link")
        snapshots.assert_not_called()

    def test_inventory_checks_child_file_privacy(self):
        child = self.project / "child.fixture"
        self.write(child, b"Invented child.\n")
        child.chmod(0o644)
        self.refuses(lambda: ROTATE.native_inventory(self.project))

    def test_rows_accepts_typed_jsonl_and_returns_identity_set(self):
        expected = self.rows()
        rows, seen, assistants = self.parse(expected)
        self.assertEqual(rows, expected)
        self.assertEqual(seen, {self.uid(0xc101), self.uid(0xc102)})
        self.assertEqual(assistants, 1)

    def test_rows_requires_nonempty_input(self):
        class EmptyWithIndependentTerminator(bytes):
            def endswith(self, suffix):
                return True
        # Neutralize the overlapping terminator predicate at this unit seam.
        # No malformed body reaches an operation; the next row guard remains.
        self.refuses(lambda: ROTATE.native_rows(EmptyWithIndependentTerminator(), SID, self.project),
                     "native-body-not-terminated")

    def test_rows_requires_terminal_newline(self):
        self.refuses(lambda: ROTATE.native_rows(self.raw(self.rows()).rstrip(b"\n"), SID, self.project),
                     "native-body-not-terminated")

    def test_rows_rejects_malformed_json(self):
        self.refuses(lambda: ROTATE.native_rows(b"{broken\n", SID, self.project))

    def test_rows_rejects_nonobject_json(self):
        for value in (None, True, 7, "invented", []):
            with self.subTest(value=value):
                self.refuses(lambda value=value: ROTATE.native_rows(self.raw([value]), SID, self.project))

    def test_rows_rejects_duplicate_json_keys(self):
        raw = b'{"type":"user","type":"assistant","sessionId":"' + SID.encode("ascii") + b'"}\n'
        self.refuses(lambda: ROTATE.native_rows(raw, SID, self.project))

    def test_rows_rejects_nonfinite_json(self):
        raw = b'{"type":"user","sessionId":"' + SID.encode("ascii") + b'","bad":NaN}\n'
        self.refuses(lambda: ROTATE.native_rows(raw, SID, self.project))

    def test_rows_enforces_upper_row_limit_before_identity_checks(self):
        raw = b'{"type":"progress"}\n' * 65537
        self.refuses(lambda: ROTATE.native_rows(raw, SID, self.project), "native-row-limit")

    def test_rows_rejects_foreign_camel_case_session(self):
        rows = self.rows()
        rows[0]["sessionId"] = DESTINATION
        self.refuses(lambda: self.parse(rows), "native-body-foreign-session")

    def test_rows_rejects_foreign_snake_case_session(self):
        rows = self.rows()
        rows[0]["session_id"] = DESTINATION
        self.refuses(lambda: self.parse(rows), "native-body-foreign-session")

    def test_rows_requires_at_least_one_top_level_identity(self):
        rows = self.rows()
        for row in rows:
            row.pop("sessionId")
            row["message"]["content"][0]["text"] = json.dumps({"sessionId": SID})
        self.refuses(lambda: self.parse(rows), "native-identities-or-tool-pairs")

    def test_rows_rejects_foreign_project(self):
        rows = self.rows()
        rows[1]["cwd"] = str(self.base)
        self.refuses(lambda: self.parse(rows), "native-body-project")

    def test_rows_rejects_nontext_project(self):
        rows = self.rows()
        rows[1]["cwd"] = None
        self.refuses(lambda: self.parse(rows), "native-body-project")

    def test_rows_message_id_must_be_a_string(self):
        rows = self.rows()
        rows[0]["uuid"] = 7
        self.refuses(lambda: self.parse(rows), "native-message-id")

    def test_rows_message_id_must_not_be_empty(self):
        rows = self.rows()
        rows[0]["uuid"] = ""
        self.refuses(lambda: self.parse(rows), "native-message-id")

    def test_rows_message_ids_must_be_unique(self):
        rows = self.rows()
        rows[1]["uuid"] = rows[0]["uuid"]
        self.refuses(lambda: self.parse(rows), "native-message-id")

    def test_rows_first_parent_must_be_null(self):
        rows = self.rows()
        rows[0]["parentUuid"] = self.uid(0xc199)
        self.refuses(lambda: self.parse(rows), "native-parent-chain")

    def test_rows_later_parent_must_have_been_seen(self):
        rows = self.rows()
        rows[1]["parentUuid"] = self.uid(0xc199)
        self.refuses(lambda: self.parse(rows), "native-parent-chain")

    def test_rows_later_parent_cannot_be_null(self):
        rows = self.rows()
        rows[1]["parentUuid"] = None
        self.refuses(lambda: self.parse(rows), "native-parent-chain")

    def test_rows_prefix_ids_admit_a_clean_append(self):
        rows = self.rows()[1:]
        parsed, seen, count = self.parse(rows, (self.uid(0xc101),))
        self.assertEqual(parsed, rows)
        self.assertEqual(seen, {self.uid(0xc101), self.uid(0xc102)})
        self.assertEqual(count, 1)

    def test_rows_prefix_ids_forbid_reusing_an_existing_message(self):
        rows = self.rows()[1:]
        self.refuses(lambda: self.parse(rows, (self.uid(0xc101), self.uid(0xc102))), "native-message-id")

    def test_rows_sidechain_assistant_is_not_a_clean_append_count(self):
        rows = self.rows()
        rows[1]["isSidechain"] = True
        self.assertEqual(self.parse(rows)[2], 0)

    def test_rows_nonassistant_does_not_increment_assistant_count(self):
        rows = self.rows()
        rows[1]["type"] = "progress"
        self.assertEqual(self.parse(rows)[2], 0)

    def test_rows_rejects_nondictionary_content_blocks(self):
        for bad in (None, "invented", 7, []):
            with self.subTest(block=bad):
                rows = self.rows()
                rows[0]["message"]["content"] = [bad]
                self.refuses(lambda: self.parse(rows), "native-message-content-block")

    def tool_rows(self, token="invented-tool"):
        rows = self.rows()
        rows[0]["type"] = rows[0]["message"]["role"] = "assistant"
        rows[1]["type"] = rows[1]["message"]["role"] = "user"
        rows[0]["message"]["content"] = [{"type": "tool_use", "id": token, "name": "invented", "input": {}}]
        rows[1]["message"]["content"] = [{"type": "tool_result", "tool_use_id": token, "content": "Invented output."}]
        return rows

    def test_rows_accepts_paired_tool_headers(self):
        rows = self.tool_rows()
        self.assertEqual(self.parse(rows)[0], rows)

    def test_rows_rejects_nontext_tool_use_id(self):
        rows = self.tool_rows()
        rows[0]["message"]["content"][0]["id"] = 7
        self.refuses(lambda: self.parse(rows), "native-tool-use")

    def test_rows_rejects_empty_tool_use_id_even_if_paired(self):
        self.refuses(lambda: self.parse(self.tool_rows("")), "native-tool-use")

    # --- Real row shapes (measured 2026-11-11 on provider 2.1.322; every value below is invented) ---

    def boundary_rows(self):
        rows = self.rows()
        rows.append({"type": "system", "subtype": "compact_boundary", "sessionId": SID, "cwd": str(self.project),
                     "uuid": self.uid(0xc103), "parentUuid": None, "logicalParentUuid": self.uid(0xc102)})
        rows.append({"type": "user", "sessionId": SID, "cwd": str(self.project), "isCompactSummary": True,
                     "uuid": self.uid(0xc104), "parentUuid": self.uid(0xc103),
                     "message": {"role": "user", "content": [{"type": "text", "text": "An invented summary."}]}})
        return rows

    def test_rows_accept_a_boundary_rooted_by_its_logical_parent(self):
        parsed, seen, _ = self.parse(self.boundary_rows())
        self.assertEqual(len(parsed), 4)
        self.assertIn(self.uid(0xc103), seen)

    def test_rows_refuse_a_boundary_whose_logical_parent_is_unseen(self):
        rows = self.boundary_rows()
        rows[2]["logicalParentUuid"] = self.uid(0xc199)
        self.refuses(lambda: self.parse(rows), "native-parent-chain")

    def test_rows_refuse_a_boundary_with_no_logical_parent(self):
        rows = self.boundary_rows()
        rows[2].pop("logicalParentUuid")
        self.refuses(lambda: self.parse(rows), "native-parent-chain")

    def test_rows_refuse_any_other_second_root(self):
        rows = self.boundary_rows()
        rows[2]["subtype"] = "local_command"
        self.refuses(lambda: self.parse(rows), "native-parent-chain")

    def test_rows_do_not_count_tool_pairs_on_housekeeping_rows(self):
        rows = self.tool_rows()
        blob = {"type": "api-request-blob", "sessionId": SID, "hash": "invented",
                "message": {"role": "assistant", "content": copy.deepcopy(rows[0]["message"]["content"])}}
        echo = {"type": "api-request-blob", "sessionId": SID, "hash": "invented-two",
                "message": {"role": "user", "content": copy.deepcopy(rows[1]["message"]["content"])}}
        parsed, _, _ = self.parse([rows[0], blob, rows[1], echo, blob])
        self.assertEqual(len(parsed), 5)

    def test_rows_still_count_tool_pairs_on_conversation_rows(self):
        rows = self.tool_rows()
        self.refuses(lambda: self.parse(rows[:1]), "native-identities-or-tool-pairs")

    def test_user_prompt_passes_over_leading_ide_notices(self):
        row = self.rows()[0]
        for content, genuine in (
                ("<ide_opened_file>An invented notice.</ide_opened_file>\nAn invented question.", True),
                ("<ide_opened_file>One.</ide_opened_file><ide_selection>Two.</ide_selection>Invented.", True),
                ("<ide_opened_file>An invented notice.</ide_opened_file>", False),
                ("<ide_opened_file>One.</ide_opened_file> stray </ide_selection> text", False),
                ("<ide_opened_file>One.</ide_opened_file><local-command-stdout>x</local-command-stdout>", False),
                ("<command-name>/compact</command-name>", False),
                ("An invented question.", True)):
            with self.subTest(content=content):
                row["message"]["content"] = content
                self.assertEqual(ROTATE.user_prompt(row), genuine)
                row["message"]["content"] = [{"type": "text", "text": content}]
                self.assertEqual(ROTATE.user_prompt(row), genuine)

    def test_ide_notice_pattern_is_the_identity_tool_s(self):
        source = (Path(ROTATE.__file__).with_name("myself.py")).read_text(encoding="utf-8")
        self.assertIn('IDE_NOTICE_RE = re.compile(r"%s", re.DOTALL)' % ROTATE.IDE_NOTICE_RE.pattern, source)

    def pristine(self, reply=None):
        rows = [{"type": "session-owner", "sessionId": SID},
                {"type": "queue-operation", "sessionId": SID, "operation": "enqueue"},
                {"type": "user", "sessionId": SID, "uuid": self.uid(0xc201), "parentUuid": None,
                 "message": {"role": "user", "content": ROTATE.FIRST_PROMPT}}]
        for index, kind in enumerate(ROTATE.PRISTINE_ATTACHMENTS):
            rows.append({"type": "attachment", "sessionId": SID, "uuid": self.uid(0xc210 + index),
                         "parentUuid": self.uid(0xc201), "attachment": {"type": kind}})
        for kind in ("file-history-snapshot", "atis-latch", "api-request-shape", "api-request-blob", "api-request",
                     "last-prompt", "ai-title", "cost-state"):
            rows.append({"type": kind, "sessionId": SID})
        for index, blocks in enumerate(reply or [[{"type": "text", "text": "READY"}]]):
            rows.append({"type": "assistant", "sessionId": SID, "uuid": self.uid(0xc230 + index),
                         "parentUuid": self.uid(0xc201),
                         "message": {"role": "assistant", "id": "invented-message", "content": blocks}})
        return rows

    def test_pristine_accepts_the_measured_fresh_chat(self):
        ROTATE.native_pristine(self.pristine())

    def test_pristine_accepts_one_reply_written_as_a_row_per_block(self):
        ROTATE.native_pristine(self.pristine([[{"type": "thinking", "thinking": "Invented."}],
                                              [{"type": "text", "text": "READY"}]]))

    def test_pristine_accepts_the_prompt_behind_an_ide_notice(self):
        rows = self.pristine()
        rows[2]["message"]["content"] = "<ide_opened_file>Invented.</ide_opened_file>\n" + ROTATE.FIRST_PROMPT
        ROTATE.native_pristine(rows)

    def test_pristine_refuses_a_second_reply(self):
        rows = self.pristine([[{"type": "text", "text": "READY"}], [{"type": "text", "text": "READY"}]])
        rows[-1]["message"]["id"] = "invented-second-message"
        self.refuses(lambda: ROTATE.native_pristine(rows), "native-pristine-first-exchange")

    def test_pristine_refuses_a_reply_without_a_message_id(self):
        rows = self.pristine()
        rows[-1]["message"].pop("id")
        self.refuses(lambda: ROTATE.native_pristine(rows), "native-pristine-first-exchange")

    def test_pristine_refuses_a_second_user_row(self):
        rows = self.pristine()
        rows.append({"type": "user", "sessionId": SID, "uuid": self.uid(0xc240), "parentUuid": self.uid(0xc230),
                     "message": {"role": "user", "content": "Invented."}})
        self.refuses(lambda: ROTATE.native_pristine(rows), "native-pristine-first-exchange")

    def test_pristine_refuses_a_tool_block_or_a_second_text(self):
        for blocks in ([[{"type": "tool_use", "id": "invented", "name": "Read", "input": {}}],
                        [{"type": "text", "text": "READY"}]],
                       [[{"type": "text", "text": "READY"}], [{"type": "text", "text": "READY"}]],
                       [[{"type": "thinking", "thinking": "Invented."}]],
                       [[{"type": "text", "text": "READY."}]]):
            with self.subTest(blocks=blocks):
                self.refuses(lambda: ROTATE.native_pristine(self.pristine(blocks)), "native-pristine-inert-exchange")

    def test_pristine_refuses_another_prompt(self):
        rows = self.pristine()
        rows[2]["message"]["content"] = "Another invented prompt."
        self.refuses(lambda: ROTATE.native_pristine(rows), "native-pristine-inert-exchange")

    def test_pristine_refuses_an_unmeasured_row_or_attachment_type(self):
        for extra in ({"type": "bridge-session", "sessionId": SID},
                      {"type": "attachment", "sessionId": SID, "attachment": {"type": "invented_kind"}},
                      {"type": "attachment", "sessionId": SID},
                      {"type": "system", "subtype": "compact_boundary", "sessionId": SID}):
            with self.subTest(extra=extra):
                self.refuses(lambda: ROTATE.native_pristine(self.pristine() + [extra]),
                             "native-pristine-unknown-envelope")

    def test_rows_rejects_duplicate_pending_tool_use(self):
        rows = self.tool_rows()
        rows[0]["message"]["content"].append(copy.deepcopy(rows[0]["message"]["content"][0]))
        self.refuses(lambda: self.parse(rows), "native-tool-use")

    def test_rows_rejects_result_without_prior_tool_use(self):
        rows = self.rows()
        rows[0]["message"]["content"] = [{"type": "tool_result", "tool_use_id": "invented-missing"}]
        self.refuses(lambda: self.parse(rows), "native-tool-result")

    def test_rows_rejects_nontext_tool_result_id(self):
        rows = self.tool_rows()
        rows[1]["message"]["content"][0]["tool_use_id"] = ["invented-nontext"]
        self.refuses(lambda: self.parse(rows))

    def test_rows_empty_result_id_has_its_own_guard(self):
        rows = self.rows()[:1]
        rows[0]["message"]["content"] = [{"type": "tool_result", "tool_use_id": ""}]
        # Model a faulty pending-set dependency so membership cannot conceal
        # removal of the separate nonempty-ID clause.
        with mock.patch.object(ROTATE, "set", create=True, side_effect=[set(), {""}]):
            self.refuses(lambda: self.parse(rows), "native-tool-result")

    def test_rows_rejects_duplicate_result_for_one_tool_use(self):
        rows = self.tool_rows()
        rows[1]["message"]["content"].append(copy.deepcopy(rows[1]["message"]["content"][0]))
        self.refuses(lambda: self.parse(rows), "native-tool-result")

    def test_rows_rejects_unfinished_tool_use(self):
        rows = self.tool_rows()
        rows[1]["message"]["content"] = [{"type": "text", "text": "No invented result."}]
        self.refuses(lambda: self.parse(rows), "native-identities-or-tool-pairs")

    def test_rows_does_not_interpret_tool_input_or_result_payload_as_headers(self):
        rows = self.tool_rows()
        opaque = {"sessionId": DESTINATION, "session_id": DESTINATION, "cwd": str(self.base),
                  "uuid": rows[0]["uuid"], "type": "tool_result", "tool_use_id": "not-an-outer-tool",
                  "message": {"content": [{"type": "tool_use", "id": "opaque-only"}]}}
        rows[0]["message"]["content"][0]["input"] = opaque
        rows[1]["message"]["content"][0]["content"] = opaque
        self.assertEqual(self.parse(rows)[0], rows)

    def test_rows_does_not_parse_json_embedded_in_text(self):
        rows = self.rows()
        rows[0]["message"]["content"] = json.dumps({"sessionId": DESTINATION, "type": "tool_use", "id": "opaque"})
        self.assertEqual(self.parse(rows)[0], rows)


    def operation_reader(self):
        operation = object.__new__(ROTATE.NativeOperation)
        operation.notice = self.notice
        operation.evidence_directory = self.project
        operation.plan = {}
        operation.state = {}
        operation.proof = {}
        return operation

    def test_native_same_checks_each_required_property(self):
        baseline = dict(type="file", size=7, sha256="a" * 64, mode=0o600,
                        uid=1000, gid=1000, nlink=1, dev=2, ino=3,
                        mtime_ns=4, ctime_ns=5)
        common = ("type", "size", "sha256", "mode", "uid", "gid", "nlink")
        identity = ("dev", "ino", "mtime_ns", "ctime_ns")
        for with_identity in (True, False):
            with self.subTest(equal=True, identity=with_identity):
                self.assertTrue(ROTATE.native_same(baseline, dict(baseline), with_identity))
            for field in common + identity:
                with self.subTest(field=field, identity=with_identity):
                    changed = {**baseline, field: "invented mismatch"}
                    expected = not with_identity and field in identity
                    self.assertIs(ROTATE.native_same(baseline, changed, with_identity), expected)
                    self.assertIs(ROTATE.native_same(changed, baseline, with_identity), expected)

    def test_guard_unsupported_action_before_records(self):
        args = types.SimpleNamespace(native_action="invented-unsupported", native_apply=True, dry_run=False)
        self.refuses(lambda: ROTATE.NativeOperation(args), "native-action-not-supported")

    def test_guard_wrong_adapter_before_records(self):
        args = types.SimpleNamespace(native_action="disposable-exercise", native_apply=True,
                                     dry_run=False, adapter="codex")
        self.refuses(lambda: ROTATE.NativeOperation(args), "native-claude-adapter-required")

    def test_guard_reference_shape(self):
        self.refuses(lambda: self.operation_reader().reference([]), "native-reference-required")

    def test_guard_reference_digest_type(self):
        self.refuses(lambda: self.operation_reader().reference({"path": str(self.source), "sha256": 12}),
                     "native-reference-required")

    def test_guard_reference_digest_shape(self):
        self.refuses(lambda: self.operation_reader().reference({"path": str(self.source), "sha256": "wrong"}),
                     "native-reference-required")

    def test_guard_record_path_required(self):
        self.refuses(lambda: self.operation_reader().record(None, "0" * 64), "native-record-hash-required")

    def test_guard_record_digest_type(self):
        self.refuses(lambda: self.operation_reader().record(str(self.source), 12), "native-record-hash-required")

    def test_guard_record_digest_shape(self):
        self.refuses(lambda: self.operation_reader().record(str(self.source), "wrong"), "native-record-hash-required")

    def test_guard_record_name_type(self):
        self.refuses(lambda: self.operation_reader().instrument_packet("I2", 12), "native-instrument-record-name")

    def test_guard_record_name_shape(self):
        self.refuses(lambda: self.operation_reader().instrument_packet("I2", "../outside.json"),
                     "native-instrument-record-name")

    def test_guard_unknown_instrument_name(self):
        self.refuses(lambda: self.operation_reader().instrument_packet("UNKNOWN", "reader.json"), "native-instrument-name")

    def test_guard_instrument_bindings_shape(self):
        self.refuses(lambda: self.operation_reader().instrument("I2"), "native-instrument-bindings-required")


    def guard_root_identity_field(self, field, value, root="project_root"):
        # A direct method fixture isolates each declared root property. It
        # changes recorded metadata only, never a host directory or account.
        operation = self.operation_reader()
        operation.project, operation.store = self.project, self.base
        operation.preimages = {"project_root": ROTATE.native_snapshot(self.project),
                               "store_root": ROTATE.native_snapshot(self.base)}
        operation.preimages[root][field] = value
        before = NativeDisposableTests.inventory(self.base)
        self.refuses(operation.root_identities, "native-operation-root-changed")
        self.assertEqual(NativeDisposableTests.inventory(self.base), before)

    def test_guard_root_identity_type(self):
        self.guard_root_identity_field("type", "file")

    def test_guard_root_identity_dev(self):
        self.guard_root_identity_field("dev", -1)

    def test_guard_root_identity_ino(self):
        self.guard_root_identity_field("ino", -1)

    def test_guard_root_identity_mode(self):
        self.guard_root_identity_field("mode", 0o755)

    def test_guard_root_identity_uid(self):
        self.guard_root_identity_field("uid", -1)

    def test_guard_root_identity_gid(self):
        self.guard_root_identity_field("gid", -1)

    def test_guard_store_root_properties_are_checked_separately(self):
        for field, value in (("type", "file"), ("dev", -1), ("ino", -1),
                             ("mode", 0o755), ("uid", -1), ("gid", -1)):
            with self.subTest(field=field):
                self.guard_root_identity_field(field, value, "store_root")


    def test_guard_empty_row_list_under_byte_reader_fault(self):
        # Ordinary nonempty newline-terminated bytes always yield at least one
        # split line. Isolate this redundant lower bound with an explicit
        # broken byte-source contract, not a claim of unsafe JSON admission.
        class EmptyRows(bytes):
            def splitlines(self):
                return []
        self.refuses(lambda: ROTATE.native_rows(EmptyRows(b"\n"), SID, self.project), "native-row-limit")


    def donor_guard_fixture(self, action, restored=None):
        operation = self.operation_reader()
        current = ROTATE.native_snapshot(self.source)
        operation.current = lambda name: dict(current)
        operation.action = action
        operation.go = {}
        operation.preimages = {"donor": {**current, "sha256": "0" * 64}}
        operation.state = {} if restored is None else {"restores": {"donor": {"installed": restored(current)}}}
        return operation

    def test_guard_donor_changed_without_authorized_restore(self):
        operation = self.donor_guard_fixture("custody")
        self.refuses(operation.unchanged_donor, "native-donor-preimage-changed")

    def test_guard_donor_restore_record_is_not_authority_outside_rollback(self):
        operation = self.donor_guard_fixture("custody", restored=lambda current: dict(current))
        self.refuses(operation.unchanged_donor, "native-donor-preimage-changed")

    def test_guard_rollback_donor_requires_an_existing_restore_record(self):
        operation = self.donor_guard_fixture("rollback")
        self.refuses(operation.unchanged_donor, "native-donor-preimage-changed")

    def test_guard_restored_donor_must_match_its_record(self):
        operation = self.donor_guard_fixture("rollback", restored=lambda current: {**current, "sha256": "1" * 64})
        self.refuses(operation.unchanged_donor, "native-donor-preimage-changed")


if __name__ == "__main__":
    unittest.main()
