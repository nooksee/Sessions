#!/usr/bin/env python3
"""Tests for ops/bin/claude-resident, the launch wrapper's dry run (W5). Standard library only.

Every case builds its own room, registry and notebook folders in a temporary
directory. No real registry, notebook, provider or plugin setting is read or
touched, and the provider is never executed. Session identifiers are invented
zero-block values. Run:

    python3 -I -B tools/test/test_claude_resident.py
"""
import importlib.machinery
import importlib.util
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

WRAPPER = Path(__file__).resolve().parents[2] / "ops" / "bin" / "claude-resident"
_loader = importlib.machinery.SourceFileLoader("claude_resident", str(WRAPPER))
_spec = importlib.util.spec_from_loader("claude_resident", _loader)
wrapper = importlib.util.module_from_spec(_spec)
_loader.exec_module(wrapper)

S_ALPHA = "0000aaaa-0000-4000-8000-00000000aaaa"
S_BETA = "0000bbbb-0000-4000-8000-00000000bbbb"
S_CODEX = "0000cccc-0000-4000-8000-00000000cccc"
S_ELSEWHERE = "0000dddd-0000-4000-8000-00000000dddd"
S_UNKNOWN = "0000eeee-0000-4000-8000-00000000eeee"


class Room:
    """A synthetic room: a registry at 0600 and one notebook folder at 0700 for the key alpha-one."""

    def __init__(self, base: Path):
        self.base = base
        self.room = base / "room"
        (self.room / "ops" / "etc").mkdir(parents=True)
        self.other = base / "other-room"
        self.other.mkdir()
        self.rows = [
            self.row("alpha-one", "claude", S_ALPHA, self.room, "Person Alpha", "Role Alpha"),
            self.row("beta-two", "claude", S_BETA, self.room, "Person Beta", "Role Beta"),
            self.row("gamma-codex", "codex", S_CODEX, self.room, "Person Gamma", "Role Gamma"),
            self.row("delta-elsewhere", "claude", S_ELSEWHERE, self.other, "Person Delta", "Role Delta"),
        ]
        self.registry = self.room / "ops" / "etc" / "resident-identities.json"
        self.save()
        self.notebook = self.room / "ops" / "etc" / "notebooks" / "alpha-one"
        self.notebook.mkdir(parents=True)
        self.notebook.parent.chmod(0o700)
        self.notebook.chmod(0o700)
        self.index = self.notebook / "MEMORY.md"
        self.index.write_text("- [Room facts](room-facts.md) - a note\n")
        self.index.chmod(0o600)

    @staticmethod
    def row(key, provider, session, room, person, role):
        return {"key": key, "provider": provider, "session_id": session, "room": str(room), "person": person,
                "role": role, "note": f"note for {key}", "verified": "synthetic"}

    def save(self, rows=None, raw: bytes = None):
        data = raw if raw is not None else json.dumps({"identities": self.rows if rows is None else rows}).encode()
        if self.registry.is_symlink() or self.registry.exists():
            self.registry.unlink()
        self.registry.write_bytes(data)
        self.registry.chmod(0o600)

    def run(self, *provider_args, wrapper_args=(), env=None, direct=False):
        head = [str(WRAPPER)] if direct else [sys.executable, "-I", "-B", str(WRAPPER)]
        cmd = head + ["--dry-run", "--room", str(self.room), *wrapper_args, "--", *provider_args]
        return subprocess.run(cmd, capture_output=True, text=True, timeout=60, env=env)


class WrapperTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="claude-resident-")
        self.r = Room(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def result(self, *provider_args, **kw) -> dict:
        done = self.r.run(*provider_args, **kw)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)   # no branch blocks the launch
        self.assertEqual(done.stderr, "")
        out = json.loads(done.stdout)
        self.assertEqual((out["mode"], out["executed"]), ("dry-run", False))
        self.assertEqual(out["argv"], ["<provider>", *provider_args])     # every argument passed through
        self.assert_no_registry_values(done.stdout, provider_args)
        return out

    def assert_no_registry_values(self, text: str, provider_args):
        """No registry value is printed; a session appears only where the provider's own arguments carry it."""
        passed = " ".join(provider_args)
        for row in self.r.rows:
            for field in ("key", "person", "role", "note", "room"):
                self.assertNotIn(row[field], text, field)
            if row["session_id"] not in passed:
                self.assertNotIn(row["session_id"], text)
        self.assertEqual(text.count(S_ALPHA), passed.count(S_ALPHA))

    def off(self, out: dict, branch: str, *words):
        self.assertEqual(out["branch"], branch, out["reason"])
        self.assertEqual((out["notebook"], out["auto_memory"]), ("none", "off"))
        self.assertEqual(out["env"], {"CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"})
        self.assertIsNone(out["notebook_route"])
        for word in words:
            self.assertIn(word, out["reason"])

    # -- branch 1: registered ---------------------------------------------------------
    def test_registered_attaches_the_notebook(self):
        for args in (["-p", "--resume", S_ALPHA, "--output-format", "stream-json"], [f"--resume={S_ALPHA}"],
                     ["-r", S_ALPHA], ["--session-id", S_ALPHA], [f"--session-id={S_ALPHA}", "-p"],
                     ["--resume", S_ALPHA, "--session-id", S_ALPHA]):
            with self.subTest(args=args):
                out = self.result(*args)
                self.assertEqual((out["branch"], out["notebook"]), ("registered", "attached"), out["reason"])
                self.assertEqual(out["env"], {})
                self.assertIn("unproven", out["notebook_route"])
                self.assertEqual(len(out["unproven"]), 5)

    def test_registered_without_a_usable_notebook_attaches_nothing(self):
        out = self.result("--resume", S_BETA)                              # beta-two has no folder
        self.off(out, "registered", "does not exist")
        self.r.notebook.chmod(0o755)
        self.off(self.result("--resume", S_ALPHA), "registered", "not 0700")
        self.r.notebook.chmod(0o700)
        self.r.index.chmod(0o644)
        self.off(self.result("--resume", S_ALPHA), "registered", "not 0600")
        self.r.index.chmod(0o600)
        self.r.index.write_text("<!-- mind-projection end key=beta-two -->\n")
        self.off(self.result("--resume", S_ALPHA), "registered", "another key")
        self.r.index.write_text("<!-- mind-projection begin key=alpha-one -->\n")
        self.off(self.result("--resume", S_ALPHA), "registered", "malformed")
        self.r.index.write_text("plain\n")
        moved = self.r.base / "real-notebook"
        self.r.notebook.rename(moved)
        self.r.notebook.symlink_to(moved)
        self.off(self.result("--resume", S_ALPHA), "registered", "symbolic link")

    def test_registered_needs_positive_git_exclusion(self):
        if shutil.which("git") is None:
            self.skipTest("git is not installed")
        subprocess.run(["git", "init", "-q", str(self.r.room)], check=True)
        self.off(self.result("--resume", S_ALPHA), "registered", "not ignored by Git")
        (self.r.room / ".gitignore").write_text("/ops/etc/notebooks/\n/ops/etc/*.json\n")
        self.assertEqual(self.result("--resume", S_ALPHA)["notebook"], "attached")

    # -- branch 2: registered elsewhere ----------------------------------------------
    def test_registered_elsewhere_passes_through_untouched(self):
        out = self.result("-p", "--resume", S_ELSEWHERE)
        self.assertEqual(out["branch"], "registered-elsewhere", out["reason"])
        self.assertEqual((out["notebook"], out["env"], out["notebook_route"]), ("none", {}, None))
        self.assertIn("unchanged", out["auto_memory"])
        self.assertIn("another room", out["reason"])
        here = self.r.room / "ops" / "etc" / "notebooks" / "delta-elsewhere"   # a usable folder here changes nothing
        here.mkdir()
        here.chmod(0o700)
        out = self.result("--session-id", S_ELSEWHERE)
        self.assertEqual((out["branch"], out["notebook"], out["env"]), ("registered-elsewhere", "none", {}))

    # -- branch 3: unregistered -------------------------------------------------------
    def test_unregistered_turns_auto_memory_off(self):
        self.off(self.result("--resume", S_UNKNOWN), "unregistered", "no Claude row")
        self.off(self.result("--session-id", S_CODEX), "unregistered", "no Claude row")   # a Codex row is not Claude

    # -- branch 4: ambiguous ----------------------------------------------------------
    def test_ambiguous_turns_auto_memory_off(self):
        self.off(self.result("--resume", S_ALPHA, "--session-id", S_BETA), "ambiguous", "more than one session")
        rows = self.r.rows + [Room.row("alpha-twin", "claude", S_ALPHA, self.r.room, "Person Twin", "Role Twin")]
        self.r.rows = rows
        self.r.save()
        self.off(self.result("--resume", S_ALPHA), "ambiguous", "more than one Claude row")

    # -- branch 5: new ----------------------------------------------------------------
    def test_new_turns_auto_memory_off(self):
        cases = {(): "no --resume", ("-p", "hello"): "no --resume", ("--continue",): "--continue names no session",
                 ("-c",): "-c names no session", ("--resume",): "--resume names no session",
                 ("--resume", "--verbose"): "--resume names no session",
                 ("--resume", S_ALPHA, "--fork-session"): "--fork-session",
                 ("-p", "--", "--resume", S_ALPHA): "no --resume"}
        for args, word in cases.items():
            with self.subTest(args=args):
                self.off(self.result(*args), "new", word)

    # -- branch 6: broken registry ----------------------------------------------------
    def test_broken_registry_turns_auto_memory_off(self):
        def absent():
            self.r.registry.unlink()

        def loose():
            self.r.registry.chmod(0o644)

        def unreadable():
            self.r.save(raw=b"{not json")

        def duplicate():
            self.r.save(self.r.rows + [Room.row("alpha-one", "codex", S_UNKNOWN, self.r.room, "Person X", "Role X")])

        def no_session():
            self.r.save([dict(self.r.rows[0], session_id="")] + self.r.rows[1:])

        def odd_key():
            self.r.save([dict(self.r.rows[0], key="../alpha")] + self.r.rows[1:])

        def linked():
            real = self.r.base / "registry-elsewhere.json"
            real.write_text(json.dumps({"identities": self.r.rows}))
            real.chmod(0o600)
            self.r.registry.unlink()
            self.r.registry.symlink_to(real)

        def no_list():
            self.r.save(raw=b'{"identities": {}}')

        cases = [(absent, "absent"), (loose, "not 0600"), (unreadable, "unreadable"), (duplicate, "more than one row"),
                 (no_session, "lacks"), (odd_key, "not a plain key"), (linked, "not a regular file"),
                 (no_list, "no identities list")]
        for breaker, word in cases:
            with self.subTest(case=breaker.__name__):
                self.r.save()
                breaker()
                self.off(self.result("--resume", S_ALPHA), "broken-registry", word)
                self.off(self.result(), "broken-registry", word)               # it shows even for a new run

    # -- the slice's boundary ---------------------------------------------------------
    def test_only_dry_run_and_nothing_is_executed(self):
        bin_dir = self.r.base / "bin"
        bin_dir.mkdir()
        marker = self.r.base / "provider-ran"
        fake = bin_dir / "claude"
        fake.write_text(f"#!/bin/sh\ntouch {marker}\n")
        fake.chmod(0o755)
        env = dict(os.environ, PATH=f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}")
        self.result("--resume", S_ALPHA, env=env)
        self.result("--resume", S_UNKNOWN, env=env)
        for argv in ([], ["--resume", S_ALPHA], ["--dry-run"], ["--dry-run", "--resume", S_ALPHA],
                     ["--dry-run", "--room"], ["--dry-run", "--bogus", "--"], ["--execute", "--"]):
            with self.subTest(argv=argv):
                done = subprocess.run([sys.executable, "-I", "-B", str(WRAPPER), *argv], capture_output=True,
                                      text=True, timeout=60, env=env)
                self.assertEqual(done.returncode, 2)
                self.assertEqual(done.stdout, "")
                self.assertIn("only --dry-run", done.stderr)
                self.assertNotIn(S_ALPHA, done.stderr)
        self.assertFalse(marker.exists())

    def test_the_wrapper_runs_directly(self):
        mode = stat.S_IMODE(WRAPPER.stat().st_mode)
        self.assertTrue(mode & stat.S_IXUSR)
        done = self.r.run("--resume", S_ALPHA, direct=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(json.loads(done.stdout)["notebook"], "attached")

    def test_an_explicit_registry_path_is_read(self):
        other = self.r.base / "registry.json"
        other.write_text(json.dumps({"identities": [Room.row("alpha-one", "claude", S_UNKNOWN, self.r.room, "P", "R")]}))
        other.chmod(0o600)
        out = self.result("--resume", S_UNKNOWN, wrapper_args=("--registry", str(other)))
        self.assertEqual(out["notebook"], "attached")

    def test_an_unexpected_error_fails_closed_without_blocking(self):
        stdout = io.StringIO()
        with mock.patch.object(wrapper, "load_mind", side_effect=RuntimeError("synthetic")), \
                mock.patch("sys.stdout", new=stdout):
            code = wrapper.main(["--dry-run", "--room", str(self.r.room), "--", "--resume", S_ALPHA])
        self.assertEqual(code, 0)
        out = json.loads(stdout.getvalue())
        self.off(out, "error", "could not decide")
        self.assertEqual(out["argv"], ["<provider>", "--resume", S_ALPHA])


if __name__ == "__main__":
    unittest.main(verbosity=1)
