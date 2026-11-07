#!/usr/bin/env python3
"""Tests for ops/bin/claude-resident, the launch wrapper (W5). Standard library only.

Every case builds its own room, registry and notebook folders in a temporary
directory. No real registry, notebook, provider or plugin setting is read or
touched. The only provider ever executed is a fake shell script, reached by
--provider or by a PATH that holds no real one. Session identifiers are invented
zero-block values. Run:

    python3 -I -B tools/test/test_claude_resident.py
"""
import calendar
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
import time
import types
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

NOT_AS_ROOT = unittest.skipIf(os.geteuid() == 0, "root ignores the modes this case relies on")

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
    """A synthetic room: a registry at 0600, a wired list at 0600 holding both Claude rows of this room, and one notebook
    folder at 0700 for the key alpha-one."""

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
        self.wired = self.room / "ops" / "etc" / "notebook-wired.json"
        self.wire("alpha-one", "beta-two")
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

    def wire(self, *keys, raw: bytes = None, mode=0o600):
        """Write the wired list, as given, or remove it when no key and no bytes are given."""
        if self.wired.is_dir() and not self.wired.is_symlink():
            self.wired.rmdir()
        elif self.wired.is_symlink() or self.wired.exists():
            self.wired.unlink()
        if keys or raw is not None:
            self.wired.write_bytes(raw if raw is not None else json.dumps(list(keys)).encode())
            self.wired.chmod(mode)

    def run(self, *provider_args, wrapper_args=(), env=None, direct=False):
        head = [str(WRAPPER)] if direct else [sys.executable, "-I", "-B", str(WRAPPER)]
        cmd = head + ["--dry-run", "--room", str(self.room), *wrapper_args, "--", *provider_args]
        return subprocess.run(cmd, capture_output=True, text=True, timeout=60, env=env, cwd=self.room)


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
        for argv in (["--dry-run"], ["--dry-run", "--resume", S_ALPHA], ["--dry-run", "--room"],
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
        self.r.wire("alpha-one")
        other = self.r.base / "registry.json"
        other.write_text(json.dumps({"identities": [Room.row("alpha-one", "claude", S_UNKNOWN, self.r.room, "P", "R")]}))
        other.chmod(0o600)
        out = self.result("--resume", S_UNKNOWN, wrapper_args=("--registry", str(other)))
        self.assertEqual(out["notebook"], "attached")

    def test_an_unexpected_error_fails_closed_without_blocking(self):
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(self.r.room)
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
        self.log = self.settings.parent / "decisions.log"

    def tearDown(self):
        self.tmp.cleanup()

    def launch(self, *provider_args, wrapper=(), env=None, stdin=b"", cwd=None, head=None):
        head = head or [sys.executable, "-I", "-B", str(WRAPPER), "--room", str(self.r.room), *wrapper, "--"]
        return subprocess.run([*head, *provider_args], input=stdin, capture_output=True, timeout=60, cwd=cwd or self.r.room,
                              env={**self.env, **(env or {})})

    def dry(self, *provider_args, cwd=None, env=None, room=None):
        done = subprocess.run([sys.executable, "-I", "-B", str(WRAPPER), "--dry-run", "--room", str(room or self.r.room), "--",
                               *provider_args], capture_output=True, text=True, timeout=60, cwd=cwd or self.r.room,
                              env={**self.env, **(env or {})})
        self.assertEqual(done.returncode, 0, done.stderr)
        return json.loads(done.stdout)

    def rows(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def enter_room(self):
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(self.r.room)

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
        self.assertEqual(sorted(os.listdir(self.settings.parent)), [self.settings.name, self.log.name])
        good = self.settings.read_text()
        for damage in (lambda: self.settings.write_text("{}"), lambda: self.settings.chmod(0o644)):
            damage()
            self.assert_ran(self.launch("--resume", S_ALPHA))
            self.assertEqual(self.settings.read_text(), good)
            self.assertEqual(stat.S_IMODE(self.settings.stat().st_mode), 0o600)
            self.assertEqual(sorted(os.listdir(self.settings.parent)), [self.settings.name, self.log.name])

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
                self.assertFalse((elsewhere / self.log.name).exists())       # the log never follows a linked folder
                if name == "the folder is loose":
                    self.assertFalse(self.log.exists())
                if os.path.lexists(home):
                    os.unlink(home) if home.is_symlink() else shutil.rmtree(home)
                (self.r.room / "logs").mkdir(exist_ok=True)
        hard_link()
        self.assert_ran(self.launch("--resume", S_ALPHA))
        self.assertEqual(self.argv()[:2], ["--settings", str(self.settings)])   # replaced: one link again
        self.assertEqual(self.settings.stat().st_nlink, 1)
        self.assertEqual((elsewhere / "other").read_text(), "x")

    @NOT_AS_ROOT
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
        self.assertFalse(self.log.exists())                               # the log is under the same Git rule
        (self.r.room / ".gitignore").write_text("/ops/etc/\n/logs/*\n")
        self.assert_ran(self.launch("--resume", S_ALPHA))
        self.assertEqual(self.argv()[:2], ["--settings", str(self.settings)])

    def test_a_failed_write_leaves_no_temporary_file_and_still_launches(self):
        saved = {s: signal.getsignal(s) for s in (signal.SIGPIPE, signal.SIGXFSZ)}
        self.addCleanup(lambda: [signal.signal(s, h) for s, h in saved.items()])
        argv = ["--room", str(self.r.room), "--provider", str(self.fake), "--", "--resume", S_ALPHA]
        self.enter_room()
        with mock.patch.object(wrapper.os, "replace", side_effect=OSError("synthetic")), \
                mock.patch.object(wrapper.os, "execve", side_effect=OSError("stop here")) as ran, \
                mock.patch("sys.stderr", new=io.StringIO()):
            self.assertEqual(wrapper.main(argv), 126)
        self.assertEqual(ran.call_args.args[2]["CLAUDE_CODE_DISABLE_AUTO_MEMORY"], "1")
        self.assertEqual(ran.call_args.args[1][1:], ["--resume", S_ALPHA])
        self.assertEqual(os.listdir(self.settings.parent), [self.log.name])
        first, second = self.rows()
        self.assertEqual((first["notebook"], first["memory_off"], first["key"]), ("none", True, "alpha-one"))
        self.assertIn("could not be written", first["reason"])
        self.assertEqual(second["provider"], "could not be executed")

    def test_a_launch_that_carries_settings_gets_memory_off(self):
        for args in (["--settings", "own.json", "--resume", S_ALPHA], [f"--settings=own.json", "--resume", S_ALPHA],
                     ["--resume", S_ALPHA, "--settings", "{}"]):
            with self.subTest(args=args):
                self.assert_ran(self.launch(*args))
                self.assert_off(args)
                self.assertFalse(self.settings.exists())
        out = json.loads(subprocess.run(
            [sys.executable, "-I", "-B", str(WRAPPER), "--dry-run", "--room", str(self.r.room), "--", "--settings", "x",
             "--resume", S_ALPHA], capture_output=True, text=True, timeout=60, cwd=self.r.room).stdout)
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
        self.assertFalse(self.settings.exists())

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
        self.assertFalse(self.settings.exists())

    def test_an_inherited_switch_is_left_on_an_attached_launch(self):
        self.assert_ran(self.launch("--resume", S_ALPHA, env={"CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"}))
        self.assertEqual(self.argv()[0], "--settings")
        self.assertEqual(self.disable(), "1")

    def test_an_error_before_the_exec_fails_closed_and_still_launches(self):
        saved = {s: signal.getsignal(s) for s in (signal.SIGPIPE, signal.SIGXFSZ)}
        self.addCleanup(lambda: [signal.signal(s, h) for s, h in saved.items()])
        argv = ["--room", str(self.r.room), "--provider", str(self.fake), "--", "--resume", S_ALPHA]
        self.enter_room()
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

    # -- no arguments: how the plugin's terminal action starts a provider ---------------------
    def test_no_arguments_is_the_bare_form_inside_the_room(self):
        done = self.launch(head=[sys.executable, "-I", "-B", str(self.installed())])
        self.assert_ran(done)
        self.assert_off([])
        self.assertEqual((self.rows()[-1]["branch"], self.rows()[-1]["notebook"]), ("new", "none"))

    def test_no_arguments_passes_through_outside_the_room(self):
        head = [sys.executable, "-I", "-B", str(self.installed())]
        for inherited in (None, "0", "1"):
            with self.subTest(inherited=inherited):
                env = {} if inherited is None else {"CLAUDE_CODE_DISABLE_AUTO_MEMORY": inherited}
                self.assert_ran(self.launch(head=head, cwd=self.r.other, env=env))
                self.assertEqual(self.argv(), [])
                self.assertEqual(self.disable(), inherited if inherited is not None else "<unset>")
                self.assertEqual(self.rows()[-1]["branch"], "outside-the-room")

    def test_no_arguments_reaches_the_provider_by_the_plugins_terminal_form(self):
        """The plugin runs: cd '<folder>' && exec '<path>', with PWD set by the shell."""
        path = self.installed()
        for folder, off in ((self.r.room, "1"), (self.r.other, "<unset>")):
            with self.subTest(folder=folder):
                done = subprocess.run(["/bin/bash", "-c", f"cd '{folder}' && exec '{path}'"], input=b"",
                                      capture_output=True, timeout=60, cwd=self.r.base, env=self.env)
                self.assert_ran(done)
                self.assertEqual((self.argv(), self.disable()), ([], off))

    # -- the wired list -----------------------------------------------------------------------
    def recorded(self, *args, through=True, env=None):
        """The environment and arguments the kernel gave a provider, byte for byte. The recorder reads its own /proc
        entries, so its interpreter's own changes do not show."""
        record = self.bin / "recorder"
        record.write_text(f"#!{sys.executable} -IB\nimport os\nc = os.environ['FAKE_CAPTURE']\n"
                          "open(c + '.environ', 'wb').write(open('/proc/self/environ', 'rb').read())\n"
                          "open(c + '.cmdline', 'wb').write(open('/proc/self/cmdline', 'rb').read())\n")
        record.chmod(0o755)
        for name in ("environ", "cmdline"):
            self.capture.with_suffix(f".{name}").unlink(missing_ok=True)
        head = [sys.executable, "-I", "-B", str(WRAPPER), "--room", str(self.r.room), "--provider", str(record), "--"] \
            if through else [str(record)]
        done = self.launch(*args, head=head, env=env)
        self.assertEqual(done.returncode, 0, done.stderr)
        return (self.capture.with_suffix(".environ").read_bytes(),
                self.capture.with_suffix(".cmdline").read_bytes().split(b"\0")[3:])

    def test_an_unwired_row_passes_through_byte_identical(self):
        self.r.wire("beta-two")
        args = ["-p", "--resume", S_ALPHA, "with space", "", "--", "--settings", "x\ny"]
        for env in ({}, {"LANG": "C.UTF-8"}, {"LANG": "C"}, {"LC_ALL": "C"}, {"LC_CTYPE": "C"}, {"LC_CTYPE": "POSIX", "LANG": "C"},
                    {"LC_CTYPE": "en_US.UTF-8"}, {"LC_CTYPE": os.fsdecode(b"\xff")}, {"LC_CTYPEX": "1"},
                    {"CLAUDE_CODE_DISABLE_AUTO_MEMORY": "0"}, {"CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"}):
            with self.subTest(env=env):
                self.assertEqual(self.recorded(*args, env=env), self.recorded(*args, through=False, env=env))
        self.assertFalse(self.settings.exists())

    def test_an_environment_entry_with_an_empty_name_is_dropped_and_the_launch_runs(self):
        self.r.wire("beta-two")
        environ, cmdline = self.recorded("-p", "--resume", S_ALPHA, env={"": "odd", "KEPT": "yes"})
        items = environ.split(b"\0")
        self.assertNotIn(b"=odd", items)
        self.assertIn(b"KEPT=yes", items)
        self.assertEqual([a.decode() for a in cmdline[:-1]], ["-p", "--resume", S_ALPHA])

    def test_a_value_error_at_the_exec_is_stated_not_a_traceback(self):
        self.enter_room()
        result = {"branch": "new", "notebook": "none", "env": {}, "reason": "x"}
        with mock.patch.object(wrapper.os, "execve", side_effect=ValueError("synthetic")):
            self.assertEqual(wrapper.launch(dict(result), self.r.room, self.fake, ["-p"]), 126)

    def test_the_other_pass_throughs_are_byte_identical_too(self):
        for args, cwd in ((["--resume", S_ELSEWHERE], None), (["--resume", S_ALPHA], self.r.other)):
            with self.subTest(args=args):
                def recorded(through):
                    return self.recorded(*args, through=through) if cwd is None else self.outside(args, through)
                self.assertEqual(recorded(True), recorded(False))

    def outside(self, args, through):
        real = self.launch
        self.launch = lambda *a, **kw: real(*a, cwd=self.r.other, **kw)
        try:
            return self.recorded(*args, through=through)
        finally:
            self.launch = real

    def test_the_locale_is_given_back_as_it_came_on_a_launch_that_changes_it(self):
        """A launch with the switch or the route still leaves the locale as it came."""
        for env in ({}, {"LC_CTYPE": "C"}):
            with self.subTest(env=env):
                environ, _ = self.recorded("-p", env=env)
                items = environ.split(b"\0")
                self.assertEqual([i for i in items if i.startswith(b"LC_CTYPE=")],
                                 [f"LC_CTYPE={v}".encode() for k, v in env.items() if k == "LC_CTYPE"])
                self.assertIn(b"CLAUDE_CODE_DISABLE_AUTO_MEMORY=1", items)

    def test_the_locale_is_left_alone_if_the_kernels_copy_cannot_be_read(self):
        env = {"LC_CTYPE": "from-python", "OTHER": "x"}
        with mock.patch.object(wrapper.Path, "read_bytes", side_effect=OSError):
            wrapper.undo_locale_coercion(env)
        self.assertEqual(env, {"LC_CTYPE": "from-python", "OTHER": "x"})

    def test_an_unwired_row_reads_as_its_own_branch_in_the_preview_and_the_log(self):
        self.r.wire("beta-two")
        out = self.dry("--resume", S_ALPHA)
        self.assertEqual((out["branch"], out["notebook"], out["env"], out["notebook_route"]),
                         ("registered-unwired", "none", {}, None))
        self.assertTrue(out["auto_memory"].startswith("unchanged"))
        self.assertEqual(out["argv"], ["<provider>", "--resume", S_ALPHA])
        self.assertNotIn("alpha-one", json.dumps(out))
        self.assert_ran(self.launch("--resume", S_ALPHA))
        row = self.rows()[-1]
        self.assertEqual((row["branch"], row["notebook"], row["memory_off"], row["key"]),
                         ("registered-unwired", "none", False, "alpha-one"))

    def test_no_list_means_nobody_is_wired(self):
        self.r.wire()
        self.assertEqual(self.dry("--resume", S_ALPHA)["branch"], "registered-unwired")
        self.assertEqual(self.dry("--resume", S_BETA)["branch"], "registered-unwired")
        self.assertEqual(self.dry("--resume", S_UNKNOWN)["branch"], "unregistered")
        self.assertEqual(self.dry("-p")["branch"], "new")

    def test_an_empty_list_wires_nobody_and_is_not_broken(self):
        self.r.wire(raw=b"[]")
        self.assertEqual(self.dry("--resume", S_ALPHA)["branch"], "registered-unwired")

    def test_a_row_on_the_list_goes_on_as_before(self):
        self.r.wire("alpha-one")
        self.assertEqual(self.dry("--resume", S_ALPHA)["notebook"], "attached")
        self.assertEqual(self.dry("--resume", S_BETA)["branch"], "registered-unwired")
        self.r.wire("beta-two", "alpha-one")
        out = self.dry("--resume", S_BETA)                                # on the list, with no folder: off, not the slot
        self.assertEqual((out["branch"], out["env"]), ("registered", {"CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"}))

    def broken_lists(self):
        """Each broken state of the list, by a function that makes it."""
        wired = self.r.wired
        target = self.r.base / "list-target"
        twin = self.r.base / "list-twin"

        def link():
            self.r.wire()
            target.write_text('["alpha-one"]')
            target.chmod(0o600)
            wired.symlink_to(target)

        def dangling():
            self.r.wire()
            wired.symlink_to(self.r.base / "nothing-here")

        def folder():
            self.r.wire()
            wired.mkdir()

        def hard_link():
            self.r.wire("alpha-one")
            twin.unlink(missing_ok=True)
            os.link(wired, twin)

        def big():
            self.r.wire(raw=b" " * (65_537 - 2) + b"[]")                 # one byte over, as a literal, so the constant cannot drift

        names_a_key = "not one Claude row of this room"
        shape = "not a list of registry keys"
        yield "a link", link, "not a regular file"
        yield "a dangling link", dangling, "not a regular file"
        yield "a folder", folder, "not a regular file"
        yield "a second hard link", hard_link, "more than one hard link"
        yield "mode 0644", lambda: self.r.wire("alpha-one", mode=0o644), "not mode 0600"
        yield "mode 0400", lambda: self.r.wire("alpha-one", mode=0o400), "not mode 0600"
        yield "over the limit", big, "larger"
        yield "not JSON", lambda: self.r.wire(raw=b"{not json"), "unreadable"
        yield "not UTF-8", lambda: self.r.wire(raw=b"\xff\xfe"), "unreadable"
        yield "an object", lambda: self.r.wire(raw=b'{"wired": ["alpha-one"]}'), shape
        yield "a string", lambda: self.r.wire(raw=b'"alpha-one"'), shape
        yield "a number in it", lambda: self.r.wire(raw=b'["alpha-one", 7]'), shape
        yield "a list in it", lambda: self.r.wire(raw=b'["alpha-one", ["beta-two"]]'), shape
        yield "a duplicate", lambda: self.r.wire(raw=b'["alpha-one", "alpha-one"]'), "twice"
        yield "a key not in the registry", lambda: self.r.wire("alpha-one", "no-such-key"), names_a_key
        yield "a key of another room", lambda: self.r.wire("alpha-one", "delta-elsewhere"), names_a_key
        yield "a key of another provider", lambda: self.r.wire("alpha-one", "gamma-codex"), names_a_key

    def test_a_broken_list_turns_memory_off_for_rows_of_this_room(self):
        for name, make, word in self.broken_lists():
            with self.subTest(state=name):
                make()
                out = self.dry("--resume", S_ALPHA)
                self.assertIn(word, out["reason"])
                self.assertEqual((out["branch"], out["notebook"], out["env"]),
                                 ("broken-wired-list", "none", {"CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"}))
                for word in ("alpha-one", "delta-elsewhere", "gamma-codex", "no-such-key", str(self.r.base)):
                    self.assertNotIn(word, out["reason"])
                self.assert_ran(self.launch("--resume", S_ALPHA, env={"CLAUDE_CODE_DISABLE_AUTO_MEMORY": "0"}))
                self.assert_off(["--resume", S_ALPHA])
                row = self.rows()[-1]
                self.assertEqual((row["branch"], row["key"], row["memory_off"]), ("broken-wired-list", "alpha-one", True))
                self.assertFalse(self.settings.exists())

    def test_a_broken_list_reaches_nothing_else(self):
        self.r.wire(raw=b"{not json")
        self.assertEqual(self.dry("--resume", S_UNKNOWN)["branch"], "unregistered")
        self.assertEqual(self.dry("-p")["branch"], "new")
        out = self.dry("--resume", S_ELSEWHERE)
        self.assertEqual((out["branch"], out["env"]), ("registered-elsewhere", {}))
        out = self.dry("--resume", S_ALPHA, cwd=self.r.other)
        self.assertEqual((out["branch"], out["env"]), ("outside-the-room", {}))

    def test_a_list_at_its_exact_limit_is_read(self):
        body = b'["alpha-one"]'
        self.r.wire(raw=b" " * (65_536 - len(body)) + body)
        self.assertEqual(self.dry("--resume", S_ALPHA)["notebook"], "attached")

    def test_a_list_that_cannot_be_inspected_is_broken_not_absent(self):
        real = os.lstat
        def lstat(path, *a, **kw):
            if str(path).endswith("notebook-wired.json"):
                raise PermissionError(13, "synthetic")
            return real(path, *a, **kw)
        with mock.patch.object(wrapper.os, "lstat", side_effect=lstat), self.assertRaises(wrapper.Broken) as caught:
            wrapper.read_wired(self.r.room, self.r.rows)
        self.assertIn("cannot be inspected", str(caught.exception))

    def test_a_list_of_another_user_is_refused(self):
        self.enter_room()
        real = os.lstat
        def lstat(path, *a, **kw):
            st = real(path, *a, **kw)
            if str(path).endswith("notebook-wired.json"):
                return os.stat_result((st.st_mode, st.st_ino, st.st_dev, st.st_nlink, os.geteuid() + 1, *st[5:]))
            return st
        with mock.patch.object(wrapper.os, "lstat", side_effect=lstat), self.assertRaises(wrapper.Broken) as caught:
            wrapper.read_wired(self.r.room, self.r.rows)
        self.assertIn("owned", str(caught.exception))

    def test_a_list_swapped_after_its_check_is_refused(self):
        real = os.open
        beside = self.r.base / "list-beside"
        beside.write_text('["alpha-one"]')
        beside.chmod(0o600)
        def swap(path, *a, **kw):
            if str(path).endswith("notebook-wired.json"):
                os.replace(beside, self.r.wired)
            return real(path, *a, **kw)
        with mock.patch.object(wrapper.os, "open", side_effect=swap), self.assertRaises(wrapper.Broken) as caught:
            wrapper.read_wired(self.r.room, self.r.rows)
        self.assertIn("changed", str(caught.exception))
        def to_a_link(path, *a, **kw):
            if str(path).endswith("notebook-wired.json"):
                self.r.wired.unlink()
                self.r.wired.symlink_to(self.r.registry)
            return real(path, *a, **kw)
        with mock.patch.object(wrapper.os, "open", side_effect=to_a_link), self.assertRaises(wrapper.Broken) as caught:
            wrapper.read_wired(self.r.room, self.r.rows)
        self.assertIn("unreadable", str(caught.exception))                 # refused by the open itself, not by the later check
        self.r.wire("alpha-one")
        def to_a_pipe(path, *a, **kw):
            if str(path).endswith("notebook-wired.json"):
                self.r.wired.unlink()
                os.mkfifo(self.r.wired)
            return real(path, *a, **kw)
        signal.signal(signal.SIGALRM, lambda *a: self.fail("the open waited on a pipe"))
        signal.alarm(10)
        try:
            with mock.patch.object(wrapper.os, "open", side_effect=to_a_pipe), self.assertRaises(wrapper.Broken) as caught:
                wrapper.read_wired(self.r.room, self.r.rows)
        finally:
            signal.alarm(0)
        self.assertRegex(str(caught.exception), "changed|unreadable")      # the open does not wait on a pipe; a reused inode number reads as unreadable

    def test_a_list_whose_row_writes_the_room_another_way_is_still_this_room(self):
        link = self.r.base / "link-to-room"
        link.symlink_to(self.r.room)
        self.r.rows[0]["room"] = str(link)
        self.r.save()
        self.assertEqual(self.dry("--resume", S_ALPHA)["notebook"], "attached")
        self.r.rows[0]["room"] = str(self.r.room)
        self.r.save()
        self.assertEqual(self.dry("--resume", S_ALPHA, room=link)["branch"], "registered")        # the list reads; the folder's rules refuse a link

    def test_a_fault_in_the_mind_tool_cannot_reach_an_unwired_launch(self):
        path = self.installed()
        self.r.wire("beta-two")
        mind = self.r.room / "ops" / "lib" / "scripts" / "mind.py"
        head = [sys.executable, "-I", "-B", str(path)]
        args = ["-p", "--resume", S_ALPHA]
        for name, make in (("removed", mind.unlink), ("broken", lambda: mind.write_text("this is not python\n")),
                           ("exits", lambda: mind.write_text("raise SystemExit(7)\n"))):
            with self.subTest(fault=name):
                mind.unlink(missing_ok=True)
                make() if name != "removed" else None
                self.assert_ran(self.launch(*args, head=head, env={"CLAUDE_CODE_DISABLE_AUTO_MEMORY": "0"}))
                self.assertEqual((self.argv(), self.disable()), (args, "0"))
                self.assertFalse(self.log.exists())               # the log's rules are the mind tool's: no row, the launch runs

    def test_a_fault_in_the_mind_tool_stops_no_wired_launch(self):
        path = self.installed()
        mind = self.r.room / "ops" / "lib" / "scripts" / "mind.py"
        head = [sys.executable, "-I", "-B", str(path)]
        args = ["-p", "--resume", S_ALPHA]
        for name, body in (("broken", "this is not python\n"), ("exits", "raise SystemExit(7)\n")):
            with self.subTest(fault=name):
                mind.write_text(body)
                self.assert_ran(self.launch(*args, head=head))
                self.assert_off(args)

    def test_a_route_that_exits_as_it_is_written_stops_no_launch(self):
        self.enter_room()
        result = {"branch": "registered", "notebook": "attached", "env": {}, "reason": "x", "_key": "alpha-one"}
        with mock.patch.object(wrapper, "write_settings", side_effect=SystemExit(7)), \
                mock.patch.object(wrapper.os, "execve", side_effect=OSError(2, "synthetic")) as execve:
            self.assertEqual(wrapper.launch(dict(result), self.r.room, self.fake, ["-p"]), 126)
        self.assertEqual(execve.call_args.args[2]["CLAUDE_CODE_DISABLE_AUTO_MEMORY"], "1")
        self.assertEqual(execve.call_args.args[1], [str(self.fake), "-p"])

    def test_the_outside_path_and_a_new_launch_survive_a_mind_tool_that_exits(self):
        path = self.installed()
        (self.r.room / "ops" / "lib" / "scripts" / "mind.py").write_text("raise SystemExit(7)\n")
        head = [sys.executable, "-I", "-B", str(path)]
        self.assert_ran(self.launch("-p", head=head))
        self.assert_off(["-p"])
        self.assert_ran(self.launch("-p", head=head, cwd=self.r.other))
        self.assertEqual((self.argv(), self.disable()), (["-p"], "<unset>"))

    # -- a failed exec under a write limit ----------------------------------------------------
    def test_a_failed_exec_under_a_write_limit_still_exits_126(self):
        self.assert_ran(self.launch("-p"))
        self.log.write_bytes(b"x" * 8192)                              # over the limit below, so the row's write hits it
        self.log.chmod(0o600)
        bad = self.bin / "bad"
        bad.write_text("#!/nonexistent/interpreter\n")
        bad.chmod(0o755)
        head = f"ulimit -f 1 && exec {sys.executable} -I -B {WRAPPER} --room {self.r.room} --provider {bad} -- -p"
        done = subprocess.run(["/bin/sh", "-c", head], capture_output=True, timeout=60, cwd=self.r.room, env=self.env)
        self.assertEqual(done.returncode, 126, done.stderr)
        self.assertIn(b"could not be executed", done.stderr)
        self.assertNotIn(b"Traceback", done.stderr)

    def test_the_exit_status_comes_through_with_standard_error_closed(self):
        bad = self.bin / "bad"
        bad.write_text("#!/nonexistent/interpreter\n")
        bad.chmod(0o755)
        plain = self.bin / "plain"
        plain.write_text("not executable")
        for named, status in ((bad, 126), (plain, 127)):
            with self.subTest(status=status):
                read, write = os.pipe()
                os.close(read)                                         # nobody will read this standard error
                try:
                    done = subprocess.run([sys.executable, "-I", "-B", str(WRAPPER), "--room", str(self.r.room), "--provider",
                                           str(named), "--", "-p"], stdout=subprocess.DEVNULL, stderr=write, stdin=subprocess.DEVNULL,
                                          timeout=60, cwd=self.r.room, env=self.env)
                finally:
                    os.close(write)
                self.assertEqual(done.returncode, status)

    # -- the working directory --------------------------------------------------------------
    def start_after(self, folder, act, *provider_args, dry=False):
        """Start the wrapper from a shell that entered the folder and then did something to it."""
        head = [sys.executable, "-I", "-B", str(WRAPPER), *(["--dry-run"] if dry else []), "--room", str(self.r.room),
                "--", *provider_args]
        return subprocess.run(["/bin/sh", "-c", f'cd "$1" && {act} && shift && exec "$@"', "sh", str(folder), *head],
                              capture_output=True, timeout=60, env=self.env, stdin=subprocess.DEVNULL, cwd=self.r.base)

    def test_a_subfolder_of_the_room_counts_as_in_the_room(self):
        sub = self.r.room / "var" / "deep"
        sub.mkdir(parents=True)
        self.assert_ran(self.launch("--resume", S_ALPHA, cwd=sub))
        self.assertEqual(self.argv()[:2], ["--settings", str(self.settings)])
        self.assertEqual(self.dry("-p", cwd=sub)["branch"], "new")

    def test_a_launch_outside_the_room_passes_through_untouched(self):
        for args in (["-p"], ["--resume", S_ALPHA], ["--resume", S_UNKNOWN], ["--resume", S_ELSEWHERE],
                     ["--resume", S_ALPHA, "--session-id", S_BETA], ["-c"]):
            for inherited, expect in ((None, "<unset>"), ("0", "0"), ("1", "1")):
                with self.subTest(args=args, inherited=inherited):
                    env = {} if inherited is None else {"CLAUDE_CODE_DISABLE_AUTO_MEMORY": inherited}
                    self.assert_ran(self.launch(*args, env=env, cwd=self.r.other))
                    self.assertEqual(self.argv(), args)
                    self.assertEqual(self.disable(), expect)
        self.assertFalse(self.settings.exists())
        out = self.dry("--resume", S_ALPHA, cwd=self.r.other)
        self.assertEqual((out["branch"], out["notebook"], out["env"], out["notebook_route"]),
                         ("outside-the-room", "none", {}, None))
        self.assertIn("unchanged", out["auto_memory"])
        self.assertEqual(out["argv"], ["<provider>", "--resume", S_ALPHA])

    def test_a_folder_whose_name_begins_with_the_rooms_is_outside_it(self):
        sibling = self.r.base / "room-two"
        sibling.mkdir()
        self.assertEqual(self.dry("--resume", S_ALPHA, cwd=sibling)["branch"], "outside-the-room")

    def test_a_room_named_through_a_link_is_still_the_room(self):
        alias = self.r.base / "alias-of-room"
        alias.symlink_to(self.r.room)
        self.assertEqual(self.dry("-p", room=alias)["branch"], "new")

    def test_outside_the_room_a_broken_registry_changes_nothing(self):
        self.r.save(raw=b"{not json")
        self.assert_ran(self.launch("--resume", S_ALPHA, cwd=self.r.other))
        self.assertEqual(self.disable(), "<unset>")
        self.assertEqual(self.dry("--resume", S_ALPHA, cwd=self.r.other)["branch"], "outside-the-room")
        self.assert_ran(self.launch("--resume", S_ALPHA))
        self.assertEqual(self.disable(), "1")
        self.assertEqual(self.rows()[-1]["branch"], "broken-registry")

    def test_a_session_of_this_room_launched_from_outside_is_logged_and_gets_no_notebook(self):
        self.assert_ran(self.launch("--resume", S_ALPHA, cwd=self.r.other))
        self.assertEqual(self.argv(), ["--resume", S_ALPHA])
        row = self.rows()[-1]
        self.assertEqual((row["branch"], row["notebook"], row["key"]), ("outside-the-room", "none", None))

    def test_an_absent_working_directory_turns_memory_off_and_does_not_block(self):
        gone = self.r.room / "gone"
        gone.mkdir()
        done = self.start_after(gone, 'rmdir "$PWD"', "--resume", S_ALPHA, dry=True)
        out = json.loads(done.stdout)
        self.assertEqual((out["branch"], out["notebook"], out["auto_memory"]), ("working-directory", "none", "off"))
        self.assertIn("absent", out["reason"])
        gone.mkdir()
        done = self.start_after(gone, 'rmdir "$PWD"', "--resume", S_ALPHA)
        self.assertEqual((done.returncode, done.stdout), (0, b"fake-out\n"))
        self.assert_off(["--resume", S_ALPHA])
        self.assertEqual(self.rows()[-1]["branch"], "working-directory")

    @NOT_AS_ROOT
    def test_an_unreadable_working_directory_turns_memory_off_and_does_not_block(self):
        locked = self.r.room / "locked"
        locked.mkdir()
        for mode in ("000", "300", "600"):
            with self.subTest(mode=mode):
                locked.chmod(0o700)
                done = self.start_after(locked, f'chmod {mode} "$PWD"', "--resume", S_ALPHA, dry=True)
                out = json.loads(done.stdout)
                self.assertEqual((out["branch"], out["auto_memory"]), ("working-directory", "off"))
                self.assertIn("cannot be read", out["reason"])
                locked.chmod(0o700)
                done = self.start_after(locked, f'chmod {mode} "$PWD"', "--resume", S_ALPHA)
                self.assertEqual((done.returncode, done.stdout), (0, b"fake-out\n"))
                self.assert_off(["--resume", S_ALPHA])
        locked.chmod(0o700)
        self.assertFalse(self.settings.exists())

    def test_a_link_through_the_room_that_resolves_elsewhere_turns_memory_off(self):
        elsewhere = self.r.base / "elsewhere-place"
        elsewhere.mkdir()
        link = self.r.room / "door"
        link.symlink_to(elsewhere)
        alias = self.r.base / "alias-of-room"
        alias.symlink_to(self.r.room)
        for pwd in (link, alias / "door"):
            with self.subTest(pwd=pwd):
                out = self.dry("--resume", S_ALPHA, cwd=link, env={"PWD": str(pwd)})
                self.assertEqual((out["branch"], out["notebook"], out["auto_memory"]), ("working-directory", "none", "off"))
                self.assertIn("link", out["reason"])
                self.assert_ran(self.launch("--resume", S_ALPHA, cwd=link, env={"PWD": str(pwd), "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "0"}))
                self.assert_off(["--resume", S_ALPHA])
                self.assertNotIn(str(elsewhere), out["reason"])

    def test_the_pwd_variable_can_only_turn_memory_off_and_only_when_it_names_this_place(self):
        elsewhere = self.r.base / "elsewhere-place"
        elsewhere.mkdir()
        door = self.r.room / "door"
        door.symlink_to(elsewhere)
        inner = self.r.room / "inner"
        inner.mkdir()
        (self.r.room / "inner-door").symlink_to(inner)
        into = self.r.base / "way-in"
        into.symlink_to(inner)
        cases = {"stale, naming the room": (elsewhere, str(self.r.room), "outside-the-room"),
                 "this place, by its own path": (elsewhere, str(elsewhere), "outside-the-room"),
                 "relative": (elsewhere, "../room/door", "outside-the-room"),
                 "absent": (elsewhere, "", "outside-the-room"),
                 "a path that is gone": (elsewhere, str(self.r.room / "no-such"), "outside-the-room"),
                 "a link in the room that stays in the room": (inner, str(self.r.room / "inner-door"), "registered"),
                 "a link outside that resolves into the room": (inner, str(into), "registered"),
                 "naming the other room while the room is here": (inner, str(self.r.other), "registered")}
        for name, (cwd, pwd, branch) in cases.items():
            with self.subTest(name):
                out = self.dry("--resume", S_ALPHA, cwd=cwd, env={"PWD": pwd})
                self.assertEqual(out["branch"], branch, out["reason"])
                self.assertEqual(out["notebook"], "attached" if branch == "registered" else "none")

    def test_a_relative_option_under_a_working_directory_that_is_gone_is_refused(self):
        gone = self.r.room / "gone"
        gone.mkdir()
        head = [sys.executable, "-I", "-B", str(WRAPPER), "--room", "relative", "--", "-p"]
        done = subprocess.run(["/bin/sh", "-c", 'cd "$1" && rmdir "$PWD" && shift && exec "$@"', "sh", str(gone), *head],
                              capture_output=True, timeout=60, env=self.env, stdin=subprocess.DEVNULL, cwd=self.r.base)
        self.assertEqual((done.returncode, done.stdout), (2, b""))
        self.assertIn(b"usage:", done.stderr)
        self.assertNotIn(b"Traceback", done.stderr)

    # -- the decision log -------------------------------------------------------------------
    def test_every_real_launch_writes_one_private_row_and_no_identifier(self):
        def check(args, branch, notebook, off, key, cwd=None):
            before = len(self.rows()) if self.log.exists() else 0
            self.assert_ran(self.launch(*args, cwd=cwd))
            rows = self.rows()
            self.assertEqual(len(rows), before + 1)
            row = rows[-1]
            self.assertEqual(sorted(row), ["branch", "key", "memory_off", "notebook", "provider", "reason", "time"])
            self.assertEqual((row["branch"], row["notebook"], row["memory_off"], row["key"], row["provider"]),
                             (branch, notebook, off, key, "found"))
            self.assertRegex(row["time"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
            self.assertTrue(row["reason"])

        check(["-p", "secret-argument", "--resume", S_ALPHA], "registered", "attached", False, "alpha-one")
        check(["--resume", S_BETA], "registered", "none", True, "beta-two")
        check(["--settings", "secret-file", "--resume", S_ALPHA], "registered", "none", True, "alpha-one")
        check(["--resume", S_ELSEWHERE], "registered-elsewhere", "none", False, None)
        check(["--resume", S_UNKNOWN], "unregistered", "none", True, None)
        check(["--resume", S_ALPHA, "--session-id", S_BETA], "ambiguous", "none", True, None)
        check(["-p", "secret-prompt"], "new", "none", True, None)
        check(["--resume", S_ALPHA], "outside-the-room", "none", False, None, cwd=self.r.other)
        rows = self.r.rows
        self.r.save(raw=b"{not json")
        check(["--resume", S_ALPHA], "broken-registry", "none", True, None)
        text = self.log.read_text()
        for row in rows:
            for field in ("session_id", "person", "role", "note", "room"):
                self.assertNotIn(row[field], text, field)
        for word in ("secret-", "delta-elsewhere", "gamma-codex", str(self.r.base)):
            self.assertNotIn(word, text)
        self.assertEqual(stat.S_IMODE(self.log.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.log.parent.stat().st_mode), 0o700)

    def test_the_row_states_a_notebook_lost_to_an_inherited_switch(self):
        self.assert_ran(self.launch("--resume", S_ALPHA, env={"CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"}))
        row = self.rows()[-1]
        self.assertEqual((row["notebook"], row["memory_off"]), ("attached", True))

    def test_the_dry_run_writes_no_row(self):
        self.dry("--resume", S_ALPHA)
        self.dry("-p")
        self.assertFalse(self.log.exists())

    def test_the_row_states_a_provider_that_was_not_found_or_could_not_run(self):
        plain = self.r.base / "plain"
        plain.write_text("not executable")
        done = self.launch("-p", wrapper=("--provider", str(plain)))
        self.assertEqual(done.returncode, 127)
        self.assertEqual(self.rows()[-1]["provider"], "none")
        bad = self.bin / "bad"
        bad.write_text("#!/nonexistent/interpreter\n")
        bad.chmod(0o755)
        done = self.launch("-p", wrapper=("--provider", str(bad)))
        self.assertEqual(done.returncode, 126)
        self.assertEqual([r["provider"] for r in self.rows()[-2:]], ["found", "could not be executed"])

    def test_a_log_in_doubt_writes_nothing_and_does_not_block(self):
        home = self.settings.parent
        home.mkdir(mode=0o700)
        elsewhere = self.r.base / "keep"
        elsewhere.write_text("keep")
        other = self.r.base / "other-link"

        def as_link():
            self.log.symlink_to(elsewhere)

        def as_fifo():
            os.mkfifo(self.log, 0o600)

        def as_folder():
            self.log.mkdir()

        def as_hard_link():
            self.log.write_text("old\n")
            self.log.chmod(0o600)
            os.link(self.log, other)

        for make in (as_link, as_fifo, as_folder, as_hard_link):
            with self.subTest(make.__name__):
                make()
                self.assert_ran(self.launch("--resume", S_ALPHA))
                self.assertEqual(self.argv()[:2], ["--settings", str(self.settings)])
                self.assertEqual(elsewhere.read_text(), "keep")
                if make is as_hard_link:
                    self.assertEqual(self.log.read_text(), "old\n")
                    self.assertEqual(other.read_text(), "old\n")
                if self.log.is_dir() and not self.log.is_symlink():
                    self.log.rmdir()
                else:
                    self.log.unlink()

    def test_the_log_checks_again_at_the_write(self):
        home = self.settings.parent
        home.mkdir(mode=0o700)
        keep = self.r.base / "keep"
        keep.write_text("keep")
        result = {"branch": "new", "notebook": "none", "reason": "synthetic"}

        def write():
            with mock.patch.object(wrapper, "place_problems", return_value=[]):
                wrapper.record(self.r.room, result, {}, "found")

        self.log.symlink_to(keep)
        write()
        self.assertEqual(keep.read_text(), "keep")
        self.log.unlink()
        os.mkfifo(self.log, 0o600)
        write()                                                      # opening a pipe with no reader must not wait
        self.assertTrue(stat.S_ISFIFO(os.lstat(self.log).st_mode))
        reader = os.open(self.log, os.O_RDONLY | os.O_NONBLOCK)
        self.addCleanup(os.close, reader)
        write()                                                      # with a reader the open succeeds; nothing is written
        self.assertEqual(os.read(reader, 4096), b"")
        self.log.unlink()
        self.log.write_text("old\n")
        self.log.chmod(0o600)
        os.link(self.log, keep.with_name("second"))
        write()
        self.assertEqual(self.log.read_text(), "old\n")
        keep.with_name("second").unlink()
        with mock.patch.object(wrapper.os, "geteuid", return_value=os.geteuid() + 1):
            write()
        self.assertEqual(self.log.read_text(), "old\n")
        write()
        self.assertEqual(len(self.log.read_text().splitlines()), 2)

    def test_a_loose_log_is_tightened_and_kept(self):
        self.log.parent.mkdir(mode=0o700)
        self.log.write_text("old\n")
        self.log.chmod(0o644)
        self.assert_ran(self.launch("-p"))
        self.assertEqual(stat.S_IMODE(self.log.stat().st_mode), 0o600)
        text = self.log.read_text().splitlines()
        self.assertEqual(text[0], "old")
        self.assertEqual(json.loads(text[1])["branch"], "new")

    def test_a_new_log_is_born_private(self):
        self.addCleanup(os.umask, os.umask(0o002))
        self.settings.parent.mkdir(mode=0o700)
        result = {"branch": "new", "notebook": "none", "reason": "synthetic"}
        with mock.patch.object(wrapper.os, "fchmod", wraps=os.fchmod) as tighten:
            wrapper.record(self.r.room, result, {}, "found")
        self.assertEqual(stat.S_IMODE(self.log.stat().st_mode), 0o600)
        tighten.assert_not_called()                                  # no moment at a looser mode to tighten from

    def test_the_log_turns_over_at_its_limit_and_keeps_one_earlier_file(self):
        self.log.parent.mkdir(mode=0o700)
        self.log.write_text("")
        self.log.chmod(0o600)
        os.truncate(self.log, wrapper.LOG_LIMIT - 1)
        self.assert_ran(self.launch("-p"))
        self.assertFalse(self.log.with_name(self.log.name + ".1").exists())
        os.truncate(self.log, wrapper.LOG_LIMIT)
        self.assert_ran(self.launch("-p"))
        earlier = self.log.with_name(self.log.name + ".1")
        self.assertEqual(earlier.stat().st_size, wrapper.LOG_LIMIT)
        self.assertEqual(stat.S_IMODE(earlier.stat().st_mode), 0o600)
        self.assertEqual(len(self.rows()), 1)

    def test_a_log_whose_earlier_file_cannot_be_placed_stays_as_it_is(self):
        if shutil.which("git") is None:
            self.skipTest("git is not installed")
        subprocess.run(["git", "init", "-q", str(self.r.room)], check=True, capture_output=True, timeout=60)
        (self.r.room / ".gitignore").write_text("/ops/etc/\n/logs/claude-resident/decisions.log\n")
        earlier = self.log.with_name(self.log.name + ".1")
        self.log.parent.mkdir(mode=0o700)
        self.log.write_text("")
        self.log.chmod(0o600)
        os.truncate(self.log, wrapper.LOG_LIMIT)
        self.assert_ran(self.launch("-p"))                           # Git would see the earlier file: no turn, no line
        self.assertFalse(earlier.exists())
        self.assertEqual(self.log.stat().st_size, wrapper.LOG_LIMIT)
        (self.r.room / ".gitignore").write_text("/ops/etc/\n/logs/*\n")
        earlier.mkdir()                                              # out of Git now, but a folder holds the name
        self.assert_ran(self.launch("-p"))
        self.assertEqual(self.log.stat().st_size, wrapper.LOG_LIMIT)
        earlier.rmdir()
        keep = self.r.base / "keep"
        keep.write_text("keep")
        earlier.symlink_to(keep)                                     # a link holds the name: it is not replaced
        self.assert_ran(self.launch("-p"))
        self.assertEqual(self.log.stat().st_size, wrapper.LOG_LIMIT)
        self.assertTrue(earlier.is_symlink())
        self.assertEqual(keep.read_text(), "keep")
        earlier.unlink()
        self.assert_ran(self.launch("-p"))                           # the place is good again: it turns over
        self.assertEqual(earlier.stat().st_size, wrapper.LOG_LIMIT)
        self.assertEqual(len(self.rows()), 1)

    def test_a_failing_log_does_not_stop_the_launch(self):
        saved = {s: signal.getsignal(s) for s in (signal.SIGPIPE, signal.SIGXFSZ)}
        self.addCleanup(lambda: [signal.signal(s, h) for s, h in saved.items()])
        self.enter_room()
        argv = ["--room", str(self.r.room), "--provider", str(self.fake), "--", "--resume", S_UNKNOWN]
        with mock.patch.object(wrapper, "make_home", side_effect=RuntimeError("synthetic")), \
                mock.patch.object(wrapper.os, "execve", side_effect=OSError("stop here")) as ran, \
                mock.patch("sys.stderr", new=io.StringIO()):
            self.assertEqual(wrapper.main(argv), 126)
        self.assertEqual(ran.call_args.args[1][1:], ["--resume", S_UNKNOWN])

    def test_two_first_launches_both_keep_the_route(self):
        real = os.mkdir

        def lose(path, mode=0o777):
            real(path, 0o700)
            raise FileExistsError(path)

        with mock.patch.object(wrapper.os, "mkdir", side_effect=lose):
            target = wrapper.write_settings(wrapper.load_mind(), self.r.room, "alpha-one")
        self.assertEqual(target, self.settings)
        self.assertTrue(self.settings.exists())
        shutil.rmtree(self.settings.parent)

        def lose_loose(path, mode=0o777):
            real(path, 0o755)
            os.chmod(path, 0o755)
            raise FileExistsError(path)

        with mock.patch.object(wrapper.os, "mkdir", side_effect=lose_loose), self.assertRaises(OSError):
            wrapper.write_settings(wrapper.load_mind(), self.r.room, "alpha-one")

    # -- the Auditor's list: the four pinned first ------------------------------------------
    def test_an_index_that_cannot_be_read_attaches_nothing(self):
        self.r.index.write_bytes(b"\xff\xfe not utf-8\n")
        out = self.dry("--resume", S_ALPHA)
        self.assertEqual((out["branch"], out["notebook"], out["auto_memory"]), ("registered", "none", "off"))
        self.assertIn("<notebook>/MEMORY.md is unreadable", out["reason"])
        self.assert_ran(self.launch("--resume", S_ALPHA))
        self.assert_off(["--resume", S_ALPHA])

    def test_a_regular_file_at_logs_gives_one_answer_from_the_preview_and_the_launch(self):
        logs = self.r.room / "logs"
        logs.rmdir()
        logs.write_text("a file")
        for mode in (0o644, 0o700):
            with self.subTest(mode=oct(mode)):
                logs.chmod(mode)
                out = self.dry("--resume", S_ALPHA)
                self.assertEqual((out["branch"], out["notebook"]), ("registered", "none"))
                self.assertIn("cannot be made", out["reason"])
                self.assert_ran(self.launch("--resume", S_ALPHA))
                self.assert_off(["--resume", S_ALPHA])
                self.assertEqual(logs.read_text(), "a file")

    def test_a_folder_named_like_the_provider_is_skipped(self):
        first = self.r.base / "folder-first"
        (first / "claude").mkdir(parents=True)
        self.assert_ran(self.launch("-p", env={"PATH": f"{first}{os.pathsep}{self.bin}{os.pathsep}{SAFE_PATH}"}))
        self.assertEqual(self.argv(), ["-p"])

    def test_a_later_dry_run_belongs_to_the_provider(self):
        self.assert_ran(self.launch("-p", "--dry-run"))
        self.assertEqual(self.argv(), ["-p", "--dry-run"])

    # -- the Auditor's list: the rest -------------------------------------------------------
    def test_a_separator_cannot_be_an_options_value(self):
        for name in ("--room", "--registry", "--provider"):
            with self.subTest(name):
                done = self.launch("-p", head=[sys.executable, "-I", "-B", str(WRAPPER), name, "--", "--"])
                self.assertEqual((done.returncode, done.stdout), (2, b""))
                self.assertIn(b"usage:", done.stderr)
                self.assertFalse(self.capture.with_suffix(".argv").exists())

    def test_a_relative_option_value_is_made_absolute(self):
        self.assert_ran(self.launch("--resume", S_ALPHA, head=[sys.executable, "-I", "-B", str(WRAPPER), "--room", ".", "--"]))
        self.assertEqual(self.argv()[:2], ["--settings", os.path.realpath(self.settings)])
        self.assertEqual(json.loads(self.settings.read_text()), {"autoMemoryDirectory": os.path.realpath(self.r.notebook)})
        out = json.loads(subprocess.run(
            [sys.executable, "-I", "-B", str(WRAPPER), "--dry-run", "--room", str(self.r.room), "--provider",
             os.path.relpath(self.fake, self.r.room), "--", "-p"], capture_output=True, text=True, timeout=60,
            cwd=self.r.room, env=self.env).stdout)
        self.assertEqual(out["provider"], os.path.realpath(self.fake))

    def test_a_fork_flag_after_the_providers_separator_is_not_read(self):
        args = ["--resume", S_ALPHA, "--", "--fork-session"]
        self.assert_ran(self.launch(*args))
        self.assertEqual(self.argv(), ["--settings", str(self.settings), *args])

    def test_an_empty_session_value_names_nothing(self):
        self.assertEqual(self.dry("--resume=")["branch"], "new")
        out = self.dry("--session-id=", "--resume", S_ALPHA)
        self.assertEqual((out["branch"], out["notebook"]), ("registered", "attached"))

    def test_a_registry_over_the_limit_is_refused_by_its_size(self):
        self.r.save(raw=json.dumps({"identities": self.r.rows, "pad": "x" * wrapper.REGISTRY_LIMIT}).encode())
        out = self.dry("--resume", S_ALPHA)
        self.assertEqual(out["branch"], "broken-registry")
        self.assertIn("larger", out["reason"])

    def test_a_registry_of_another_user_is_refused(self):
        with mock.patch.object(wrapper.os, "geteuid", return_value=os.geteuid() + 1), \
                self.assertRaises(wrapper.Broken) as caught:
            wrapper.read_rows(self.r.registry)
        self.assertIn("not owned", str(caught.exception))

    def test_a_settings_file_of_another_user_is_refused(self):
        self.settings.parent.mkdir(mode=0o700)
        self.settings.write_text("{}")
        calm = types.SimpleNamespace(private_path_problems=lambda path: [], git_exposed=lambda start, paths: [])
        self.assertEqual(wrapper.settings_problems(calm, self.r.room, "alpha-one"), [])
        with mock.patch.object(wrapper.os, "geteuid", return_value=os.geteuid() + 1):
            self.assertEqual(wrapper.settings_problems(calm, self.r.room, "alpha-one"), ["the settings file cannot be used"])

    def test_a_row_of_the_wrong_shape_is_a_broken_registry(self):
        whole, rest = self.r.rows[0], self.r.rows[1:]
        shapes = {"a number": 1, "a list": ["key"], "a string": "row"}
        for field in ("key", "provider", "session_id", "room"):
            shapes[f"{field} missing"] = {k: v for k, v in whole.items() if k != field}
            shapes[f"{field} a number"] = dict(whole, **{field: 5})
            shapes[f"{field} a list"] = dict(whole, **{field: ["x"]})
        for name, row in shapes.items():
            with self.subTest(name):
                self.r.save([row] + rest)
                out = self.dry("--resume", S_ALPHA)
                self.assertEqual(out["branch"], "broken-registry", out["reason"])
                self.assertIn("lacks", out["reason"])

    def test_a_key_with_a_trailing_newline_is_not_a_plain_key(self):
        self.r.save([dict(self.r.rows[0], key="alpha-one\n")] + self.r.rows[1:])
        out = self.dry("--resume", S_ALPHA)
        self.assertEqual(out["branch"], "broken-registry")
        self.assertIn("not a plain key", out["reason"])

    @NOT_AS_ROOT
    def test_a_logs_folder_that_cannot_be_entered_gives_one_answer(self):
        logs = self.r.room / "logs"
        logs.chmod(0o600)
        out = self.dry("--resume", S_ALPHA)
        self.assertEqual((out["branch"], out["notebook"]), ("registered", "none"))
        self.assertIn("cannot be made", out["reason"])
        self.assert_ran(self.launch("--resume", S_ALPHA))
        self.assert_off(["--resume", S_ALPHA])
        logs.chmod(0o700)
        self.assertEqual(os.listdir(logs), [])

    def test_a_row_whose_room_is_written_another_way_is_this_room(self):
        alias = self.r.base / "alias-of-room"
        alias.symlink_to(self.r.room)
        for form in (str(alias), f"{self.r.room}/"):
            with self.subTest(form=form):
                self.r.save([dict(self.r.rows[0], room=form)] + self.r.rows[1:])
                out = self.dry("--resume", S_ALPHA)
                self.assertEqual((out["branch"], out["notebook"]), ("registered", "attached"))

    def test_a_registry_swapped_after_its_check_is_refused(self):
        real_lstat = os.lstat
        other = self.r.base / "other-registry.json"
        other.write_text(json.dumps({"identities": self.r.rows}))
        other.chmod(0o600)

        def to_link(path, *a, **k):
            st = real_lstat(path, *a, **k)
            os.unlink(path)
            os.symlink(other, path)
            return st

        with mock.patch.object(wrapper.os, "lstat", side_effect=to_link), self.assertRaises(wrapper.Broken) as caught:
            wrapper.read_rows(self.r.registry)
        self.assertIn("unreadable", str(caught.exception))
        self.r.save()
        moved = self.r.base / "moved-registry.json"

        def to_new_file(path, *a, **k):
            st = real_lstat(path, *a, **k)
            os.rename(path, moved)                                  # kept, so the new file cannot reuse its inode
            shutil.copy(other, path)
            return st

        with mock.patch.object(wrapper.os, "lstat", side_effect=to_new_file), self.assertRaises(wrapper.Broken) as caught:
            wrapper.read_rows(self.r.registry)
        self.assertIn("changed", str(caught.exception))

    def test_a_link_high_above_an_absent_settings_folder_is_seen(self):
        real = self.r.base / "real-parent"
        real.mkdir()
        self.r.room.rename(real / "room")
        high = self.r.base / "high"
        high.symlink_to(real)
        problems = wrapper.settings_problems(wrapper.load_mind(), high / "room", "alpha-one")
        self.assertEqual(problems, ["a link stands in the settings folder's path"])
        (real / "room").rename(self.r.room)

    def test_the_settings_file_reaches_the_disk_before_it_replaces_the_old_one(self):
        order = []
        real_fsync, real_replace = os.fsync, os.replace
        with mock.patch.object(wrapper.os, "fsync", side_effect=lambda fd: (order.append("fsync"), real_fsync(fd))[1]), \
                mock.patch.object(wrapper.os, "replace", side_effect=lambda a, b: (order.append("replace"), real_replace(a, b))[1]):
            wrapper.write_settings(wrapper.load_mind(), self.r.room, "alpha-one")
        self.assertEqual(order, ["fsync", "replace"])

    # -- the Auditor's second list: the two pinned first ---------------------------------------
    def test_a_link_deep_through_the_room_that_resolves_elsewhere_turns_memory_off(self):
        elsewhere = self.r.base / "elsewhere-place"
        (elsewhere / "sub").mkdir(parents=True)
        (self.r.room / "door").symlink_to(elsewhere)
        deep = self.r.room / "door" / "sub"
        out = self.dry("--resume", S_ALPHA, cwd=deep, env={"PWD": str(deep)})
        self.assertEqual((out["branch"], out["notebook"], out["auto_memory"]), ("working-directory", "none", "off"))
        self.assert_ran(self.launch("--resume", S_ALPHA, cwd=deep, env={"PWD": str(deep), "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "0"}))
        self.assert_off(["--resume", S_ALPHA])

    def test_a_pwd_that_cannot_be_resolved_is_ignored_outside_the_room(self):
        a_file = self.r.room / "a-file"
        a_file.write_text("x")
        loop = self.r.room / "loop"
        loop.symlink_to(loop)
        for pwd in (a_file / "below", loop / "below"):
            with self.subTest(pwd=pwd.parent.name):
                out = self.dry("--resume", S_ALPHA, cwd=self.r.other, env={"PWD": str(pwd)})
                self.assertEqual((out["branch"], out["env"]), ("outside-the-room", {}))
                self.assert_ran(self.launch("--resume", S_ALPHA, cwd=self.r.other, env={"PWD": str(pwd)}))
                self.assertEqual(self.argv(), ["--resume", S_ALPHA])
                self.assertEqual(self.disable(), "<unset>")

    @NOT_AS_ROOT
    def test_an_unreadable_working_directory_outside_the_room_turns_memory_off(self):
        locked = self.r.other / "locked"
        locked.mkdir()
        for mode in ("000", "300", "600"):
            with self.subTest(mode=mode):
                locked.chmod(0o700)
                done = self.start_after(locked, f'chmod {mode} "$PWD"', "--resume", S_ALPHA, dry=True)
                out = json.loads(done.stdout)
                self.assertEqual((out["branch"], out["auto_memory"]), ("working-directory", "off"))
                locked.chmod(0o700)
                done = self.start_after(locked, f'chmod {mode} "$PWD"', "--resume", S_ALPHA)
                self.assertEqual((done.returncode, done.stdout), (0, b"fake-out\n"))
                self.assert_off(["--resume", S_ALPHA])
        locked.chmod(0o700)

    def test_the_row_reads_the_switch_by_its_value(self):
        for inherited, off in (("0", False), ("yes", False), ("1", True)):
            with self.subTest(inherited=inherited):
                self.assert_ran(self.launch("--resume", S_ALPHA, env={"CLAUDE_CODE_DISABLE_AUTO_MEMORY": inherited}))
                row = self.rows()[-1]
                self.assertEqual((row["notebook"], row["memory_off"]), ("attached", off))

    def test_the_rows_time_is_utc_whatever_the_zone(self):
        self.assert_ran(self.launch("-p", env={"TZ": "XXX5"}))                 # five hours behind, no zone database needed
        stamp = calendar.timegm(time.strptime(self.rows()[-1]["time"], "%Y-%m-%dT%H:%M:%SZ"))
        self.assertLess(abs(time.time() - stamp), 120)

    def test_the_log_turns_over_at_one_mebibyte_by_its_literal_size(self):
        self.log.parent.mkdir(mode=0o700)
        self.log.write_text("")
        self.log.chmod(0o600)
        os.truncate(self.log, 1_048_575)
        self.assert_ran(self.launch("-p"))
        earlier = self.log.with_name(self.log.name + ".1")
        self.assertFalse(earlier.exists())
        os.truncate(self.log, 1_048_576)
        self.assert_ran(self.launch("-p"))
        self.assertEqual(earlier.stat().st_size, 1_048_576)


if __name__ == "__main__":
    unittest.main(verbosity=1)
