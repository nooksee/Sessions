#!/usr/bin/env python3
"""Tests for ops/lib/scripts/mind.py, in synthetic rooms only. Standard library only.

Every case builds its own room, registry and change files in a temporary
directory; no real room, mind or body is touched. Each of Claudio's section 130
items that the port fixes has a test named for it. Run:

    python3 -I -B tools/test/test_mind.py
"""
import importlib.util
import fcntl
import io
import json
import os
import re
import selectors
import shlex
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest import mock

MIND = Path(__file__).resolve().parents[2] / "ops" / "lib" / "scripts" / "mind.py"
_spec = importlib.util.spec_from_file_location("mind", MIND)
mind = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mind)

CORE = {"layer": "core", "kind": "identity", "text": "I chose the name Shannon: what survives a lossy channel.",
        "event": "naming", "date": "2026-08-09", "source": "Receipts/naming.md"}
LESSON = {"layer": "lesson", "text": "Measure before explaining.", "event": "a claim falsified by looking",
          "date": "2026-08-09", "source": "Receipts/x.md", "applies_when": "about to explain",
          "not_when": "the measurement is in hand"}
COMMIT = {"layer": "commitment", "text": "Run Joy's cutover.", "event": "Kevin asked", "date": "2026-10-30",
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
            "a uuid": dict(LESSON, source="0000abcd-0000-4000-8000-00000000abcd"),
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
        subprocess.run(["git", "init", "-q", str(self.r.room)], check=True)
        real = subprocess.run

        def fake(cmd, **kw):
            if "check-ignore" in cmd:
                raise subprocess.TimeoutExpired(cmd, kw.get("timeout"))
            if "--show-toplevel" in cmd:
                return subprocess.CompletedProcess(cmd, 0, str(self.r.room) + "\n", "")
            return subprocess.CompletedProcess(cmd, 0, "true\n", "")
        with mock.patch.object(mind.subprocess, "run", side_effect=fake):
            problems = mind.git_exposed(self.r.room, [self.r.room / mind.POINTER])
        self.assertEqual(problems, [f"git check-ignore gave no answer within {mind.GIT_TIMEOUT:g} seconds"])
        self.assertIs(subprocess.run, real)

    def test_f1_a_broken_repository_is_a_refusal(self):
        subprocess.run(["git", "init", "-q", str(self.r.room)], check=True)
        (self.r.room / ".gitignore").write_text("/MIND.md\n/archives/MIND-*\n/storage/\n")
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
        self.refused(self.r.write({"add": [CORE]}, env=env), "a broken repository is not proof of being outside Git")
        head.write_text("ref: refs/heads/main\n")
        (self.r.room / ".git" / "config").write_text("[[[ broken\n")
        self.refused(self.r.write({"add": [CORE]}, env=env), "git rev-parse failed (exit 128")
        self.assertFalse((self.r.room / mind.POINTER).exists())
        self.assertEqual(list(self.r.room.glob("archives/MIND-*")), [])

    def test_f1_a_broken_inner_repository_is_refused_with_valid_parent(self):
        subprocess.run(["git", "init", "-q", str(self.r.base)], check=True)
        (self.r.base / ".gitignore").write_text(
            "/room/MIND.md\n/room/archives/MIND-*\n/room/storage/\n"
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
            ["git", "-C", str(self.r.room), "check-ignore", "-q", str(self.r.room / mind.POINTER)],
            check=False,
        )
        self.assertEqual(inside.stdout.strip(), "true")
        self.assertEqual(Path(top.stdout.strip()), self.r.base)
        self.assertEqual(ignored.returncode, 0)
        self.refused(self.r.write({"add": [CORE]}), "a broken repository is not proof of being outside Git")
        self.assertFalse((self.r.room / mind.POINTER).exists())
        self.assertEqual(list(self.r.room.glob("archives/MIND-*")), [])

        shutil.rmtree(self.r.room / ".git")
        self.ok(self.r.write({"add": [CORE]}))

    def test_f1_a_broken_nearest_ancestor_is_refused(self):
        outer = Path(self.tmp.name) / "outer"
        middle = outer / "middle"
        outer.mkdir()
        subprocess.run(["git", "init", "-q", str(outer)], check=True)
        (outer / ".gitignore").write_text(
            "/middle/room/MIND.md\n/middle/room/archives/MIND-*\n/middle/room/storage/\n"
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
            ["git", "-C", str(room.room), "check-ignore", "-q", str(room.room / mind.POINTER)],
            check=False,
        )
        self.assertFalse((room.room / ".git").exists())
        self.assertEqual(inside.stdout.strip(), "true")
        self.assertEqual(Path(top.stdout.strip()), outer)
        self.assertEqual(ignored.returncode, 0)
        self.refused(room.write({"add": [CORE]}), "nearest .git marker", "broken repository")
        self.assertFalse((room.room / mind.POINTER).exists())
        self.assertEqual(list(room.room.glob("archives/MIND-*")), [])

    def test_f1_valid_nearer_repository_ignores_broken_higher_ancestor(self):
        outer = Path(self.tmp.name) / "outer"
        middle = outer / "middle"
        outer.mkdir()
        subprocess.run(["git", "init", "-q", str(outer)], check=True)
        subprocess.run(["git", "init", "-q", str(middle)], check=True)
        room = Room(middle)
        (middle / ".gitignore").write_text("/room/MIND.md\n/room/archives/MIND-*\n/room/storage/\n")
        (outer / ".git" / "HEAD").write_text("not a ref\n")

        top = subprocess.run(
            ["git", "-C", str(room.room), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(Path(top.stdout.strip()), middle)
        self.ok(room.write({"add": [CORE]}))

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
        (self.r.room / ".gitignore").write_text("/MIND.md\n/archives/MIND-*\n/storage/\n")
        self.ok(self.r.write({"add": [CORE]}))

    def test_f1_only_a_positive_answer_passes(self):
        path = shlex.quote(str(self.r.room))
        (self.r.room / ".git").mkdir()
        cases = {
            "rev-parse says false": ('echo false\n', "not 'true'"),
            "rev-parse fails otherwise": ('echo "fatal: something else" >&2; exit 128\n', "git rev-parse failed (exit 128: fatal: something else)"),
            "check-ignore errors": (
                'case "$4" in --is-inside-work-tree) echo true;; '
                f'--show-toplevel) echo {path};; *) echo "fatal: boom" >&2; exit 128;; esac\n',
                                    "git check-ignore failed for archives/MIND-"),
        }
        for label, (script, words) in cases.items():
            with self.subTest(label):
                self.refused(self.r.write({"add": [CORE]}, env=self.fake_git(script)), words)
                self.assertEqual(self.r.files(), [])
        ignored = self.fake_git(
            'case "$4" in --is-inside-work-tree) echo true;; '
            f'--show-toplevel) echo {path};; *) exit 0;; esac\n'
        )
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
            result = room.write({"add": [CORE]})
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
                result = room.write({"add": [CORE]})
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
                result = room.write({"add": [CORE]})
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
            result = room.write({"add": [CORE]})
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
            result = room.write({"add": [CORE]})
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

    def test_legacy_lock_does_not_block_read_only_preview(self):
        room = self.room("preview")
        old = room.room / "storage/mind.lock"
        old.parent.mkdir()
        old.write_bytes(b"preserved")
        changes = room.changes({"add": [CORE]})
        self.assertTrue(room.preview("session-doctor", changes))
        self.assertFalse((room.room / "logs").exists())
        self.assertEqual(old.read_bytes(), b"preserved")


class ProjectTests(unittest.TestCase):
    """W5 first slice: mind project --key K --notebook DIR, in synthetic rooms and notebooks only."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="mind-project-")
        self.r = Room(Path(self.tmp.name))
        self.nb = Path(self.tmp.name) / "notebooks" / "session-doctor"
        self.nb.mkdir(parents=True)
        self.nb.chmod(0o700)
        self.index = self.nb / "MEMORY.md"
        self.tail = "- [Room facts](room-facts.md) - a note the resident keeps\n"
        self.index.write_text(self.tail)
        self.index.chmod(0o600)

    def tearDown(self):
        self.tmp.cleanup()

    def project(self, key="session-doctor", notebook=None, env=None):
        return self.r.run("project", "--key", key, "--notebook", str(notebook or self.nb), env=env)

    def ok(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def refused(self, result, *words):
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        for word in words:
            self.assertIn(word, result.stderr)
        return result

    def genesis(self):
        self.assertEqual(self.r.write({"add": [CORE, LESSON, COMMIT]}).returncode, 0)

    def block(self, key="session-doctor"):
        rel, digest = self.r.pointer()[key]
        data = (self.r.room / rel).read_bytes()
        return (f"<!-- mind-projection begin key={key} leaf={rel} sha256={digest}: a copy written by mind.py project; "
                f"the leaf is the authority -->\n" + data.decode("utf-8") + f"<!-- mind-projection end key={key} -->\n")

    def room_bytes(self):
        return {p: (self.r.room / p).read_bytes() for p in self.r.files()}

    def test_w5_project_puts_one_block_at_the_top_and_keeps_every_other_byte(self):
        self.genesis()
        before = self.room_bytes()
        out = self.ok(self.project()).stdout
        self.assertEqual(self.index.read_text(), self.block() + self.tail)
        self.assertEqual(stat.S_IMODE(self.index.stat().st_mode), 0o600)
        self.assertIn("projection written", out)
        self.assertIn("not evidence that any provider loaded it", out)
        self.assertEqual(self.room_bytes(), before)                 # leaf and pointer untouched
        self.assertNotIn("never-printed", out)

    def test_w5_project_creates_the_index_in_a_named_empty_notebook(self):
        self.genesis()
        self.index.unlink()
        self.ok(self.project())
        self.assertEqual(self.index.read_text(), self.block())
        self.assertEqual(stat.S_IMODE(self.index.stat().st_mode), 0o600)

    def test_w5_project_is_idempotent_and_follows_a_new_leaf(self):
        self.genesis()
        self.ok(self.project())
        first = self.index.read_bytes()
        self.assertIn("projection unchanged", self.ok(self.project()).stdout)
        self.assertEqual(self.index.read_bytes(), first)
        self.assertEqual(self.r.write({"add": [dict(LESSON, text="Another lesson.")]}, yes="yes, add it").returncode, 0)
        out = self.ok(self.project()).stdout
        self.assertIn("matched the leaf it named", out)
        self.assertEqual(self.index.read_text(), self.block() + self.tail)
        self.assertNotEqual(self.index.read_bytes(), first)

    def test_w5_project_has_no_default_notebook(self):
        self.genesis()
        result = self.r.run("project", "--key", "session-doctor")
        self.assertEqual(result.returncode, 2)
        self.assertIn("--notebook", result.stderr)
        missing = Path(self.tmp.name) / "notebooks" / "absent"
        self.refused(self.project(notebook=missing), "creates none")
        self.assertFalse(missing.exists())
        self.refused(self.project(notebook=" "), "--notebook")
        self.assertEqual(self.index.read_text(), self.tail)

    def test_w5_project_refuses_unsafe_notebook_paths(self):
        self.genesis()
        real = Path(self.tmp.name) / "real"
        real.mkdir(mode=0o700)
        real.chmod(0o700)
        (real / "nb").mkdir()
        (real / "nb").chmod(0o700)
        link_parent = Path(self.tmp.name) / "linked-parent"
        link_parent.symlink_to(real)
        self.refused(self.project(notebook=link_parent / "nb"), "symbolic link")
        link_dir = Path(self.tmp.name) / "linked-nb"
        link_dir.symlink_to(self.nb)
        self.refused(self.project(notebook=link_dir), "symbolic link")
        self.nb.chmod(0o755)
        self.refused(self.project(), "not 0700")
        self.nb.chmod(0o700)
        self.index.chmod(0o644)
        self.refused(self.project(), "not 0600")
        self.index.chmod(0o600)
        twin = Path(self.tmp.name) / "twin"
        os.link(self.index, twin)
        self.refused(self.project(), "hard links")
        twin.unlink()
        self.index.unlink()
        other = Path(self.tmp.name) / "elsewhere.md"
        other.write_text(self.tail)
        self.index.symlink_to(other)
        self.refused(self.project(), "not a regular file")
        self.assertEqual(other.read_text(), self.tail)
        self.index.unlink()
        plain = Path(self.tmp.name) / "plain-file"
        plain.write_text("x")
        self.refused(self.project(notebook=plain), "not a directory")
        self.assertEqual(plain.read_text(), "x")

    def test_w5_project_refuses_wrong_duplicate_malformed_and_misplaced_markers(self):
        self.genesis()
        self.assertEqual(self.r.write({"add": [CORE]}, key="claudine-colbert").returncode, 0)
        cases = {
            "another key": (self.block("claudine-colbert") + self.tail, "not session-doctor"),
            "duplicate": (self.block() + self.block() + self.tail, "4 projection markers"),
            "malformed": ("<!-- mind-projection begin key=session-doctor -->\n" + self.tail, "malformed"),
            "end only": (self.tail + "<!-- mind-projection end key=session-doctor -->\n", "1 projection markers"),
            "not at the top": (self.tail + self.block(), "not at the top"),
            "crlf marker": (self.block().replace("-->\n", "-->\r\n", 1) + self.tail, "malformed"),
        }
        for name, (text, word) in cases.items():
            with self.subTest(case=name):
                self.index.write_text(text)
                before = self.index.read_bytes()
                self.refused(self.project(), word)
                self.assertEqual(self.index.read_bytes(), before)

    def test_w5_an_edited_block_is_reported_and_replaced(self):
        self.genesis()
        self.ok(self.project())
        self.index.write_text(self.index.read_text().replace("Measure before explaining.", "Explain first."))
        out = self.ok(self.project()).stdout
        self.assertIn("edited by hand", out)
        self.assertEqual(self.index.read_text(), self.block() + self.tail)

    def test_w5_an_unverified_mind_is_never_projected_and_nothing_is_locked(self):
        self.refused(self.project(), "not projected until its check passes")
        self.assertFalse((self.r.room / "logs").exists())
        self.assertEqual(self.index.read_text(), self.tail)
        self.genesis()
        leaf = self.r.leaf()
        leaf.write_text(leaf.read_text().replace("Measure before explaining.", "Explain first."))
        self.refused(self.project(), "not projected until its check passes")
        self.assertEqual(self.index.read_text(), self.tail)
        self.refused(self.project(key="nobody-here"), "not projected until its check passes")

    def test_w5_oversize_is_refused_never_truncated(self):
        many = [dict(LESSON, text=f"Lesson number {n} in words.") for n in range(1, 31)]
        self.assertEqual(self.r.write({"add": many}).returncode, 0)
        self.assertGreater(len(self.r.leaf().read_text().splitlines()), mind.LOAD_LINES)
        self.refused(self.project(), "never truncated")
        self.assertEqual(self.index.read_text(), self.tail)

    def test_w5_project_needs_positive_git_exclusion(self):
        if subprocess.run(["git", "--version"], capture_output=True).returncode != 0:
            self.skipTest("git is not installed")
        self.genesis()
        subprocess.run(["git", "init", "-q", str(self.nb)], check=True)
        self.refused(self.project(), "not ignored by Git")
        self.assertEqual(self.index.read_text(), self.tail)
        (self.nb / ".gitignore").write_text("/MEMORY.md\n")
        self.ok(self.project())
        self.assertEqual(self.index.read_text(), self.block() + self.tail)


class SealTests(unittest.TestCase):
    """W5 second slice: seal, unseal and the two check gates, in synthetic rooms and notebooks only."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="mind-seal-")
        self.base = Path(self.tmp.name)
        self.r = Room(self.base)
        self.nb = self.base / "notebooks" / "session-doctor"
        self.nb.mkdir(parents=True)
        self.nb.chmod(0o700)
        self.files = {"MEMORY.md": b"- [Room facts](room-facts.md) - a note\n", "room-facts.md": b"The room has one door.\n",
                      "topics/deep.md": b"A note in a subfolder.\n"}
        (self.nb / "topics").mkdir()
        (self.nb / "topics").chmod(0o700)
        for rel, data in self.files.items():
            (self.nb / rel).write_bytes(data)
            (self.nb / rel).chmod(0o600)

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

    def seal(self, key="session-doctor", notebook=None, env=None):
        return self.r.run("seal", "--key", key, "--notebook", str(notebook or self.nb), env=env)

    def unseal(self, name, into, key="session-doctor", replace=False):
        return self.r.run("unseal", "--key", key, "--seal", name, "--into", str(into), *(["--replace"] if replace else []))

    def seals(self):
        return sorted(p.name for p in (self.r.room / "archives").glob("NOTEBOOK-*")) if (self.r.room / "archives").exists() else []

    def sealed(self, **kw) -> str:
        out = self.ok(self.seal(**kw)).stdout
        return re.search(r"archives/(NOTEBOOK-\S+\.tar)", out).group(1)

    def tree(self, folder: Path) -> dict:
        return {p.relative_to(folder).as_posix(): (p.read_bytes() if p.is_file() else None, stat.S_IMODE(p.lstat().st_mode))
                for p in folder.rglob("*")}

    def plant(self, members, key="session-doctor", manifest=None, date="2026-10-30") -> str:
        """A hand-made seal with a correct name hash, as a forger would write one."""
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w", format=tarfile.PAX_FORMAT) as tar:
            listed = []
            for info, data in members:
                if info.name.startswith("notebook/") and (info.isreg() or info.isdir()):
                    listed.append({"path": info.name[len("notebook/"):], "type": "file" if info.isreg() else "dir"}
                                  | ({"sha256": mind.sha256(data), "size": len(data)} if info.isreg() else {}))
            body = json.dumps(manifest if manifest is not None else
                              {"format": mind.SEAL_FORMAT, "key": key, "members": listed}).encode("utf-8")
            for info, data in [(self.info("SEAL.json", size=len(body)), body), (self.info("notebook", kind=tarfile.DIRTYPE), b"")] + members:
                tar.addfile(info, io.BytesIO(data) if info.isreg() else None)
        data = buf.getvalue()
        name = f"NOTEBOOK-{key}-{date}-{mind.sha256(data)[:8]}.tar"
        (self.r.room / "archives").mkdir(exist_ok=True)
        (self.r.room / "archives" / name).write_bytes(data)
        return name

    @staticmethod
    def info(name, kind=tarfile.REGTYPE, size=0, uid=None, linkname=""):
        info = tarfile.TarInfo(name)
        info.type, info.size, info.linkname = kind, size, linkname
        info.uid, info.gid, info.uname, info.gname = os.geteuid() if uid is None else uid, os.getegid(), "", ""
        info.mode = 0o700 if kind == tarfile.DIRTYPE else 0o600
        return info

    # -- seal ------------------------------------------------------------------
    def test_w5_seal_writes_once_binding_key_and_hash(self):
        name = self.sealed()
        path = self.r.room / "archives" / name
        self.assertRegex(name, r"^NOTEBOOK-session-doctor-2026-10-30-[0-9a-f]{8}\.tar$")
        self.assertTrue(mind.sha256(path.read_bytes()).startswith(name[-12:-4]))
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        with tarfile.open(path) as tar:
            names = tar.getnames()
            manifest = json.loads(tar.extractfile("SEAL.json").read())
        self.assertEqual(names[:2], ["SEAL.json", "notebook"])
        self.assertEqual(manifest["key"], "session-doctor")
        self.assertEqual(sorted(m["path"] for m in manifest["members"]), ["MEMORY.md", "room-facts.md", "topics", "topics/deep.md"])
        first = path.read_bytes()
        self.assertIn("already sealed, unchanged", self.ok(self.seal()).stdout)
        self.assertEqual(self.seals(), [name])
        (self.nb / "room-facts.md").write_bytes(b"The room has two doors.\n")
        second = self.sealed()
        self.assertNotEqual(second, name)
        self.assertEqual(path.read_bytes(), first)                     # the earlier seal is untouched

    def test_w5_seal_never_overwrites_other_bytes(self):
        name = self.sealed()
        path = self.r.room / "archives" / name
        path.write_bytes(path.read_bytes() + b"x")
        tampered = path.read_bytes()
        self.refused(self.seal(), "never overwritten")
        self.assertEqual(path.read_bytes(), tampered)

    def test_w5_seal_refuses_links_specials_hard_links_and_an_unregistered_key(self):
        cases = []
        link = self.nb / "linked.md"
        link.symlink_to(self.nb / "room-facts.md")
        cases.append(("symbolic link", link.unlink))
        for word, cleanup in cases:
            self.refused(self.seal(), word)
            cleanup()
        os.mkfifo(self.nb / "pipe")
        self.refused(self.seal(), "device, pipe or socket")
        (self.nb / "pipe").unlink()
        os.link(self.nb / "room-facts.md", self.base / "twin")
        self.refused(self.seal(), "hard links")
        (self.base / "twin").unlink()
        self.refused(self.seal(key="nobody-here"), "registered 0 times")
        self.nb.chmod(0o755)
        self.refused(self.seal(), "not 0700")
        self.nb.chmod(0o700)
        self.refused(self.r.run("seal", "--key", "session-doctor", "--notebook", " "), "--notebook is required")
        self.assertEqual(self.r.run("seal", "--key", "session-doctor").returncode, 2)
        self.assertEqual(self.seals(), [])
        self.assertFalse((self.r.room / "logs").exists())             # refused before the lock

    def test_w5_seal_needs_positive_git_exclusion(self):
        if subprocess.run(["git", "--version"], capture_output=True).returncode != 0:
            self.skipTest("git is not installed")
        subprocess.run(["git", "init", "-q", str(self.r.room)], check=True)
        self.refused(self.seal(), "not ignored by Git")
        self.assertEqual(self.seals(), [])
        (self.r.room / ".gitignore").write_text("/archives/NOTEBOOK-*\n/logs/\n")
        self.ok(self.seal())

    # -- unseal ----------------------------------------------------------------
    def test_w5_unseal_restores_byte_for_byte_into_an_absent_folder(self):
        name = self.sealed()
        into = self.base / "successor" / "session-doctor"
        into.parent.mkdir()
        self.ok(self.unseal(name, into))
        got = self.tree(into)
        self.assertEqual({k: v[0] for k, v in got.items()}, {**self.files, "topics": None})
        self.assertEqual({k: v[1] for k, v in got.items()}, {"MEMORY.md": 0o600, "room-facts.md": 0o600, "topics": 0o700,
                                                             "topics/deep.md": 0o600})
        self.assertEqual(stat.S_IMODE(into.stat().st_mode), 0o700)
        self.assertEqual(sorted(p.name for p in into.parent.iterdir()), ["session-doctor"])   # no staging left

    def test_w5_unseal_fills_an_empty_folder_and_replaces_only_with_replace(self):
        name = self.sealed()
        into = self.base / "successor"
        into.mkdir(mode=0o700)
        into.chmod(0o700)
        self.ok(self.unseal(name, into))
        (into / "MEMORY.md").write_bytes(b"newer work\n")
        self.refused(self.unseal(name, into), "not empty", "--replace")
        self.assertEqual((into / "MEMORY.md").read_bytes(), b"newer work\n")
        out = self.ok(self.unseal(name, into, replace=True)).stdout
        self.assertEqual((into / "MEMORY.md").read_bytes(), self.files["MEMORY.md"])
        kept = [p for p in self.base.iterdir() if p.name.startswith(".successor.replaced-")]
        self.assertEqual(len(kept), 1)
        self.assertEqual((kept[0] / "MEMORY.md").read_bytes(), b"newer work\n")       # the earlier notebook is kept
        self.assertIn("kept, unread", out)

    def test_w5_unseal_checks_fixity_before_extracting(self):
        name = self.sealed()
        path = self.r.room / "archives" / name
        data = bytearray(path.read_bytes())
        data[600] ^= 1
        path.write_bytes(bytes(data))
        into = self.base / "successor"
        self.refused(self.unseal(name, into), "no longer match the hash in its name")
        self.assertFalse(into.exists())
        self.assertEqual([p.name for p in self.base.iterdir() if ".unseal-" in p.name], [])

    def test_w5_unseal_refuses_hostile_members_without_extracting(self):
        payload = b"x\n"
        good = (self.info("notebook/MEMORY.md", size=len(payload)), payload)
        cases = {
            "absolute": [(self.info("/etc/evil", size=2), payload)],
            "escape": [(self.info("notebook/../evil", size=2), payload)],
            "symlink": [(self.info("notebook/l", kind=tarfile.SYMTYPE, linkname="/etc/passwd"), b"")],
            "hard link": [good, (self.info("notebook/h", kind=tarfile.LNKTYPE, linkname="notebook/MEMORY.md"), b"")],
            "device": [(self.info("notebook/d", kind=tarfile.CHRTYPE), b"")],
            "pipe": [(self.info("notebook/p", kind=tarfile.FIFOTYPE), b"")],
            "foreign owner": [(self.info("notebook/MEMORY.md", size=2, uid=os.geteuid() + 1), payload)],
            "outside the root": [(self.info("elsewhere.md", size=2), payload)],
            "before its folder": [(self.info("notebook/sub/a.md", size=2), payload)],
        }
        words = {"absolute": "escapes", "escape": "escapes", "symlink": "special", "hard link": "special",
                 "device": "special", "pipe": "special", "foreign owner": "foreign ownership",
                 "outside the root": "manifest lists", "before its folder": "comes before its folder"}
        into = self.base / "successor"
        for case, members in cases.items():
            with self.subTest(case=case):
                name = self.plant(members)
                self.refused(self.unseal(name, into), words[case])
                self.assertFalse(into.exists())
        name = self.plant([good], manifest={"format": mind.SEAL_FORMAT, "key": "claudine-colbert", "members": [
            {"path": "MEMORY.md", "type": "file", "sha256": mind.sha256(payload), "size": 2}]})
        self.refused(self.unseal(name, into), "belongs to 'claudine-colbert'")
        name = self.plant([good], manifest={"format": mind.SEAL_FORMAT, "key": "session-doctor", "members": [
            {"path": "MEMORY.md", "type": "file", "sha256": "0" * 64, "size": 2}]})
        self.refused(self.unseal(name, into), "does not hash as its manifest records")
        name = self.plant([good], manifest={"format": mind.SEAL_FORMAT, "key": "session-doctor", "members": []})
        self.refused(self.unseal(name, into), "not the ones its manifest lists")
        self.assertFalse(into.exists())
        self.assertEqual([p.name for p in self.base.iterdir() if ".unseal-" in p.name], [])

    def test_w5_unseal_binds_the_key(self):
        name = self.sealed()
        into = self.base / "successor"
        self.refused(self.unseal(name, into, key="claudine-colbert"), f"{name} belongs to 'session-doctor'")
        moved = name.replace("session-doctor", "claudine-colbert")
        (self.r.room / "archives" / name).rename(self.r.room / "archives" / moved)
        self.refused(self.unseal(moved, into, key="claudine-colbert"), "manifest belongs to 'session-doctor'")
        self.refused(self.unseal("NOTEBOOK-oops.tar", into), "not a seal name")
        self.assertFalse(into.exists())

    def test_w5_unseal_refuses_unsafe_targets(self):
        name = self.sealed()
        real = self.base / "real"
        real.mkdir(mode=0o700)
        real.chmod(0o700)
        linked = self.base / "linked"
        linked.symlink_to(real)
        self.refused(self.unseal(name, linked / "nb"), "symbolic link")
        self.refused(self.unseal(name, linked), "symbolic link")
        loose = self.base / "loose"
        loose.mkdir()
        loose.chmod(0o755)
        self.refused(self.unseal(name, loose), "not 0700")
        self.refused(self.unseal(name, self.base / "absent-parent" / "nb"), "does not exist")
        self.assertEqual(list(real.iterdir()), [])

    def test_w5_unseal_needs_positive_git_exclusion(self):
        if subprocess.run(["git", "--version"], capture_output=True).returncode != 0:
            self.skipTest("git is not installed")
        name = self.sealed()
        home = self.base / "home"
        home.mkdir()
        subprocess.run(["git", "init", "-q", str(home)], check=True)
        self.refused(self.unseal(name, home / "nb"), "not ignored by Git")
        self.assertFalse((home / "nb").exists())
        (home / ".gitignore").write_text("/nb/\n/.nb.*\n")
        self.ok(self.unseal(name, home / "nb"))

    def test_w5_a_staged_tree_must_equal_the_seal(self):
        members = [("MEMORY.md", "file", b"x\n", 0), ("topics", "dir", b"", 0)]
        stage = self.base / "stage"
        stage.mkdir(mode=0o700)
        (stage / "topics").mkdir(mode=0o700)
        (stage / "topics").chmod(0o700)
        (stage / "MEMORY.md").write_bytes(b"x\n")
        (stage / "MEMORY.md").chmod(0o600)
        self.assertTrue(mind.staged_matches(stage, members))
        (stage / "MEMORY.md").write_bytes(b"y\n")
        self.assertFalse(mind.staged_matches(stage, members))
        (stage / "MEMORY.md").write_bytes(b"x\n")
        (stage / "MEMORY.md").chmod(0o644)
        self.assertFalse(mind.staged_matches(stage, members))
        (stage / "MEMORY.md").chmod(0o600)
        (stage / "extra.md").write_bytes(b"")
        self.assertFalse(mind.staged_matches(stage, members))

    def test_w5_a_bad_staged_write_never_takes_the_name(self):
        name = self.sealed()
        into = self.base / "successor"
        argv = ["--room", str(self.r.room), "--registry", str(self.r.registry), "--now", "2026-10-30T18:00:00Z",
                "unseal", "--key", "session-doctor", "--seal", name, "--into", str(into)]
        short = lambda fd, data: os.write(fd, data[:-1]) if data else None
        with mock.patch.object(mind, "write_all", side_effect=short), mock.patch("sys.stderr", new=io.StringIO()) as err:
            self.assertEqual(mind.main(argv), 2)
        self.assertIn("does not match the seal", err.getvalue())
        self.assertFalse(into.exists())
        self.assertEqual([p.name for p in self.base.iterdir() if ".unseal-" in p.name], [])

    # -- the two check gates ---------------------------------------------------------
    def test_w5_check_seal_gate(self):
        self.assertEqual(self.r.write({"add": [CORE]}).returncode, 0)
        self.assertIn("PASS session-doctor seal : no seals", self.ok(self.r.run("check")).stdout)
        name = self.sealed()
        self.assertIn("1 seals, each hashing as named", self.ok(self.r.run("check", "--key", "session-doctor")).stdout)
        path = self.r.room / "archives" / name
        path.write_bytes(path.read_bytes()[:-1] + b"\x01")
        result = self.r.run("check", "--key", "session-doctor")
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("FAIL session-doctor seal", result.stdout)
        self.ok(self.r.run("show", "session-doctor"))                  # show is unchanged: the gate lives in check
        path.unlink()
        (self.r.room / "archives" / "NOTEBOOK-garbled.tar").write_bytes(b"")
        self.assertIn("1 NOTEBOOK- files", self.ok(self.r.run("check")).stdout)

    def test_w5_check_projection_gate(self):
        self.assertEqual(self.r.write({"add": [CORE]}).returncode, 0)
        check = ("check", "--key", "session-doctor", "--notebook", str(self.nb))
        self.assertIn("holds no projection", self.r.run(*check).stdout)
        self.ok(self.r.run("project", "--key", "session-doctor", "--notebook", str(self.nb)))
        self.assertIn("PASS session-doctor projection : matches", self.ok(self.r.run(*check)).stdout)
        index = self.nb / "MEMORY.md"
        projected = index.read_text()
        index.write_text(projected.replace("I chose the name Shannon", "I chose a name"))
        result = self.r.run(*check)
        self.assertEqual(result.returncode, 1)
        self.assertIn("byte for byte", result.stdout)
        index.write_text(projected)
        self.assertEqual(self.r.write({"add": [LESSON]}, yes="yes, add it").returncode, 0)
        result = self.r.run(*check)
        self.assertEqual(result.returncode, 1)
        self.assertIn("project again", result.stdout)
        self.refused(self.r.run("check", "--notebook", str(self.nb)), "needs --key")


class SealFieldTests(unittest.TestCase):
    """W5 third slice: leaf format 2, a notebook line naming a seal, in synthetic rooms only."""

    OLD_POLICY = "a92a7c3f6a3b6112"          # the policy digest at main b710b60c, before leaf format 2

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="mind-sealfield-")
        self.base = Path(self.tmp.name)
        self.r = Room(self.base)
        self.nb = self.base / "notebooks" / "session-doctor"
        self.nb.mkdir(parents=True)
        self.nb.chmod(0o700)
        (self.nb / "MEMORY.md").write_bytes(b"- [Room facts](room-facts.md) - a note\n")
        (self.nb / "MEMORY.md").chmod(0o600)

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

    def seal(self, key="session-doctor", notebook=None) -> str:
        out = self.ok(self.r.run("seal", "--key", key, "--notebook", str(notebook or self.nb))).stdout
        return re.search(r"archives/(NOTEBOOK-\S+\.tar)", out).group(1)

    def preview(self, path, seal=None, key="session-doctor"):
        result = self.r.run("preview", key, "--changes", path, *(["--seal", seal] if seal else []))
        m = re.search(r"^binding: ([0-9a-f]{64})$", result.stdout, re.M)
        return (m.group(1) if m else ""), result

    def write(self, obj, seal=None, preview_seal="same", binding=None, key="session-doctor"):
        """As a writer does it: preview with the seal, then write with the binding preview printed."""
        path = self.r.changes(obj)
        shown, _ = self.preview(path, seal if preview_seal == "same" else preview_seal, key)
        return self.r.run("write", key, "--changes", path, "--preview", binding or shown or "0" * 64,
                          "--yes", "yes, record it", "--by", "claudine-colbert", *(["--seal", seal] if seal else []))

    def reference(self, name: str) -> str:
        return f"archives/{name} sha256={mind.sha256((self.r.room / 'archives' / name).read_bytes())}"

    def check(self, *extra):
        return self.r.run("check", "--key", "session-doctor", *extra)

    # -- version 1 stays as it was ------------------------------------------------------
    def test_w5_a_version_1_leaf_of_the_real_shape_still_passes(self):
        """A first leaf of three lessons, two of them closed incidents, written under the old policy."""
        lesson = {"layer": "lesson", "event": "a value written before it was measured", "date": "2026-10-29",
                  "source": "Receipts/x.md", "applies_when": "a record carries a value", "not_when": "nothing is recorded"}
        yes = '2026-10-30, "yes, all three"'
        entries = [dict(lesson, id="lesson-001", text="Stamp every value inside the writing command.", kind="incident",
                        fix="the append reads the clock itself", closed="2026-10-30", yes=yes),
                   dict(lesson, id="lesson-002", text="Keep no sole copy of work in volatile scratch.", kind="incident",
                        fix="build in the room scratch and push early", closed="2026-10-29", yes=yes),
                   dict(lesson, id="lesson-003", text="Make the unknown form fail closed.", yes=yes)]
        head = {"title": "Role (Person session-doctor)", "resident": "session-doctor", "written": "2026-10-30T06:49:00Z",
                "by": "session-doctor", "predecessor": "none", "change": "add lesson-001, lesson-002, lesson-003",
                "yes": yes, "issued": "core=0 bond=0 lesson=3 commitment=0 pointer=0", "policy": self.OLD_POLICY}
        data = mind.render_leaf(head, entries).encode("utf-8")
        name = f"MIND-session-doctor-2026-10-30-{mind.sha256(data)[:8]}.md"
        (self.r.room / "archives").mkdir()
        (self.r.room / "archives" / name).write_bytes(data)
        (self.r.room / mind.POINTER).write_text(mind.pointer_text({"session-doctor": (f"archives/{name}", mind.sha256(data))}))
        text = self.r.leaf().read_text()
        self.assertNotIn("\nnotebook: ", text)
        self.assertEqual(mind.render_leaf(*mind.parse_leaf(text)), text)
        self.assertEqual(mind.leaf_format(mind.parse_leaf(text)[0]), 1)
        out = self.ok(self.check()).stdout
        self.assertIn(f"REPORT session-doctor policy : written under policy {self.OLD_POLICY}", out)
        self.assertIn("PASS session-doctor leaf-seal : no leaf names a seal", out)
        self.assertEqual(self.ok(self.r.run("show", "session-doctor")).stdout, text)
        self.assertNotIn("notebook", self.ok(self.r.run("history", "session-doctor")).stdout)
        name = self.seal()                                      # a version 2 leaf builds on it
        self.ok(self.write({"add": [CORE]}, seal=name))
        self.ok(self.check())

    def test_w5_the_binding_without_a_seal_is_unchanged(self):
        changes = ([{"layer": "core", "text": "x"}], [], [])
        old = mind.sha256(json.dumps({"key": "k", "predecessor": "none", "changes": {"add": changes[0], "amend": [],
                                     "retire": []}}, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode())
        self.assertEqual(mind.binding_of("k", "none", *changes), old)
        self.assertNotEqual(mind.binding_of("k", "none", *changes, "archives/NOTEBOOK-k-2026-10-30-00000000.tar"), old)

    # -- version 2 -------------------------------------------------------------------------
    def test_w5_write_with_a_seal_records_a_version_2_leaf(self):
        self.ok(self.r.write({"add": [CORE]}))
        name = self.seal()
        self.ok(self.write({"add": [LESSON]}, seal=name))
        text = self.r.leaf().read_text()
        lines = text.split("\n")
        policy_at = next(i for i, line in enumerate(lines) if line.startswith("policy: "))
        self.assertEqual(lines[policy_at + 1], f"notebook: {self.reference(name)}")
        head, _ = mind.parse_leaf(text)
        self.assertEqual((mind.leaf_format(head), mind.render_leaf(*mind.parse_leaf(text))), (2, text))
        self.assertEqual(stat.S_IMODE(self.r.leaf().stat().st_mode), 0o600)
        self.assertIn("PASS session-doctor leaf-seal : 1 leaves of the chain name a seal", self.ok(self.check()).stdout)
        self.assertIn(f"notebook: {self.reference(name)}", self.ok(self.r.run("show", "session-doctor")).stdout)
        self.ok(self.r.write({"add": [COMMIT]}, yes="yes, a plain one"))   # a version 1 leaf after it
        self.assertNotIn("\nnotebook: ", self.r.leaf().read_text())
        history = self.ok(self.r.run("history", "session-doctor")).stdout.splitlines()
        self.assertEqual([("; notebook " + self.reference(name)) in line for line in history], [False, True, False])
        self.assertIn("1 leaves of the chain name a seal", self.ok(self.check()).stdout)

    def test_w5_preview_shows_the_seal_and_the_binding_covers_it(self):
        self.ok(self.r.write({"add": [CORE]}))
        first = self.seal()
        (self.nb / "MEMORY.md").write_bytes(b"- [Room facts](room-facts.md) - a newer note\n")
        second = self.seal()
        path = self.r.changes({"add": [LESSON]})
        plain, _ = self.preview(path)
        shown, result = self.preview(path, first)
        self.assertIn(f"notebook: {self.reference(first)}", result.stdout)
        self.assertIn(f"--seal {first}", result.stdout)
        self.assertNotEqual(plain, shown)
        before = self.r.pointer()
        for seal in (second, None):
            with self.subTest(seal=seal):
                self.refused(self.r.run("write", "session-doctor", "--changes", path, "--preview", shown, "--yes",
                                        "yes, record it", "--by", "claudine-colbert", *(["--seal", seal] if seal else [])),
                             "the binding differs")
        self.refused(self.write({"add": [LESSON]}, seal=first, preview_seal=None), "the binding differs")
        self.assertEqual(self.r.pointer(), before)

    def test_w5_write_refuses_a_seal_it_cannot_trust(self):
        self.ok(self.r.write({"add": [CORE]}))
        name = self.seal()
        other_nb = self.base / "notebooks" / "claudine-colbert"
        other_nb.mkdir()
        other_nb.chmod(0o700)
        foreign = self.seal(key="claudine-colbert", notebook=other_nb)
        path = self.r.room / "archives" / name
        before = self.r.pointer()
        self.refused(self.write({"add": [LESSON]}, seal=name.replace(name[-12:-4], "00000000")), "not on disk")
        self.refused(self.write({"add": [LESSON]}, seal=foreign), "belongs to 'claudine-colbert'")
        self.refused(self.write({"add": [LESSON]}, seal="NOTEBOOK-oops.tar"), "not a seal name")
        path.chmod(0o644)
        self.refused(self.write({"add": [LESSON]}, seal=name), "not 0600")
        path.chmod(0o600)
        moved = self.base / "seal-elsewhere.tar"
        path.rename(moved)
        path.symlink_to(moved)
        self.refused(self.write({"add": [LESSON]}, seal=name), "symbolic link")
        path.unlink()
        moved.rename(path)
        data = path.read_bytes()
        path.write_bytes(data[:-1] + bytes([data[-1] ^ 1]))
        self.refused(self.write({"add": [LESSON]}, seal=name), "no longer match the hash in its name")
        path.write_bytes(data)
        renamed = name.replace("session-doctor", "claudine-colbert")
        self.refused(self.write({"add": [LESSON]}, seal=renamed), "belongs to 'claudine-colbert'")
        self.assertEqual(self.r.pointer(), before)

    def test_w5_check_gate_for_the_leaf_seal(self):
        self.ok(self.r.write({"add": [CORE]}))
        name = self.seal()
        self.ok(self.write({"add": [LESSON]}, seal=name))
        path = self.r.room / "archives" / name
        kept = self.base / "custody.tar"
        path.rename(kept)
        out = self.ok(self.check()).stdout                           # in custody: reported, not failed
        self.assertIn("REPORT session-doctor seal-history", out)
        self.assertIn("not on disk", out)
        kept.rename(path)
        data = path.read_bytes()
        path.write_bytes(data[:-1] + bytes([data[-1] ^ 1]))
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL session-doctor leaf-seal", result.stdout)
        path.write_bytes(data)
        head, entries = mind.parse_leaf(self.r.leaf().read_text())
        m = mind.NOTEBOOK_REF_RE.match(head["notebook"])
        head = dict(head, notebook=head["notebook"][:-56] + ("0" * 56 if m.group("sha")[8:] != "0" * 56 else "1" * 56))
        self.r.plant(head, entries)
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("does not hash to the digest the leaf records", result.stdout)

    def test_w5_a_version_2_header_is_canonical_and_checked(self):
        self.ok(self.r.write({"add": [CORE]}))
        name = self.seal()
        self.ok(self.write({"add": [LESSON]}, seal=name))
        text = self.r.leaf().read_text()
        ref = self.reference(name)
        lines = text.split("\n")
        i = lines.index(f"notebook: {ref}")
        swapped = lines[:i - 1] + [lines[i], lines[i - 1]] + lines[i + 1:]
        for bad in ("\n".join(swapped), text.replace(f"notebook: {ref}\n", f"notebook: {ref}\nformat: 3\n"),
                    text.replace(f"notebook: {ref}\n", f"format: 3\nnotebook: {ref}\n"),
                    text.replace(f"notebook: {ref}\n", "notebook: \n")):
            with self.subTest(bad=bad[:0]):
                with self.assertRaises(mind.Refused):
                    mind.parse_leaf(bad)
        head, _ = mind.parse_leaf(text)
        sha = ref.split("sha256=")[1]
        cases = {"archives/elsewhere.tar sha256=" + sha: "not a seal reference",
                 ref.replace("NOTEBOOK-session-doctor-", "NOTEBOOK-claudine-colbert-"): "another resident",
                 ref.replace(sha, ("f" if sha[0] != "f" else "e") + sha[1:]): "disagree",
                 ref.replace("-2026-10-30-", "-2026-13-40-"): "not a date"}
        for value, word in cases.items():
            with self.subTest(word=word):
                self.assertTrue(any(word in p for p in mind.head_problems(dict(head, notebook=value))), word)
        self.assertEqual([p for p in mind.head_problems(head) if "notebook" in p], [])

    def test_w5_the_policy_digest_covers_the_leaf_formats(self):
        self.assertNotEqual(mind.policy_digest(), self.OLD_POLICY)
        now = mind.policy_digest()
        with mock.patch.object(mind, "LEAF_FORMATS", {1: mind.HEAD_KEYS}):
            self.assertNotEqual(mind.policy_digest(), now)


if __name__ == "__main__":
    unittest.main(verbosity=1)
