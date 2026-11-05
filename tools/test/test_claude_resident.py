#!/usr/bin/env python3
"""Tests for ops/bin/claude-resident, the launch wrapper (W5). Standard library only.

Every case builds its own room, registry and notebook folders in a temporary
directory. No real registry, notebook, provider or plugin setting is read or
touched. The only provider ever executed is a fake shell script, reached by
--provider or by a PATH that holds no real one. Session identifiers are invented
zero-block values. Run:

    python3 -I -B tools/test/test_claude_resident.py
"""
import importlib.machinery
import importlib.util
import io
import json
import os
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

# No case may reach a real provider, even when a mutation check breaks the wrapper under test: this process and
# every child keep a PATH with no folder that holds a `claude`. The only `claude` on it is a tripwire, and
# tearDownModule fails the suite if anything ran it.
SAFE_PATH = os.pathsep.join(d for d in os.environ.get("PATH", "").split(os.pathsep)
                            if d and not os.path.exists(os.path.join(d, "claude")))
_TRIP = tempfile.TemporaryDirectory(prefix="claude-resident-tripwire-")
TRIPWIRE = Path(_TRIP.name) / "claude"
TRIP_MARK = Path(_TRIP.name) / "reached"
TRIPWIRE.write_text(f"#!/bin/sh\ntouch {TRIP_MARK}\nexit 99\n")
TRIPWIRE.chmod(0o755)
os.environ["PATH"] = f"{_TRIP.name}{os.pathsep}{SAFE_PATH}"


def tearDownModule():
    reached = TRIP_MARK.exists()
    _TRIP.cleanup()
    if reached:
        raise AssertionError("a case reached a provider on the suite's PATH")

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
        (self.room / "logs").mkdir()
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
        route = ["--settings", "<settings>"] if out["notebook"] == "attached" else []
        self.assertEqual(out["argv"], ["<provider>", *route, *provider_args])     # every argument passed through
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
                self.assertEqual(len(out["unproven"]), 9)

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
        (self.r.room / ".gitignore").write_text("/ops/etc/notebooks/\n/ops/etc/*.json\n/logs/*\n")
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
    def test_the_dry_run_executes_nothing_and_writes_nothing(self):
        bin_dir = self.r.base / "bin"
        bin_dir.mkdir()
        marker = self.r.base / "provider-ran"
        fake = bin_dir / "claude"
        fake.write_text(f"#!/bin/sh\ntouch {marker}\n")
        fake.chmod(0o755)
        env = dict(os.environ, PATH=f"{bin_dir}{os.pathsep}{SAFE_PATH}")
        out = self.result("--resume", S_ALPHA, env=env)
        self.assertEqual(out["provider"], str(fake))
        self.result("--resume", S_UNKNOWN, env=env)
        self.assertFalse(marker.exists())
        self.assertFalse((self.r.room / "logs" / "claude-resident").exists())

    def test_a_malformed_wrapper_form_is_refused_and_echoes_nothing(self):
        for argv in ([], ["--dry-run"], ["--dry-run", "--resume", S_ALPHA], ["--dry-run", "--room"],
                     ["--dry-run", "--bogus", "--"], ["--room"], ["--registry"], ["--provider"], ["--dry-run", "--"][:1],
                     ["--room", "--"], ["--room", str(self.r.room)], ["--registry", S_ALPHA, "-p"],
                     ["--provider", S_ALPHA, "--resume", S_ALPHA], ["--room", str(self.r.room), "--dry-run", "--"]):
            with self.subTest(argv=argv):
                done = subprocess.run([sys.executable, "-I", "-B", str(WRAPPER), *argv], capture_output=True,
                                      text=True, timeout=60)
                self.assertEqual(done.returncode, 2)
                self.assertEqual(done.stdout, "")
                self.assertIn("usage:", done.stderr)
                self.assertNotIn(S_ALPHA, done.stderr)

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


FAKE = """#!/bin/sh
for a in "$@"; do printf '%s\\0' "$a"; done > "$FAKE_CAPTURE.argv"
printf '%s' "${CLAUDE_CODE_DISABLE_AUTO_MEMORY-<unset>}" > "$FAKE_CAPTURE.disable"
cat > "$FAKE_CAPTURE.stdin"
grep '^SigIgn:' /proc/self/status > "$FAKE_CAPTURE.sigign"
pwd > "$FAKE_CAPTURE.cwd"
printf 'fake-out\\n'
printf 'fake-err\\n' >&2
exit "${FAKE_EXIT:-0}"
"""


class ExecTests(unittest.TestCase):
    """The real form, against a fake provider. The real provider is never reachable: PATH holds none."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="claude-resident-")
        self.r = Room(Path(self.tmp.name))
        self.bin = self.r.base / "bin"
        self.bin.mkdir()
        self.fake = self.bin / "claude"
        self.fake.write_text(FAKE)
        self.fake.chmod(0o755)
        self.capture = self.r.base / "capture"
        self.env = {"PATH": f"{self.bin}{os.pathsep}{SAFE_PATH}", "FAKE_CAPTURE": str(self.capture),
                    "HOME": str(self.r.base)}
        self.settings = self.r.room / "logs" / "claude-resident" / "alpha-one.settings.json"

    def tearDown(self):
        self.tmp.cleanup()

    def launch(self, *provider_args, wrapper=(), env=None, stdin=b"", cwd=None, head=None):
        head = head or [sys.executable, "-I", "-B", str(WRAPPER), "--room", str(self.r.room), *wrapper, "--"]
        return subprocess.run([*head, *provider_args], input=stdin, capture_output=True, timeout=60, cwd=cwd,
                              env={**self.env, **(env or {})})

    def dry(self, *provider_args):
        done = subprocess.run([sys.executable, "-I", "-B", str(WRAPPER), "--dry-run", "--room", str(self.r.room), "--",
                               *provider_args], capture_output=True, text=True, timeout=60, env=self.env)
        self.assertEqual(done.returncode, 0, done.stderr)
        return json.loads(done.stdout)

    def argv(self):
        return [a.decode() for a in self.capture.with_suffix(".argv").read_bytes().split(b"\0")[:-1]]

    def disable(self):
        return self.capture.with_suffix(".disable").read_text()

    def assert_ran(self, done):
        self.assertEqual((done.returncode, done.stdout, done.stderr), (0, b"fake-out\n", b"fake-err\n"))

    def assert_off(self, args):
        self.assertEqual(self.argv(), list(args))
        self.assertEqual(self.disable(), "1")

    def test_no_real_provider_is_reachable_from_this_suite(self):
        self.assertEqual(shutil.which("claude"), str(TRIPWIRE))
        self.assertEqual(wrapper.find_provider(None, dict(os.environ)), str(TRIPWIRE))
        self.assertIsNone(shutil.which("claude", path=SAFE_PATH))

    # -- the exec ---------------------------------------------------------------------------
    def test_every_argument_stream_and_status_pass_through(self):
        args = ["-p", "a b", "", "line\nbreak", "--flag=x", "--", "--resume", "*", "$HOME"]
        done = self.launch(*args, env={"FAKE_EXIT": "37"}, stdin=b"in\x00put\n", cwd=self.r.base)
        self.assertEqual((done.returncode, done.stdout, done.stderr), (37, b"fake-out\n", b"fake-err\n"))
        self.assertEqual(self.argv(), args)
        self.assertEqual(self.capture.with_suffix(".stdin").read_bytes(), b"in\x00put\n")
        self.assertEqual(self.capture.with_suffix(".cwd").read_text().strip(), os.path.realpath(self.r.base))

    def test_the_provider_inherits_no_ignored_signal_from_python(self):
        subprocess.run([str(self.fake)], input=b"", capture_output=True, env=self.env, timeout=60)
        direct = self.capture.with_suffix(".sigign").read_text()
        self.assert_ran(self.launch("-p"))
        self.assertEqual(self.capture.with_suffix(".sigign").read_text(), direct)

    # -- the route --------------------------------------------------------------------------
    def test_a_registered_launch_gets_the_route_and_nothing_else(self):
        before = self.r.index.read_bytes()
        self.assert_ran(self.launch("-p", "--resume", S_ALPHA))
        self.assertEqual(self.argv(), ["--settings", str(self.settings), "-p", "--resume", S_ALPHA])
        self.assertEqual(self.disable(), "<unset>")
        self.assertEqual(json.loads(self.settings.read_text()), {"autoMemoryDirectory": str(self.r.notebook)})
        self.assertEqual(stat.S_IMODE(self.settings.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.settings.parent.stat().st_mode), 0o700)
        self.assertEqual(self.r.index.read_bytes(), before)
        self.assertEqual(os.listdir(self.r.notebook), ["MEMORY.md"])

    def test_the_settings_file_is_stable_and_replaced_only_when_it_differs(self):
        self.launch("--resume", S_ALPHA)
        first = self.settings.stat()
        self.launch("--resume", S_ALPHA)
        again = self.settings.stat()
        self.assertEqual((first.st_ino, first.st_mtime_ns), (again.st_ino, again.st_mtime_ns))
        self.assertEqual(os.listdir(self.settings.parent), [self.settings.name])
        good = self.settings.read_text()
        for damage in (lambda: self.settings.write_text("{}"), lambda: self.settings.chmod(0o644)):
            damage()
            self.assert_ran(self.launch("--resume", S_ALPHA))
            self.assertEqual(self.settings.read_text(), good)
            self.assertEqual(stat.S_IMODE(self.settings.stat().st_mode), 0o600)
            self.assertEqual(os.listdir(self.settings.parent), [self.settings.name])

    def test_a_settings_place_in_doubt_turns_memory_off_and_does_not_block(self):
        home = self.settings.parent
        elsewhere = self.r.base / "elsewhere"
        elsewhere.mkdir(mode=0o700)

        def link_the_file():
            home.mkdir(mode=0o700)
            (elsewhere / "target").write_text("keep")
            self.settings.symlink_to(elsewhere / "target")

        def dir_as_file():
            home.mkdir(mode=0o700)
            self.settings.mkdir()

        def hard_link():
            home.mkdir(mode=0o700)
            self.settings.write_text("x")
            self.settings.chmod(0o600)
            os.link(self.settings, elsewhere / "other")

        cases = {"the folder is a link": lambda: home.symlink_to(elsewhere),
                 "the folder is loose": lambda: (home.mkdir(), home.chmod(0o755)),
                 "the file is a link": link_the_file, "a folder holds the file's name": dir_as_file,
                 "logs is absent": lambda: shutil.rmtree(self.r.room / "logs")}
        for name, make in cases.items():
            with self.subTest(name):
                make()
                out = self.dry("--resume", S_ALPHA)                     # the preview and the launch give one answer
                self.assertEqual((out["branch"], out["notebook"], out["env"]),
                                 ("registered", "none", {"CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"}), name)
                self.assertEqual(out["argv"], ["<provider>", "--resume", S_ALPHA])
                self.assert_ran(self.launch("--resume", S_ALPHA))
                self.assert_off(["--resume", S_ALPHA])
                if name == "the file is a link":
                    self.assertEqual((elsewhere / "target").read_text(), "keep")
                if os.path.lexists(home):
                    os.unlink(home) if home.is_symlink() else shutil.rmtree(home)
                (self.r.room / "logs").mkdir(exist_ok=True)
        hard_link()
        self.assert_ran(self.launch("--resume", S_ALPHA))
        self.assertEqual(self.argv()[:2], ["--settings", str(self.settings)])   # replaced: one link again
        self.assertEqual(self.settings.stat().st_nlink, 1)
        self.assertEqual((elsewhere / "other").read_text(), "x")

    def test_the_dry_run_previews_a_folder_it_would_make_without_making_it(self):
        out = self.dry("--resume", S_ALPHA)
        self.assertEqual((out["notebook"], out["env"]), ("attached", {}))
        self.assertEqual(out["argv"], ["<provider>", "--settings", "<settings>", "--resume", S_ALPHA])
        self.assertFalse(self.settings.parent.exists())
        (self.r.room / "logs").chmod(0o500)
        self.assertEqual(self.dry("--resume", S_ALPHA)["notebook"], "none")
        (self.r.room / "logs").chmod(0o700)
        (self.r.room / "logs").rename(self.r.base / "logs-real")
        (self.r.room / "logs").symlink_to(self.r.base / "logs-real")
        self.assertEqual(self.dry("--resume", S_ALPHA)["notebook"], "none")
        self.assert_ran(self.launch("--resume", S_ALPHA))
        self.assert_off(["--resume", S_ALPHA])
        self.assertFalse((self.r.base / "logs-real" / "claude-resident").exists())
        (self.r.room / "logs").unlink()
        (self.r.base / "logs-real").rename(self.r.room / "logs")

    def test_the_launch_asks_again_if_the_place_changed_after_the_decision(self):
        saved = {s: signal.getsignal(s) for s in (signal.SIGPIPE, signal.SIGXFSZ)}
        self.addCleanup(lambda: [signal.signal(s, h) for s, h in saved.items()])
        decided = {"branch": "registered", "notebook": "attached", "auto_memory": "the attached notebook", "env": {},
                   "reason": "synthetic", "notebook_route": "synthetic", "_key": "alpha-one"}
        self.settings.parent.mkdir()
        self.settings.parent.chmod(0o755)                                 # the place is in doubt only after the decision
        argv = ["--room", str(self.r.room), "--provider", str(self.fake), "--", "--resume", S_ALPHA]
        with mock.patch.object(wrapper, "decide", return_value=decided), \
                mock.patch.object(wrapper.os, "execve", side_effect=OSError("stop here")) as ran, \
                mock.patch("sys.stderr", new=io.StringIO()):
            self.assertEqual(wrapper.main(argv), 126)
        self.assertEqual(ran.call_args.args[1][1:], ["--resume", S_ALPHA])
        self.assertEqual(ran.call_args.args[2]["CLAUDE_CODE_DISABLE_AUTO_MEMORY"], "1")
        self.assertEqual(os.listdir(self.settings.parent), [])

    def test_a_second_hard_link_is_replaced_even_with_the_right_bytes(self):
        self.assert_ran(self.launch("--resume", S_ALPHA))
        other = self.r.base / "other-link"
        os.link(self.settings, other)
        self.assert_ran(self.launch("--resume", S_ALPHA))
        self.assertEqual(self.settings.stat().st_nlink, 1)
        self.assertEqual(other.read_text(), self.settings.read_text())

    def test_a_settings_file_git_would_track_turns_memory_off(self):
        if shutil.which("git") is None:
            self.skipTest("git is not installed")
        subprocess.run(["git", "init", "-q", str(self.r.room)], check=True, capture_output=True, timeout=60)
        (self.r.room / ".gitignore").write_text("/ops/etc/\n")           # the notebooks are out of Git; logs/ is not
        self.assert_ran(self.launch("--resume", S_ALPHA))
        self.assert_off(["--resume", S_ALPHA])
        self.assertFalse(self.settings.exists())
        (self.r.room / ".gitignore").write_text("/ops/etc/\n/logs/*\n")
        self.assert_ran(self.launch("--resume", S_ALPHA))
        self.assertEqual(self.argv()[:2], ["--settings", str(self.settings)])

    def test_a_failed_write_leaves_no_temporary_file_and_still_launches(self):
        saved = {s: signal.getsignal(s) for s in (signal.SIGPIPE, signal.SIGXFSZ)}
        self.addCleanup(lambda: [signal.signal(s, h) for s, h in saved.items()])
        argv = ["--room", str(self.r.room), "--provider", str(self.fake), "--", "--resume", S_ALPHA]
        with mock.patch.object(wrapper.os, "replace", side_effect=OSError("synthetic")), \
                mock.patch.object(wrapper.os, "execve", side_effect=OSError("stop here")) as ran, \
                mock.patch("sys.stderr", new=io.StringIO()):
            self.assertEqual(wrapper.main(argv), 126)
        self.assertEqual(ran.call_args.args[2]["CLAUDE_CODE_DISABLE_AUTO_MEMORY"], "1")
        self.assertEqual(ran.call_args.args[1][1:], ["--resume", S_ALPHA])
        self.assertEqual(os.listdir(self.settings.parent), [])

    def test_a_launch_that_carries_settings_gets_memory_off(self):
        for args in (["--settings", "own.json", "--resume", S_ALPHA], [f"--settings=own.json", "--resume", S_ALPHA],
                     ["--resume", S_ALPHA, "--settings", "{}"]):
            with self.subTest(args=args):
                self.assert_ran(self.launch(*args))
                self.assert_off(args)
                self.assertFalse(self.settings.exists())
        out = json.loads(subprocess.run(
            [sys.executable, "-I", "-B", str(WRAPPER), "--dry-run", "--room", str(self.r.room), "--", "--settings", "x",
             "--resume", S_ALPHA], capture_output=True, text=True, timeout=60).stdout)
        self.assertEqual((out["branch"], out["notebook"], out["auto_memory"]), ("registered", "none", "off"))
        self.assertIn("--settings", out["reason"])

    def test_settings_after_the_providers_own_separator_is_not_a_settings_source(self):
        args = ["--resume", S_ALPHA, "--", "--settings"]
        self.assert_ran(self.launch(*args))
        self.assertEqual(self.argv(), ["--settings", str(self.settings), *args])

    # -- the other branches -----------------------------------------------------------------
    def test_registered_elsewhere_is_untouched(self):
        for inherited, expect in ((None, "<unset>"), ("0", "0"), ("1", "1")):
            with self.subTest(inherited=inherited):
                env = {} if inherited is None else {"CLAUDE_CODE_DISABLE_AUTO_MEMORY": inherited}
                self.assert_ran(self.launch("-p", "--resume", S_ELSEWHERE, env=env))
                self.assertEqual(self.argv(), ["-p", "--resume", S_ELSEWHERE])
                self.assertEqual(self.disable(), expect)
        self.assertFalse(self.settings.parent.exists())

    def test_every_other_branch_turns_memory_off_even_against_an_inherited_zero(self):
        cases = {"unregistered": ["--resume", S_UNKNOWN], "new": ["-p"], "continue": ["-c"],
                 "fork": ["--resume", S_ALPHA, "--fork-session"], "ambiguous": ["--resume", S_ALPHA, "--session-id", S_BETA],
                 "other provider": ["--resume", S_CODEX], "no notebook": ["--resume", S_BETA]}
        for name, args in cases.items():
            with self.subTest(name):
                self.assert_ran(self.launch(*args, env={"CLAUDE_CODE_DISABLE_AUTO_MEMORY": "0"}))
                self.assert_off(args)
        self.r.save(raw=b"{not json")
        self.assert_ran(self.launch("--resume", S_ALPHA))
        self.assert_off(["--resume", S_ALPHA])
        self.assertFalse(self.settings.parent.exists())

    def test_an_inherited_switch_is_left_on_an_attached_launch(self):
        self.assert_ran(self.launch("--resume", S_ALPHA, env={"CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"}))
        self.assertEqual(self.argv()[0], "--settings")
        self.assertEqual(self.disable(), "1")

    def test_an_error_before_the_exec_fails_closed_and_still_launches(self):
        saved = {s: signal.getsignal(s) for s in (signal.SIGPIPE, signal.SIGXFSZ)}
        self.addCleanup(lambda: [signal.signal(s, h) for s, h in saved.items()])
        argv = ["--room", str(self.r.room), "--provider", str(self.fake), "--", "--resume", S_ALPHA]
        for target, name in ((wrapper, "load_mind"), (wrapper, "write_settings")):
            with self.subTest(name), mock.patch.object(target, name, side_effect=RuntimeError("synthetic")), \
                    mock.patch.object(wrapper.os, "execve", side_effect=OSError("stop here")) as ran, \
                    mock.patch("sys.stderr", new=io.StringIO()):
                self.assertEqual(wrapper.main(argv), 126)
                path, passed, env = ran.call_args.args
                self.assertEqual(path, str(self.fake))
                self.assertEqual(passed[1:], ["--resume", S_ALPHA])
                self.assertEqual(env["CLAUDE_CODE_DISABLE_AUTO_MEMORY"], "1")

    # -- finding the provider ---------------------------------------------------------------
    def test_the_first_claude_on_path_runs_never_this_wrapper_or_a_relative_entry(self):
        loop = self.r.base / "loop"
        loop.mkdir()
        (loop / "claude").symlink_to(WRAPPER)
        here = self.r.base / "cwd"
        here.mkdir()
        trap = here / "claude"
        trap.write_text(f"#!/bin/sh\ntouch {self.r.base / 'trap-ran'}\n")
        trap.chmod(0o755)
        path = os.pathsep.join(["", ".", str(loop), str(self.bin), SAFE_PATH])
        self.assert_ran(self.launch("-p", env={"PATH": path}, cwd=here))
        self.assertFalse((self.r.base / "trap-ran").exists())
        self.assertEqual(self.argv(), ["-p"])

    def test_no_provider_is_stated_and_echoes_nothing(self):
        empty = self.r.base / "empty"
        empty.mkdir()
        plain = self.r.base / "plain"
        plain.write_text("not executable")
        for wrapper_args, env in (((), {"PATH": str(empty)}), (("--provider", str(plain)), {}),
                                  (("--provider", str(WRAPPER)), {})):
            with self.subTest(wrapper_args=wrapper_args):
                done = self.launch("--resume", S_ALPHA, wrapper=wrapper_args, env=env)
                self.assertEqual((done.returncode, done.stdout), (127, b""))
                self.assertIn(b"no provider", done.stderr)
                self.assertNotIn(S_ALPHA.encode(), done.stderr)

    def test_a_provider_that_cannot_run_is_stated(self):
        bad = self.bin / "bad"
        bad.write_text("#!/nonexistent/interpreter\n")
        bad.chmod(0o755)
        done = self.launch("-p", wrapper=("--provider", str(bad)))
        self.assertEqual((done.returncode, done.stdout), (126, b""))
        self.assertIn(b"could not be executed", done.stderr)

    def test_the_provider_option_is_used(self):
        other = self.bin / "other-name"
        shutil.copy(self.fake, other)
        self.assert_ran(self.launch("-p", wrapper=("--provider", str(other)), env={"PATH": SAFE_PATH}))
        self.assertEqual(self.argv(), ["-p"])

    def test_a_wrapper_may_be_reached_by_its_interpreter_line(self):
        done = self.launch("-p", head=[str(WRAPPER), "--room", str(self.r.room), "--"])
        self.assert_ran(done)

    # -- the bare form ----------------------------------------------------------------------
    def installed(self) -> Path:
        """A copy of the wrapper and the mind tool inside the synthetic room, so the bare form's defaults stay there."""
        real_scripts = WRAPPER.parents[1] / "lib" / "scripts"
        (self.r.room / "ops" / "bin").mkdir(exist_ok=True)
        (self.r.room / "ops" / "lib" / "scripts").mkdir(parents=True, exist_ok=True)
        shutil.copy(WRAPPER, self.r.room / "ops" / "bin" / "claude-resident")
        shutil.copy(real_scripts / "mind.py", self.r.room / "ops" / "lib" / "scripts" / "mind.py")
        return self.r.room / "ops" / "bin" / "claude-resident"

    def test_the_bare_form_applies_the_defaults_and_passes_everything(self):
        head = [sys.executable, "-I", "-B", str(self.installed())]
        args = ["-p", "--output-format", "stream-json", "--resume", S_ALPHA, "--permission-mode", "bypassPermissions"]
        self.assert_ran(self.launch(*args, head=head))
        self.assertEqual(self.argv(), ["--settings", str(self.settings), *args])
        self.assert_ran(self.launch("-p", "--resume", S_UNKNOWN, head=head))
        self.assert_off(["-p", "--resume", S_UNKNOWN])

    def test_in_the_bare_form_every_argument_is_the_providers(self):
        head = [sys.executable, "-I", "-B", str(self.installed())]
        for args in (["-p", "--", "--resume"], ["-p", "--room", "/elsewhere"], ["-p", "--registry", "/elsewhere"],
                     ["-p", "--provider", "/elsewhere"], ["-p", "--dry-run"], ["--execute", "--"], ["literal", "--"]):
            with self.subTest(args=args):
                self.assert_ran(self.launch(*args, head=head))
                self.assert_off(args)

    def test_a_first_argument_equal_to_a_wrapper_option_is_the_wrappers(self):
        head = [sys.executable, "-I", "-B", str(self.installed())]
        for args in (["--dry-run"], ["--room"], ["--registry"], ["--provider"], ["--room", "x", "-p"],
                     ["--provider", str(self.fake), "-p"]):
            with self.subTest(args=args):
                done = self.launch(*args, head=head)
                self.assertEqual((done.returncode, done.stdout), (2, b""))
                self.assertIn(b"usage:", done.stderr)
                self.assertFalse(self.capture.with_suffix(".argv").exists())

    def test_the_explicit_form_keeps_a_separator_as_the_wrappers(self):
        self.assert_ran(self.launch("--", "x", head=[sys.executable, "-I", "-B", str(WRAPPER), "--room", str(self.r.room), "--"]))
        self.assertEqual(self.argv(), ["--", "x"])
        self.assert_ran(self.launch("-p", head=[sys.executable, "-I", "-B", str(self.installed()), "--"]))
        self.assertEqual(self.argv(), ["-p"])


if __name__ == "__main__":
    unittest.main(verbosity=1)
