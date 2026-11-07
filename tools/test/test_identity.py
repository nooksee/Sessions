"""Tests for the registry-only Copilot support in identity.py.

Standard library only, because control-gates runs `python3 -m unittest
discover` with nothing installed. Every fixture lives in a temporary folder,
so the tests do not depend on this host's homes, registry or bindings.

Optional review gate: set LIVE to the pre-change script to compare it byte for
byte with the candidate on this host's real registry (skipped otherwise).
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(os.environ.get(
    "CANDIDATE", Path(__file__).resolve().parents[2] / "ops" / "lib" / "scripts" / "identity.py"))
LIVE = os.environ.get("LIVE")
SID = "0000d1d1-0000-4000-8000-00000000d1d1"
ORIENT = ("<session_clinic_orientation>\nYou are `Chief Repository Operations Officer (JoJo Git)`, "
          "the continuing GitHub resident.\n</session_clinic_orientation>")
DOCK_NOTE = "Agent Dock title in the room's window not set by the operator"
PLAIN = "workspace.yaml not in the plain form"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run(mod, *argv: str) -> tuple[int, str]:
    buf = io.StringIO()
    with mock.patch("sys.argv", ["identity.py", *argv]), \
            contextlib.redirect_stdout(buf):
        code = mod.main()
    return code, buf.getvalue()


class Office:
    """A hermetic set of registry, roster, bindings and stores."""

    def __init__(self, base: Path):
        self.base = base
        self.room = os.path.realpath(base / "GitHub")
        os.makedirs(self.room)
        self.slug = re.sub(r"[^A-Za-z0-9]", "-", self.room).strip("-")
        for d in ("copilot", "dock", "claude", "codex"):
            (base / d).mkdir()
        self.roster = {"residents": []}
        self.bindings = {"residents": []}
        self.mod = load(SCRIPT, "cand")
        self.mod.REGISTRY = base / "registry.json"
        self.mod.ROSTER = base / "roster.json"
        self.mod.BINDINGS = base / "bindings.json"
        self.mod.CLAUDE_PROJECTS = base / "claude"
        self.mod.CODEX_SESSIONS = base / "codex"
        self.mod.CODEX_ARCHIVED = base / "codex-archived"
        self.mod.CODEX_INDEX = base / "codex-index.jsonl"
        self.mod.COPILOT_SESSIONS = base / "copilot"
        self.mod.AGENT_DOCK_PROJECTS = base / "dock"
        self.mod.acp_titles = lambda: {}

    def jojo(self, **over) -> dict:
        row = {"key": "jojo-git", "role": "Chief Repository Operations Officer", "person": "JoJo Git",
               "provider": "copilot", "session_id": SID, "room": self.room,
               "verified": "kevin", "note": "test"}
        row.update(over)
        return row

    def workspace(self, sid=SID, cwd=None) -> str:
        cwd = self.room if cwd is None else cwd
        return (f"id: {sid}\ncwd: {cwd}\ngit_root: {cwd}\nbranch: main\n"
                "client_name: github/acp\nname: x\nuser_named: false\n")

    def body(self, sid=SID, *, cwd=None, orientation=ORIENT, first_type="session.start",
             workspace=None, extra_rows=None, agent_row=False, tail=b"") -> Path:
        d = self.base / "copilot" / sid
        d.mkdir(parents=True)
        (d / "workspace.yaml").write_text(
            workspace if workspace is not None else self.workspace(sid, cwd), encoding="utf-8")
        rows = [{"type": first_type, "data": {"sessionId": sid, "version": 1,
                                              "producer": "copilot-agent"}},
                {"type": "user.message", "data": {"content": "hello"}}]
        if orientation is not None:
            row = {"type": "user.message", "data": {"content": orientation}}
            if agent_row:
                row["agentId"] = "sub-1"
            rows.append(row)
        rows += extra_rows or []
        (d / "events.jsonl").write_bytes(
            "".join(json.dumps(r) + "\n" for r in rows).encode() + tail)
        return d

    def dock(self, chats=None, project=None, raw=None) -> None:
        p = self.base / "dock" / (project or self.slug)
        p.mkdir(parents=True, exist_ok=True)
        (p / "index.json").write_bytes(raw if raw is not None else json.dumps(chats).encode())

    def run(self, *rows, argv=()) -> tuple[int, str]:
        (self.base / "registry.json").write_text(json.dumps({"identities": list(rows)}))
        (self.base / "roster.json").write_text(json.dumps(self.roster))
        (self.base / "bindings.json").write_text(json.dumps(self.bindings))
        return run(self.mod, *argv)


def chat(title, sid=SID, user_set=True, adapter="github-copilot-cli", **extra) -> dict:
    return {"id": "conv-1", "title": title, "titleUserSet": user_set,
            "sessions": [{"sessionId": sid, "adapterName": adapter}], **extra}


def legacy_rows() -> list[dict]:
    return [
        {"key": "claude-one", "role": "Lead", "person": "Claude One", "provider": "claude",
         "session_id": "0000aaaa-0000-4000-8000-00000000aaaa", "room": "/x", "verified": "kevin"},
        {"key": "codex-one", "role": "Dev", "person": "Codex One", "provider": "codex",
         "session_id": "0000bbbb-0000-4000-8000-00000000bbbb", "room": "/y",
         "verified": "unverified", "note": "pending"},
    ]


class OfficeTest(unittest.TestCase):
    def office(self) -> Office:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return Office(Path(tmp.name))

    def assert_incomplete(self, out: str, code: int, expect: str):
        self.assertIn(expect, out)
        self.assertIn("?   jojo-git", out)
        self.assertEqual(code, 1)


class ExistingRows(OfficeTest):
    def test_format_without_copilot_rows(self):
        o = self.office()
        o.roster["residents"] = [{"key": "claude-one", "display_name": "Lead (Claude One)"}]
        o.bindings["residents"] = [{"key": "claude-one",
                                    "session_id": "0000aaaa-0000-4000-8000-00000000aaaa"}]
        with mock.patch.object(o.mod, "agent_dock_title", side_effect=AssertionError), \
                mock.patch.object(o.mod, "copilot_body", side_effect=AssertionError):
            code, out = o.run(*legacy_rows())
        self.assertNotIn("Agent Dock", out)
        self.assertIn("identities: 2   mismatches: 2   unverified: 1   incomplete: 2   "
                      "PyCharm leg compared: 0/2\n", out)
        self.assertIn("  ?   claude-one                 Lead (Claude One)\n"
                      "        body identity unreadable (container missing)\n"
                      "        PyCharm label not on disk; this leg was NOT compared\n", out)
        self.assertIn("MISMATCH  codex-one: absent from roster", out)
        self.assertEqual(code, 1)

    def test_rows_unchanged_by_inserting_copilot(self):
        for at in (0, 1, 2):
            with self.subTest(at=at):
                o = self.office()
                o.body()
                o.dock([chat("JoJo Git")])
                _, base = o.run(*legacy_rows())
                rows = legacy_rows()
                rows.insert(at, o.jojo())
                _, out = o.run(*rows)

                def strip(text):
                    return [l for l in text.splitlines()
                            if not l.startswith("identities:") and "jojo-git" not in l]
                self.assertEqual(strip(out), strip(base))

    @unittest.skipUnless(LIVE and Path(LIVE).is_file(), "set LIVE to the pre-change script")
    def test_live_byte_identical(self):
        live, cand = load(Path(LIVE), "live"), load(SCRIPT, "cand_live")
        cand.REGISTRY, cand.ROSTER, cand.BINDINGS = live.REGISTRY, live.ROSTER, live.BINDINGS
        for argv in ((), ("--quiet",)):
            with self.subTest(argv=argv), \
                    mock.patch.object(cand, "agent_dock_title", side_effect=AssertionError), \
                    mock.patch.object(cand, "copilot_body", side_effect=AssertionError):
                self.assertEqual(run(live, *argv), run(cand, *argv))


class HealthyRow(OfficeTest):
    def test_healthy_copilot_row_exits_zero(self):
        o = self.office()
        o.body()
        o.dock([chat("JoJo Git")])
        code, out = o.run(o.jojo())
        self.assertEqual(code, 0, out)
        self.assertIn("  ok  jojo-git", out)
        self.assertIn("PyCharm leg compared: 0/0   Agent Dock leg compared: 1/1", out)

    def test_full_label_title(self):
        o = self.office()
        o.body()
        o.dock([chat("Chief Repository Operations Officer (JoJo Git)")])
        self.assertEqual(o.run(o.jojo())[0], 0)

    def test_registry_only_absence_is_clean(self):
        o = self.office()
        o.body()
        o.dock([chat("JoJo Git")])
        _, out = o.run(o.jojo())
        self.assertNotIn("absent from", out)

    def test_orientation_after_clear_counts(self):
        o = self.office()
        o.body(extra_rows=[{"type": "session.context_cleared", "data": {}},
                           {"type": "user.message", "data": {"content": ORIENT}}])
        o.dock([chat("JoJo Git")])
        self.assertEqual(o.run(o.jojo())[0], 0)

    def test_cut_multibyte_tail_reads(self):
        o = self.office()
        o.body(tail=b'{"type":"user.message","data":{"content":"caf\xc3')
        o.dock([chat("JoJo Git")])
        self.assertEqual(o.run(o.jojo())[0], 0)

    def test_quoted_value_outside_id_and_cwd_reads(self):
        o = self.office()
        o.body(workspace=o.workspace().replace("name: x", "name: 'Reply with: ready'"))
        o.dock([chat("JoJo Git")])
        self.assertEqual(o.run(o.jojo())[0], 0)

    def test_block_scalar_name_reads(self):
        # The shape Copilot wrote for JoJo's admission body on 2026-10-22: a
        # name taken from the multi-line first prompt, as a block scalar.
        # Indented lines that look like keys are content, never keys.
        for header in ("|", "|-", "|+", ">", ">-", ">+", "|2-", "|2", "|-2", ">2+"):
            with self.subTest(header=header):
                o = self.office()
                ws = (f"id: {SID}\ncwd: {o.room}\ngit_root: {o.room}\nbranch: main\n"
                      f"client_name: github/acp\nname: {header}\n  <session_clinic_orientation>\n"
                      "  You are `Chief Repository Operations Officer (JoJo Git)`, the lead.\n\n"
                      "  cwd: /media/nos4r2/user_vol\n    id: 0000d9d9-0000-4000-8000-00000000d9d9\n"
                      "user_named: false\nsummary_count: 0\nfork_count: 0\n"
                      "created_at: 2026-10-22T17:01:16.583Z\nupdated_at: 2026-10-22T17:01:16.919Z\n")
                o.body(workspace=ws)
                o.dock([chat("JoJo Git")])
                code, out = o.run(o.jojo())
                self.assertEqual(code, 0, out)
                self.assertIn("  ok  jojo-git", out)

    def test_other_written_forms_read(self):
        # Forms Copilot's YAML writers emit for unusual names: an
        # indentation digit for a name that opens with spaces, a final `...`
        # that libyaml writes after a kept block ending the document, complete
        # one-line quoted values, an empty value, and later block lines that
        # hold a tab after the indent. A deep first block must not leak into
        # the next block's check.
        cases = {
            "empty value": "name:\n",
            "dash text": "name: -x\n",
            "escapes": ('name: "' + r'\0\a\b\t' + '\\\t'
                        + r'\n\v\f\r\e\ \"\/\\\N\_\L\P\x4A\x4a\u00e9\U0001F600' + '"\n'),
            "space-only line at indent": "name: |-\n  \n  x\n",
            "later tab": "name: |-\n  a\n  \tb\n",
            "spaces after cwd": "",
            "digit": "name: |2-\n   indented first line\n  second\n",
            "document end": "name: |+\n  kept\n\n...\n",
            "double quoted": 'name: "tab\\there: \\"q\\" \\u00e9 # not a comment"\n',
            "single quoted": "name: 'it''s: fine # too'\n",
            "two blocks": "name: |-\n      \n      deep\nsummary: |-\n  shallow\n",
        }
        for name, tail in cases.items():
            with self.subTest(case=name):
                o = self.office()
                ws = o.workspace().replace("name: x\n", "").replace("user_named: false\n", "")
                if name == "spaces after cwd":
                    ws = ws.replace(f"cwd: {o.room}\n", f"cwd: {o.room} \t\n")
                o.body(workspace=ws + tail)
                o.dock([chat("JoJo Git")])
                code, out = o.run(o.jojo())
                self.assertEqual(code, 0, out)
                self.assertIn("  ok  jojo-git", out)

    def test_bad_index_in_other_window(self):
        o = self.office()
        o.body()
        o.dock([chat("JoJo Git")])
        o.dock(project="media-nos4r2-user-vol-Sessions", raw=b'[{"title": "\xe9')
        self.assertEqual(o.run(o.jojo())[0], 0)


class Mismatches(OfficeTest):
    def test_stored_folder_outside_room(self):
        for suffix in ("-elsewhere", "/", "/./"):
            with self.subTest(suffix=suffix):
                o = self.office()
                cwd = o.room + suffix
                o.body(cwd=cwd)
                o.dock([chat("JoJo Git")])
                code, out = o.run(o.jojo())
                self.assertIn(f"MISMATCH  jojo-git: Copilot body is stored in {cwd!r}", out)
                self.assertEqual(code, 1)

    def test_room_must_be_existing_canonical(self):
        for make in (lambda r: r + "-gone", lambda r: r + "/",
                     lambda r: os.path.dirname(r) + "/./" + os.path.basename(r)):
            with self.subTest():
                o = self.office()
                room = make(o.room)
                o.body(cwd=room)
                o.dock([chat("JoJo Git")])
                code, out = o.run(o.jojo(room=room))
                self.assertIn("is not an existing canonical directory", out)
                self.assertEqual(code, 1)

    def test_registry_only_presence(self):
        for where in ("roster", "bindings"):
            with self.subTest(where=where):
                o = self.office()
                o.body()
                o.dock([chat("JoJo Git")])
                getattr(o, where)["residents"].append(
                    {"key": "jojo-git", "display_name": "Chief Repository Operations Officer (JoJo Git)",
                     "session_id": SID})
                code, out = o.run(o.jojo())
                self.assertIn(f"MISMATCH  jojo-git: present in {where} before launcher support "
                              f"for provider 'copilot' (the launcher rejects the whole roster)\n", out)
                self.assertNotIn("absent from", out)
                self.assertEqual(code, 1)

    def test_held_marker_on_copilot_fails_closed(self):
        # "launcher": "held" is for claude and codex rows only; on a Copilot
        # row it is a mismatch and must not soften the launcher-outage message.
        for where in (None, "roster", "bindings"):
            with self.subTest(where=where):
                o = self.office()
                o.body()
                o.dock([chat("JoJo Git")])
                if where:
                    getattr(o, where)["residents"].append(
                        {"key": "jojo-git", "display_name": "Chief Repository Operations Officer (JoJo Git)",
                         "session_id": SID})
                code, out = o.run(o.jojo(launcher="held"))
                self.assertIn("MISMATCH  jojo-git: registry launcher value 'held' applies only "
                              "to a claude or codex row, not provider 'copilot'\n", out)
                if where:
                    self.assertIn(f"MISMATCH  jojo-git: present in {where} before launcher support "
                                  f"for provider 'copilot' (the launcher rejects the whole roster)\n", out)
                self.assertNotIn("although the registry holds it", out)
                self.assertNotIn("held from launcher", out)
                self.assertEqual(code, 1)

    def test_body_names_someone_else(self):
        o = self.office()
        o.body(orientation=ORIENT.replace("JoJo Git", "Someone Else"))
        o.dock([chat("JoJo Git")])
        code, out = o.run(o.jojo())
        self.assertIn("jojo-git: body says 'Someone Else' (orientation row)", out)
        self.assertEqual(code, 1)

    def test_title_mismatch(self):
        for title in ("Wrong Resident", "NOT JoJo Git - retired donor"):
            with self.subTest(title=title):
                o = self.office()
                o.body()
                o.dock([chat(title)])
                code, out = o.run(o.jojo())
                self.assertIn(f"jojo-git: Agent Dock title {title!r} does not match registry", out)
                self.assertEqual(code, 1)


class FailClosed(OfficeTest):
    def test_unreadable_body(self):
        other = "0000d9d9-0000-4000-8000-00000000d9d9"
        cases = [
            ("missing", lambda o: None, "container missing"),
            ("no orientation", lambda o: o.body(orientation=None), "no orientation row"),
            ("other id", lambda o: o.body(workspace=o.workspace(sid=other)),
             "workspace.yaml names another session"),
            ("schema", lambda o: o.body(first_type="session.resume"), "unsupported events schema"),
            ("sub-agent", lambda o: o.body(agent_row=True), "no orientation row"),
            ("no cwd", lambda o: o.body(workspace=f"id: {SID}\n"), PLAIN),
            ("spaced key", lambda o: o.body(workspace=o.workspace().replace("cwd: ", "cwd : ")), PLAIN),
            ("duplicate", lambda o: o.body(workspace=o.workspace(cwd="/elsewhere") + f"cwd: {o.room}\n"), PLAIN),
            ("two docs", lambda o: o.body(workspace=o.workspace() + "---\nid: x\n"), PLAIN),
            ("continuation", lambda o: o.body(workspace=o.workspace().replace(
                f"cwd: {o.room}\n", f"cwd: {o.room}\n  -old\n")), PLAIN),
            ("quoted", lambda o: o.body(workspace=o.workspace().replace(
                f"cwd: {o.room}", f"cwd: '{o.room}'")), PLAIN),
            ("bom", lambda o: o.body(workspace="\ufeff" + o.workspace()), PLAIN),
            ("cleared", lambda o: o.body(extra_rows=[{"type": "session.context_cleared",
                                                      "data": {}}]), "no orientation row"),
            ("block cwd", lambda o: o.body(workspace=o.workspace().replace(
                f"cwd: {o.room}\n", f"cwd: |-\n  {o.room}\n")), PLAIN),
            ("block id", lambda o: o.body(workspace=o.workspace().replace(
                f"id: {SID}\n", f"id: >-\n  {SID}\n")), PLAIN),
            ("below digit", lambda o: o.body(workspace=o.workspace().replace(
                "name: x\n", "name: |3\n  x\n")), PLAIN),
            ("bad header", lambda o: o.body(workspace=o.workspace().replace(
                "name: x\n", "name: |x\n")), PLAIN),
            ("zero digit", lambda o: o.body(workspace=o.workspace().replace(
                "name: x\n", "name: |0\n  x\n")), PLAIN),
            ("two digits", lambda o: o.body(workspace=o.workspace().replace(
                "name: x\n", "name: |10\n  x\n")), PLAIN),
            ("deeper leading line", lambda o: o.body(workspace=o.workspace().replace(
                "name: x\n", "name: |-\n   \n\n  x\n")), PLAIN),
            ("no space after colon", lambda o: o.body(workspace=o.workspace().replace(
                "cwd: ", "cwd:")), PLAIN),
            ("quoted id", lambda o: o.body(workspace=o.workspace().replace(
                f"id: {SID}", f"id: '{SID}'")), PLAIN),
            ("duplicate other key", lambda o: o.body(workspace=o.workspace() + "name: y\n"), PLAIN),
            ("core-word keys", lambda o: o.body(workspace=o.workspace() + "null: a\nNull: b\n"), PLAIN),
            ("core-word key", lambda o: o.body(workspace=o.workspace() + "true: a\n"), PLAIN),
            ("merge value", lambda o: o.body(workspace=o.workspace().replace(
                "name: x\n", "name: <<\n")), PLAIN),
            ("value key", lambda o: o.body(workspace=o.workspace().replace(
                "name: x\n", "name: =\n")), PLAIN),
            ("marker suffix", lambda o: o.body(workspace=o.workspace() + "...x\n"), PLAIN),
            ("second document", lambda o: o.body(workspace=o.workspace() + "...\n---\n"), PLAIN),
            ("final document start", lambda o: o.body(workspace=o.workspace() + "---\n"), PLAIN),
            ("digit key", lambda o: o.body(workspace=o.workspace() + "1: a\n"), PLAIN),
            ("first-line tab", lambda o: o.body(workspace=o.workspace().replace(
                "name: x\n", "name: |-\n  \tx\n")), PLAIN),
            ("tab before first line", lambda o: o.body(workspace=o.workspace().replace(
                "name: x\n", "name: |-\n \t\n  x\n")), PLAIN),
            ("continuation after block", lambda o: o.body(workspace=(
                f"id: {SID}\nname: |-\n  a\ncwd: {o.room}\n  -old\n")), PLAIN),
            ("unclosed quote", lambda o: o.body(workspace=(
                f'id: {SID}\nname: "x\ncwd: {o.room}\nbranch: y"\n')), PLAIN),
            ("bad escape", lambda o: o.body(workspace=o.workspace().replace(
                "name: x\n", 'name: "\\q"\n')), PLAIN),
            ("mapping in value", lambda o: o.body(workspace=o.workspace().replace(
                "name: x\n", "name: a: b\n")), PLAIN),
            ("comment on other key", lambda o: o.body(workspace=o.workspace().replace(
                "name: x\n", "name: x # c\n")), PLAIN),
            ("alias", lambda o: o.body(workspace=o.workspace().replace(
                "name: x\n", "name: *a\n")), PLAIN),
            ("anchor", lambda o: o.body(workspace=o.workspace().replace(
                "name: x\n", "name: &a x\n")), PLAIN),
            ("tag", lambda o: o.body(workspace=o.workspace().replace(
                "name: x\n", "name: !t x\n")), PLAIN),
            ("flow", lambda o: o.body(workspace=o.workspace().replace(
                "name: x\n", "name: [a\n")), PLAIN),
            ("long key", lambda o: o.body(workspace=o.workspace() + "k" * 1025 + ": v\n"), PLAIN),
            ("after document end", lambda o: o.body(workspace=o.workspace() + "...\nextra: 1\n"), PLAIN),
            ("header comment", lambda o: o.body(workspace=o.workspace().replace(
                "name: x\n", "name: |- # note\n  x\n")), PLAIN),
            ("block dedent", lambda o: o.body(workspace=o.workspace().replace(
                "name: x\n", "name: |-\n    a\n  b\n")), PLAIN),
            ("block tab", lambda o: o.body(workspace=o.workspace().replace(
                "name: x\n", "name: |-\n\tx\n")), PLAIN),
            ("deep leading blank", lambda o: o.body(workspace=o.workspace().replace(
                "name: x\n", "name: |-\n      \n  x\n")), PLAIN),
            ("nested map", lambda o: o.body(workspace=o.workspace().replace(
                "name: x\n", "name:\n  sub: x\n")), PLAIN),
            ("tab-only line", lambda o: o.body(workspace=o.workspace() + "\t\n"), PLAIN),
            ("crlf", lambda o: o.body(workspace=o.workspace().replace("\n", "\r\n")), PLAIN),
        ]
        for name, make, expect in cases:
            with self.subTest(case=name):
                o = self.office()
                make(o)
                o.dock([chat("JoJo Git")])
                code, out = o.run(o.jojo())
                self.assert_incomplete(out, code, expect)

    def test_workspace_bad_utf8(self):
        o = self.office()
        d = o.body()
        (d / "workspace.yaml").write_bytes(o.workspace().encode() + b"name: caf\xe9\n")
        o.dock([chat("JoJo Git")])
        code, out = o.run(o.jojo())
        self.assert_incomplete(out, code, "workspace.yaml unreadable")

    def test_yaml_terminator_cannot_confirm_room(self):
        # Copilot's YAML reader ends a plain value at a space or tab before
        # `#`, and rejects `: ` inside it, so a room whose name holds either
        # must not be confirmed from the unquoted form (PR #108 review).
        for name, suffix in (("tab comment", "\t#old"), ("space comment", " #old"),
                             ("mapping", ": b"), ("trailing colon", ":")):
            with self.subTest(case=name):
                o = self.office()
                room = os.path.realpath(o.base / "GitHub") + suffix
                os.makedirs(room)
                o.body(cwd=room)
                o.dock([chat("JoJo Git")], project=re.sub(
                    r"[^A-Za-z0-9]", "-", room).strip("-"))
                code, out = o.run(o.jojo(room=room))
                self.assert_incomplete(out, code, PLAIN)

    def test_malformed_values(self):
        # Every header, quoting and plain-value form that libyaml or YAML 1.2
        # refuses or reads differently is refused, on any key it can reach.
        names = ["|-0", "|23", "|2-3", "|--", "|-2-", '"\\x4"', '"\\u41"', '"\\U41"',
                 "'x''", '"a"b', '"\\ud800"', '"\\uDFFF"', '"\\U0000D800"', '"\\U00110000"']
        cwds = ["]x", "{x", "}x", ",x", "#x", ">", '"x"', "'x'", "%x", "@x", "`x", "- x",
                "-\tx", "? x", "?", "-", "x:\ty", ""]
        cases = [("name", v) for v in names] + [("cwd", v) for v in cwds]
        for key, value in cases:
            with self.subTest(key=key, value=value):
                o = self.office()
                if key == "name":
                    ws = o.workspace().replace("name: x\n", f"name: {value}\n  x\n"
                                               if value[0] in "|>" else f"name: {value}\n")
                else:
                    ws = o.workspace().replace(f"cwd: {o.room}\n",
                                               f"cwd: {value}\n" if value else "cwd:\n")
                o.body(workspace=ws)
                o.dock([chat("JoJo Git")])
                code, out = o.run(o.jojo())
                self.assert_incomplete(out, code, PLAIN)

    def test_every_unsafe_character(self):
        # The whole refused set, one code point at a time, after the cwd.
        points = [*range(0x00, 0x09), *range(0x0b, 0x20), *range(0x7f, 0xa0),
                  0x2028, 0x2029, 0xfeff, 0xfffe, 0xffff]
        for cp in points:
            with self.subTest(code_point=hex(cp)):
                o = self.office()
                o.body(workspace=o.workspace().replace(
                    f"cwd: {o.room}\n", f"cwd: {o.room}{chr(cp)}\n"))
                o.dock([chat("JoJo Git")])
                code, out = o.run(o.jojo())
                self.assert_incomplete(out, code, PLAIN)

    def test_separator_cannot_confirm_room(self):
        # Copilot's libyaml-based folder reader ends a line at NEL, LS or PS
        # and refuses the other controls and U+FFFE/U+FFFF; its YAML 1.2
        # library keeps NEL, LS and PS as text. A stored folder followed by
        # any of them must not be read as the room (Claudio's PR #108
        # review), nor smuggle a key inside a block. A carriage return or a
        # byte-order mark, which Copilot does not write, is refused by policy.
        for name, ch in (("NEL", "\x85"), ("LS", "\u2028"), ("PS", "\u2029"),
                         ("VT", "\x0b"), ("FF", "\x0c"), ("FS", "\x1c"), ("GS", "\x1d"),
                         ("US", "\x1f"), ("NUL", "\x00"), ("DEL", "\x7f"), ("C1 first", "\x80"),
                         ("C1 last", "\x9f"), ("FFFE", "\ufffe"), ("FFFF", "\uffff"),
                         ("CR", "\r"), ("BOM", "\ufeff")):
            with self.subTest(case=name):
                o = self.office()
                o.body(workspace=o.workspace().replace(
                    f"cwd: {o.room}\n", f"cwd: {o.room}{ch}\n"))
                o.dock([chat("JoJo Git")])
                code, out = o.run(o.jojo())
                self.assert_incomplete(out, code, PLAIN)
        with self.subTest(case="smuggled key"):
            o = self.office()
            o.body(workspace=o.workspace().replace(
                "name: x\n", "name: |-\n  x\u2028cwd: /elsewhere\n"))
            o.dock([chat("JoJo Git")])
            code, out = o.run(o.jojo())
            self.assert_incomplete(out, code, PLAIN)

    def test_event_payload_shapes(self):
        # A JSON event whose data is not an object must not abort the whole
        # check (PR #108 review): an unusable session.start is an unsupported
        # schema, and an unusable user message cannot be an orientation row.
        o = self.office()
        d = o.body()
        events = d / "events.jsonl"
        rows = events.read_text(encoding="utf-8").splitlines()
        rows[0] = json.dumps({"type": "session.start", "data": [SID]})
        events.write_text("\n".join(rows) + "\n", encoding="utf-8")
        o.dock([chat("JoJo Git")])
        code, out = o.run(o.jojo(), *legacy_rows())
        self.assert_incomplete(out, code, "unsupported events schema")
        self.assertIn("claude-one", out)
        for data in (["x"], "text", 1):
            with self.subTest(data=data):
                o = self.office()
                o.body(extra_rows=[{"type": "user.message", "data": data}])
                o.dock([chat("JoJo Git")])
                code, out = o.run(o.jojo())
                self.assertEqual(code, 0, out)
                self.assertIn("  ok  jojo-git", out)

    def test_title_leg_uncompared(self):
        cases = [
            ("automatic", dict(chats=[chat("JoJo Git", user_set=False)])),
            ("ambiguous", dict(chats=[chat("JoJo Git"), chat("Other Name")])),
            ("other adapter", dict(chats=[chat("JoJo Git", adapter="codex")])),
            ("archived", dict(chats=[chat("JoJo Git", archived=True)])),
            ("other window", dict(chats=[chat("JoJo Git")], project="media-nos4r2-user-vol")),
            ("bad bytes", dict(raw=b'[{"title": "caf\xe9')),
            ("bad sessions", dict(chats=[chat("JoJo Git"), {
                "id": "conv-2", "title": "Other Name", "titleUserSet": True, "sessions": 1}])),
        ]
        for name, kwargs in cases:
            with self.subTest(case=name):
                o = self.office()
                o.body()
                o.dock(**kwargs)
                code, out = o.run(o.jojo())
                self.assertIn(DOCK_NOTE, out)
                self.assertIn("Agent Dock leg compared: 0/1", out)
                self.assertNotIn("PyCharm label absent from disk", out)
                self.assertEqual(code, 1)

    def test_unknown_provider_not_scanned_as_codex(self):
        o = self.office()
        with mock.patch.object(type(o.mod.CODEX_SESSIONS), "rglob", side_effect=AssertionError):
            self.assertEqual(o.mod.body_identity(o.jojo(provider="gemini")),
                             (None, "unsupported provider 'gemini'"))


class ReadOnly(OfficeTest):
    def test_no_file_changes(self):
        o = self.office()
        o.body()
        o.dock([chat("JoJo Git")])
        o.run(o.jojo())

        def snap():
            return {p: (p.stat().st_mtime_ns, p.read_bytes())
                    for p in sorted(o.base.rglob("*")) if p.is_file()}
        before = snap()
        run(o.mod)
        self.assertEqual(snap(), before)



class LiveFolderAndTitleRows(unittest.TestCase):
    """The label leg reads the live IDE folder, and a Claude body's title row."""

    UID = "11111111-2222-4333-8444-555555555555"
    THREAD = "0aaaaaaa-0000-7000-8000-000000000000"

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.mod = load(SCRIPT, "cand_live")
        patcher = mock.patch.object(self.mod.Path, "home", return_value=self.home)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.mod.CLAUDE_PROJECTS = self.home / "claude"

    def folder(self, name: str, label: str | None = None, *, bind: bool = True,
               name_it: bool = True) -> Path:
        root = self.home / ".config/JetBrains" / name
        (root / "aia-task-history").mkdir(parents=True)
        (root / "workspace").mkdir()
        if label is not None and bind:
            (root / "aia-task-history" / f"{self.UID}.agentsession").write_text(
                f"acp.registry.codex-acp:{self.THREAD}\n", encoding="utf-8")
        if label is not None and name_it:
            (root / "workspace" / "w.xml").write_text(
                '<SerializedChat><option name="custom" value="true" />\n'
                f'<option name="text" value="{label}" />\n'
                f'<option name="uid" value="{self.UID}" />\n</SerializedChat>', encoding="utf-8")
        return root

    def body(self, sid: str, rows: list[str], project: str = "p") -> None:
        d = self.mod.CLAUDE_PROJECTS / project
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{sid}.jsonl").write_text("\n".join(rows) + "\n", encoding="utf-8")

    def test_the_highest_version_is_live_by_number_not_by_name(self) -> None:
        for name in ("PyCharm2026.1", "PyCharm2026.3", "PyCharm2026.10", "PyCharmCE2027.1",
                     "PyCharm2027.1-backup"):
            self.folder(name)
        (self.home / ".config/JetBrains/PyCharm2028.1").write_text("a file", encoding="utf-8")
        self.assertEqual(self.mod.live_pycharm_config().name, "PyCharm2026.10")

    def test_two_folders_of_one_version_name_no_live_folder(self) -> None:
        self.folder("PyCharm2026.3", "Fixture Label (Either)")
        self.folder("PyCharm2026.03")
        self.folder("PyCharm2026.1")
        self.assertEqual([p.name for p in self.mod.newest_pycharm_folders()], ["PyCharm2026.03", "PyCharm2026.3"])
        self.assertIsNone(self.mod.live_pycharm_config())
        self.assertEqual(self.mod.acp_titles(), {})

    def test_a_link_is_not_a_version_folder(self) -> None:
        real = self.folder("PyCharm2026.1")
        (self.home / ".config/JetBrains/PyCharm2027.1").symlink_to(real)
        self.assertEqual(self.mod.live_pycharm_config().name, "PyCharm2026.1")

    def test_no_folder_gives_no_titles(self) -> None:
        self.assertIsNone(self.mod.live_pycharm_config())
        self.assertEqual(self.mod.acp_titles(), {})

    def test_a_chat_only_in_a_dead_folder_does_not_count(self) -> None:
        self.folder("PyCharm2026.1", "Fixture Label (Dead Folder)")
        self.folder("PyCharm2026.3")
        self.assertEqual(self.mod.acp_titles(), {})

    def test_a_live_binding_does_not_borrow_a_label_from_a_dead_folder(self) -> None:
        self.folder("PyCharm2026.1", "Fixture Label (Dead Folder)", bind=False)
        self.folder("PyCharm2026.3", "unused", name_it=False)
        self.assertEqual(self.mod.acp_titles(), {})

    def test_a_live_label_does_not_borrow_a_binding_from_a_dead_folder(self) -> None:
        self.folder("PyCharm2026.1", "unused", name_it=False)
        self.folder("PyCharm2026.3", "Fixture Label (Live Folder)", bind=False)
        self.assertEqual(self.mod.acp_titles(), {})

    def test_the_live_label_is_read_and_a_dead_one_cannot_win(self) -> None:
        self.folder("PyCharm2026.1", "Old Label (Dead Folder)")
        self.folder("PyCharm2026.3", "Live Label (Live Folder)")
        self.assertEqual(self.mod.acp_titles(), {self.THREAD: "Live Label (Live Folder)"})

    def test_the_last_title_row_wins_and_other_rows_do_not_count(self) -> None:
        self.body("s1", ['{"type":"custom-title","customTitle":"First (One)"}', "not json",
                         '{"type":"ai-title","aiTitle":"Hello"}',
                         '{"type":"custom-title","customTitle":"Second (Two)"}',
                         '{"type":"user","text":"\\"custom-title\\" in a message"}'])
        self.assertEqual(self.mod.body_custom_title("s1"), "Second (Two)")

    def test_no_title_row_and_no_body_give_none(self) -> None:
        self.body("s2", ['{"type":"ai-title","aiTitle":"Hello"}'])
        self.assertIsNone(self.mod.body_custom_title("s2"))
        self.assertIsNone(self.mod.body_custom_title("absent"))

    def test_two_bodies_that_disagree_are_ambiguous(self) -> None:
        self.body("s3", ['{"type":"custom-title","customTitle":"A (One)"}'], "p")
        self.body("s3", ['{"type":"custom-title","customTitle":"B (Two)"}'], "q")
        self.assertIsNone(self.mod.body_custom_title("s3"))

    def test_rows_that_are_not_title_rows_do_not_count(self) -> None:
        self.body("s4", ['{"type":"custom-title","customTitle":"Kept (One)"}', '["custom-title"]',
                         '{"type":"note","tag":"custom-title","customTitle":"Other (Two)"}',
                         '{"type":"custom-title","customTitle":7}',
                         '{"type":"custom-title","customTitle":""}', '{"type":"custom-title", bad'])
        self.assertEqual(self.mod.body_custom_title("s4"), "Kept (One)")

    def test_a_titleless_body_beside_a_titled_one_leaves_the_title(self) -> None:
        self.body("s5", ['{"type":"ai-title","aiTitle":"Hello"}'], "p")
        self.body("s5", ['{"type":"custom-title","customTitle":"A (One)"}'], "q")
        self.assertEqual(self.mod.body_custom_title("s5"), "A (One)")

    @unittest.skipIf(os.geteuid() == 0, "root ignores file modes")
    def test_an_unreadable_body_gives_none(self) -> None:
        self.body("s6", ['{"type":"custom-title","customTitle":"A (One)"}'])
        path = self.mod.CLAUDE_PROJECTS / "p" / "s6.jsonl"
        path.chmod(0)
        self.addCleanup(path.chmod, 0o600)
        self.assertIsNone(self.mod.body_custom_title("s6"))


class OtherThreadsAndThePhone(OfficeTest):
    """Two reports that change no count and print no identifier and no phone name."""

    THREAD = "0aaaaaaa-0000-7000-8000-000000000000"
    STUB1 = "0bbbbbbb-0000-7000-8000-000000000000"
    STUB2 = "0ccccccc-0000-7000-8000-000000000000"
    LIVE2 = "0ddddddd-0000-7000-8000-000000000000"
    BLANK = "0eeeeeee-0000-7000-8000-000000000000"
    LABEL = "Dev (Fixture Codex)"

    def row(self, key="fixture-codex", sid=None, person="Fixture Codex", role="Dev"):
        return {"key": key, "role": role, "person": person, "provider": "codex", "session_id": sid or self.THREAD,
                "room": "/x", "verified": "operator", "note": "test"}

    def rollout(self, o, sid, archived=False):
        folder = o.base / ("codex-archived" if archived else "codex/2026/11/06")
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"rollout-2026-11-06T00-00-00-{sid}.jsonl").write_text(
            json.dumps({"type": "session_meta", "payload": {"id": sid, "cwd": "/x"}}) + "\n", encoding="utf-8")

    def index(self, o, *rows):
        (o.base / "codex-index.jsonl").write_text("".join(
            r if isinstance(r, str) else json.dumps(r) + "\n" for r in rows), encoding="utf-8")

    def test_the_label_on_other_threads_marks_archived_stubs(self):
        o = self.office()
        self.rollout(o, self.THREAD)
        self.rollout(o, self.STUB1, archived=True)
        self.rollout(o, self.STUB2, archived=True)
        self.rollout(o, self.LIVE2)
        o.mod.acp_titles = lambda: {self.THREAD: self.LABEL, self.STUB1: self.LABEL, self.STUB2: self.LABEL,
                                    self.LIVE2: self.LABEL, self.BLANK: self.LABEL, "0fffffff": "Another Label"}
        self.index(o, {"id": self.THREAD, "thread_name": self.LABEL})
        _, out = o.run(self.row())
        self.assertIn("registered label also on other threads in the live folder (report only):", out)
        self.assertIn(f"fixture-codex: {self.LABEL}: 2 archived stub, 1 live, 1 no rollout", out)
        for thread in (self.THREAD, self.STUB1, self.STUB2, self.LIVE2, self.BLANK):
            self.assertNotIn(thread, out)

    def test_no_other_thread_says_nothing(self):
        o = self.office()
        self.rollout(o, self.THREAD)
        o.mod.acp_titles = lambda: {self.THREAD: self.LABEL, self.STUB1: "Another Label"}
        self.index(o, {"id": self.THREAD, "thread_name": self.LABEL})
        _, out = o.run(self.row())
        self.assertNotIn("also on other threads", out)

    def test_the_report_changes_no_count_and_no_exit(self):
        def result(with_other):
            o = self.office()
            self.rollout(o, self.THREAD)
            titles = {self.THREAD: self.LABEL}
            if with_other:
                titles[self.STUB1] = self.LABEL
                self.rollout(o, self.STUB1, archived=True)
            o.mod.acp_titles = lambda: titles
            self.index(o, {"id": self.THREAD, "thread_name": "Something Else" if with_other else self.LABEL})
            code, out = o.run(self.row())
            return code, [line for line in out.splitlines() if line.startswith("identities:")]
        self.assertEqual(result(True), result(False))

    def test_the_phone_leg_counts_each_state_by_key_and_prints_no_name(self):
        o = self.office()
        rows = [self.row("same-one", "1aaaaaaa-0000-7000-8000-000000000000", "Same One"),
                self.row("differs-one", "2aaaaaaa-0000-7000-8000-000000000000", "Differs One"),
                self.row("absent-one", "3aaaaaaa-0000-7000-8000-000000000000", "Absent One"),
                self.row("blank-one", "4aaaaaaa-0000-7000-8000-000000000000", "Blank One"),
                self.row("archived-one", "5aaaaaaa-0000-7000-8000-000000000000", "Archived One"),
                self.row("person-only", "6aaaaaaa-0000-7000-8000-000000000000", "Person Only")]
        for r in rows[:4] + rows[5:]:
            self.rollout(o, r["session_id"])
        self.rollout(o, rows[4]["session_id"], archived=True)
        self.index(o, {"id": rows[0]["session_id"], "thread_name": "an old name"},
                   {"id": rows[0]["session_id"], "thread_name": "Dev (Same One)"},
                   "not json\n", "[1, 2]\n", {"thread_name": "no id"},
                   {"id": rows[1]["session_id"], "thread_name": "SYNTHETIC-FIRST-TURN-SUMMARY"},
                   {"id": rows[3]["session_id"], "thread_name": ""},
                   {"id": rows[4]["session_id"], "thread_name": "SYNTHETIC-ARCHIVED-NAME"},
                   {"id": rows[5]["session_id"], "thread_name": "Person Only"})
        _, out = o.run(*rows)
        self.assertIn("phone names, from Codex's session index (report only): same 1, differs 2, absent 2, archived and not asked 1", out)
        self.assertIn("  - differs-one: differs", out)
        self.assertIn("  - absent-one: absent", out)
        self.assertIn("  - blank-one: absent", out)
        self.assertIn("  - person-only: differs", out)       # the whole label is the question, not the person's name inside a longer one
        for key in ("same-one", "archived-one"):
            for state in ("same", "differs", "absent", "archived"):
                self.assertNotIn(f"  - {key}: {state}", out)
        self.assertNotIn("SYNTHETIC", out)
        for r in rows:
            self.assertNotIn(r["session_id"], out)

    def test_a_non_string_id_in_the_index_is_passed_over(self):
        o = self.office()
        self.rollout(o, self.THREAD)
        self.index(o, {"id": 7, "thread_name": "x"}, {"id": None, "thread_name": "y"}, {"id": ["z"], "thread_name": "z"},
                   {"id": self.THREAD, "thread_name": self.LABEL})
        self.assertEqual(o.mod.phone_names(), {self.THREAD: self.LABEL})

    def test_a_codex_row_of_no_usable_session_is_not_asked(self):
        o = self.office()
        self.rollout(o, self.THREAD)
        self.index(o, {"id": self.THREAD, "thread_name": self.LABEL})
        rows = [self.row(), dict(self.row("none-key"), session_id=None), dict(self.row("number-key"), session_id=7)]
        rows[2].pop("note")
        self.assertEqual(o.mod.phone_leg(rows), {"same": ["fixture-codex"], "differs": [], "absent": [], "archived": []})

    def test_only_codex_rows_are_asked(self):
        o = self.office()
        self.rollout(o, self.THREAD)
        self.index(o, {"id": self.THREAD, "thread_name": self.LABEL})
        _, out = o.run(self.row(), *legacy_rows()[:1])
        self.assertIn("same 1, differs 0, absent 0, archived and not asked 0", out)

    def test_a_clean_run_stays_exit_zero_whatever_the_reports_say(self):
        def clean(with_findings):
            o = self.office()
            row = self.row()
            o.roster["residents"].append({"key": row["key"], "display_name": self.LABEL, "comment": "x", "provider_id": "codex", "enabled": True})
            o.bindings["residents"].append({"key": row["key"], "provider_id": "codex", "session_id": self.THREAD, "project_root": "/x"})
            self.rollout(o, self.THREAD)
            titles = {self.THREAD: self.LABEL}
            if with_findings:
                titles[self.STUB1] = self.LABEL
            o.mod.acp_titles = lambda: titles
            self.index(o, {"id": self.THREAD, "thread_name": "Something Else" if with_findings else self.LABEL})
            with mock.patch.object(o.mod, "body_identity", return_value=("Fixture Codex", "test body")):
                return o.run(row)
        code, out = clean(False)
        self.assertEqual(code, 0, out)
        o = self.office()
        row = self.row()
        o.roster["residents"].append({"key": row["key"], "display_name": self.LABEL, "comment": "x", "provider_id": "codex", "enabled": True})
        o.bindings["residents"].append({"key": row["key"], "provider_id": "codex", "session_id": self.THREAD, "project_root": "/x"})
        self.rollout(o, self.THREAD)
        o.mod.acp_titles = lambda: {self.THREAD: self.LABEL}
        self.index(o, {"id": "0fffffff-0000-7000-8000-000000000000", "thread_name": "another thread"})
        with mock.patch.object(o.mod, "body_identity", return_value=("Fixture Codex", "test body")):
            absent_code, absent_out = o.run(row)
        self.assertEqual(absent_code, 0, absent_out)
        self.assertIn("  - fixture-codex: absent", absent_out)
        code, out = clean(True)
        self.assertEqual(code, 0, out)
        self.assertIn("also on other threads", out)
        self.assertIn("differs 1", out)

    def test_the_last_row_of_a_thread_stands(self):
        o = self.office()
        self.index(o, {"id": self.THREAD, "thread_name": "first"}, {"id": self.THREAD, "thread_name": "second"})
        self.assertEqual(o.mod.phone_names(), {self.THREAD: "second"})
        self.index(o, {"id": self.THREAD, "thread_name": "first"}, {"id": self.THREAD})
        self.assertEqual(o.mod.phone_names(), {self.THREAD: ""})

    def test_an_unreadable_index_is_said_and_changes_nothing(self):
        o = self.office()
        self.rollout(o, self.THREAD)
        code, out = o.run(self.row())
        self.assertIn("the session index could not be read, so nothing was compared", out)
        self.assertIsNone(o.mod.phone_names())
        self.index(o, {"id": self.THREAD, "thread_name": self.LABEL})
        code2, out2 = o.run(self.row())
        self.assertEqual(code, code2)
        self.assertEqual([l for l in out.splitlines() if l.startswith("identities:")], [l for l in out2.splitlines() if l.startswith("identities:")])

    def test_a_row_of_no_codex_provider_reads_no_store_and_no_index(self):
        o = self.office()
        rows = legacy_rows()[:1]
        with mock.patch.object(o.mod, "phone_names", side_effect=AssertionError):
            o.run(*rows)

    def test_quiet_prints_neither(self):
        o = self.office()
        self.rollout(o, self.THREAD)
        o.mod.acp_titles = lambda: {self.THREAD: self.LABEL, self.STUB1: self.LABEL}
        self.index(o, {"id": self.THREAD, "thread_name": "Something Else"})
        _, out = o.run(self.row(), argv=("--quiet",))
        self.assertNotIn("report only", out)

    def test_unreadable_stores_read_as_unread(self):
        o = self.office()
        with mock.patch.object(type(o.mod.CODEX_SESSIONS), "rglob", side_effect=OSError):
            self.assertEqual(o.mod.thread_states({self.THREAD}), {self.THREAD: "unread"})
        with mock.patch.object(type(o.mod.CODEX_SESSIONS), "rglob", side_effect=AssertionError):
            self.assertEqual(o.mod.thread_states(set()), {})

    def test_a_rollout_in_both_places_reads_live(self):
        o = self.office()
        self.rollout(o, self.THREAD)
        self.rollout(o, self.THREAD, archived=True)
        self.rollout(o, self.STUB1, archived=True)
        self.assertEqual(o.mod.thread_states({self.THREAD, self.STUB1, self.BLANK}),
                         {self.THREAD: "live", self.STUB1: "archived stub", self.BLANK: "no rollout"})

    def test_none_of_it_is_read_from_the_real_home(self):
        o = self.office()
        for name in ("CODEX_ARCHIVED", "CODEX_INDEX", "CODEX_SESSIONS"):
            self.assertEqual(Path(getattr(o.mod, name)).parent, o.base)


class LabelLegInMain(unittest.TestCase):
    """The label leg as main runs it: the source named, and only Claude reading a body."""

    SID = "0000aaaa-0000-4000-8000-00000000aaaa"
    WANT = "Lead (Claude One)"

    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.o = Office(Path(tmp.name))
        self.project = Path(tmp.name) / "claude" / "p"
        self.project.mkdir()

    def row(self, provider: str = "claude") -> dict:
        return {"key": "claude-one", "role": "Lead", "person": "Claude One", "provider": provider,
                "session_id": self.SID, "room": "/x", "verified": "kevin"}

    def title_row(self, title: str) -> None:
        (self.project / f"{self.SID}.jsonl").write_text(
            json.dumps({"type": "custom-title", "customTitle": title}) + "\n", encoding="utf-8")

    def store(self, title: str) -> None:
        (self.project / ".claude-code-gui-session-titles.json").write_text(
            json.dumps({self.SID: title}), encoding="utf-8")

    def test_a_body_title_that_matches_is_compared_and_named_as_its_source(self) -> None:
        self.title_row(self.WANT)
        _, out = self.o.run(self.row())
        self.assertIn("PyCharm leg compared: 1/1", out)
        self.assertIn("[label from the body's title row]", out)
        self.assertIn("1 of those compared from a body's title row", out)
        self.assertNotIn("title row 'Lead", out)

    def test_a_body_title_that_differs_is_a_mismatch_naming_the_body(self) -> None:
        self.title_row("Someone (Another Person)")
        _, out = self.o.run(self.row())
        self.assertIn("MISMATCH  claude-one: body title row 'Someone (Another Person)' does not match", out)
        self.assertNotIn("PyCharm label 'Someone", out)

    def test_the_store_alone_is_the_ide_label_and_carries_no_mark(self) -> None:
        self.store("Someone (Another Person)")
        _, out = self.o.run(self.row())
        self.assertIn("MISMATCH  claude-one: PyCharm label 'Someone (Another Person)'", out)
        self.assertNotIn("title row", out)

    def test_store_and_row_that_agree_read_as_the_ide_label(self) -> None:
        self.store(self.WANT)
        self.title_row(self.WANT)
        _, out = self.o.run(self.row())
        self.assertIn("PyCharm leg compared: 1/1", out)
        self.assertNotIn("title row", out)

    def test_store_and_row_that_disagree_are_left_uncompared(self) -> None:
        self.store(self.WANT)
        self.title_row("Renamed (Since Then)")
        _, out = self.o.run(self.row())
        self.assertIn("PyCharm label store and body title row disagree", out)
        self.assertIn("PyCharm leg compared: 0/1", out)

    def test_no_label_anywhere_is_not_on_disk(self) -> None:
        _, out = self.o.run(self.row())
        self.assertIn("PyCharm label not on disk", out)
        self.assertIn("PyCharm leg compared: 0/1", out)

    def test_a_codex_row_never_reads_a_body_for_its_label(self) -> None:
        with mock.patch.object(self.o.mod, "body_custom_title", side_effect=AssertionError):
            _, out = self.o.run(self.row("codex"))
        self.assertIn("PyCharm label not on disk", out)

if __name__ == "__main__":
    unittest.main()
