#!/usr/bin/env python3
"""Tests for ops/lib/scripts/mind.py, in synthetic rooms only. Standard library only.

Every case builds its own room, registry and change files in a temporary
directory; no real room, mind or body is touched. Each of Claudio's section 130
items that the port fixes has a test named for it. Run:

    python3 -I -B tools/test/test_mind.py
"""
import importlib.util
import json
import os
import re
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

CORE = {"layer": "core", "kind": "identity", "text": "I chose the name Shannon: what survives a lossy channel.",
        "event": "naming", "[words sha256=0e87632cd46bd4907c516317eb6d81fe0f921a23c7643018f21292894b470681]": "2026-08-09", "source": "Receipts/naming.md"}
LESSON = {"layer": "lesson", "text": "Measure before explaining.", "event": "a claim falsified by looking",
          "[words sha256=0e87632cd46bd4907c516317eb6d81fe0f921a23c7643018f21292894b470681]": "2026-08-09", "source": "Receipts/x.md", "applies_when": "about to explain",
          "not_when": "the measurement is in hand"}
COMMIT = {"layer": "commitment", "text": "Run Joy's cutover.", "event": "Kevin asked", "[words sha256=0e87632cd46bd4907c516317eb6d81fe0f921a23c7643018f21292894b470681]": "[words sha256=c9c37f3f041ea4694d0764b4b1dbf3d53551e7be57c4a4823ed2b6981db13c90]",
          "source": "Receipts/joy.md", "owner": "Shannon"}


class Room:
    def __init__(self, base: Path, keys=("session-doctor", "claudine-colbert"), extra=()):
        self.base = base
        self.room = base / "room"
        self.room.mkdir()
        self.registry = base / "registry.json"
        identities = [{"key": k, "person": f"Person {k}", "role": "Role", "room": str(self.room),
                       "session_id": "never-printed"} for k in keys] + list(extra)
        self.registry.write_text(json.dumps({"identities": identities}))
        self.minute = 0

    def run(self, *args, stdin=None, env=None):
        self.minute += 1
        cmd = [sys.executable, "-I", "-B", str(MIND), "--room", str(self.room), "--registry", str(self.registry),
               "--now", f"2026-10-30T17:{self.minute:02d}:00Z", *args]
        return subprocess.run(cmd, capture_output=True, text=True, input=stdin, timeout=60, env=env)

    def preview(self, key, changes, stdin=None, env=None) -> str:
        """The binding preview prints, or '' when preview refuses."""
        result = self.run("preview", key, "--changes", changes, stdin=stdin, env=env)
        m = re.search(r"^binding: ([0-9a-f]{64})$", result.stdout, re.M)
        return m.group(1) if m else ""

    def changes(self, obj, raw: bytes = None) -> str:
        path = self.base / f"changes-{self.minute}-{len(list(self.base.glob('changes-*')))}.json"
        path.write_bytes(raw if raw is not None else json.dumps(obj).encode("utf-8"))
        return str(path)

    def write(self, obj, key="session-doctor", yes="yes, write it", by="claudine-colbert", env=None):
        """As a writer does it: preview, then write with the binding the preview printed."""
        path = self.changes(obj)
        binding = self.preview(key, path, env=env) or "0" * 64
        return self.run("write", key, "--changes", path, "--preview", binding, "--yes", yes, "--by", by, env=env)

    def pointer(self) -> dict:
        return mind.read_pointer(self.room)

    def leaf(self, key="session-doctor") -> Path:
        return self.room / self.pointer()[key][0]

    def files(self) -> list:
        return sorted(p.relative_to(self.room).as_posix() for p in self.room.rglob("*") if p.is_file()
                      and p.name != "mind.lock")

    def plant(self, head: dict, entries: list, key="session-doctor") -> str:
        """Write a hand-made leaf and point MIND.md at it, as a forger would."""
        data = mind.render_leaf(head, entries).encode("utf-8")
        name = f"MIND-{key}-{head['written'][:10]}-{mind.sha256(data)[:8]}.md"
        (self.room / mind.SURFACES / name).write_bytes(data)
        lines = self.pointer()
        lines[key] = (f"{mind.SURFACES}/{name}", mind.sha256(data))
        (self.room / mind.POINTER).write_text(mind.pointer_text(lines))
        return name


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

    def genesis(self):
        self.ok(self.r.write({"add": [CORE, LESSON, COMMIT]}))
        return self.r.leaf()

    # -- the basic loop ----------------------------------------------------
    def test_write_check_show_round_trip(self):
        leaf = self.genesis()
        self.ok(self.r.run("check"))
        shown = self.ok(self.r.run("show", "session-doctor"))
        self.assertEqual(shown.stdout.encode("utf-8"), leaf.read_bytes())
        text = leaf.read_text()
        self.assertIn('yes: 2026-10-30, "yes, write it"', text)
        self.assertIn("by: claudine-colbert", text)
        self.assertIn("predecessor: none", text)
        self.assertIn("change: add core-001, lesson-001, commitment-001", text)

    def test_c11_show_ref_binds_the_capsule_to_the_leaf_hash(self):
        leaf = self.genesis()
        ref = self.ok(self.r.run("show", "session-doctor", "--ref")).stdout.strip()
        self.assertEqual(ref, f"leaf={leaf.relative_to(self.r.room).as_posix()}|sha256={mind.sha256(leaf.read_bytes())}")

    def test_write_needs_kevins_words_and_a_registered_writer(self):
        self.refused(self.r.write({"add": [CORE]}, yes=""), "Kevin's own words")
        self.refused(self.r.write({"add": [CORE]}, yes="ok"), "Kevin's own words")
        self.refused(self.r.write({"add": [CORE]}, by="nobody-here"), "--by")
        self.assertEqual(self.r.files(), [])

    # -- Claudio's blockers ------------------------------------------------
    def test_b1_an_amendment_keeps_the_core_entry_and_carries_the_new_yes(self):
        self.genesis()
        self.ok(self.r.write({"amend": [{"id": "core-001", "text": "I chose the name Shannon, for the channel."}]},
                             yes="yes, fix the wording"))
        text = self.r.leaf().read_text()
        self.assertIn("- [core-001] I chose the name Shannon, for the channel.", text)
        self.assertIn('yes: 2026-10-30, "yes, fix the wording"', text)
        self.assertIn("change: amend core-001", text)
        self.ok(self.r.run("check"))
        history = self.ok(self.r.run("history", "session-doctor")).stdout
        self.assertIn("amend core-001", history)
        self.assertIn("add core-001", history)

    def test_b1_a_leaf_that_silently_drops_a_core_entry_fails_check(self):
        self.genesis()
        head, entries, data = mind.load_leaf(self.r.room, "session-doctor", self.r.pointer()["session-doctor"][0])
        forged = dict(head, written="2026-10-30T18:00:00Z", change="amend lesson-001",
                      predecessor=f"{self.r.pointer()['session-doctor'][0]} sha256={mind.sha256(data)}")
        self.r.plant(forged, [e for e in entries if e["id"] != "core-001"])
        self.failed_check("declares 'amend lesson-001', but the difference from its predecessor is 'retire core-001'")
        self.refused(self.r.run("show", "session-doctor"), "not served")

    def test_b2_a_retired_entry_never_revives(self):
        self.genesis()
        self.ok(self.r.write({"retire": ["commitment-001"]}, yes="yes, that is closed"))
        self.refused(self.r.write({"amend": [{"id": "commitment-001", "text": "back again"}]}), "no such entry")
        self.ok(self.r.write({"add": [COMMIT]}, yes="yes, it is open again"))
        text = self.r.leaf().read_text()
        self.assertIn("[commitment-002]", text)
        self.assertNotIn("[commitment-001]", text)
        self.ok(self.r.run("check"))

    def test_b2_a_forged_leaf_reusing_a_retired_number_fails_check(self):
        self.genesis()
        self.ok(self.r.write({"retire": ["commitment-001"]}, yes="yes, that is closed"))
        rel = self.r.pointer()["session-doctor"][0]
        head, entries, data = mind.load_leaf(self.r.room, "session-doctor", rel)
        back = dict(COMMIT, id="commitment-001", yes=head["yes"])
        back.pop("layer")
        back["layer"] = "commitment"
        forged = dict(head, written="2026-10-30T18:30:00Z", change="add commitment-001",
                      predecessor=f"{rel} sha256={mind.sha256(data)}")
        self.r.plant(forged, entries + [back])
        self.failed_check("reuses a number already issued")

    # -- Claudio's conditions ----------------------------------------------
    def test_c1_preview_shows_before_and_after_and_writes_nothing(self):
        self.genesis()
        before = self.r.files()
        result = self.ok(self.r.run("preview", "session-doctor", "--changes",
                                    self.r.changes({"amend": [{"id": "lesson-001", "text": "Measure first."}]})))
        self.assertIn("Nothing is written", result.stdout)
        self.assertIn("before:\n    - [lesson-001] Measure before explaining.", result.stdout)
        self.assertIn("after:\n    - [lesson-001] Measure first.", result.stdout)
        self.assertEqual(self.r.files(), before)

    def test_c2_an_ancestor_changed_after_it_was_written_is_detected(self):
        first = self.genesis()
        self.ok(self.r.write({"add": [dict(LESSON, text="Second lesson.")]}, yes="yes, add it"))
        os.chmod(first, 0o600)
        first.write_bytes(first.read_bytes().replace(b"Measure before", b"Measure after"))
        self.failed_check("no longer match the hash in its name")

    def test_c3_a_forged_current_leaf_fails(self):
        leaf = self.genesis()
        data = leaf.read_bytes().replace(b"Measure before", b"Measure after")
        leaf.write_bytes(data)
        lines = self.r.pointer()
        lines["session-doctor"] = (lines["session-doctor"][0], mind.sha256(data))
        (self.r.room / mind.POINTER).write_text(mind.pointer_text(lines))
        self.failed_check("no longer match the hash in its name")

    def test_c3_c4_a_leaf_from_another_mind_is_never_served(self):
        self.genesis()
        self.ok(self.r.write({"add": [CORE]}, key="claudine-colbert", yes="yes, hers too"))
        lines = self.r.pointer()
        lines["session-doctor"] = lines["claudine-colbert"]
        (self.r.room / mind.POINTER).write_text(mind.pointer_text(lines))
        self.failed_check("belongs to 'claudine-colbert', not 'session-doctor'")
        shown = self.refused(self.r.run("show", "session-doctor"), "not served")
        self.assertEqual(shown.stdout, "")

    def test_c3_a_pointer_moved_back_to_an_older_genuine_leaf_fails(self):
        first = self.genesis()
        first_sha = mind.sha256(first.read_bytes())
        self.ok(self.r.write({"retire": ["commitment-001"]}, yes="yes, closed"))
        lines = self.r.pointer()
        lines["session-doctor"] = (first.relative_to(self.r.room).as_posix(), first_sha)
        (self.r.room / mind.POINTER).write_text(mind.pointer_text(lines))
        self.failed_check("points behind the newest leaf")

    def test_c3_a_leaf_outside_the_archives_root_is_refused(self):
        leaf = self.genesis()
        for folder in ("elsewhere", "surfaces"):                # "surfaces" was the leaf home before RoR-3
            with self.subTest(folder):
                other = self.r.room / "archives" / folder
                other.mkdir(exist_ok=True)
                (other / leaf.name).write_bytes(leaf.read_bytes())
                lines = self.r.pointer()
                lines["session-doctor"] = (f"archives/{folder}/{leaf.name}", lines["session-doctor"][1])
                (self.r.room / mind.POINTER).write_text(mind.pointer_text(lines))
                self.failed_check("is not a leaf name in archives/")

    # -- RoR-3: leaves at the archives/ root, grouped by their MIND- prefix -------
    def test_ror3_leaves_sit_at_the_archives_root(self):
        leaf = self.genesis()
        self.assertEqual(leaf.parent, self.r.room / "archives")
        self.assertTrue(leaf.name.startswith("MIND-session-doctor-"))
        self.assertTrue(self.r.pointer()["session-doctor"][0].startswith("archives/MIND-session-doctor-"))
        self.ok(self.r.run("check"))

    def test_ror3_other_archive_files_are_not_minds(self):
        self.genesis()
        archives = self.r.room / "archives"
        (archives / "receipts").mkdir()
        (archives / "receipts" / "some-receipt.md").write_text("a receipt\n")
        (archives / "PoT-38854647.md").write_text("a snapshot\n")
        (archives / "README.md").write_text("not a mind\n")
        result = self.ok(self.r.run("check"))
        self.assertNotIn("outside-pointer", result.stdout)
        (archives / "MIND-nobody-2026-11-01-deadbeef.md").write_text("a stray leaf\n")
        result = self.ok(self.r.run("check"))
        self.assertIn("REPORT room outside-pointer : 1 MIND- files in archives/", result.stdout)

    def test_ror3_a_linked_leaf_name_is_never_read(self):
        leaf = self.genesis()
        archives = self.r.room / "archives"
        (archives / "receipts").mkdir()
        target = archives / "receipts" / "x.md"
        target.write_text("a receipt, not a mind\n")
        link = archives / "MIND-session-doctor-2026-11-01-deadbeef.md"
        link.symlink_to(target)
        real = mind.Path.read_bytes
        seen = []
        def spy(path):
            seen.append(Path(path))
            return real(path)
        with mock.patch.object(mind.Path, "read_bytes", autospec=True, side_effect=spy):
            ahead, outside = mind.other_leaves(self.r.room, "session-doctor", set(), mind.sha256(leaf.read_bytes()))
        self.assertIn(link.name, outside)
        self.assertNotIn(link, seen)
        self.assertNotIn(target, seen)

    def test_c4_a_resident_of_another_room_cannot_write_here(self):
        base = Path(self.tmp.name)
        self.r.registry.write_text(json.dumps({"identities": [
            {"key": "session-doctor", "person": "P", "role": "R", "room": str(base / "elsewhere")},
            {"key": "claudine-colbert", "person": "P", "role": "R", "room": str(self.r.room)}]}))
        self.refused(self.r.write({"add": [CORE]}), "registered to the room")
        self.assertEqual(self.r.files(), [])

    def test_c5_one_resident_has_one_mind(self):
        self.genesis()
        text = (self.r.room / mind.POINTER).read_text()
        line = text.splitlines()[-1]
        (self.r.room / mind.POINTER).write_text(text + line + "\n")
        self.refused(self.r.run("check"), "twice")
        self.refused(self.r.write({"add": [LESSON]}), "twice")

    def test_c5_a_key_registered_twice_is_refused(self):
        self.r.registry.write_text(json.dumps({"identities": [
            {"key": "session-doctor", "person": "P", "role": "R", "room": str(self.r.room)},
            {"key": "session-doctor", "person": "Q", "role": "R", "room": str(self.r.room)},
            {"key": "claudine-colbert", "person": "P", "role": "R", "room": str(self.r.room)}]}))
        self.refused(self.r.write({"add": [CORE]}), "registered 2 times")

    def test_c6_each_leaf_records_the_policy_it_was_written_under(self):
        leaf = self.genesis()
        self.assertIn(f"policy: {mind.policy_digest()}", leaf.read_text())
        head, entries, data = mind.load_leaf(self.r.room, "session-doctor", self.r.pointer()["session-doctor"][0])
        changed = dict(head, written="2026-10-30T19:00:00Z", policy="0" * 16, change="retire commitment-001",
                       predecessor=f"{self.r.pointer()['session-doctor'][0]} sha256={mind.sha256(data)}")
        self.r.plant(changed, [e for e in entries if e["id"] != "commitment-001"])
        result = self.ok(self.r.run("check"))
        self.assertIn(f"REPORT session-doctor policy : written under policy {'0' * 16}", result.stdout)

    def test_c7_values_are_screened_as_plain_lines(self):
        cases = {
            "newline before a short id": dict(CORE, text="see\nab12cd34 for it"),
            "tab before a long id": dict(CORE, text="see\t" + "ab12" * 8),
            "secret with a tab": dict(LESSON, text="password\t= hunter"),
            "zero-width joiner": dict(CORE, text="Shan\u200bnon"),
            "a uuid": dict(LESSON, source="0000d024-0000-4000-8000-00000000d024"),
            "a sixteen-digit hash (F6)": dict(LESSON, text="commit e75e115474f87cf1"),
            "medical": dict(LESSON, event="after the surgery"),
        }
        for label, entry in cases.items():
            with self.subTest(label):
                self.refused(self.r.write({"add": [entry]}), "nothing was written")
                self.assertEqual(self.r.files(), [])
        self.refused(self.r.write({"add": [CORE]}, yes="yes\nab12cd34"), "nothing was written")

    def test_c7_the_yes_words_are_screened(self):
        self.refused(self.r.write({"add": [CORE]}, yes="yes, token: abc"), "possible secret")

    def test_c9_leaves_survive_an_ancestor_moved_to_custody(self):
        first = self.genesis()
        self.ok(self.r.write({"retire": ["commitment-001"]}, yes="yes, closed"))
        self.ok(self.r.write({"add": [COMMIT]}, yes="yes, open again"))
        first.unlink()
        result = self.ok(self.r.run("check"))
        self.assertIn("REPORT session-doctor chain-history", result.stdout)
        self.ok(self.r.write({"retire": ["commitment-002"]}, yes="yes, closed again"))

    def test_c9_the_immediate_predecessor_must_exist(self):
        first = self.genesis()
        self.ok(self.r.write({"retire": ["commitment-001"]}, yes="yes, closed"))
        first.unlink()
        self.failed_check("is not on disk")

    def test_c10_a_change_file_that_is_not_utf8_is_refused(self):
        path = self.r.changes(None, raw=b'{"add": [{"layer": "core", "text": "\xff\xfe"}]}')
        self.refused(self.r.run("write", "session-doctor", "--changes", path, "--preview", "0" * 64, "--yes", "yes, go",
                                "--by", "claudine-colbert"), "not UTF-8")
        dup = self.r.changes(None, raw=b'{"add": [{"layer": "core", "text": "a", "text": "b"}]}')
        self.refused(self.r.run("preview", "session-doctor", "--changes", dup), "twice")
        self.assertEqual(self.r.files(), [])

    # -- rules the port keeps ----------------------------------------------
    def test_layer_rules_and_trauma_guard(self):
        cases = {
            "incident without fix": (dict(LESSON, kind="incident", closed="2026-10-29"), "incident"),
            "blame in core": (dict(CORE, text="My careless mistake defines me."), "blame words"),
            "lesson without not_when": ({k: v for k, v in LESSON.items() if k != "not_when"}, "needs not_when"),
            "commitment without owner": ({k: v for k, v in COMMIT.items() if k != "owner"}, "needs owner"),
            "core without kind": ({k: v for k, v in CORE.items() if k != "kind"}, "needs kind"),
            "owner on core": (dict(CORE, owner="me"), "cannot be set here"),
            "an id from the writer": (dict(CORE, id="core-009"), "cannot be set here"),
            "a yes inside the change": (dict(CORE, yes="2026-10-30, \"yes\""), "cannot be set here"),
            "bad date": (dict(CORE, date="2026-13-40"), "not a YYYY-MM-DD date"),
        }
        for label, (entry, words) in cases.items():
            with self.subTest(label):
                self.refused(self.r.write({"add": [entry]}), words)
        self.assertEqual(self.r.files(), [])

    def test_core_over_budget_is_refused_whole(self):
        big = [dict(CORE, text=f"Entry {i} " + "x" * 2000) for i in range(7)]
        self.refused(self.r.write({"add": big}), "over its budget")

    def test_amend_cannot_change_layer_or_change_nothing(self):
        self.genesis()
        self.refused(self.r.write({"amend": [{"id": "core-001", "layer": "bond"}]}), "cannot be set here")
        self.refused(self.r.write({"amend": [{"id": "core-001", "text": CORE["text"]}]}), "changes nothing")

    def test_a_hand_written_pointer_is_left_as_it_is(self):
        (self.r.room / mind.POINTER).write_text("# My mind, by hand\n")
        self.refused(self.r.write({"add": [CORE]}), "not a pointer this tool wrote")
        self.assertEqual((self.r.room / mind.POINTER).read_text(), "# My mind, by hand\n")

    def test_no_first_leaf_while_leaves_exist_without_a_pointer(self):
        self.genesis()
        (self.r.room / mind.POINTER).write_text(mind.POINTER_HEAD)
        self.refused(self.r.write({"add": [CORE]}), "restore the pointer first")

    def test_a_reordered_leaf_is_not_canonical(self):
        leaf = self.genesis()
        text = leaf.read_text().replace("  event: naming\n  date: 2026-08-09\n", "  date: 2026-08-09\n  event: naming\n")
        with self.assertRaises(mind.Refused):
            mind.parse_leaf(text)

    def test_leaves_and_pointer_are_private(self):
        leaf = self.genesis()
        for path in (leaf, self.r.room / mind.POINTER):
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600, path.name)

    def test_minds_live_out_of_git(self):
        if subprocess.run(["git", "--version"], capture_output=True).returncode != 0:
            self.skipTest("git is not installed")
        subprocess.run(["git", "init", "-q", str(self.r.room)], check=True)
        self.refused(self.r.write({"add": [CORE]}), "not ignored by Git")
        self.assertFalse((self.r.room / mind.POINTER).exists())
        self.assertEqual(list(self.r.room.glob("archives/MIND-*")), [])
        (self.r.room / ".gitignore").write_text("/MIND.md\n/archives/MIND-*\n/storage/\n")
        self.ok(self.r.write({"add": [CORE]}))

    # -- George's read, 10-30: F1, the Git check fails closed --------------------
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
        result = self.r.write({"add": [CORE]}, env=dict(os.environ, PATH=str(empty)))
        self.refused(result, "Git is not installed")
        self.assertEqual(self.r.files(), [])

    def test_f1_a_git_that_does_not_answer_is_a_refusal(self):
        env = self.fake_git(f"exec {shutil.which('sleep')} 5\n")
        with mock.patch.dict(os.environ, {"PATH": env["PATH"]}), mock.patch.object(mind, "GIT_TIMEOUT", 0.3):
            problems = mind.git_exposed(self.r.room, [self.r.room / mind.POINTER])
        self.assertEqual(len(problems), 1)
        self.assertIn("gave no answer within 0.3 seconds", problems[0])

    def test_f1_a_check_ignore_that_does_not_answer_is_a_refusal(self):
        real = subprocess.run

        def fake(cmd, **kw):
            if "check-ignore" in cmd:
                raise subprocess.TimeoutExpired(cmd, kw.get("timeout"))
            return subprocess.CompletedProcess(cmd, 0, "true\n", "")
        with mock.patch.object(mind.subprocess, "run", side_effect=fake):
            problems = mind.git_exposed(self.r.room, [self.r.room / mind.POINTER])
        self.assertEqual(problems, [f"git check-ignore gave no answer within {mind.GIT_TIMEOUT:g} seconds"])
        self.assertIs(subprocess.run, real)

    def test_f1_a_broken_repository_is_a_refusal(self):
        subprocess.run(["git", "init", "-q", str(self.r.room)], check=True)
        (self.r.room / ".gitignore").write_text("/MIND.md\n/archives/MIND-*\n/storage/\n")
        head = self.r.room / ".git" / "HEAD"
        head.write_text("not a ref\n")                          # Git now says "not a git repository" here
        self.refused(self.r.write({"add": [CORE]}), "a broken repository is not proof of being outside Git")
        head.write_text("ref: refs/heads/main\n")
        (self.r.room / ".git" / "config").write_text("[[[ broken\n")
        self.refused(self.r.write({"add": [CORE]}), "git rev-parse failed (exit 128")
        self.assertFalse((self.r.room / mind.POINTER).exists())
        self.assertEqual(list(self.r.room.glob("archives/MIND-*")), [])

    def test_f1_only_a_positive_answer_passes(self):
        cases = {
            "rev-parse says false": ('echo false\n', "not 'true'"),
            "rev-parse fails otherwise": ('echo "fatal: something else" >&2; exit 128\n', "git rev-parse failed (exit 128: fatal: something else)"),
            "check-ignore errors": ('case "$3" in rev-parse) echo true;; *) echo "fatal: boom" >&2; exit 128;; esac\n',
                                    "git check-ignore failed for archives/MIND-"),
        }
        for label, (script, words) in cases.items():
            with self.subTest(label):
                self.refused(self.r.write({"add": [CORE]}, env=self.fake_git(script)), words)
                self.assertEqual(self.r.files(), [])
        ignored = self.fake_git('case "$3" in rev-parse) echo true;; *) exit 0;; esac\n')
        self.ok(self.r.write({"add": [CORE]}, env=ignored))

    # -- George's read, 10-30: F2, the write is bound to the preview ------------
    def test_f2_write_needs_the_preview_binding(self):
        path = self.r.changes({"add": [CORE]})
        for extra in ((), ("--preview", "abc")):
            with self.subTest(extra=extra):
                self.refused(self.r.run("write", "session-doctor", "--changes", path, *extra, "--yes", "yes, go",
                                        "--by", "claudine-colbert"), "write needs --preview")
        self.assertEqual(self.r.files(), [])

    def test_f2_a_change_file_edited_after_the_preview_is_refused(self):
        path = self.r.changes({"add": [CORE]})
        binding = self.r.preview("session-doctor", path)
        Path(path).write_text(json.dumps({"add": [dict(CORE, text="Something Kevin never saw.")]}))
        args = ("write", "session-doctor", "--changes", path, "--yes", "yes, go", "--by", "claudine-colbert")
        self.refused(self.r.run(*args, "--preview", binding), "is not what the preview showed")
        self.assertEqual(self.r.files(), [])
        self.ok(self.r.run(*args, "--preview", self.r.preview("session-doctor", path)))
        self.assertIn("Something Kevin never saw.", self.r.leaf().read_text())

    def test_f2_layout_does_not_matter_but_content_does(self):
        compact = self.r.changes({"add": [CORE]})
        spaced = self.r.changes(None, raw=json.dumps({"add": [CORE]}, indent=4).encode())
        self.assertEqual(self.r.preview("session-doctor", compact), self.r.preview("session-doctor", spaced))
        self.assertNotEqual(self.r.preview("session-doctor", compact),
                            self.r.preview("claudine-colbert", compact))

    def test_f2_changes_from_standard_input(self):
        text = json.dumps({"add": [CORE]})
        binding = self.r.preview("session-doctor", "-", stdin=text)
        args = ("write", "session-doctor", "--changes", "-", "--preview", binding, "--yes", "yes, go", "--by", "claudine-colbert")
        self.refused(self.r.run(*args, stdin=json.dumps({"add": [LESSON]})), "is not what the preview showed")
        self.assertEqual(self.r.files(), [])
        self.ok(self.r.run(*args, stdin=text))

    def test_f2_a_moved_predecessor_is_refused(self):
        self.genesis()
        path = self.r.changes({"retire": ["commitment-001"]})
        binding = self.r.preview("session-doctor", path)
        self.ok(self.r.write({"add": [dict(LESSON, text="Another lesson.")]}, yes="yes, add it"))
        moved = self.r.pointer()["session-doctor"]
        self.refused(self.r.run("write", "session-doctor", "--changes", path, "--preview", binding, "--yes", "yes, close it",
                                "--by", "claudine-colbert"), "is not what the preview showed")
        self.assertEqual(self.r.pointer()["session-doctor"], moved)


if __name__ == "__main__":
    unittest.main(verbosity=1)
