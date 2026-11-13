#!/usr/bin/env python3
"""Tests for ops/lib/scripts/mind.py, in synthetic rooms only. Standard library only.

Every case builds its own room, registry and leaf bodies in a temporary
directory; no real room, mind or body is touched. Run:

    python3 -I -B tools/test/test_mind.py
"""
import contextlib
import importlib.util
import fcntl
import io
import json
import os
import selectors
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

MIND = Path(__file__).resolve().parents[2] / "ops" / "lib" / "scripts" / "mind.py"
_spec = importlib.util.spec_from_file_location("mind", MIND)
mind = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mind)

IDEA = "Evidence outranks recollection. What a resident remembers is a lead to check, never a finding."
SECOND = "A rotation keeps the person and slims the body; the receipts remember what the body forgets."
SESSION = "0000f00d-0000-4000-8000-000000000000"
AUTO = object()   # the test seam's caller defaults to the --agent a write names


def seam_env(args, env=None, caller=AUTO) -> dict:
    """The environment for one call: MIND_TEST_CALLER is the --agent of an add or retire,
    or the caller given, or absent when caller is None. The parent's own value never leaks in."""
    base = dict(os.environ if env is None else env)
    base.pop(mind.SEAM, None)
    if caller is AUTO:
        caller = (args[args.index("--agent") + 1]
                  if args and args[0] in ("add", "retire") and "--agent" in args else None)
    if caller is not None:
        base[mind.SEAM] = caller
    return base


class Room:
    def __init__(self, base: Path, keys=("session-doctor", "claudine-colbert"), extra=()):
        self.base = base
        self.room = base / "room"
        self.room.mkdir()
        self.registry = base / "registry.json"
        identities = [{"key": k, "person": f"Person {k}", "role": "Role", "room": str(self.room),
                       "session_id": SESSION} for k in keys] + list(extra)
        self.registry.write_text(json.dumps({"identities": identities}))
        self.minute = 0

    def run(self, *args, stdin=None, env=None, day="2026-10-30", caller=AUTO):
        self.minute += 1
        cmd = [sys.executable, "-I", "-B", str(MIND), "--room", str(self.room), "--registry", str(self.registry),
               "--now", f"{day}T17:{self.minute:02d}:00Z", *args]
        return subprocess.run(cmd, capture_output=True, text=True, input=stdin, timeout=60,
                              env=seam_env(args, env, caller))

    def add(self, body=IDEA, title="Evidence outranks recollection", agent="session-doctor", supersedes=None,
            env=None, day="2026-10-30", caller=AUTO):
        path = self.base / f"body-{self.minute}.md"
        path.write_text(body, encoding="utf-8")
        extra = ("--supersedes", supersedes) if supersedes else ()
        return self.run("add", "--agent", agent, "--title", title, "--body", str(path), *extra, env=env, day=day,
                        caller=caller)

    def index(self) -> list:
        return mind.read_index(self.room) or []

    def ids(self) -> list:
        return [i for i, _, _ in self.index()]

    def leaf(self, leaf_id: str) -> Path:
        return self.room / "archives" / "mind" / f"{leaf_id}.md"

    def ledger(self) -> list:
        path = self.room / "logs" / "mind" / "ledger.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    def files(self) -> list:
        return sorted(p.relative_to(self.room).as_posix() for p in self.room.rglob("*") if p.is_file()
                      and p.name != "mind.lock")


def in_process(room: Room, *args, caller=AUTO) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), \
            mock.patch.dict(os.environ, seam_env(args, caller=caller), clear=True):
        rc = mind.main(["--room", str(room.room), "--registry", str(room.registry),
                        "--now", "2026-10-30T18:00:00Z", *args])
    return rc, out.getvalue(), err.getvalue()


class MindTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.r = Room(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def ok(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def refused(self, result, *words):
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        for word in words:
            self.assertIn(word, result.stderr)
        return result

    def failed_check(self, *words):
        result = self.r.run("check")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        for word in words:
            self.assertIn(word, result.stdout)
        return result

    # -- the loop: add, show, read, check -------------------------------------
    def test_an_empty_room_checks_clean_and_shows_nothing(self):
        result = self.ok(self.r.run("check"))
        self.assertIn("no MIND.md yet", result.stdout)
        self.assertIn("the mind holds no leaves", self.ok(self.r.run("show")).stdout)
        self.assertEqual(self.r.files(), [])

    def test_add_show_read_check_round_trip(self):
        self.assertIn("MIND-2026-10-30-001 written by session-doctor", self.ok(self.r.add()).stdout)
        shown = self.ok(self.r.run("show")).stdout
        self.assertEqual(shown, "- [MIND-2026-10-30-001](archives/mind/MIND-2026-10-30-001.md) session-doctor"
                                " — Evidence outranks recollection\n")
        leaf = self.ok(self.r.run("read", "MIND-2026-10-30-001")).stdout
        self.assertEqual(leaf.encode(), self.r.leaf("MIND-2026-10-30-001").read_bytes())
        check = self.ok(self.r.run("check"))
        self.assertIn("PASS leaf : MIND-2026-10-30-001 session-doctor", check.stdout)
        self.assertIn("blocking failures: 0", check.stdout)

    def test_the_index_is_pointers_only_and_the_leaf_carries_id_agent_time_and_title(self):
        self.ok(self.r.add())
        index = (self.r.room / "MIND.md").read_text()
        self.assertTrue(index.startswith(mind.INDEX_HEAD))
        self.assertNotIn(IDEA, index)
        self.assertEqual(self.r.leaf("MIND-2026-10-30-001").read_text(),
                         "---\nid: MIND-2026-10-30-001\nagent: session-doctor\nwritten: 2026-10-30T17:01:00Z\n"
                         "title: Evidence outranks recollection\nsupersedes: none\n---\n\n" + IDEA + "\n")

    def test_ids_count_up_within_a_day_and_never_repeat(self):
        self.ok(self.r.add())
        self.ok(self.r.add(SECOND, "Rotation is continuity"))
        self.ok(self.r.run("retire", "--agent", "session-doctor", "MIND-2026-10-30-002"))
        self.ok(self.r.add(SECOND, "Rotation is continuity, slimmed"))
        self.ok(self.r.add(SECOND, "A new day starts at one", day="2026-10-31"))
        self.assertEqual(self.r.ids(), ["MIND-2026-10-30-001", "MIND-2026-10-30-003", "MIND-2026-10-31-001"])

    def test_the_ledger_records_every_write_with_its_hash_and_size(self):
        self.ok(self.r.add())
        self.ok(self.r.run("retire", "--agent", "session-doctor", "MIND-2026-10-30-001"))
        add, retire = self.r.ledger()
        data = self.r.leaf("MIND-2026-10-30-001").read_bytes()
        self.assertEqual(add, {"action": "add", "id": "MIND-2026-10-30-001", "agent": "session-doctor",
                               "time": "2026-10-30T17:01:00Z", "sha256": mind.sha256(data), "bytes": len(data),
                               "supersedes": "none"})
        self.assertEqual(retire, {"action": "retire", "id": "MIND-2026-10-30-001", "agent": "session-doctor",
                                  "time": "2026-10-30T17:02:00Z", "sha256": mind.sha256(data), "bytes": len(data)})

    def test_body_from_standard_input(self):
        self.ok(self.r.run("add", "--agent", "session-doctor", "--title", "From input", "--body", "-", stdin=IDEA))
        self.assertIn(IDEA, self.r.leaf("MIND-2026-10-30-001").read_text())

    # -- concepts only ----------------------------------------------------------
    def test_the_screen_refuses_the_fact_of_the_moment(self):
        cases = {
            "a date": "The cutover landed on 2026-11-09 and held.",
            "a time": "Rotate at 14:30 when the room is quiet.",
            "a word that dates the text": "The board is currently clean.",
            "a count or size": "All 51 suites pass before a merge.",
            "a path or file name": "The tool lives in ops/lib/scripts and nowhere else.",
            "an address": "The source is https://example.invalid for this.",
            "a pull request, issue or version number": "The cutover left with #71.",
            "code or a command line": "Run it with --force when stuck.",
            "an identifier": "The body was " + SESSION + ".",
            "medical content": "A hospital stay changes the schedule.",
            "possible secret": "The password is in the vault.",
        }
        for kind, body in cases.items():
            with self.subTest(kind=kind):
                result = self.refused(self.r.add(body, "A plain title"), kind)
                self.assertNotIn(body, result.stderr)
                self.assertEqual(self.r.files(), [])

    def test_the_title_is_screened_too(self):
        self.refused(self.r.add(IDEA, "What happened on 2026-11-09"), "title: a date")
        self.assertEqual(self.r.files(), [])

    def test_abstractions_pass(self):
        for n, body in enumerate((
                "Measure before explaining: a claim is a lead until the evidence is read.",
                "PoT 4.2.4 and 1.2.10 say who decides; read them before acting on a mind.",
                "Two readers who disagree are a finding, not a fault.",
                "A resident's handoff is for the present; a mind is for what stays true."), 1):
            with self.subTest(body=body):
                self.ok(self.r.add(body, f"An idea, number {n}"))

    def test_limits_are_generous_but_bounded(self):
        self.refused(self.r.add(IDEA, "t" * (mind.TITLE_LIMIT + 1)), "the limit is 100")
        self.refused(self.r.add("word " * 401, "Too long"), "the limit is 2000")
        self.refused(self.r.add("   \n\n", "Empty"), "body: empty")
        self.refused(self.r.add("A line\x07 with a bell.", "Bell"), "U+0007")
        self.assertEqual(self.r.files(), [])
        self.ok(self.r.add("word " * 399, "t" * mind.TITLE_LIMIT))

    def test_the_index_is_refused_when_full_but_supersede_still_flows(self):
        with mock.patch.object(mind, "INDEX_LIMIT", 2):
            self.assertEqual(self.r.add().returncode, 0)
            for title in ("First", "Second"):
                rc, _, err = in_process(self.r, "add", "--agent", "session-doctor", "--title", title,
                                        "--body", str(self.write_body(IDEA)))
            self.assertEqual(rc, 2, err)
            self.assertIn("holds 2 pointers, its limit", err)
            first = self.r.ids()[1]
            rc, out, err = in_process(self.r, "add", "--agent", "session-doctor", "--title", "Replaced",
                                      "--body", str(self.write_body(SECOND)), "--supersedes", first)
            self.assertEqual(rc, 0, err)
            self.assertEqual(len(self.r.index()), 2)

    def write_body(self, text):
        path = self.r.base / "in-process-body.md"
        path.write_text(text)
        return path

    # -- ownership and authority ------------------------------------------------
    def test_supersede_replaces_the_line_in_place_and_the_old_leaf_is_not_served(self):
        self.ok(self.r.add())
        self.ok(self.r.add(SECOND, "Rotation is continuity"))
        self.ok(self.r.add(IDEA + " Read the record first.", "Evidence outranks recollection, always",
                           supersedes="MIND-2026-10-30-001"))
        self.assertEqual(self.r.ids(), ["MIND-2026-10-30-003", "MIND-2026-10-30-002"])
        self.assertIn("supersedes: MIND-2026-10-30-001", self.r.leaf("MIND-2026-10-30-003").read_text())
        self.assertTrue(self.r.leaf("MIND-2026-10-30-001").exists())
        self.refused(self.r.run("read", "MIND-2026-10-30-001"), "only live leaves are served")
        self.refused(self.r.add(SECOND, "Again", supersedes="MIND-2026-10-30-001"), "is not a live leaf")

    def test_a_resident_changes_only_its_own_leaves(self):
        self.ok(self.r.add())
        self.refused(self.r.run("retire", "--agent", "claudine-colbert", "MIND-2026-10-30-001"),
                     "belongs to session-doctor")
        self.refused(self.r.add(SECOND, "Mine now", agent="claudine-colbert", supersedes="MIND-2026-10-30-001"),
                     "belongs to session-doctor")
        self.assertEqual(self.r.ids(), ["MIND-2026-10-30-001"])

    def test_only_a_resident_registered_once_in_this_room_writes(self):
        elsewhere = Path(self.tmp.name) / "elsewhere"
        elsewhere.mkdir()
        other = Room(elsewhere)
        # Each row carries a synthetic session, so the test seam is open and the registration checks are reached.
        extra = ({"key": "visitor", "room": str(other.room), "session_id": SESSION},
                 {"key": "twice", "room": str(self.r.room), "session_id": SESSION},
                 {"key": "twice", "room": str(self.r.room), "session_id": SESSION})
        self.r.registry.write_text(json.dumps({"identities": [
            {"key": "session-doctor", "room": str(self.r.room), "session_id": SESSION}, *extra]}))
        self.refused(self.r.add(agent="nobody"), "registered 0 times")
        self.refused(self.r.add(agent="twice"), "registered 2 times")
        self.refused(self.r.add(agent="visitor"), "registered to another room")
        self.refused(self.r.add(agent="Not A Key"), "is not a registry key")
        self.assertEqual(self.r.files(), [])

    def test_no_approval_is_asked_and_the_chain_commands_are_gone(self):
        self.ok(self.r.add())
        for args in (("preview", "session-doctor", "--changes", "-"), ("write", "session-doctor"),
                     ("history", "session-doctor"), ("add", "--agent", "session-doctor", "--title", "x",
                                                     "--body", "-", "--yes", "yes")):
            with self.subTest(command=args[0]):
                result = self.r.run(*args, stdin=IDEA)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn("usage:", result.stderr)

    def test_retire_takes_the_pointer_out_and_keeps_the_leaf(self):
        self.ok(self.r.add())
        self.ok(self.r.run("retire", "--agent", "session-doctor", "MIND-2026-10-30-001"))
        self.assertEqual(self.r.index(), [])
        self.assertTrue(self.r.leaf("MIND-2026-10-30-001").exists())
        self.ok(self.r.run("check"))

    # -- integrity --------------------------------------------------------------
    def test_a_changed_leaf_fails_check_and_is_not_served_until_its_owner_retires_it(self):
        self.ok(self.r.add())
        self.ok(self.r.add(SECOND, "Rotation is continuity"))
        leaf = self.r.leaf("MIND-2026-10-30-001")
        leaf.write_text(leaf.read_text().replace("never a finding", "always a finding"))
        self.failed_check("not the one the ledger recorded")
        self.refused(self.r.run("show"), "not served until its check passes")
        self.refused(self.r.run("read", "MIND-2026-10-30-002"), "not served until its check passes")
        self.ok(self.r.run("retire", "--agent", "session-doctor", "MIND-2026-10-30-001"))
        self.ok(self.r.run("check"))

    def test_a_hand_written_index_line_is_refused(self):
        self.ok(self.r.add())
        index = self.r.room / "MIND.md"
        index.write_text(index.read_text() + "a note added by hand\n")
        self.failed_check("holds a line that is not a pointer")
        self.refused(self.r.add(SECOND, "Another"), "holds a line that is not a pointer")

    def test_an_index_line_without_a_ledger_record_fails(self):
        self.ok(self.r.add())
        data = mind.render_leaf({"id": "MIND-2026-10-30-009", "agent": "session-doctor",
                                 "written": "2026-10-30T17:09:00Z", "title": "Planted", "supersedes": "none"}, SECOND)
        self.r.leaf("MIND-2026-10-30-009").write_text(data)
        lines = self.r.index() + [("MIND-2026-10-30-009", "session-doctor", "Planted")]
        (self.r.room / "MIND.md").write_text(mind.index_text(lines))
        self.failed_check("the ledger records no add of this leaf")

    def test_the_retired_chain_format_is_refused_with_a_custody_instruction(self):
        (self.r.room / "MIND.md").write_text("resident=session-doctor|leaf=archives/MIND-x.md|sha256=" + "0" * 64 + "\n")
        for result in (self.r.add(), self.r.run("show")):
            self.refused(result, "move it and every archives/MIND-*.md", "to custody")
        self.failed_check("not a pointer index")
        (self.r.room / "MIND.md").unlink()
        (self.r.room / "archives").mkdir()
        (self.r.room / "archives" / "MIND-session-doctor-2026-10-30-0a1b2c3d.md").write_text("old\n")
        self.refused(self.r.add(), "retired chain format", "move them to custody")
        self.failed_check("FAIL legacy")
        self.assertFalse((self.r.room / "MIND.md").exists())

    def test_a_leaf_that_fails_a_tightened_screen_is_reported_not_blocked(self):
        self.ok(self.r.add())
        tighter = mind.CONCEPT_SCREEN + (("a new kind", __import__("re").compile("recollection")),)
        with mock.patch.object(mind, "CONCEPT_SCREEN", tighter):
            rc, out, _ = in_process(self.r, "check")
        self.assertEqual(rc, 0, out)
        self.assertIn("REPORT leaf : MIND-2026-10-30-001: no longer passes the current screen", out)
        self.assertIn("supersede or retire it", out)

    def test_strays_are_reported(self):
        self.ok(self.r.add())
        (self.r.leaf("MIND-2026-10-30-001").parent / "stray.md").write_text("x\n")
        result = self.ok(self.r.run("check"))
        self.assertIn("REPORT strays : 1 files under archives/mind/", result.stdout)

    def test_every_file_and_directory_is_private(self):
        previous = os.umask(0)
        try:
            self.ok(self.r.add())
        finally:
            os.umask(previous)
        for rel, mode in (("MIND.md", 0o600), ("archives", 0o700), ("archives/mind", 0o700),
                          ("archives/mind/MIND-2026-10-30-001.md", 0o600), ("logs", 0o700), ("logs/mind", 0o700),
                          ("logs/mind/ledger.jsonl", 0o600), ("logs/mind.lock", 0o600)):
            with self.subTest(path=rel):
                self.assertEqual(stat.S_IMODE((self.r.room / rel).stat().st_mode), mode)

    def test_no_output_carries_a_session_identifier(self):
        self.ok(self.r.add())
        for args in (("show",), ("check",), ("read", "MIND-2026-10-30-001")):
            result = self.ok(self.r.run(*args))
            self.assertNotIn(SESSION, result.stdout + result.stderr)
        self.assertNotIn(SESSION, (self.r.room / "MIND.md").read_text())

    def test_reading_runs_no_git_and_check_does(self):
        self.ok(self.r.add())
        with mock.patch.object(mind.subprocess, "run", side_effect=AssertionError("git was called")):
            self.assertEqual(in_process(self.r, "show")[0], 0)
            self.assertEqual(in_process(self.r, "read", "MIND-2026-10-30-001")[0], 0)
            self.assertEqual(mind.verify(self.r.room, mind.read_registry(self.r.registry))[1], [])
        self.assertIn("PASS out-of-git", self.ok(self.r.run("check")).stdout)

    def test_minds_live_out_of_git(self):
        if subprocess.run(["git", "--version"], capture_output=True).returncode != 0:
            self.skipTest("git is not installed")
        subprocess.run(["git", "init", "-q", str(self.r.room)], check=True)
        self.refused(self.r.add(), "not ignored by Git")
        self.assertFalse((self.r.room / mind.INDEX).exists())
        self.assertEqual(list(self.r.room.glob("archives/mind/*")), [])
        (self.r.room / ".gitignore").write_text("/MIND.md\n/archives/\n/logs/\n")
        self.ok(self.r.add())
        self.assertIn("PASS out-of-git", self.ok(self.r.run("check")).stdout)
        (self.r.room / ".gitignore").write_text("/archives/\n/logs/\n")
        self.failed_check("FAIL out-of-git", "MIND.md is not ignored by Git")

    # -- the Git check fails closed ---------------------------------------------
    def fake_git(self, script: str) -> dict:
        """A PATH whose only git is this shell script; the env for a run of mind.py."""
        bin_dir = Path(self.tmp.name) / "fakebin"
        bin_dir.mkdir(exist_ok=True)
        git = bin_dir / "git"
        git.write_text("#!/bin/sh\n" + script)
        git.chmod(0o755)
        return dict(os.environ, PATH=str(bin_dir))

    def test_f1_no_git_on_path_is_a_refusal(self):
        empty = Path(self.tmp.name) / "empty-bin"
        empty.mkdir()
        result = self.r.add(env=dict(os.environ, PATH=str(empty)))
        self.refused(result, "Git is not installed")
        self.assertEqual(self.r.files(), [])

    def test_f1_a_git_that_does_not_answer_is_a_refusal(self):
        env = self.fake_git(f"exec {shutil.which('sleep')} 5\n")
        with mock.patch.dict(os.environ, {"PATH": env["PATH"]}), mock.patch.object(mind, "GIT_TIMEOUT", 0.3):
            problems = mind.git_exposed(self.r.room, [self.r.room / mind.INDEX])
        self.assertEqual(len(problems), 1)
        self.assertIn("gave no answer within 0.3 seconds", problems[0])

    def test_f1_a_check_ignore_that_does_not_answer_is_a_refusal(self):
        subprocess.run(["git", "init", "-q", str(self.r.room)], check=True)
        real = subprocess.run

        def fake(cmd, **kw):
            if "check-ignore" in cmd:
                raise subprocess.TimeoutExpired(cmd, kw.get("timeout"))
            if "--show-toplevel" in cmd:
                return subprocess.CompletedProcess(cmd, 0, str(self.r.room) + "\n", "")
            return subprocess.CompletedProcess(cmd, 0, "true\n", "")
        with mock.patch.object(mind.subprocess, "run", side_effect=fake):
            problems = mind.git_exposed(self.r.room, [self.r.room / mind.INDEX])
        self.assertEqual(problems, [f"git check-ignore gave no answer within {mind.GIT_TIMEOUT:g} seconds"])
        self.assertIs(subprocess.run, real)

    def test_f1_a_broken_repository_is_a_refusal(self):
        subprocess.run(["git", "init", "-q", str(self.r.room)], check=True)
        (self.r.room / ".gitignore").write_text("/MIND.md\n/archives/\n/logs/\n")
        real_git = shutil.which("git")
        self.assertIsNotNone(real_git)
        bin_dir = self.r.base / "ceiling-bin"
        bin_dir.mkdir()
        wrapper = bin_dir / "git"
        wrapper.write_text(
            "#!/bin/sh\nGIT_CEILING_DIRECTORIES="
            + shlex.quote(str(self.r.base))
            + " exec "
            + shlex.quote(real_git)
            + ' "$@"\n'
        )
        wrapper.chmod(0o755)
        env = dict(os.environ, PATH=str(bin_dir))
        head = self.r.room / ".git" / "HEAD"
        head.write_text("not a ref\n")                          # Git now says "not a git repository" here
        self.refused(self.r.add(env=env), "a broken repository is not proof of being outside Git")
        head.write_text("ref: refs/heads/main\n")
        (self.r.room / ".git" / "config").write_text("[[[ broken\n")
        self.refused(self.r.add(env=env), "git rev-parse failed (exit 128")
        self.assertFalse((self.r.room / mind.INDEX).exists())
        self.assertEqual(list(self.r.room.glob("archives/mind/*")), [])

    def test_f1_a_broken_inner_repository_is_refused_with_valid_parent(self):
        subprocess.run(["git", "init", "-q", str(self.r.base)], check=True)
        (self.r.base / ".gitignore").write_text(
            "/room/MIND.md\n/room/archives/\n/room/logs/\n"
        )
        subprocess.run(["git", "init", "-q", str(self.r.room)], check=True)
        head = self.r.room / ".git" / "HEAD"
        head.write_text("not a ref\n")
        inside = subprocess.run(
            ["git", "-C", str(self.r.room), "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            check=True,
        )
        top = subprocess.run(
            ["git", "-C", str(self.r.room), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        ignored = subprocess.run(
            ["git", "-C", str(self.r.room), "check-ignore", "-q", str(self.r.room / mind.INDEX)],
            check=False,
        )
        self.assertEqual(inside.stdout.strip(), "true")
        self.assertEqual(Path(top.stdout.strip()), self.r.base)
        self.assertEqual(ignored.returncode, 0)
        self.refused(self.r.add(), "a broken repository is not proof of being outside Git")
        self.assertFalse((self.r.room / mind.INDEX).exists())
        self.assertEqual(list(self.r.room.glob("archives/mind/*")), [])

        shutil.rmtree(self.r.room / ".git")
        self.ok(self.r.add())

    def test_f1_a_broken_nearest_ancestor_is_refused(self):
        outer = Path(self.tmp.name) / "outer"
        middle = outer / "middle"
        outer.mkdir()
        subprocess.run(["git", "init", "-q", str(outer)], check=True)
        (outer / ".gitignore").write_text(
            "/middle/room/MIND.md\n/middle/room/archives/\n/middle/room/logs/\n"
        )
        subprocess.run(["git", "init", "-q", str(middle)], check=True)
        room = Room(middle)
        head = middle / ".git" / "HEAD"
        head.write_text("not a ref\n")

        inside = subprocess.run(
            ["git", "-C", str(room.room), "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            check=True,
        )
        top = subprocess.run(
            ["git", "-C", str(room.room), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        ignored = subprocess.run(
            ["git", "-C", str(room.room), "check-ignore", "-q", str(room.room / mind.INDEX)],
            check=False,
        )
        self.assertFalse((room.room / ".git").exists())
        self.assertEqual(inside.stdout.strip(), "true")
        self.assertEqual(Path(top.stdout.strip()), outer)
        self.assertEqual(ignored.returncode, 0)
        self.refused(room.add(), "nearest .git marker", "broken repository")
        self.assertFalse((room.room / mind.INDEX).exists())
        self.assertEqual(list(room.room.glob("archives/mind/*")), [])

    def test_f1_valid_nearer_repository_ignores_broken_higher_ancestor(self):
        outer = Path(self.tmp.name) / "outer"
        middle = outer / "middle"
        outer.mkdir()
        subprocess.run(["git", "init", "-q", str(outer)], check=True)
        subprocess.run(["git", "init", "-q", str(middle)], check=True)
        room = Room(middle)
        (middle / ".gitignore").write_text("/room/MIND.md\n/room/archives/\n/room/logs/\n")
        (outer / ".git" / "HEAD").write_text("not a ref\n")

        top = subprocess.run(
            ["git", "-C", str(room.room), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(Path(top.stdout.strip()), middle)
        self.ok(room.add())

    def test_f1_valid_worktree_git_file_allows_ignored_writes(self):
        repository = self.r.base / "worktree-source"
        subprocess.run(["git", "init", "-q", str(repository)], check=True)
        subprocess.run(["git", "-C", str(repository), "config", "user.name", "Synthetic Test"], check=True)
        subprocess.run(
            ["git", "-C", str(repository), "config", "user.email", "synthetic@example.invalid"],
            check=True,
        )
        (repository / "seed").write_text("synthetic\n")
        subprocess.run(["git", "-C", str(repository), "add", "seed"], check=True)
        subprocess.run(["git", "-C", str(repository), "commit", "-qm", "seed"], check=True)
        shutil.rmtree(self.r.room)
        subprocess.run(
            ["git", "-C", str(repository), "worktree", "add", "-q", "--detach", str(self.r.room)],
            check=True,
        )
        self.assertTrue((self.r.room / ".git").is_file())
        (self.r.room / ".gitignore").write_text("/MIND.md\n/archives/\n/logs/\n")
        self.ok(self.r.add())

    def test_f1_only_a_positive_answer_passes(self):
        path = shlex.quote(str(self.r.room))
        (self.r.room / ".git").mkdir()
        cases = {
            "rev-parse says false": ('echo false\n', "not 'true'"),
            "rev-parse fails otherwise": ('echo "fatal: something else" >&2; exit 128\n', "git rev-parse failed (exit 128: fatal: something else)"),
            "check-ignore errors": (
                'case "$4" in --is-inside-work-tree) echo true;; '
                f'--show-toplevel) echo {path};; *) echo "fatal: boom" >&2; exit 128;; esac\n',
                                    "git check-ignore failed for MIND.md"),
        }
        for label, (script, words) in cases.items():
            with self.subTest(label):
                self.refused(self.r.add(env=self.fake_git(script)), words)
                self.assertEqual(self.r.files(), [])
        ignored = self.fake_git(
            'case "$4" in --is-inside-work-tree) echo true;; '
            f'--show-toplevel) echo {path};; *) exit 0;; esac\n'
        )
        self.ok(self.r.add(env=ignored))


class LegacyStateGuard(unittest.TestCase):
    """The shared guard is metadata-only and never mutates legacy evidence."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="state-guard-")
        self.room = Path(self.tmp.name)
        spec = importlib.util.spec_from_file_location("state_guard_test", MIND.parents[1] / "statepaths.py")
        self.guard = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.guard)

    def tearDown(self):
        self.tmp.cleanup()

    def test_missing_parent_and_missing_leaf_create_nothing(self):
        self.guard.require_absent_legacy(self.room, Path("storage/mind.lock"))
        self.assertEqual(list(self.room.iterdir()), [])
        (self.room / "storage").mkdir()
        self.guard.require_absent_legacy(self.room, Path("storage/mind.lock"))
        self.assertEqual(list((self.room / "storage").iterdir()), [])

    def test_existing_final_node_is_always_refused(self):
        old = self.room / "storage/mind.lock"
        old.parent.mkdir()
        old.write_bytes(b"retained")
        before = old.stat()
        with self.assertRaises(self.guard.StatePathError):
            self.guard.require_absent_legacy(self.room, Path("storage/mind.lock"))
        self.assertEqual((old.stat().st_ino, old.read_bytes()), (before.st_ino, b"retained"))

    def test_absolute_empty_and_parent_escape_fail_before_inspection(self):
        for value in (Path("/outside"), Path("."), Path("../outside"), Path("a/../outside")):
            with self.subTest(path=str(value)), mock.patch.object(Path, "lstat") as inspect:
                with self.assertRaises(self.guard.StatePathError):
                    self.guard.require_absent_legacy(self.room, value)
                inspect.assert_not_called()

    def test_metadata_error_is_not_absence(self):
        with mock.patch.object(Path, "lstat", side_effect=PermissionError("synthetic refusal")):
            with self.assertRaisesRegex(self.guard.StatePathError, "cannot be inspected"):
                self.guard.require_absent_legacy(self.room, Path("storage/mind.lock"))
        self.assertEqual(list(self.room.iterdir()), [])


class MindLockLocation(unittest.TestCase):
    """Real lock/write calls in synthetic rooms; no installed mind changes."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="mind-lock-location-")
        self.base = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def room(self, name):
        base = self.base / name
        base.mkdir()
        return Room(base)

    def test_fresh_write_uses_only_private_logs_lock_even_with_open_umask(self):
        room = self.room("fresh")
        previous = os.umask(0)
        try:
            result = room.add()
        finally:
            os.umask(previous)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((room.room / "storage").exists())
        for path, mode in ((room.room / "logs", 0o700), (room.room / "logs/mind.lock", 0o600)):
            self.assertEqual(path.stat().st_mode & 0o777, mode)

    def test_every_legacy_lock_node_blocks_new_writes_without_changing_it(self):
        for kind in ("file", "directory", "symlink", "fifo"):
            with self.subTest(kind=kind):
                room = self.room(kind)
                old = room.room / "storage/mind.lock"
                old.parent.mkdir()
                target = room.room / "not-created"
                if kind == "file":
                    old.write_bytes(b"retained old lock")
                elif kind == "directory":
                    old.mkdir()
                elif kind == "symlink":
                    old.symlink_to(target)
                else:
                    os.mkfifo(old)
                before = old.lstat()
                result = room.add()
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn("legacy state", result.stderr)
                after = old.lstat()
                self.assertEqual((before.st_dev, before.st_ino, before.st_mode, before.st_size, before.st_mtime_ns),
                                 (after.st_dev, after.st_ino, after.st_mode, after.st_size, after.st_mtime_ns))
                self.assertFalse((room.room / "logs").exists())
                self.assertFalse((room.room / "MIND.md").exists())
                self.assertFalse((room.room / "archives").exists())
                self.assertFalse(target.exists())
                if kind == "file":
                    self.assertEqual(old.read_bytes(), b"retained old lock")
                if kind == "symlink":
                    self.assertEqual(os.readlink(old), str(target))

    def test_unsafe_legacy_parent_is_not_mistaken_for_absence(self):
        for kind in ("file", "dangling-link", "directory-link"):
            with self.subTest(kind=kind):
                room = self.room(kind)
                parent = room.room / "storage"
                target = room.room / "legacy-target"
                if kind == "file":
                    parent.write_bytes(b"retained parent")
                else:
                    if kind == "directory-link":
                        target.mkdir()
                    parent.symlink_to(target)
                before = parent.lstat()
                result = room.add()
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn("legacy state parent", result.stderr)
                after = parent.lstat()
                self.assertEqual((before.st_ino, before.st_mode, before.st_mtime_ns),
                                 (after.st_ino, after.st_mode, after.st_mtime_ns))
                self.assertFalse((room.room / "logs").exists())
                self.assertFalse((room.room / "MIND.md").exists())

    def test_unsearchable_legacy_parent_refuses_without_new_lock(self):
        if os.geteuid() == 0:
            self.skipTest("requires ordinary-user permission enforcement")
        room = self.room("unsearchable")
        parent = room.room / "storage"
        parent.mkdir()
        parent.chmod(0)
        try:
            result = room.add()
        finally:
            parent.chmod(0o700)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("legacy state cannot be inspected", result.stderr)
        self.assertFalse((room.room / "logs").exists())

    def test_live_legacy_flock_is_never_replaced_by_a_new_lock(self):
        room = self.room("legacy-held")
        old = room.room / "storage/mind.lock"
        old.parent.mkdir()
        with old.open("w") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            before = old.stat().st_ino
            result = room.add()
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertEqual(old.stat().st_ino, before)
            self.assertFalse((room.room / "logs").exists())

    def test_fresh_process_holds_the_exact_shared_logs_inode(self):
        room = self.room("new-held")
        code = ("import importlib.util, pathlib, sys; "
                "s=importlib.util.spec_from_file_location('mind',sys.argv[1]); "
                "m=importlib.util.module_from_spec(s); s.loader.exec_module(m); "
                "ctx=m.room_lock(pathlib.Path(sys.argv[2])); ctx.__enter__(); "
                "print('held',flush=True); sys.stdin.readline(); ctx.__exit__(None,None,None)")
        child = subprocess.Popen([sys.executable, "-I", "-B", "-c", code, str(MIND), str(room.room)],
                                 stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(child.stdout, selectors.EVENT_READ)
                self.assertTrue(selector.select(5), "lock holder did not become ready")
                self.assertEqual(child.stdout.readline(), "held\n")
            path = room.room / "logs/mind.lock"
            inode = path.stat().st_ino
            with path.open("a") as other:
                with self.assertRaises(BlockingIOError):
                    fcntl.flock(other.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            child.communicate("release\n", timeout=5)
            self.assertEqual(child.returncode, 0)
            with mind.room_lock(room.room):
                self.assertEqual(path.stat().st_ino, inode)
        finally:
            if child.poll() is None:
                child.kill()
                child.communicate(timeout=5)

    def test_reviewed_fixture_relocation_preserves_the_lock_inode(self):
        room = self.room("relocated")
        old = room.room / "storage/mind.lock"
        old.parent.mkdir()
        old.write_bytes(b"retained lock fixture")
        before = old.stat()
        new = room.room / "logs/mind.lock"
        new.parent.mkdir(mode=0o700)
        # A fixture's explicit relocation is not an automatic production migrator.
        old.rename(new)
        with mind.room_lock(room.room):
            self.assertEqual((new.stat().st_dev, new.stat().st_ino), (before.st_dev, before.st_ino))
            self.assertEqual(new.read_bytes(), b"retained lock fixture")
        self.assertFalse(old.exists())

    def test_legacy_lock_does_not_block_read_only_commands(self):
        room = self.room("read-only")
        old = room.room / "storage/mind.lock"
        old.parent.mkdir()
        old.write_bytes(b"preserved")
        for args in (("check",), ("show",)):
            self.assertEqual(room.run(*args).returncode, 0, args)
        self.assertFalse((room.room / "logs").exists())
        self.assertEqual(old.read_bytes(), b"preserved")



DOCTOR_SID = "0000d0c0-0000-4000-8000-000000000001"
CONTRACTOR_SID = "0000c1a0-0000-4000-8000-000000000002"
CODEX_SID = "0000c0de-0000-4000-8000-000000000003"


class BindingTests(unittest.TestCase):
    """add and retire write only as the caller: myself.py's resolution, the canonical registry, and one seam."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.r = Room(self.base, keys=())
        rows = [("session-doctor", DOCTOR_SID, "claude"), ("claudine-colbert", CONTRACTOR_SID, "claude"),
                ("joe-codex", CODEX_SID, "codex")]
        self.r.registry.write_text(json.dumps({"identities": [
            {"key": k, "person": f"Person {k}", "role": "Role", "room": str(self.r.room), "session_id": sid,
             "provider": provider} for k, sid, provider in rows]}))
        self.myself = mind.sibling("myself")

    def tearDown(self):
        self.tmp.cleanup()

    def ok(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def refused(self, result, *words):
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        for word in words:
            self.assertIn(word, result.stderr)
        return result

    def nothing_written(self):
        self.assertEqual(self.r.files(), [])
        self.assertFalse((self.r.room / "logs").exists())

    def body(self) -> Path:
        path = self.base / "idea.md"
        path.write_text(IDEA, encoding="utf-8")
        return path

    def add_args(self, agent="session-doctor"):
        return ("add", "--agent", agent, "--title", "Evidence outranks recollection", "--body", str(self.body()))

    # -- the seam: a resident writes only as itself ----------------------------
    def test_add_as_another_resident_is_refused(self):
        self.refused(self.r.add(agent="session-doctor", caller="claudine-colbert"),
                     "the caller is 'claudine-colbert', not --agent 'session-doctor'")
        self.nothing_written()

    def test_retire_of_another_residents_leaf_is_refused_by_the_binding(self):
        self.ok(self.r.add(agent="session-doctor"))
        before = self.r.files(), (self.r.room / "MIND.md").read_bytes()
        self.refused(self.r.run("retire", "--agent", "session-doctor", "MIND-2026-10-30-001",
                                caller="claudine-colbert"), "a resident writes only as itself")
        self.assertEqual((self.r.files(), (self.r.room / "MIND.md").read_bytes()), before)
        self.assertEqual(self.r.ids(), ["MIND-2026-10-30-001"])

    def test_a_resident_writes_and_retires_as_itself_through_the_seam(self):
        self.ok(self.r.add(agent="claudine-colbert"))
        self.ok(self.r.run("retire", "--agent", "claudine-colbert", "MIND-2026-10-30-001"))
        self.assertEqual([r["agent"] for r in self.r.ledger()], ["claudine-colbert", "claudine-colbert"])

    def test_show_read_and_check_stay_open_without_any_caller(self):
        self.ok(self.r.add())
        self.ok(self.r.run("show", caller=None))
        self.ok(self.r.run("read", "MIND-2026-10-30-001", caller=None))
        self.ok(self.r.run("check", caller=None))

    def test_the_seam_value_must_be_a_registry_key(self):
        self.refused(self.r.add(caller="Not A Key"), "MIND_TEST_CALLER is not a registry key")
        self.nothing_written()

    # -- the seam's three conditions, each refused where it fails -----------------
    def test_seam_refused_with_the_canonical_registry(self):
        with mock.patch.object(mind, "REGISTRY", self.r.registry):
            rc, _, err = in_process(self.r, *self.add_args())
        self.assertEqual(rc, 2)
        self.assertIn("honoured only in a synthetic room: the registry is the room's canonical one", err)
        self.nothing_written()

    def test_seam_refused_when_a_registry_session_is_not_synthetic(self):
        data = json.loads(self.r.registry.read_text())
        data["identities"].append({"key": "real-resident", "room": "/elsewhere",
                                   "session_id": "1234abcd-0000-4000-8000-000000000009", "provider": "claude"})
        self.r.registry.write_text(json.dumps(data))
        self.refused(self.r.add(), "a registry session is not a synthetic 0000 identifier")
        self.nothing_written()

    def test_seam_refused_when_a_registry_row_has_no_session(self):
        data = json.loads(self.r.registry.read_text())
        data["identities"].append({"key": "no-session", "room": str(self.r.room)})
        self.r.registry.write_text(json.dumps(data))
        self.refused(self.r.add(), "a registry session is not a synthetic 0000 identifier")
        self.nothing_written()

    def test_seam_refused_in_the_tools_own_room(self):
        with mock.patch.object(mind, "SESSIONS", self.r.room):
            rc, _, err = in_process(self.r, *self.add_args())
        self.assertEqual(rc, 2)
        self.assertIn("the room is this tool's own room", err)
        self.nothing_written()

    def test_seam_refused_in_a_room_the_canonical_registry_names(self):
        canonical = self.base / "canonical.json"
        canonical.write_text(json.dumps({"identities": [{"key": "a-resident", "room": str(self.r.room),
                                                         "session_id": "1234abcd-0000-4000-8000-000000000009"}]}))
        with mock.patch.object(mind, "REGISTRY", canonical):
            rc, _, err = in_process(self.r, *self.add_args())
        self.assertEqual(rc, 2)
        self.assertIn("the room is named by the canonical registry", err)
        self.nothing_written()

    def test_seam_refused_when_the_canonical_registry_is_unreadable(self):
        canonical = self.base / "canonical.json"
        canonical.write_text("{not json")
        with mock.patch.object(mind, "REGISTRY", canonical):
            rc, _, err = in_process(self.r, *self.add_args())
        self.assertEqual(rc, 2)
        self.assertIn("the canonical registry is unreadable, so its rooms cannot be ruled out", err)
        self.nothing_written()

    def test_an_absent_canonical_registry_names_no_room(self):
        with mock.patch.object(mind, "REGISTRY", self.base / "absent.json"):
            rc, out, err = in_process(self.r, *self.add_args())
        self.assertEqual(rc, 0, err)
        self.assertIn("written by session-doctor", out)

    # -- the real route: myself.py's resolve_caller and the canonical registry ----
    def real(self, caller, errors=(), agent="session-doctor", command="add"):
        """One in-process write with no seam: the canonical registry is the room's, and
        myself.py's resolve_caller answers as given. Nothing else of myself.py is replaced."""
        resolved = mock.Mock(return_value=(caller, (), list(errors)))
        args = self.add_args(agent) if command == "add" else ("retire", "--agent", agent, "MIND-2026-10-30-001")
        with mock.patch.object(mind, "REGISTRY", self.r.registry), \
                mock.patch.object(self.myself, "resolve_caller", resolved), \
                mock.patch.object(mind, "sibling", return_value=self.myself):
            rc, out, err = in_process(self.r, *args, caller=None)
        self.assertEqual(resolved.call_count, 1)
        return rc, out, err

    def signal(self, provider, sid):
        return self.myself.CallerSignal(provider, sid, "/proc/self/environ::FIXTURE")

    def test_real_route_writes_as_the_resolved_resident(self):
        rc, out, err = self.real(self.signal("claude", DOCTOR_SID))
        self.assertEqual(rc, 0, err)
        self.assertIn("written by session-doctor", out)

    def test_real_route_refuses_another_residents_key(self):
        rc, _, err = self.real(self.signal("claude", CONTRACTOR_SID), agent="session-doctor")
        self.assertEqual(rc, 2)
        self.assertIn("the caller is 'claudine-colbert', not --agent 'session-doctor'", err)
        self.nothing_written()

    def test_real_route_retire_refuses_another_residents_key(self):
        self.ok(self.r.add(agent="session-doctor"))
        rc, _, err = self.real(self.signal("claude", CONTRACTOR_SID), agent="session-doctor", command="retire")
        self.assertEqual(rc, 2)
        self.assertIn("a resident writes only as itself", err)
        self.assertEqual(self.r.ids(), ["MIND-2026-10-30-001"])

    def test_real_route_works_for_a_codex_resident(self):
        rc, out, err = self.real(self.signal("codex", CODEX_SID), agent="joe-codex")
        self.assertEqual(rc, 0, err)
        self.assertIn("written by joe-codex", out)

    def test_real_route_refuses_an_unverified_caller(self):
        rc, _, err = self.real(None, errors=["no provider-bound native session signal was found"])
        self.assertEqual(rc, 2)
        self.assertIn("the caller's identity is unverified (1 signal problems)", err)
        self.nothing_written()

    def test_real_route_refuses_a_caller_with_any_signal_problem(self):
        rc, _, err = self.real(self.signal("claude", DOCTOR_SID), errors=["a disagreeing signal"])
        self.assertEqual(rc, 2)
        self.assertIn("the caller's identity is unverified", err)
        self.nothing_written()

    def test_real_route_refuses_an_unregistered_caller(self):
        rc, _, err = self.real(self.signal("claude", "0000eeee-0000-4000-8000-00000000000e"))
        self.assertEqual(rc, 2)
        self.assertIn("the caller matches 0 keyed registry rows", err)
        self.nothing_written()

    def test_real_route_refuses_a_provider_mismatch(self):
        rc, _, err = self.real(self.signal("codex", DOCTOR_SID))
        self.assertEqual(rc, 2)
        self.assertIn("the caller matches 0 keyed registry rows", err)

    def test_real_route_refuses_an_ambiguous_caller(self):
        data = json.loads(self.r.registry.read_text())
        data["identities"].append(dict(data["identities"][0], key="a-second-key"))
        self.r.registry.write_text(json.dumps(data))
        rc, _, err = self.real(self.signal("claude", DOCTOR_SID))
        self.assertEqual(rc, 2)
        self.assertIn("the caller matches 2 keyed registry rows", err)
        self.nothing_written()

    def test_real_route_never_prints_a_session_id(self):
        for caller in (self.signal("claude", CONTRACTOR_SID), self.signal("claude", "0000eeee-0000-4000-8000-00000000000e")):
            _, out, err = self.real(caller)
            for sid in (DOCTOR_SID, CONTRACTOR_SID, "0000eeee-0000-4000-8000-00000000000e"):
                self.assertNotIn(sid, out + err)

    def test_without_the_seam_another_registry_is_refused(self):
        self.refused(self.r.add(caller=None), "another registry serves tests only, through the test seam")
        self.nothing_written()

    def test_a_missing_sibling_refuses_rather_than_guessing(self):
        with self.assertRaises(mind.Refused) as caught:
            mind.sibling("no-such-script")
        self.assertIn("cannot be verified", str(caught.exception))

    def test_resolution_is_myself_resolve_caller_from_the_parent_process(self):
        resolved = mock.Mock(return_value=(None, (), ["none"]))
        with mock.patch.object(mind, "REGISTRY", self.r.registry), \
                mock.patch.object(self.myself, "resolve_caller", resolved), \
                mock.patch.object(mind, "sibling", return_value=self.myself) as loaded:
            in_process(self.r, *self.add_args(), caller=None)
        loaded.assert_called_once_with("myself")
        environ, proc_root, start_pid, lock_root = resolved.call_args.args
        live = self.myself.CheckPaths.live()
        self.assertEqual((proc_root, start_pid, lock_root), (live.proc_root, os.getppid(), live.codex_lock_root))
        self.assertIs(environ, os.environ)

    def test_the_registry_match_agrees_with_myself_identity_registry_leg(self):
        """Contract: for the same resolved caller, mind's key is the key myself.py's identity-registry leg
        passes, and mind refuses wherever that leg does not pass. Roster and bindings are absent, so
        myself.py has no session root and searches no store."""
        absent = self.base / "absent"
        paths = self.myself.CheckPaths(registry=self.r.registry, roster=absent / "roster.json",
                                       bindings=absent / "bindings.json", codex_lock_root=absent,
                                       proc_root=absent / "proc")
        data = json.loads(self.r.registry.read_text())
        data["identities"].append(dict(data["identities"][1], key="claudine-twin"))
        self.r.registry.write_text(json.dumps(data))
        cases = [self.signal("claude", DOCTOR_SID), self.signal("codex", CODEX_SID),
                 self.signal("claude", CONTRACTOR_SID), self.signal("claude", "0000eeee-0000-4000-8000-00000000000e"),
                 self.signal("codex", DOCTOR_SID)]
        for caller in cases:
            with self.subTest(caller=caller.provider + ":" + caller.session_id[:8]):
                with mock.patch.object(self.myself, "resolve_caller", return_value=(caller, (), [])):
                    report = self.myself.run_check(paths, environ={}, start_pid=None)
                legs = {leg.name: leg for leg in report.legs}
                self.assertEqual(legs["native session body"].status, "undetermined")
                leg = legs["identity registry"]
                args = mock.Mock(registry=self.r.registry, room=self.r.room)
                with mock.patch.object(mind, "REGISTRY", self.r.registry), \
                        mock.patch.object(self.myself, "resolve_caller", return_value=(caller, (), [])), \
                        mock.patch.object(mind, "sibling", return_value=self.myself), \
                        mock.patch.dict(os.environ, {}, clear=True):
                    try:
                        key = mind.caller_key(args)
                    except mind.Refused:
                        key = None
                if leg.status == "pass":
                    self.assertEqual("key=" + str(key), leg.detail.split(";")[0])
                else:
                    self.assertIsNone(key)


if __name__ == "__main__":
    unittest.main(verbosity=1)
