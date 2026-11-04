#!/usr/bin/env python3
"""Tests for ops/lib/scripts/closeout.py, on synthetic bodies only. Standard library only.

Every case builds its own registry, transcripts, window table and state folder
in a temporary directory and runs closeout as the hook would: hook input on
standard input. No real body, registry or settings file is touched, and nothing
is wired. Run:

    python3 -I -B tools/test/test_closeout.py
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

CLOSEOUT = Path(__file__).resolve().parents[2] / "ops" / "lib" / "scripts" / "closeout.py"
ROOM_TEMPLATE = Path(__file__).resolve().parents[2] / "ops" / "src" / "reports" / "closeout.md.tpl"
SECRET = "SECRET-CONTENT-DO-NOT-PRINT"
FRONT = """---
template_type: report
template_id: closeout
template_version: 9
requires_slots:
  - PERCENT
  - WINDOW
  - READING_TIME
  - ROTATION_WRITER
slot_notes:
  PERCENT: p
  WINDOW: w
  READING_TIME: t
  ROTATION_WRITER: r
---
"""
BODY = "TEST CARD {{PERCENT}} of {{WINDOW}} at {{READING_TIME}}.\nStep five: {{ROTATION_WRITER}} runs it.\n"
MANAGER = {"key": "session-doctor", "provider": "claude", "session_id": "00000384-0000-4000-8000-000000000384",
           "person": "Claude Shannon", "role": "Session Continuity Manager"}
ASSISTANT = {"key": "claudine-colbert", "provider": "claude", "session_id": "00000385-0000-4000-8000-000000000385",
             "person": "Claudine Colbert", "role": "Assistant Session Continuity Manager"}


def cid(n):
    return f"{n:08x}-0000-4000-8000-{n:012x}"


def claude_call(msg_id, tokens, ts, model="claude-opus-5-5"):
    return {"parentUuid": None, "isSidechain": False, "type": "assistant", "timestamp": ts,
            "message": {"id": msg_id, "model": model, "role": "assistant",
                        "content": [{"type": "text", "text": SECRET}],
                        "usage": {"input_tokens": 10, "cache_read_input_tokens": tokens - 10,
                                  "cache_creation_input_tokens": 0, "output_tokens": 5}}}


def boundary(ts):
    return {"parentUuid": None, "logicalParentUuid": None, "isSidechain": False, "type": "system",
            "subtype": "compact_boundary", "content": "Conversation compacted", "timestamp": ts}


class World:
    def __init__(self, base: Path):
        self.base = base
        self.projects = base / "claude" / "projects" / "-room"
        self.projects.mkdir(parents=True)
        self.registry = base / "registry.json"
        self.spec = base / "gauge.md"
        self.spec.write_text("model=claude-opus-5-5|window=1000000|source=test|observed=2026-10-30\n")
        self.state = base / "state"
        self.template = base / "closeout.md.tpl"
        self.template.write_text(FRONT + BODY)
        self.identities = [dict(MANAGER), dict(ASSISTANT)]
        self.write_registry()

    def write_registry(self):
        self.registry.write_text(json.dumps({"identities": self.identities}))

    def resident(self, key, n, provider="claude"):
        self.identities.append({"key": key, "provider": provider, "session_id": cid(n), "person": key, "role": "r"})
        self.write_registry()
        return cid(n)

    def body(self, sid, rows):
        path = self.projects / f"{sid}.jsonl"
        path.write_text("".join(json.dumps(r) + "\n" for r in rows))
        return path

    def codex_body(self, sid, tokens, window):
        path = self.base / "codex" / f"rollout-2026-10-30T10-00-00-{sid}.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        rows = [{"timestamp": "2026-10-30T15:00:00Z", "type": "turn_context", "payload": {"model": "gpt-6.1-terra"}},
                {"timestamp": "2026-10-30T15:01:00Z", "type": "event_msg", "payload": {"type": "token_count", "info": {
                    "last_token_usage": {"input_tokens": tokens}, "model_context_window": window}}}]
        path.write_text("".join(json.dumps(r) + "\n" for r in rows))
        return path

    def hook(self, sid, transcript, *extra, raw=None, timeout=20, env=None):
        payload = raw if raw is not None else json.dumps({
            "session_id": sid, "transcript_path": str(transcript), "cwd": str(self.base),
            "hook_event_name": "UserPromptSubmit", "prompt": f"please continue {SECRET}"}).encode()
        cmd = [sys.executable, "-I", "-B", str(CLOSEOUT), f"--registry={self.registry}", f"--spec={self.spec}",
               f"--state-dir={self.state}", f"--template={self.template}", "--now=2026-10-30T16:00:00Z", *extra]
        return subprocess.run(cmd, input=payload, capture_output=True, timeout=timeout, env=env)

    def log(self):
        path = self.state / "log.jsonl"
        return [json.loads(l) for l in path.read_text().splitlines()] if path.exists() else []


class Closeout(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="closeout-test-")
        self.w = World(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def card(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        out = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual(out["hookEventName"], "UserPromptSubmit")
        return out["additionalContext"]

    def silent(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, b"")
        self.assertEqual(result.stderr, b"")

    def at(self, sid, tokens, msg="m", ts="2026-10-30T15:00:00Z"):
        return self.w.body(sid, [claude_call(msg, tokens, ts)])

    # -- the 50,000-token reserve ------------------------------------------------
    def test_reserve_on_a_1m_window_begins_at_650000(self):
        sid = self.w.resident("shannon", 1)
        self.silent(self.w.hook(sid, self.at(sid, 649_999)))
        text = self.card(self.w.hook(sid, self.at(sid, 650_000)))
        self.assertTrue(text.startswith("TEST CARD 65.0 of 1,000,000 tokens at "))

    def test_reserve_on_codex_windows_is_tokens_not_percent(self):
        for n, window, trigger in ((2, 475_000, 282_500), (3, 258_400, 130_880)):
            with self.subTest(window=window):
                sid = self.w.resident(f"codex-{n}", n, provider="codex")
                self.silent(self.w.hook(sid, self.w.codex_body(sid, trigger - 1, window)))
                text = self.card(self.w.hook(sid, self.w.codex_body(sid, trigger, window)))
                self.assertIn(f"{100.0 * trigger / window:.1f} of {window:,} tokens", text)

    def test_once_per_five_points_and_rearmed_after_a_drop(self):
        sid = self.w.resident("shannon", 4)
        self.card(self.w.hook(sid, self.at(sid, 655_000)))
        self.silent(self.w.hook(sid, self.at(sid, 699_999, "m2")))
        self.card(self.w.hook(sid, self.at(sid, 700_000, "m3")))
        self.silent(self.w.hook(sid, self.at(sid, 720_000, "m4")))
        self.silent(self.w.hook(sid, self.at(sid, 300_000, "m5")))          # after a compaction: fresh and low
        self.card(self.w.hook(sid, self.at(sid, 660_000, "m6")))
        events = [e["event"] for e in self.w.log()]
        self.assertEqual(events.count("card"), 3)
        self.assertEqual(events.count("rearmed"), 1)

    def test_only_a_current_reading_counts(self):
        sid = self.w.resident("shannon", 5)
        self.silent(self.w.hook(sid, self.w.body(sid, [claude_call("m", 900_000, "2026-10-30T15:00:00Z"),
                                                      boundary("2026-10-30T15:05:00Z")])))
        self.silent(self.w.hook(sid, self.w.body(sid, [boundary("2026-10-30T15:05:00Z")])))
        self.assertEqual([e for e in self.w.log() if e["event"] == "unknown"], [])

    # -- own transcript only --------------------------------------------------------
    def test_own_transcript_only(self):
        mine = self.w.resident("claudine", 6)
        other = self.w.resident("shannon", 7)
        self.at(mine, 100_000)
        full = self.at(other, 900_000)
        self.silent(self.w.hook(mine, full))                                    # another body, even at 90 percent
        renamed = self.w.base / "elsewhere" / f"{mine}.jsonl"
        renamed.parent.mkdir()
        os.symlink(full, renamed)
        self.silent(self.w.hook(mine, renamed))                                 # a link to another body
        whys = [e["why"] for e in self.w.log() if e["event"] == "unknown"]
        self.assertEqual(whys, ["the transcript is not this session's own body", "the transcript is not a regular file"])

    # -- registered sessions only ----------------------------------------------------
    def test_registered_sessions_only(self):
        helper = cid(8)
        self.silent(self.w.hook(helper, self.at(helper, 900_000)))
        self.assertEqual(self.w.log(), [])
        self.assertFalse((self.w.state / "state.json").exists())
        twice = self.w.resident("a", 9)
        self.w.identities.append({"key": "b", "provider": "claude", "session_id": twice})
        self.w.write_registry()
        self.silent(self.w.hook(twice, self.at(twice, 900_000)))
        self.assertEqual(self.w.log()[-1]["why"], "the session is registered more than once")

    # -- always exit 0, never in the way --------------------------------------------
    def test_always_exit_zero(self):
        sid = self.w.resident("shannon", 10)
        body = self.at(sid, 900_000)
        cases = {
            "empty input": (b"", ()),
            "not JSON": (b"{not json", ()),
            "not UTF-8": (b"\xff\xfe", ()),
            "a list": (b"[1, 2]", ()),
            "stray and help flags": (None, ("--bogus", "-h", "--help", "--limit-seconds=abc")),
            "bad time": (None, ("--now=yesterday",)),
            "missing registry": (None, (f"--registry={self.w.base / 'none.json'}",)),
            "missing transcript": (json.dumps({"session_id": sid, "transcript_path": str(self.w.projects / "gone.jsonl")}).encode(), ()),
            "unreadable state folder": (None, (f"--state-dir={self.w.registry}",)),
        }
        for label, (raw, extra) in cases.items():
            with self.subTest(label):
                result = self.w.hook(sid, body, *extra, raw=raw)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stderr, b"")

    def test_a_window_the_table_lacks_is_unknown_and_kevin_hears_after_three(self):
        sid = self.w.resident("joy", 11)
        body = self.w.body(sid, [claude_call("m", 900_000, "2026-10-30T15:00:00Z", model="claude-fable-5-1")])
        for _ in range(4):
            self.silent(self.w.hook(sid, body))
        events = [e["event"] for e in self.w.log()]
        self.assertEqual((events.count("unknown"), events.count("kevin-notice")), (4, 1))
        notice = [e for e in self.w.log() if e["event"] == "kevin-notice"][0]
        self.assertEqual((notice["delivered"], notice["key"]), (False, "joy"))

    # -- the 5-second limit ------------------------------------------------------------
    def test_the_time_limit_ends_a_blocked_run_with_exit_zero(self):
        sid = self.w.resident("shannon", 12)
        body = self.at(sid, 900_000)
        fifo = self.w.base / "registry.fifo"
        os.mkfifo(fifo)                                   # opening it blocks forever: no writer
        start = time.monotonic()
        result = self.w.hook(sid, body, f"--registry={fifo}", "--limit-seconds=0.5")
        self.assertLess(time.monotonic() - start, 4)
        self.silent(result)

    def test_the_default_limit_is_five_seconds(self):
        sid = self.w.resident("shannon", 13)
        body = self.at(sid, 900_000)
        fifo = self.w.base / "registry.fifo"
        os.mkfifo(fifo)
        start = time.monotonic()
        result = self.w.hook(sid, body, f"--registry={fifo}")
        elapsed = time.monotonic() - start
        self.silent(result)
        self.assertGreaterEqual(elapsed, 4.4)                # the soft limit: 90 percent of 5 seconds
        self.assertLess(elapsed, 4.95)
        self.assertIn("5-second limit", self.w.log()[-1]["why"])

    # -- content ------------------------------------------------------------------------
    def test_content_is_never_printed_or_logged(self):
        sid = self.w.resident("shannon", 14)
        result = self.w.hook(sid, self.at(sid, 900_000))
        self.card(result)
        self.assertNotIn(SECRET.encode(), result.stdout)
        self.assertNotIn(SECRET, (self.w.state / "log.jsonl").read_text())
        self.assertNotIn(SECRET, (self.w.state / "state.json").read_text())
        for name in ("log.jsonl", "state.json"):
            self.assertEqual(oct((self.w.state / name).stat().st_mode & 0o777), "0o600")

    # -- the card has one source: its template (Shannon, 10-30) ---------------------
    def test_the_card_is_the_template_rendered(self):
        sid = self.w.resident("shannon-like", 15)
        text = self.card(self.w.hook(sid, self.at(sid, 700_000)))
        self.assertRegex(text, r"^TEST CARD 70\.0 of 1,000,000 tokens at .+\.\nStep five: Claude Shannon's desk runs it\.$")
        source = CLOSEOUT.read_text()
        self.assertNotIn("CLOSEOUT. Your context is", source)               # no second copy in the script
        self.assertNotIn("Tell Kevin plainly", source)

    def test_the_managers_own_rotation_is_run_by_the_assistant(self):
        sid = MANAGER["session_id"]
        text = self.card(self.w.hook(sid, self.at(sid, 700_000)))
        self.assertTrue(text.endswith("Step five: Claudine Colbert runs it."))

    def test_the_rooms_template_renders_six_lines(self):
        """Contract with the shipped template: read only, copied into the temporary room first."""
        self.w.template.write_bytes(ROOM_TEMPLATE.read_bytes())
        sid = self.w.resident("shannon-like", 16)
        lines = self.card(self.w.hook(sid, self.at(sid, 650_000))).split("\n")
        self.assertEqual(len(lines), 6)
        self.assertTrue(lines[0].startswith("CLOSEOUT. Your context is 65.0 percent of 1,000,000 tokens, measured from your own body at "))
        self.assertTrue(lines[4].endswith("then it is written with his words and the date."))
        self.assertEqual(lines[5], "5. Tell Kevin you are ready for rotation. Claude Shannon's desk runs it.")

    def test_a_template_it_cannot_read_or_fill_is_unknown_never_a_fallback(self):
        cases = {
            "missing": None,
            "not UTF-8": b"\xff\xfe",
            "no front matter": BODY.encode(),
            "front matter not closed": (FRONT[:-4] + BODY).encode(),
            "another template": (FRONT.replace("template_id: closeout", "template_id: receipt") + BODY).encode(),
            "a version that is not a whole number": (FRONT.replace("template_version: 9", "template_version: two") + BODY).encode(),
            "a slot this hook cannot fill": (FRONT.replace("  - ROTATION_WRITER\n", "  - ROTATION_WRITER\n  - EXTRA\n") + BODY + "{{EXTRA}}\n").encode(),
            "a declared slot the body never uses": (FRONT + BODY.replace("{{READING_TIME}}", "noon")).encode(),
            "a marker never declared": (FRONT + BODY + "{{OTHER}}\n").encode(),
            "a first line that is not ---": (" " + FRONT + BODY).encode(),
            "template_type tool": (FRONT.replace("template_type: report", "template_type: tool") + BODY).encode(),
            "version 0": (FRONT.replace("template_version: 9", "template_version: 0") + BODY).encode(),
            "a slot listed twice": (FRONT.replace("  - PERCENT\n", "  - PERCENT\n  - PERCENT\n") + BODY).encode(),
            "requires_slots missing a slot the body uses": (FRONT.replace("  - WINDOW\n", "").replace("  WINDOW: w\n", "") + BODY).encode(),
            "no slot_notes section": (FRONT.split("slot_notes:")[0] + "---\n" + BODY).encode(),
            "a required slot without a note": (FRONT.replace("  WINDOW: w\n", "") + BODY).encode(),
            "a note for an undeclared slot": (FRONT.replace("  WINDOW: w\n", "  WINDOW: w\n  OTHER: o\n") + BODY).encode(),
            "a front matter line not understood": (FRONT.replace("template_id: closeout\n", "template_id: closeout\nNot A Key\n") + BODY).encode(),
            "a lowercase list item": (FRONT.replace("  - PERCENT\n", "  - PERCENT\n  - percent\n") + BODY).encode(),
            "a slot item under slot_notes": (FRONT.replace("  PERCENT: p\n", "  PERCENT: p\n  - EXTRA\n") + BODY).encode(),
            "an inline value on requires_slots": (FRONT.replace("requires_slots:\n", "requires_slots: PERCENT\n") + BODY).encode(),
            "a lowercase marker in the body": (FRONT + BODY + "{{percent}}\n").encode(),
            "a consistent template of three slots": (FRONT.replace("  - ROTATION_WRITER\n", "").replace("  ROTATION_WRITER: r\n", "")
                                                    + BODY.replace("{{ROTATION_WRITER}}", "Shannon's desk")).encode(),
            "a slot item after slot_notes": (FRONT.replace("  - ROTATION_WRITER\n", "").replace("  ROTATION_WRITER: r\n", "  ROTATION_WRITER: r\n  - ROTATION_WRITER\n") + BODY).encode(),
            "a slot note inside requires_slots": (FRONT.replace("  ROTATION_WRITER: r\n", "").replace("  - ROTATION_WRITER\n", "  - ROTATION_WRITER\n  ROTATION_WRITER: r\n") + BODY).encode(),
            "a key line ends the requires_slots list": (FRONT.replace("  - READING_TIME\n", "source: x\n  - READING_TIME\n") + BODY).encode(),
            "a line holding # after other text": (FRONT.replace("template_id: closeout\n", "template_id: closeout\ngarbage # comment\n") + BODY).encode(),
            "a slot item with no indentation": (FRONT.replace("  - PERCENT\n", "- PERCENT\n") + BODY).encode(),
            "a slot note with no text": (FRONT.replace("  PERCENT: p\n", "  PERCENT:\n") + BODY).encode(),
            "a version with a suffix": (FRONT.replace("template_version: 9", "template_version: 9x") + BODY).encode(),
            "a line of Unicode space only": (FRONT.replace("template_id: closeout\n", "template_id: closeout\n\u00a0\n") + BODY).encode(),
        }
        for n, (label, data) in enumerate(cases.items(), 20):
            with self.subTest(label):
                if data is None:
                    self.w.template.unlink(missing_ok=True)
                else:
                    self.w.template.write_bytes(data)
                sid = self.w.resident(f"r{n}", n)
                self.silent(self.w.hook(sid, self.at(sid, 900_000)))
                last = self.w.log()[-1]
                self.assertEqual((last["event"], last["key"]), ("unknown", f"r{n}"))
                self.assertIn("card template", last["why"])
                self.assertFalse(any(e["event"] == "card" for e in self.w.log()))

    def test_a_value_holding_a_marker_is_unknown(self):
        self.w.identities[0]["person"] = "{{PERCENT}}"
        self.w.write_registry()
        sid = self.w.resident("shannon-like", 30)
        self.silent(self.w.hook(sid, self.at(sid, 900_000)))
        self.assertEqual(self.w.log()[-1]["why"], "a {{...}} marker would remain in the card")

    def test_no_continuity_manager_in_the_registry_is_unknown(self):
        self.w.identities = [i for i in self.w.identities if i["role"] != "Session Continuity Manager"]
        sid = self.w.resident("shannon-like", 31)
        self.silent(self.w.hook(sid, self.at(sid, 900_000)))
        self.assertIn("exactly one continuity manager", self.w.log()[-1]["why"])

    def test_a_template_defect_uses_up_no_band(self):
        sid = self.w.resident("shannon-like", 32)
        good = self.w.template.read_bytes()
        self.w.template.write_bytes(b"broken")
        self.silent(self.w.hook(sid, self.at(sid, 660_000)))
        self.w.template.write_bytes(good)
        self.card(self.w.hook(sid, self.at(sid, 661_000, "m2")))

    # -- the review of this change (Claudine's workflow, 10-30) ---------------------
    def test_braces_that_would_leave_a_marker_are_unknown(self):
        cases = {"triple braces in the template": (FRONT + BODY.replace("{{PERCENT}}", "{{{PERCENT}}}")).encode()}
        for n, (label, data) in enumerate(cases.items(), 40):
            with self.subTest(label):
                self.w.template.write_bytes(data)
                sid = self.w.resident(f"b{n}", n)
                self.silent(self.w.hook(sid, self.at(sid, 900_000)))
                self.assertEqual(self.w.log()[-1]["why"], "a {{...}} marker would remain in the card")

    def test_registry_values_that_cannot_fill_the_card_are_unknown(self):
        cases = {
            "a value holding nested braces": ("{{x}y}}", "a {{...}} marker would remain in the card"),
            "a placeholder": ("[PLACEHOLDER: name]", "holds a placeholder"),
            "an empty name": ("", "has no key or no name"),
            "a blank name": ("   ", "has no key or no name"),
            "no name at all": (None, "has no key or no name"),
        }
        for n, (label, (person, why)) in enumerate(cases.items(), 45):
            with self.subTest(label):
                self.w.identities[0]["person"] = person
                self.w.write_registry()
                sid = self.w.resident(f"v{n}", n)
                self.silent(self.w.hook(sid, self.at(sid, 900_000)))
                self.assertIn(why, self.w.log()[-1]["why"])

    def test_who_runs_the_rotation(self):
        assistant = ASSISTANT["session_id"]
        text = self.card(self.w.hook(assistant, self.at(assistant, 700_000)))
        self.assertTrue(text.endswith("Step five: Claude Shannon's desk runs it."))    # the assistant's own closeout
        manager = MANAGER["session_id"]
        cases = {
            "the assistant holds the manager's key": ({"key": "session-doctor"}, "holds the manager's own key"),
            "the assistant has a blank name": ({"person": " "}, "has no key or no name"),
            "two assistants": (None, "exactly one assistant"),
        }
        for label, (change, why) in cases.items():
            with self.subTest(label):
                self.w.identities[1] = dict(ASSISTANT, **(change or {}))
                if change is None:
                    self.w.identities.append(dict(ASSISTANT, key="second", session_id=cid(60)))
                self.w.write_registry()
                self.silent(self.w.hook(manager, self.at(manager, 750_000 + len(self.w.log()))))
                self.assertIn(why, [e for e in self.w.log() if e["event"] == "unknown"][-1]["why"])
                self.w.identities = [i for i in self.w.identities if i.get("key") != "second"]

    def test_the_manager_must_have_a_key_and_be_one(self):
        for label, change in (("no key", {"key": None}), ("two managers", "two")):
            with self.subTest(label):
                self.w.identities = [dict(MANAGER), dict(ASSISTANT)]
                if change == "two":
                    self.w.identities.append(dict(MANAGER, key="other-manager", session_id=cid(61)))
                else:
                    self.w.identities[0].update(change)
                sid = self.w.resident(f"m-{len(self.w.log())}", 62 + len(self.w.log()))
                self.silent(self.w.hook(sid, self.at(sid, 900_000)))
                self.assertIn("continuity manager", self.w.log()[-1]["why"])

    def test_a_resident_entry_without_a_key_is_unknown(self):
        self.w.identities.append({"provider": "claude", "session_id": cid(70), "person": "x", "role": "r"})
        self.w.write_registry()
        self.silent(self.w.hook(cid(70), self.at(cid(70), 900_000)))
        self.assertEqual(self.w.log()[-1]["why"], "the session's registry entry has no key")

    def test_a_registry_defect_uses_up_no_band(self):
        sid = self.w.resident("shannon-like", 71)
        self.w.identities[0]["person"] = ""
        self.w.write_registry()
        self.silent(self.w.hook(sid, self.at(sid, 660_000)))
        self.w.identities[0]["person"] = "Claude Shannon"
        self.w.write_registry()
        self.card(self.w.hook(sid, self.at(sid, 661_000, "m2")))

    def test_the_reading_time_on_the_card(self):
        utc = dict(os.environ, TZ="UTC")
        sid = self.w.resident("shannon-like", 72)
        text = self.card(self.w.hook(sid, self.at(sid, 700_000, ts="2026-10-30T15:00:00Z"), env=utc))
        self.assertIn(" at 2026-10-30 15:00 UTC.", text)
        sid = self.w.resident("no-time", 73)
        row = claude_call("m", 700_000, None)
        row.pop("timestamp")
        text = self.card(self.w.hook(sid, self.w.body(sid, [row]), env=utc))
        self.assertIn(" at an unknown time.", text)

    def test_a_card_is_delivered_even_when_the_log_cannot_be_written(self):
        sid = self.w.resident("shannon-like", 74)
        self.w.state.mkdir()
        (self.w.state / "log.jsonl").mkdir()
        self.card(self.w.hook(sid, self.at(sid, 660_000)))
        self.silent(self.w.hook(sid, self.at(sid, 661_000, "m2")))          # the band was recorded after delivery

    def test_a_state_that_cannot_be_written_repeats_the_card_rather_than_losing_it(self):
        sid = self.w.resident("shannon-like", 75)
        self.w.state.write_text("a file where the state folder should be")
        self.card(self.w.hook(sid, self.at(sid, 660_000)))
        self.card(self.w.hook(sid, self.at(sid, 661_000, "m2")))

    def test_the_limit_is_a_hard_stop_even_when_the_unknown_path_blocks(self):
        sid = self.w.resident("shannon-like", 76)
        body = self.at(sid, 900_000)
        registry, log = self.w.base / "registry.fifo", self.w.base / "blocked-state"
        os.mkfifo(registry)
        log.mkdir()
        os.mkfifo(log / "log.jsonl")                       # the unknown path's log write blocks too
        start = time.monotonic()
        result = self.w.hook(sid, body, f"--registry={registry}", f"--state-dir={log}", "--limit-seconds=1")
        elapsed = time.monotonic() - start
        self.assertGreaterEqual(elapsed, 0.95)               # the hard stop: the limit itself
        self.assertLess(elapsed, 1.6)
        self.silent(result)

    def test_a_compaction_then_a_fresh_reading_gives_the_card(self):
        sid = self.w.resident("shannon-like", 77)
        rows = [claude_call("m1", 900_000, "2026-10-30T15:00:00Z"), boundary("2026-10-30T15:05:00Z"),
                claude_call("m2", 660_000, "2026-10-30T15:10:00Z")]
        self.card(self.w.hook(sid, self.w.body(sid, rows)))

    # -- the re-check of the fixes (Claudine's second workflow, 10-30) ---------------
    def test_front_matter_blank_and_comment_lines_are_accepted_as_ops_bin_template_accepts_them(self):
        self.w.template.write_text(FRONT.replace("template_id: closeout\n", "template_id: closeout\n\n# a comment\n   # indented\n")
                                   + BODY + "Braces {{ on one line\nand }} on the next,\nand a lone {{ here.\n")
        sid = self.w.resident("shannon-like", 80)
        text = self.card(self.w.hook(sid, self.at(sid, 700_000)))
        self.assertTrue(text.endswith("Braces {{ on one line\nand }} on the next,\nand a lone {{ here."))

    def test_an_undelivered_card_records_no_band(self):
        sid = self.w.resident("shannon-like", 81)
        sink = self.w.base / "readonly-stdout"
        sink.write_text("")
        cmd = [sys.executable, "-I", "-B", str(CLOSEOUT), f"--registry={self.w.registry}", f"--spec={self.w.spec}",
               f"--state-dir={self.w.state}", f"--template={self.w.template}", "--now=2026-10-30T16:00:00Z"]
        payload = json.dumps({"session_id": sid, "transcript_path": str(self.at(sid, 660_000))}).encode()
        with open(sink, "rb") as readonly:                       # writing the card fails: it is not delivered
            result = subprocess.run(cmd, input=payload, stdout=readonly, stderr=subprocess.PIPE, timeout=20)
        self.assertEqual((result.returncode, result.stderr), (0, b""))
        self.assertFalse(any(e["event"] == "card" for e in self.w.log()))
        self.card(self.w.hook(sid, self.at(sid, 661_000, "m2")))  # so the same band still gets its card

    def test_a_commit_that_blocks_ends_at_the_limit_with_the_card_delivered(self):
        sid = self.w.resident("shannon-like", 82)
        self.w.state.mkdir()
        os.mkfifo(self.w.state / "log.jsonl")                   # the card's log line blocks after delivery
        start = time.monotonic()
        result = self.w.hook(sid, self.at(sid, 660_000), "--limit-seconds=1")
        self.assertLess(time.monotonic() - start, 1.6)
        self.card(result)

    def test_a_tiny_limit_is_clamped_and_never_hangs(self):
        sid = self.w.resident("shannon-like", 83)
        body = self.at(sid, 900_000)
        for limit in ("0.000001", "0", "-1"):
            with self.subTest(limit=limit):
                start = time.monotonic()
                result = self.w.hook(sid, body, f"--limit-seconds={limit}", timeout=10)
                self.assertLess(time.monotonic() - start, 3)
                self.assertEqual((result.returncode, result.stderr), (0, b""))

    def test_a_card_and_a_told_prompt_reset_the_unknown_count(self):
        sid = self.w.resident("shannon-like", 84)
        unknown = self.w.body(sid, [claude_call("u", 900_000, "2026-10-30T15:00:00Z", model="claude-fable-5-1")])
        for _ in range(2):
            self.silent(self.w.hook(sid, unknown))
        self.card(self.w.hook(sid, self.at(sid, 660_000, "m1")))           # the card resets the count
        for _ in range(2):
            self.silent(self.w.hook(sid, self.w.body(sid, [claude_call("u2", 900_000, "2026-10-30T15:00:00Z", model="claude-fable-5-1")])))
        self.silent(self.w.hook(sid, self.at(sid, 661_000, "m2")))         # told in this band: resets the count again
        self.silent(self.w.hook(sid, self.w.body(sid, [claude_call("u3", 900_000, "2026-10-30T15:00:00Z", model="claude-fable-5-1")])))
        self.assertEqual([e["event"] for e in self.w.log()].count("kevin-notice"), 1)  # the card's notice only

    def test_a_corrupt_band_in_the_state_never_silences_the_resident(self):
        sid = self.w.resident("shannon-like", 85)
        self.w.state.mkdir()
        (self.w.state / "state.json").write_text(json.dumps({sid: {"band": "9", "unknown": 0}}))
        self.card(self.w.hook(sid, self.at(sid, 660_000)))

    def test_a_registry_defect_inside_a_told_band_is_still_counted(self):
        sid = self.w.resident("shannon-like", 86)
        self.card(self.w.hook(sid, self.at(sid, 660_000)))
        self.w.identities = [i for i in self.w.identities if i["role"] != "Session Continuity Manager"]
        self.w.write_registry()
        self.silent(self.w.hook(sid, self.at(sid, 661_000, "m2")))
        self.assertIn("exactly one continuity manager", self.w.log()[-1]["why"])

    def test_registry_names_and_keys_are_checked_exactly(self):
        manager = MANAGER["session_id"]
        cases = {
            "manager key empty": (0, {"key": ""}, "continuity manager has no key or no name"),
            "manager key blank": (0, {"key": "   "}, "continuity manager has no key or no name"),
            "manager key a number": (0, {"key": 7}, "continuity manager has no key or no name"),
            "assistant name missing": (1, {"person": None}, "assistant has no key or no name"),
            "no assistant at all": (1, None, "exactly one assistant"),
        }
        for n, (label, (index, change, why)) in enumerate(cases.items(), 90):
            with self.subTest(label):
                self.w.identities = [dict(MANAGER), dict(ASSISTANT)]
                if change is None:
                    self.w.identities.pop(index)
                else:
                    self.w.identities[index].update(change)
                self.w.write_registry()
                closer = manager if index == 1 else self.w.resident(f"c{n}", n)
                self.silent(self.w.hook(closer, self.at(closer, 900_000 + n)))
                self.assertIn(why, [e for e in self.w.log() if e["event"] == "unknown"][-1]["why"])

    def test_names_are_stripped_and_a_blank_resident_key_is_unknown(self):
        self.w.identities[0]["person"] = "  Claude Shannon  "
        self.w.write_registry()
        sid = self.w.resident("shannon-like", 95)
        self.assertTrue(self.card(self.w.hook(sid, self.at(sid, 700_000))).endswith("Claude Shannon's desk runs it."))
        self.w.identities.append({"key": "  ", "provider": "claude", "session_id": cid(96), "person": "x", "role": "r"})
        self.w.write_registry()
        self.silent(self.w.hook(cid(96), self.at(cid(96), 900_000)))
        self.assertEqual(self.w.log()[-1]["why"], "the session's registry entry has no key")

    # -- the third pass (Claudine's workflow, 10-30 night) ---------------------------
    def test_an_unusable_limit_falls_back_to_five_seconds_and_still_delivers(self):
        sid = self.w.resident("shannon-like", 100)
        for n, limit in enumerate(("nan", "inf", "1e308", "abc", "0x10")):
            with self.subTest(limit=limit):
                body = self.at(sid, 660_000 + 60_000 * n, f"m{n}")      # a new band each time
                self.card(self.w.hook(sid, body, f"--limit-seconds={limit}"))

    def test_temporary_state_files_left_by_a_cut_write_are_removed(self):
        sid = self.w.resident("shannon-like", 101)
        self.w.state.mkdir()
        (self.w.state / ".state.leftover").write_text("{}")
        self.card(self.w.hook(sid, self.at(sid, 660_000)))
        self.assertEqual(sorted(p.name for p in self.w.state.glob(".state.*")), [])

    def test_ascii_whitespace_in_the_front_matter_matches_ops_bin_template(self):
        variants = {
            "a vertical tab after a key": FRONT.replace("template_id: closeout", "template_id:\vcloseout"),
            "a form feed before an item": FRONT.replace("  - PERCENT\n", "\f- PERCENT\n"),
            "a carriage return after a note": FRONT.replace("  WINDOW: w\n", "  WINDOW: w\r\n"),
        }
        for n, (label, front) in enumerate(variants.items(), 102):
            with self.subTest(label):
                self.w.template.write_bytes((front + BODY).encode())
                sid = self.w.resident(f"ws{n}", n)
                self.card(self.w.hook(sid, self.at(sid, 700_000)))

    def test_a_comment_led_by_a_unicode_space_is_not_a_comment(self):
        self.w.template.write_bytes((FRONT.replace("template_id: closeout\n", "template_id: closeout\n\u00a0# a note\n") + BODY).encode())
        sid = self.w.resident("nbsp", 105)
        self.silent(self.w.hook(sid, self.at(sid, 700_000)))
        self.assertIn("is not understood", self.w.log()[-1]["why"])


class StateLocation(unittest.TestCase):
    """Exercise actual defaults in an isolated room, never the live room."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="closeout-location-")
        self.base = Path(self.tmp.name)
        self.world = World(self.base / "fixture")

    def tearDown(self):
        self.tmp.cleanup()

    def stage(self, world=None):
        world = world or self.world
        room = world.base / "default-room"
        script = room / "ops/lib/scripts/closeout.py"
        script.parent.mkdir(parents=True)
        shutil.copyfile(CLOSEOUT, script)
        shutil.copyfile(CLOSEOUT.with_name("gauge.py"), script.with_name("gauge.py"))
        for path, data in ((room / "ops/etc/resident-identities.json", world.registry.read_bytes()),
                           (room / "docs/ops/specs/scripts/gauge.md", world.spec.read_bytes()),
                           (room / "ops/src/reports/closeout.md.tpl", world.template.read_bytes())):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        return room, script

    def run_hook(self, script, sid, body, *args):
        payload = json.dumps({"session_id": sid, "transcript_path": str(body),
                              "hook_event_name": "UserPromptSubmit", "prompt": SECRET}).encode()
        return subprocess.run([sys.executable, "-I", "-B", str(script),
                               "--now=2026-10-30T16:00:00Z", *args],
                              input=payload, capture_output=True, timeout=10)

    def resident(self, world=None):
        world = world or self.world
        sid = world.resident("default-state", 1200)
        return sid, world.body(sid, [claude_call("m", 660_000, "2026-10-30T15:00:00Z")])

    def assert_silent(self, result):
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b"", b""))

    def test_default_creates_only_logs_closeout_state(self):
        sid, body = self.resident()
        room, script = self.stage()
        result = self.run_hook(script, sid, body)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["hookSpecificOutput"]["hookEventName"], "UserPromptSubmit")
        self.assertTrue((room / "logs/closeout/state.json").is_file())
        self.assertTrue((room / "logs/closeout/log.jsonl").is_file())
        self.assertFalse((room / "storage").exists())

    def test_legacy_state_refuses_default_card_without_rewriting_legacy_bytes(self):
        sid, body = self.resident()
        room, script = self.stage()
        legacy = room / "storage/closeout"
        legacy.mkdir(parents=True)
        old = json.dumps({sid: {"band": 9, "unknown": 0}}).encode()
        (legacy / "state.json").write_bytes(old)
        self.assert_silent(self.run_hook(script, sid, body))
        self.assertEqual((legacy / "state.json").read_bytes(), old)
        self.assertEqual(sorted(p.name for p in legacy.iterdir()), ["state.json"])
        logs = room / "logs/closeout"
        report = json.loads((logs / "log.jsonl").read_text().splitlines()[-1])
        self.assertEqual(report["event"], "unknown")
        self.assertIn("legacy closeout state", report["why"])
        self.assertNotIn("band", json.loads((logs / "state.json").read_text())[sid])

    def test_legacy_empty_directory_file_symlink_and_fifo_all_refuse_default(self):
        for name in ("empty-directory", "file", "broken-symlink", "fifo"):
            with self.subTest(kind=name):
                world = World(self.base / name)
                sid, body = self.resident(world)
                room, script = self.stage(world)
                legacy = room / "storage/closeout"
                legacy.parent.mkdir()
                if name == "empty-directory":
                    legacy.mkdir()
                elif name == "file":
                    legacy.write_bytes(b"invented legacy evidence")
                elif name == "broken-symlink":
                    legacy.symlink_to(room / "absent-target")
                else:
                    os.mkfifo(legacy)
                before = legacy.lstat()
                self.assert_silent(self.run_hook(script, sid, body))
                after = legacy.lstat()
                self.assertEqual((before.st_ino, before.st_mode, before.st_size, before.st_mtime_ns),
                                 (after.st_ino, after.st_mode, after.st_size, after.st_mtime_ns))
                self.assertFalse((room / "absent-target").exists())

    def test_explicit_state_override_keeps_its_existing_contract(self):
        sid, body = self.resident()
        room, script = self.stage()
        legacy = room / "storage/closeout"
        legacy.parent.mkdir()
        legacy.write_bytes(b"retained legacy evidence")
        custom = self.base / "explicit-state"
        result = self.run_hook(script, sid, body, f"--state-dir={custom}")
        self.assertEqual(result.returncode, 0)
        self.assertIn(b"hookSpecificOutput", result.stdout)
        self.assertTrue((custom / "state.json").is_file())
        self.assertFalse((room / "logs").exists())
        self.assertEqual(legacy.read_bytes(), b"retained legacy evidence")

    def test_uninspectable_legacy_parent_is_unknown_not_absent(self):
        if os.geteuid() == 0:
            self.skipTest("requires ordinary-user permission enforcement")
        for name in ("parent-file", "parent-unsearchable"):
            with self.subTest(kind=name):
                world = World(self.base / name)
                sid, body = self.resident(world)
                room, script = self.stage(world)
                parent = room / "storage"
                if name == "parent-file":
                    parent.write_bytes(b"invented parent evidence")
                else:
                    parent.mkdir()
                    parent.chmod(0)
                try:
                    self.assert_silent(self.run_hook(script, sid, body))
                finally:
                    if name == "parent-unsearchable":
                        parent.chmod(0o700)
                report = json.loads((room / "logs/closeout/log.jsonl").read_text().splitlines()[-1])
                self.assertEqual(report["event"], "unknown")
                self.assertIn("legacy closeout state", report["why"])

    def test_dangling_legacy_parent_is_unknown_without_touching_the_link_or_target(self):
        for name in ("absolute-target", "relative-target", "chained-target"):
            with self.subTest(kind=name):
                world = World(self.base / name)
                sid, body = self.resident(world)
                room, script = self.stage(world)
                parent = room / "storage"
                target = room / "absent-legacy-parent"
                if name == "chained-target":
                    intermediate = room / "legacy-parent-link"
                    intermediate.symlink_to(target)
                    parent.symlink_to(intermediate)
                else:
                    parent.symlink_to(target.name if name == "relative-target" else target)
                before = parent.lstat()
                link = os.readlink(parent)
                self.assert_silent(self.run_hook(script, sid, body))
                after = parent.lstat()
                self.assertEqual((before.st_dev, before.st_ino, before.st_mode,
                                  before.st_size, before.st_mtime_ns, before.st_ctime_ns),
                                 (after.st_dev, after.st_ino, after.st_mode,
                                  after.st_size, after.st_mtime_ns, after.st_ctime_ns))
                self.assertEqual(os.readlink(parent), link)
                self.assertFalse(target.exists())
                logs = room / "logs/closeout"
                events = [json.loads(line) for line in (logs / "log.jsonl").read_text().splitlines()]
                self.assertEqual([event["event"] for event in events], ["unknown"])
                self.assertIn("legacy closeout state", events[0]["why"])
                self.assertNotIn("band", json.loads((logs / "state.json").read_text())[sid])

    def test_existing_empty_legacy_parent_is_true_absence(self):
        sid, body = self.resident()
        room, script = self.stage()
        parent = room / "storage"
        parent.mkdir()
        before = parent.stat()
        result = self.run_hook(script, sid, body)
        self.assertEqual(result.returncode, 0)
        self.assertIn(b"hookSpecificOutput", result.stdout)
        self.assertEqual(list(parent.iterdir()), [])
        self.assertEqual(parent.stat().st_ino, before.st_ino)

    def test_reviewed_fixture_copy_and_legacy_release_preserve_deduplication(self):
        sid, body = self.resident()
        room, script = self.stage()
        legacy = room / "storage/closeout"
        legacy.mkdir(parents=True)
        state = json.dumps({sid: {"band": 0, "unknown": 0, "key": "default-state"}}).encode()
        (legacy / "state.json").write_bytes(state)
        self.assert_silent(self.run_hook(script, sid, body))
        current = room / "logs/closeout"
        retained = room / "storage/closeout-retained"
        # This is the test's explicitly staged copy, not a production migrator.
        shutil.copyfile(legacy / "state.json", current / "state.json")
        legacy.rename(retained)
        self.assert_silent(self.run_hook(script, sid, body))
        self.assertEqual((retained / "state.json").read_bytes(), state)
        self.assertEqual((current / "state.json").read_bytes(), state)
        self.assertNotIn('"event": "card"', (current / "log.jsonl").read_text())

    def test_unregistered_session_does_not_create_state_even_with_legacy_residue(self):
        room, script = self.stage()
        legacy = room / "storage/closeout"
        legacy.mkdir(parents=True)
        self.assert_silent(self.run_hook(script, cid(1201), self.base / "not-a-body"))
        self.assertFalse((room / "logs").exists())
        self.assertEqual(list(legacy.iterdir()), [])

    def test_new_state_directory_and_files_are_private_even_with_open_umask(self):
        sid, body = self.resident()
        room, script = self.stage()
        previous = os.umask(0)
        try:
            result = self.run_hook(script, sid, body)
        finally:
            os.umask(previous)
        self.assertEqual(result.returncode, 0)
        state = room / "logs/closeout"
        for path, mode in ((state, 0o700), (state / ".lock", 0o600),
                           (state / "state.json", 0o600), (state / "log.jsonl", 0o600)):
            with self.subTest(path=path.name):
                self.assertEqual(path.stat().st_mode & 0o777, mode)


if __name__ == "__main__":
    unittest.main(verbosity=1)
