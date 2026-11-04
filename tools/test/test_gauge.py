#!/usr/bin/env python3
"""Tests for ops/lib/scripts/gauge.py, on synthetic bodies only. Standard library only.

Every case builds its own registry, bodies, spec and status-line record in a
temporary directory and runs gauge against them; no real body is read. Run:

    python3 -I -B tools/test/test_gauge.py
"""
import fcntl
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

GAUGE = Path(__file__).resolve().parents[2] / "ops" / "lib" / "scripts" / "gauge.py"
NOW = "2026-10-30T16:00:00Z"
SECRET = "SECRET-CONTENT-DO-NOT-PRINT"


def cid(n):
    return f"{n:08x}-0000-4000-8000-{n:012x}"


def j(row, spaced=False):
    return json.dumps(row, separators=(", ", ": ") if spaced else (",", ":"))


def claude_call(msg_id, model, inp, cache_read, cache_create, ts, blocks=2, sidechain=False):
    rows = []
    for b in range(blocks):
        rows.append({"parentUuid": None, "isSidechain": sidechain, "type": "assistant", "timestamp": ts,
                     "message": {"id": msg_id, "model": model, "role": "assistant",
                                 "content": [{"type": "text", "text": f"{SECRET} block {b}"}],
                                 "usage": {"input_tokens": inp, "cache_read_input_tokens": cache_read,
                                           "cache_creation_input_tokens": cache_create, "output_tokens": 50}}})
    return rows


def claude_user(text, ts):
    return {"parentUuid": None, "isSidechain": False, "type": "user", "timestamp": ts,
            "message": {"role": "user", "content": text}}


def claude_boundary(ts):
    return {"parentUuid": None, "logicalParentUuid": None, "isSidechain": False, "type": "system",
            "subtype": "compact_boundary", "content": "Conversation compacted", "timestamp": ts,
            "compactMetadata": {"trigger": "manual", "preTokens": 900000, "postTokens": 20000}}


def codex_context(model, ts, n):
    return {"timestamp": ts, "ordinal": n, "type": "turn_context", "payload": {"model": model, "cwd": "/x"}}


def codex_tokens(inp, window, ts, n):
    return {"timestamp": ts, "ordinal": n, "type": "event_msg",
            "payload": {"type": "token_count", "info": {"last_token_usage": {"input_tokens": inp, "output_tokens": 10},
                                                         "model_context_window": window}}}


def codex_message(text, ts, n):
    return {"timestamp": ts, "ordinal": n, "type": "response_item",
            "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": text}]}}


def codex_compacted(ts, n):
    return {"timestamp": ts, "ordinal": n, "type": "compacted",
            "payload": {"message": "", "replacement_history": [{"type": "message", "content": SECRET}], "window_number": 3}}


def copilot_usage(inp, window, model, ts):
    return {"type": "session.usage_record", "data": {"usage": {"model": model, "inputTokens": inp, "maxPromptTokens": window,
                                                               "cacheReadTokens": 5}}, "timestamp": ts}


class World:
    def __init__(self):
        scratch = GAUGE.parents[3] / "var" / "tmp"
        scratch.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(prefix="joe-gauge-test-", dir=scratch)
        self.root = Path(self.tmp.name)
        self.script = GAUGE
        self.default_ledger = False
        self.claude = self.root / "claude"
        self.codex_live = self.root / "codex" / "sessions"
        self.codex_arch = self.root / "codex" / "archived_sessions"
        self.copilot = self.root / "copilot"
        self.ledger = self.root / "storage" / "gauges" / "ledger.jsonl"
        self.spec = self.root / "gauge.md"
        self.spec.write_text("# gauge\n\nmodel=claude-opus-5-5|window=1000000|source=status line|observed=2026-10-26\n")
        self.state = self.root / "resource-state.json"
        self.identities = []

    def resident(self, key, provider, n):
        self.identities.append({"key": key, "person": key.title(), "provider": provider, "session_id": cid(n), "role": "r"})
        return cid(n)

    def claude_body(self, sid, rows, room="-room", tail=b""):
        path = self.claude / room / f"{sid}.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes("".join(r if isinstance(r, str) else j(r) + "\n" for r in rows).encode() + tail)
        return path

    def codex_body(self, sid, rows, archived=False, name="rollout-2026-10-30T10-00-00"):
        root = self.codex_arch if archived else self.codex_live / "2026" / "10" / "30"
        path = root / f"{name}-{sid}.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(j(r) + "\n" for r in rows))
        return path

    def copilot_body(self, sid, rows):
        path = self.copilot / sid / "events.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(j(r) + "\n" for r in rows))

    def command(self, *extra, ledger=True):
        reg = self.root / "registry.json"
        reg.write_text(json.dumps({"identities": self.identities}))
        cmd = [sys.executable, "-I", "-B", str(self.script), "--registry", str(reg), "--claude-root", str(self.claude),
               "--codex-root", str(self.codex_live), "--codex-archived-root", str(self.codex_arch),
               "--copilot-root", str(self.copilot), "--spec", str(self.spec), "--resource-state", str(self.state),
               "--now", NOW]
        if not self.default_ledger:
            cmd.extend(["--ledger", str(self.ledger)])
        cmd.extend(extra)
        if not ledger:
            cmd.append("--no-ledger")
        return cmd

    def run(self, *extra, ledger=True, umask=-1):
        return subprocess.run(self.command(*extra, ledger=ledger), capture_output=True, text=True, umask=umask)

    def rows(self):
        r = self.run("--json", ledger=False)
        assert r.returncode == 0, r.stderr
        return {row["key"]: row for row in map(json.loads, r.stdout.splitlines())}

    def close(self):
        self.tmp.cleanup()


class Base(unittest.TestCase):
    def setUp(self):
        self.w = World()

    def tearDown(self):
        self.w.close()


class ClaudeSide(Base):
    def test_latest_call_sum_and_table_window(self):
        sid = self.w.resident("shannon", "claude", 1)
        rows = (claude_call("m1", "claude-opus-5-5", 10, 100000, 2000, "2026-10-30T15:00:00Z")
                + [claude_user("next", "2026-10-30T15:01:00Z")]
                + claude_call("m2", "claude-opus-5-5", 20, 300000, 5000, "2026-10-30T15:30:00Z", blocks=3))
        self.w.claude_body(sid, rows)
        r = self.w.rows()["shannon"]
        self.assertEqual((r["tokens"], r["window"], r["percent"], r["state"]), (305020, 1000000, 30.5, "last observed"))
        self.assertEqual(r["age_seconds"], 1800)
        self.assertIn("spec table", r["window_source"])

    def test_zero_usage_and_sidechain_rows_are_never_readings(self):
        sid = self.w.resident("claudine", "claude", 2)
        rows = (claude_call("m1", "claude-opus-5-5", 0, 400000, 0, "2026-10-30T15:00:00Z")
                + claude_call("side", "claude-opus-5-5", 0, 900000, 0, "2026-10-30T15:10:00Z", sidechain=True)
                + claude_call("synth", "<synthetic>", 0, 0, 0, "2026-10-30T15:20:00Z", blocks=1))
        self.w.claude_body(sid, rows)
        r = self.w.rows()["claudine"]
        self.assertEqual((r["tokens"], r["model"]), (400000, "claude-opus-5-5"))

    def test_status_line_window_for_the_same_model(self):
        sid = self.w.resident("joy", "claude", 3)
        self.w.claude_body(sid, claude_call("m1", "claude-fable-5-1", 0, 500000, 0, "2026-10-30T15:00:00Z"))
        self.w.state.write_text(json.dumps({"generated_at": "2026-10-30T15:59:00Z",
                                            "model": {"id": "claude-fable-5-1"}, "context": {"window_size": 1000000}}))
        r = self.w.rows()["joy"]
        self.assertEqual(r["percent"], 50.0)
        self.assertIn("status line, unverified", r["window_source"])
        self.assertIn("window unverified", r["reason"])

    def test_unknown_window_is_printed_unknown_not_guessed(self):
        sid = self.w.resident("claudio", "claude", 4)
        self.w.claude_body(sid, claude_call("m1", "claude-sonnet-5-5", 0, 250000, 0, "2026-10-30T15:00:00Z"))
        r = self.w.rows()["claudio"]
        self.assertEqual((r["tokens"], r["window"], r["percent"], r["state"]), (250000, None, None, "window unknown"))
        self.assertIn("no reviewed window for claude-sonnet-5-5", r["reason"])
        table = self.w.run(ledger=False).stdout
        self.assertIn("unknown", table.split("claudio")[1].splitlines()[0])

    def test_compaction_after_the_reading(self):
        sid = self.w.resident("shannon", "claude", 5)
        rows = claude_call("m1", "claude-opus-5-5", 0, 900000, 0, "2026-10-30T15:00:00Z") + [claude_boundary("2026-10-30T15:05:00Z")]
        self.w.claude_body(sid, rows)
        r = self.w.rows()["shannon"]
        self.assertEqual((r["state"], r["percent"]), ("before compaction", None))
        self.assertEqual(r["tokens"], 900000)

    def test_spaced_json_from_a_rebuilt_body(self):
        sid = self.w.resident("shannon", "claude", 6)
        lines = [j(r, spaced=True) + "\n" for r in claude_call("m1", "claude-opus-5-5", 0, 123456, 0, "2026-10-30T15:00:00Z")]
        self.w.claude_body(sid, lines)
        self.assertEqual(self.w.rows()["shannon"]["tokens"], 123456)

    def test_unterminated_final_line_is_ignored(self):
        sid = self.w.resident("shannon", "claude", 7)
        self.w.claude_body(sid, claude_call("m1", "claude-opus-5-5", 0, 111111, 0, "2026-10-30T15:00:00Z"),
                           tail=b'{"type":"assistant","message":{"usage":{"input_tokens":9')
        self.assertEqual(self.w.rows()["shannon"]["tokens"], 111111)

    def test_a_quoted_boundary_in_content_is_not_a_compaction(self):
        sid = self.w.resident("shannon", "claude", 8)
        rows = (claude_call("m1", "claude-opus-5-5", 0, 222222, 0, "2026-10-30T15:00:00Z")
                + [claude_user('look: {"type":"system","subtype":"compact_boundary"}', "2026-10-30T15:01:00Z")])
        self.w.claude_body(sid, rows)
        self.assertEqual(self.w.rows()["shannon"]["state"], "last observed")

    def test_reading_found_deep_in_the_tail_and_unknown_beyond_the_bound(self):
        sid = self.w.resident("deep", "claude", 9)
        filler = [claude_user("x" * 1000, "2026-10-30T15:01:00Z")] * 3000          # about 3.1 MB
        self.w.claude_body(sid, claude_call("m1", "claude-opus-5-5", 0, 333333, 0, "2026-10-30T15:00:00Z") + filler)
        self.assertEqual(self.w.rows()["deep"]["tokens"], 333333)
        sid2 = self.w.resident("buried", "claude", 10)
        filler = [claude_user("x" * 1000, "2026-10-30T15:01:00Z")] * 17000         # about 17.6 MB, beyond 16,000,000
        self.w.claude_body(sid2, claude_call("m1", "claude-opus-5-5", 0, 444444, 0, "2026-10-30T15:00:00Z") + filler)
        r = self.w.rows()["buried"]
        self.assertEqual((r["tokens"], r["state"]), (None, "unknown"))
        self.assertIn("16,000,000", r["reason"])

    def test_content_is_never_printed_or_stored(self):
        sid = self.w.resident("shannon", "claude", 11)
        self.w.claude_body(sid, claude_call("m1", "claude-opus-5-5", 0, 100, 0, "2026-10-30T15:00:00Z"))
        out = self.w.run().stdout + self.w.run("--json").stdout
        self.assertNotIn(SECRET, out)
        self.assertNotIn(SECRET, self.w.ledger.read_text())

    # -- Claudio section 131 -------------------------------------------------
    def test_c1_the_reviewed_table_outranks_a_status_line_for_the_same_model(self):
        sid = self.w.resident("shannon", "claude", 12)
        self.w.claude_body(sid, claude_call("m1", "claude-opus-5-5", 0, 150000, 0, "2026-10-30T15:00:00Z"))
        self.w.state.write_text(json.dumps({"generated_at": "2026-08-01T00:00:00Z",
                                            "model": {"id": "claude-opus-5-5"}, "context": {"window_size": 200000}}))
        r = self.w.rows()["shannon"]
        self.assertEqual((r["window"], r["percent"], r["state"]), (1000000, 15.0, "last observed"))
        self.assertIn("spec table", r["window_source"])
        self.assertIn("status line (unverified) says 200,000", r["reason"])

    def test_c1_the_provider_window_outranks_the_table(self):
        sid = self.w.resident("george", "codex", 13)
        self.w.spec.write_text("model=gpt-6.1-terra|window=999999|source=test|observed=2026-10-30\n")
        self.w.codex_body(sid, [codex_context("gpt-6.1-terra", "2026-10-30T15:00:00Z", 1),
                                codex_tokens(237500, 475000, "2026-10-30T15:01:00Z", 2)])
        r = self.w.rows()["george"]
        self.assertEqual((r["window"], r["percent"]), (475000, 50.0))

    def test_c2_compacted_with_no_reading_since(self):
        sid = self.w.resident("shannon", "claude", 14)
        self.w.claude_body(sid, [claude_user("hello", "2026-10-30T15:00:00Z"), claude_boundary("2026-10-30T15:05:00Z"),
                                 claude_user("after", "2026-10-30T15:06:00Z")])
        r = self.w.rows()["shannon"]
        self.assertEqual((r["state"], r["tokens"], r["percent"]), ("compacted", None, None))
        self.assertIn("compacted, no call since", r["reason"])
        sid = self.w.resident("david", "codex", 15)
        self.w.codex_body(sid, [codex_context("gpt-5.6-sol", "2026-10-30T15:00:00Z", 1), codex_compacted("2026-10-30T15:02:00Z", 2)])
        r = self.w.rows()["david"]
        self.assertEqual((r["state"], r["tokens"]), ("compacted", None))

    def test_o1_boundary_rows_are_found_in_any_field_order_and_length(self):
        """The writer's order is kept as a regression (Claude Code 2.1.314: parentUuid, logicalParentUuid,
        isSidechain, then optionally teamName, agentName, agentId, then type and subtype). The match no longer
        depends on field order, field count or the 320-byte head (Shannon's decision on Claudio section 131, O1)."""
        def boundary(extra, spaced=False, tail=None):
            row = {"parentUuid": None, "logicalParentUuid": cid(99), "isSidechain": False}
            row.update(extra)
            row.update(tail if tail is not None else {"type": "system", "subtype": "compact_boundary"})
            row.update({"content": "Conversation compacted", "timestamp": "2026-10-30T15:05:00Z",
                        "compactMetadata": {"trigger": "auto", "preTokens": 900000}})
            return j(row, spaced=spaced) + "\n"
        team = {"teamName": "sessions-continuity-team", "agentName": "continuity-manager-two", "agentId": cid(98)}
        many = {f"field{i}": "x" * 40 for i in range(12)}
        cases = (("writer base, 3 fields", boundary({})),
                 ("team variant, 6 fields", boundary(team)),
                 ("team variant, 6 fields, spaced", boundary(team, spaced=True)),
                 ("7 fields", boundary(dict(team, extraField="x"))),
                 ("15 fields, type past byte 320", boundary(many)),
                 ("subtype before type", boundary({}, tail={"subtype": "compact_boundary", "type": "system"})),
                 ("subtype not adjacent to type", boundary({}, tail={"type": "system", "level": "info", "subtype": "compact_boundary"})))
        for n, (label, line) in enumerate(cases, 60):
            with self.subTest(label):
                sid = self.w.resident(f"k{n}", "claude", n)
                lines = [j(r) + "\n" for r in claude_call("m1", "claude-opus-5-5", 0, 845000, 0, "2026-10-30T15:00:00Z")]
                self.w.claude_body(sid, lines + [line])
                self.assertEqual(self.w.rows()[f"k{n}"]["state"], "before compaction")

    def test_o1_the_token_elsewhere_is_not_a_compaction(self):
        cases = {
            "nested in an assistant's tool input": claude_call("m2", "claude-opus-5-5", 0, 500000, 0, "2026-10-30T15:06:00Z")[0],
            "a system row of another subtype": {"type": "system", "subtype": "informational", "note": "compact_boundary",
                                                "timestamp": "2026-10-30T15:06:00Z", "x": {"subtype": "compact_boundary"}},
            "a top-level subtype on a user row": {"type": "user", "subtype": "compact_boundary", "timestamp": "2026-10-30T15:06:00Z",
                                                  "message": {"role": "user", "content": "x"}},
        }
        cases["nested in an assistant's tool input"]["message"]["content"].append(
            {"type": "tool_use", "name": "probe", "input": {"type": "system", "subtype": "compact_boundary"}})
        for n, (label, row) in enumerate(cases.items(), 80):
            with self.subTest(label):
                sid = self.w.resident(f"t{n}", "claude", n)
                rows = claude_call("m1", "claude-opus-5-5", 0, 400000, 0, "2026-10-30T15:00:00Z") + [row]
                self.w.claude_body(sid, rows)
                r = self.w.rows()[f"t{n}"]
                self.assertEqual(r["state"], "last observed")
        self.assertEqual(self.w.rows()["t80"]["tokens"], 500000)          # the reading in that row still counts

    def test_o1_a_boundary_without_a_timestamp_still_counts(self):
        sid = self.w.resident("k90", "claude", 90)
        row = {"type": "system", "subtype": "compact_boundary", "content": "Conversation compacted"}
        self.w.claude_body(sid, claude_call("m1", "claude-opus-5-5", 0, 845000, 0, "2026-10-30T15:00:00Z") + [row])
        r = self.w.rows()["k90"]
        self.assertEqual(r["state"], "before compaction")
        self.assertIn("unknown time", r["reason"])
    # -- the review of the order-independent match (Claudine's workflow, 10-30) ------
    def test_a_compaction_then_a_fresh_call_is_current(self):
        sid = self.w.resident("shannon", "claude", 91)
        rows = [claude_boundary("2026-10-30T15:05:00Z")] + claude_call("m2", "claude-opus-5-5", 0, 300000, 0, "2026-10-30T15:10:00Z")
        self.w.claude_body(sid, claude_call("m1", "claude-opus-5-5", 0, 900000, 0, "2026-10-30T15:00:00Z") + rows)
        r = self.w.rows()["shannon"]
        self.assertEqual((r["state"], r["tokens"], r["percent"]), ("last observed", 300000, 30.0))

    def test_the_newest_of_several_boundaries_is_reported(self):
        sid = self.w.resident("shannon", "claude", 92)
        self.w.claude_body(sid, claude_call("m1", "claude-opus-5-5", 0, 900000, 0, "2026-10-30T15:00:00Z")
                           + [claude_boundary("2026-10-30T15:05:00Z"), claude_boundary("2026-10-30T15:09:00Z")])
        r = self.w.rows()["shannon"]
        self.assertEqual(r["state"], "before compaction")
        self.assertIn("compacted at 2026-10-30T15:09:00Z", r["reason"])

    def test_a_corrupt_line_carrying_the_token_is_not_a_compaction(self):
        for n, where in ((93, "after"), (94, "before")):
            with self.subTest(where):
                sid = self.w.resident(f"c{n}", "claude", n)
                broken = '{"type":"system","subtype":"compact_boundary","timestamp":"2026-10-30T15:05:00Z",' + "\n"
                call = [j(r) + "\n" for r in claude_call("m1", "claude-opus-5-5", 0, 400000, 0, "2026-10-30T15:00:00Z")]
                self.w.claude_body(sid, call + [broken] if where == "after" else [broken] + call)
                r = self.w.rows()[f"c{n}"]
                self.assertEqual((r["state"], r["tokens"]), ("last observed", 400000))

    def test_the_token_far_into_the_line_and_subtype_last(self):
        lines = {
            "100,000 bytes before type": {"parentUuid": None, "pad": "x" * 100000, "type": "system", "subtype": "compact_boundary",
                                          "timestamp": "2026-10-30T15:05:00Z"},
            "subtype is the last field": {"timestamp": "2026-10-30T15:05:00Z", "type": "system", "subtype": "compact_boundary"},
        }
        for n, (label, row) in enumerate(lines.items(), 95):
            with self.subTest(label):
                sid = self.w.resident(f"f{n}", "claude", n)
                self.w.claude_body(sid, claude_call("m1", "claude-opus-5-5", 0, 845000, 0, "2026-10-30T15:00:00Z") + [row])
                self.assertEqual(self.w.rows()[f"f{n}"]["state"], "before compaction")

    def test_a_boundary_time_that_is_not_a_time_reads_unknown_time(self):
        for n, stamp in ((97, None), (98, ""), (99, 12345), (100, "not a time")):
            with self.subTest(stamp=stamp):
                sid = self.w.resident(f"s{n}", "claude", n)
                row = {"type": "system", "subtype": "compact_boundary", "timestamp": stamp}
                self.w.claude_body(sid, claude_call("m1", "claude-opus-5-5", 0, 845000, 0, "2026-10-30T15:00:00Z") + [row])
                r = self.w.rows()[f"s{n}"]
                self.assertEqual(r["state"], "before compaction")
                self.assertIn("compacted at unknown time", r["reason"])

    def test_a_deeply_nested_row_with_the_token_never_ends_the_run(self):
        sid = self.w.resident("deep", "claude", 101)
        deep = '{"type":"user","x":' + "[" * 200000 + '"compact_boundary"' + "]" * 200000 + "}\n"
        call = [j(r) + "\n" for r in claude_call("m1", "claude-opus-5-5", 0, 400000, 0, "2026-10-30T15:00:00Z")]
        self.w.claude_body(sid, call + [deep])
        other = self.w.resident("other", "claude", 102)
        self.w.claude_body(other, claude_call("m1", "claude-opus-5-5", 0, 100000, 0, "2026-10-30T15:00:00Z"))
        rows = self.w.rows()
        self.assertEqual((rows["deep"]["state"], rows["deep"]["tokens"]), ("last observed", 400000))
        self.assertEqual(rows["other"]["tokens"], 100000)

    def test_the_real_boundary_time_form_is_shown(self):
        sid = self.w.resident("ms", "claude", 103)
        row = {"type": "system", "subtype": "compact_boundary", "timestamp": "2026-10-30T15:05:00.123Z"}
        self.w.claude_body(sid, claude_call("m1", "claude-opus-5-5", 0, 845000, 0, "2026-10-30T15:00:00Z") + [row])
        self.assertIn("compacted at 2026-10-30T15:05:00.123Z", self.w.rows()["ms"]["reason"])

    def test_one_body_that_breaks_its_reader_is_one_unknown_row(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("gauge_under_test", GAUGE)
        gauge = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gauge)
        sid = self.w.resident("broken", "claude", 104)
        self.w.claude_body(sid, claude_call("m1", "claude-opus-5-5", 0, 845000, 0, "2026-10-30T15:00:00Z"))

        def explode(path):
            raise ValueError("synthetic")
        gauge.read_claude = explode
        row = gauge.measure(self.w.identities[-1], gauge.parse_time(NOW), {}, None, self.w.claude, [], [], self.w.copilot)
        self.assertEqual((row["state"], row["tokens"], row["reason"]), ("unknown", None, "body unreadable: ValueError"))

    def test_a_side_conversation_boundary_does_not_count(self):
        sid = self.w.resident("side", "claude", 105)
        side = dict(claude_boundary("2026-10-30T15:05:00Z"), isSidechain=True)
        self.w.claude_body(sid, claude_call("m1", "claude-opus-5-5", 0, 400000, 0, "2026-10-30T15:00:00Z") + [side])
        r = self.w.rows()["side"]
        self.assertEqual((r["state"], r["tokens"], r["percent"]), ("last observed", 400000, 40.0))
        sid = self.w.resident("main", "claude", 106)
        main = dict(claude_boundary("2026-10-30T15:05:00Z"), isSidechain=False)
        self.w.claude_body(sid, claude_call("m1", "claude-opus-5-5", 0, 400000, 0, "2026-10-30T15:00:00Z") + [main])
        self.assertEqual(self.w.rows()["main"]["state"], "before compaction")

    def test_a_boundary_time_longer_than_40_characters_reads_unknown_time(self):
        sid = self.w.resident("long", "claude", 107)
        row = {"type": "system", "subtype": "compact_boundary", "timestamp": "2026-10-30T15:05:00.123456+00:00:00.123456"}
        self.w.claude_body(sid, claude_call("m1", "claude-opus-5-5", 0, 845000, 0, "2026-10-30T15:00:00Z") + [row])
        self.assertIn("compacted at unknown time", self.w.rows()["long"]["reason"])

    def test_load_json_swallows_only_parse_failures(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("gauge_under_test", GAUGE)
        gauge = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gauge)

        class Interrupt(Exception):
            pass

        def interrupted(line):
            raise Interrupt()
        import types
        gauge.json = types.SimpleNamespace(loads=interrupted)   # this loaded copy only; the json module is untouched
        with self.assertRaises(Interrupt):                      # a time limit raised mid-parse must reach the caller
            gauge.load_json(b'{"a": 1}')


class CodexSide(Base):
    def test_joe_method_model_from_the_preceding_turn_context(self):
        sid = self.w.resident("george", "codex", 20)
        rows = [codex_context("gpt-6.1-terra", "2026-10-30T15:00:00Z", 1),
                codex_tokens(286264, 475000, "2026-10-30T15:03:34Z", 2),
                codex_context("gpt-later-model", "2026-10-30T15:04:00Z", 3)]
        self.w.codex_body(sid, rows)
        r = self.w.rows()["george"]
        self.assertEqual((r["model"], r["tokens"], r["window"], r["percent"]), ("gpt-6.1-terra", 286264, 475000, 60.3))
        self.assertIn("same event", r["window_source"])

    def test_compacted_row_after_the_reading_supersedes_without_parsing(self):
        sid = self.w.resident("david", "codex", 21)
        rows = [codex_context("gpt-5.6-sol", "2026-10-30T15:00:00Z", 1), codex_tokens(163383, 258400, "2026-10-30T15:01:00Z", 2),
                codex_compacted("2026-10-30T15:02:00Z", 3)]
        self.w.codex_body(sid, rows)
        r = self.w.rows()["david"]
        self.assertEqual((r["state"], r["percent"]), ("before compaction", None))
        self.assertIn("2026-10-30T15:02:00Z", r["reason"])
        self.assertNotIn(SECRET, self.w.run("--json", ledger=False).stdout)

    def test_quoted_structure_in_a_message_is_ignored(self):
        sid = self.w.resident("alan", "codex", 22)
        rows = [codex_context("gpt-6.1-terra", "2026-10-30T15:00:00Z", 1), codex_tokens(1000, 475000, "2026-10-30T15:01:00Z", 2),
                codex_message('{"type":"compacted"} and "token_count" quoted', "2026-10-30T15:02:00Z", 3)]
        self.w.codex_body(sid, rows)
        r = self.w.rows()["alan"]
        self.assertEqual((r["state"], r["tokens"]), ("last observed", 1000))

    def test_archived_body_is_labelled(self):
        sid = self.w.resident("king", "codex", 23)
        self.w.codex_body(sid, [codex_context("gpt-5.6-sol", "2026-08-08T04:10:00Z", 1),
                                codex_tokens(16670, 258400, "2026-08-08T04:10:43Z", 2)], archived=True)
        r = self.w.rows()["king"]
        self.assertEqual((r["body"], r["state"]), ("archived", "archived body"))

    def test_live_preferred_over_archived_and_ambiguity_refused(self):
        sid = self.w.resident("steve", "codex", 24)
        self.w.codex_body(sid, [codex_tokens(5, 475000, "2026-08-01T00:00:00Z", 1)], archived=True)
        self.w.codex_body(sid, [codex_context("gpt-6.1-sol", "2026-10-19T17:00:00Z", 1),
                                codex_tokens(127766, 475000, "2026-10-19T17:12:46Z", 2)])
        self.assertEqual(self.w.rows()["steve"]["tokens"], 127766)
        self.w.codex_body(sid, [codex_tokens(9, 475000, "2026-10-19T17:13:00Z", 1)], name="rollout-2026-10-20T00-00-00")
        r = self.w.rows()["steve"]
        self.assertEqual(r["state"], "unknown")
        self.assertIn("refusing to choose", r["reason"])

    def test_a_partial_id_never_matches_as_a_suffix(self):
        full = self.w.resident("steve", "codex", 25)
        self.w.codex_body(full, [codex_context("gpt-6.1-sol", "2026-10-19T17:00:00Z", 1),
                                 codex_tokens(127766, 475000, "2026-10-19T17:12:46Z", 2)])
        self.w.identities.append({"key": "partial", "provider": "codex", "session_id": full.split("-", 3)[3]})
        rows = self.w.rows()
        self.assertEqual(rows["steve"]["tokens"], 127766)
        self.assertEqual((rows["partial"]["tokens"], rows["partial"]["reason"]), (None, "body not found"))


class CopilotAndRegistry(Base):
    def test_copilot_usage_record(self):
        sid = self.w.resident("jojo-git", "copilot", 30)
        self.w.copilot_body(sid, [copilot_usage(114880, 272000, "gpt-6.1-sol", "2026-10-29T18:41:57Z")])
        r = self.w.rows()["jojo-git"]
        self.assertEqual((r["tokens"], r["window"], r["percent"]), (114880, 272000, 42.2))

    def test_copilot_compaction_after(self):
        sid = self.w.resident("jojo-git", "copilot", 31)
        self.w.copilot_body(sid, [copilot_usage(1000, 272000, "m", "2026-10-29T18:41:57Z"),
                                  {"type": "session.compaction_complete", "timestamp": "2026-10-29T19:00:00Z", "data": {}}])
        self.assertEqual(self.w.rows()["jojo-git"]["state"], "before compaction")

    def test_missing_body_unknown_provider_and_bad_id(self):
        self.w.resident("ghost", "claude", 40)
        self.w.identities.append({"key": "odd", "provider": "gemini", "session_id": cid(41)})
        self.w.identities.append({"key": "bad", "provider": "claude", "session_id": "../../etc/passwd"})
        rows = self.w.rows()
        self.assertEqual(rows["ghost"]["reason"], "body not found")
        self.assertIn("no reader for provider gemini", rows["odd"]["reason"])
        self.assertIn("not a plain identifier", rows["bad"]["reason"])

    def test_tokens_above_the_window_are_invalid(self):
        sid = self.w.resident("over", "codex", 42)
        self.w.codex_body(sid, [codex_tokens(500000, 475000, "2026-10-30T15:00:00Z", 1)])
        self.assertEqual(self.w.rows()["over"]["state"], "invalid")


class Ledger(Base):
    def test_one_line_per_resident_per_run_and_no_ledger_writes_nothing(self):
        for n, key in ((50, "a"), (51, "b")):
            sid = self.w.resident(key, "claude", n)
            self.w.claude_body(sid, claude_call("m", "claude-opus-5-5", 0, 1000 * n, 0, "2026-10-30T15:00:00Z"))
        self.w.run("--json", ledger=False)
        self.assertFalse(self.w.ledger.exists())
        self.w.run()
        self.w.run()
        lines = [json.loads(l) for l in self.w.ledger.read_text().splitlines()]
        self.assertEqual(len(lines), 4)
        self.assertEqual({l["schema"] for l in lines}, {"gauge/1"})
        self.assertEqual(oct(self.w.ledger.stat().st_mode & 0o777), "0o600")

    def test_unreadable_registry_measures_nothing(self):
        r = subprocess.run([sys.executable, "-I", "-B", str(GAUGE), "--registry", str(self.w.root / "none.json"),
                            "--ledger", str(self.w.ledger)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        self.assertFalse(self.w.ledger.exists())


class DefaultLedger(Base):
    """Execute the actual script and shared guard in a synthetic room layout."""

    def setUp(self):
        super().setUp()
        self.w.script = self.w.root / "ops" / "lib" / "scripts" / "gauge.py"
        self.w.script.parent.mkdir(parents=True)
        shutil.copy2(GAUGE, self.w.script)
        shutil.copy2(GAUGE.parents[1] / "statepaths.py", self.w.script.parents[1] / "statepaths.py")
        self.w.default_ledger = True
        self.w.ledger = self.w.root / "logs" / "gauges" / "ledger.jsonl"
        self.legacy = self.w.root / "storage" / "gauges"
        sid = self.w.resident("fixture", "codex", 200)
        self.w.codex_body(sid, [codex_context("fixture-model", "2026-10-30T15:00:00Z", 1),
                                codex_tokens(12345, 100000, "2026-10-30T15:01:00Z", 2)])

    def refused(self):
        r = self.w.run("--json")
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertEqual(json.loads(r.stdout)["tokens"], 12345)
        self.assertNotIn("Traceback", r.stderr)
        diagnostic = json.loads(r.stderr)
        self.assertEqual(diagnostic["tool"], "gauge")
        self.assertEqual(diagnostic["error"], "ledger_append_failed")
        self.assertEqual(diagnostic["ledger"], str(self.w.ledger))
        self.assertIn("legacy", diagnostic["reason"])
        self.assertFalse((self.w.root / "logs").exists())
        return r

    def test_fresh_default_creates_only_logs_with_unchanged_rows(self):
        r = self.w.run("--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.w.ledger.read_text(), r.stdout)
        row = json.loads(r.stdout)
        self.assertEqual((row["schema"], row["tokens"], row["window"], row["percent"], row["state"]),
                         ("gauge/1", 12345, 100000, 12.3, "last observed"))
        self.assertFalse((self.w.root / "storage").exists())
        self.assertEqual({p.name for p in self.w.ledger.parent.iterdir()}, {"ledger.jsonl", "ledger.lock"})

    def test_populated_legacy_ledger_and_lock_bytes_and_modes_untouched(self):
        self.legacy.mkdir(parents=True)
        ledger = self.legacy / "ledger.jsonl"
        lock = self.legacy / "ledger.lock"
        ledger.write_bytes(b'{"old":"fixture"}\n')
        lock.write_bytes(b"old lock fixture\x00\n")
        ledger.chmod(0o640)
        lock.chmod(0o660)
        before = [(p.read_bytes(), p.stat().st_mode, p.stat().st_mtime_ns) for p in (ledger, lock)]
        self.refused()
        self.assertEqual(before, [(p.read_bytes(), p.stat().st_mode, p.stat().st_mtime_ns) for p in (ledger, lock)])

    def test_empty_legacy_directory_refuses(self):
        self.legacy.mkdir(parents=True)
        self.refused()
        self.assertEqual(list(self.legacy.iterdir()), [])

    def test_explicit_default_or_normalized_alias_cannot_bypass_legacy_guard(self):
        self.legacy.mkdir(parents=True)
        for ledger in (self.w.ledger, self.w.ledger.parent / ".." / "gauges" / "ledger.jsonl"):
            with self.subTest(ledger=str(ledger)):
                result = self.w.run("--json", "--ledger", str(ledger))
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertEqual(json.loads(result.stderr)["error"], "ledger_append_failed")
                self.assertIn("legacy state", json.loads(result.stderr)["reason"])
                self.assertFalse((self.w.root / "logs").exists())

    def test_legacy_refusal_also_preserves_existing_destination(self):
        self.legacy.mkdir(parents=True)
        self.w.ledger.parent.mkdir(parents=True)
        lock = self.w.ledger.with_suffix(".lock")
        self.w.ledger.write_bytes(b"destination fixture prefix\n")
        lock.write_bytes(b"destination lock fixture\n")
        before = [(p.read_bytes(), p.stat().st_mode, p.stat().st_mtime_ns) for p in (self.w.ledger, lock)]
        r = self.w.run("--json")
        self.assertEqual(r.returncode, 2)
        self.assertEqual(json.loads(r.stdout)["tokens"], 12345)
        self.assertEqual(json.loads(r.stderr)["error"], "ledger_append_failed")
        self.assertEqual(before, [(p.read_bytes(), p.stat().st_mode, p.stat().st_mtime_ns)
                                 for p in (self.w.ledger, lock)])

    def test_legacy_file_refuses(self):
        self.legacy.parent.mkdir()
        self.legacy.write_bytes(b"legacy fixture")
        self.refused()
        self.assertEqual(self.legacy.read_bytes(), b"legacy fixture")

    def test_legacy_symlink_refuses_without_touching_target(self):
        self.legacy.parent.mkdir()
        target = self.w.root / "target"
        target.mkdir()
        self.legacy.symlink_to(target, target_is_directory=True)
        self.refused()
        self.assertTrue(self.legacy.is_symlink())
        self.assertEqual(list(target.iterdir()), [])

    def test_dangling_legacy_symlink_refuses(self):
        self.legacy.parent.mkdir()
        self.legacy.symlink_to(self.w.root / "missing")
        self.refused()
        self.assertTrue(self.legacy.is_symlink())

    def test_legacy_fifo_refuses_without_opening_it(self):
        self.legacy.parent.mkdir()
        os.mkfifo(self.legacy, 0o600)
        self.refused()
        self.assertTrue(stat.S_ISFIFO(self.legacy.lstat().st_mode))

    def test_dangling_legacy_parent_refuses(self):
        self.legacy.parent.symlink_to(self.w.root / "missing")
        self.refused()
        self.assertTrue(self.legacy.parent.is_symlink())

    def test_nondirectory_legacy_parent_refuses(self):
        self.legacy.parent.write_bytes(b"parent fixture")
        self.refused()
        self.assertEqual(self.legacy.parent.read_bytes(), b"parent fixture")

    def test_symlink_legacy_parent_refuses_even_with_absent_leaf(self):
        target = self.w.root / "target"
        target.mkdir()
        self.legacy.parent.symlink_to(target, target_is_directory=True)
        self.refused()
        self.assertEqual(list(target.iterdir()), [])

    def test_unsearchable_legacy_parent_refuses(self):
        if os.geteuid() == 0:
            self.skipTest("root bypasses directory search permissions")
        self.legacy.parent.mkdir(mode=0o600)
        try:
            self.refused()
            self.assertEqual(stat.S_IMODE(self.legacy.parent.stat().st_mode), 0o600)
        finally:
            self.legacy.parent.chmod(0o700)  # synthetic fixture cleanup only

    def test_no_ledger_with_legacy_writes_zero_files(self):
        self.legacy.mkdir(parents=True)
        old = self.legacy / "ledger.jsonl"
        old.write_bytes(b"fixture prefix\n")
        cmd = self.w.command("--json", ledger=False)
        before = {p.relative_to(self.w.root): (p.lstat().st_mode, p.lstat().st_mtime_ns,
                                               p.read_bytes() if p.is_file() else None)
                  for p in self.w.root.rglob("*")}
        r = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["tokens"], 12345)
        after = {p.relative_to(self.w.root): (p.lstat().st_mode, p.lstat().st_mtime_ns,
                                              p.read_bytes() if p.is_file() else None)
                 for p in self.w.root.rglob("*")}
        self.assertEqual(after, before)

    def test_copied_script_no_helper_supports_no_ledger_and_explicit_ledger(self):
        script = self.w.root / "copy-only" / "ops" / "lib" / "scripts" / "gauge.py"
        script.parent.mkdir(parents=True)
        shutil.copy2(GAUGE, script)
        self.w.script = script
        self.assertEqual(self.w.run("--json", ledger=False).returncode, 0)
        custom = self.w.root / "custom" / "fixture.jsonl"
        r = self.w.run("--json", "--ledger", str(custom))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(custom.read_text(), r.stdout)
        r = self.w.run("--json")
        self.assertEqual(r.returncode, 2)
        self.assertEqual(json.loads(r.stderr)["error"], "ledger_append_failed")
        self.assertEqual(json.loads(r.stdout)["tokens"], 12345)
        self.assertFalse((script.parents[3] / "logs").exists())

    def test_explicit_legacy_ledger_interface_remains_compatible(self):
        self.legacy.mkdir(parents=True)
        custom = self.legacy / "ledger.jsonl"
        prefix = b'{"schema":"old-fixture"}\n'
        custom.write_bytes(prefix)
        r = self.w.run("--json", "--ledger", str(custom))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(custom.read_bytes(), prefix + r.stdout.encode())
        self.assertFalse((self.w.root / "logs").exists())

    def test_reviewed_copy_release_preserves_old_prefix_then_appends(self):
        self.legacy.mkdir(parents=True)
        old = self.legacy / "ledger.jsonl"
        prefix = b'{"schema": "fixture-old", "tokens": 17}\n\n'
        old.write_bytes(prefix)
        self.refused()
        self.w.ledger.parent.mkdir(parents=True)
        shutil.copy2(old, self.w.ledger)  # simulate the separately reviewed fixture copy
        self.legacy.rename(self.w.root / "released-fixture")
        r = self.w.run("--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.w.ledger.read_bytes(), prefix + r.stdout.encode())
        self.assertEqual((self.w.root / "released-fixture" / "ledger.jsonl").read_bytes(), prefix)

    def test_new_default_modes_are_private_under_umask_zero(self):
        r = self.w.run("--json", umask=0)
        self.assertEqual(r.returncode, 0, r.stderr)
        for path in (self.w.root / "logs", self.w.ledger.parent):
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o700)
        for path in (self.w.ledger, self.w.ledger.with_suffix(".lock")):
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)

    def test_existing_modes_are_preserved(self):
        self.w.ledger.parent.mkdir(parents=True)
        paths = (self.w.root / "logs", self.w.ledger.parent, self.w.ledger, self.w.ledger.with_suffix(".lock"))
        self.w.ledger.write_bytes(b"fixture-prefix\n")
        paths[-1].write_bytes(b"fixture-lock\n")
        modes = (0o755, 0o750, 0o640, 0o660)
        for path, mode in zip(paths, modes):
            path.chmod(mode)
        r = self.w.run("--json", umask=0)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(tuple(stat.S_IMODE(p.stat().st_mode) for p in paths), modes)
        self.assertEqual(paths[-1].read_bytes(), b"fixture-lock\n")

    def test_append_io_failure_is_structured_after_truthful_table(self):
        self.w.ledger.parent.mkdir(parents=True)
        self.w.ledger.mkdir()
        r = self.w.run()
        self.assertEqual(r.returncode, 2)
        self.assertIn("fixture", r.stdout)
        self.assertIn("12,345", r.stdout)
        self.assertNotIn("Traceback", r.stderr)
        self.assertEqual(json.loads(r.stderr)["error"], "ledger_append_failed")

    def test_shared_append_lock_blocks_then_releases(self):
        self.w.ledger.parent.mkdir(parents=True)
        lock_path = self.w.ledger.with_suffix(".lock")
        with lock_path.open("a") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            proc = subprocess.Popen(self.w.command("--json"), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                with self.assertRaises(subprocess.TimeoutExpired):
                    proc.communicate(timeout=0.2)
                self.assertFalse(self.w.ledger.exists())
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
                stdout, stderr = proc.communicate(timeout=5)
                self.assertEqual(proc.returncode, 0, stderr)
                self.assertEqual(self.w.ledger.read_text(), stdout)
            finally:
                if proc.poll() is None:
                    proc.kill()
                    proc.communicate()


if __name__ == "__main__":
    unittest.main(verbosity=1)
