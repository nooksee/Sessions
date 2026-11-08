#!/usr/bin/env python3
"""The host fingerprint reader, on files this suite writes in a temporary root. The live host is never read."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

TOOL = Path(__file__).resolve().parents[2] / "ops" / "lib" / "scripts" / "fingerprint.py"
SPEC = importlib.util.spec_from_file_location("fingerprint_under_test", TOOL)
fingerprint = importlib.util.module_from_spec(SPEC)
sys.modules["fingerprint_under_test"] = fingerprint
SPEC.loader.exec_module(fingerprint)

WORKING = "/media/example/working_volume"
ARCHIVE = "/media/example/archive_volume"
GOOD = {"schema_version": "host-fingerprint/1", "volume_roots": {"working": WORKING, "archive": ARCHIVE}}


class Base(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.path = self.root / "host-fingerprint.json"

    def write(self, data: object = GOOD, mode: int = 0o600) -> Path:
        if self.path.exists():
            self.path.chmod(0o600)
        self.path.write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")
        self.path.chmod(mode)
        return self.path

    def fault(self, words: str, *secrets: str) -> None:
        with self.assertRaises(fingerprint.FingerprintError) as caught:
            fingerprint.read_fingerprint(self.path)
        text = str(caught.exception)
        self.assertIn(words, text)
        for secret in (WORKING, ARCHIVE, *secrets):
            self.assertNotIn(secret, text)


class TheGoodFile(Base):
    def test_it_reads_whole(self) -> None:
        self.write()
        self.assertEqual(fingerprint.read_fingerprint(self.path), fingerprint.Fingerprint(working=WORKING, archive=ARCHIVE))

    def test_the_record_cannot_be_changed(self) -> None:
        self.write()
        with self.assertRaises(AttributeError):
            fingerprint.read_fingerprint(self.path).working = "/x"

    def test_the_default_is_the_rooms_ignored_file(self) -> None:
        self.assertEqual(fingerprint.FILE, Path(__file__).resolve().parents[2] / "ops" / "etc" / "host-fingerprint.json")
        self.assertEqual(fingerprint.read_fingerprint.__defaults__, (fingerprint.FILE,))


class TheFile(Base):
    def test_absent(self) -> None:
        self.fault("does not exist")

    def test_a_link_is_refused_even_to_a_good_file(self) -> None:
        target = self.root / "elsewhere.json"
        target.write_text(json.dumps(GOOD))
        target.chmod(0o600)
        self.path.symlink_to(target)
        self.fault("cannot be opened as a file, not a link")

    def test_a_folder(self) -> None:
        self.path.mkdir(mode=0o700)
        self.fault("is not a regular file")

    def test_a_fifo_does_not_hang(self) -> None:
        os.mkfifo(self.path, 0o600)
        self.fault("is not a regular file")

    def test_each_mode_but_0600(self) -> None:
        for mode in (0o400, 0o640, 0o604, 0o644, 0o660, 0o700, 0o666):
            with self.subTest(oct(mode)):
                self.write(mode=mode)
                self.fault("is not private")

    def test_another_owner(self) -> None:
        self.write()
        with mock.patch.object(os, "getuid", lambda: os.geteuid() + 1):
            self.fault("is not owned by this user")

    def test_unreadable_at_open(self) -> None:
        self.write()
        with mock.patch.object(os, "open", side_effect=PermissionError(13, "synthetic")):
            self.fault("cannot be opened as a file")

    def test_unreadable_at_read(self) -> None:
        self.write()
        with mock.patch.object(os, "read", side_effect=OSError(5, "synthetic")):
            self.fault("cannot be read")

    def test_a_long_file_is_read_whole(self) -> None:
        self.write(json.dumps(GOOD, indent=70000))
        self.assertEqual(fingerprint.read_fingerprint(self.path).working, WORKING)

    def test_no_descriptor_is_left_open_on_a_refusal_or_a_read(self) -> None:
        before = len(os.listdir("/proc/self/fd"))
        self.write(mode=0o644)
        self.fault("is not private")
        self.write()
        fingerprint.read_fingerprint(self.path)
        self.assertEqual(len(os.listdir("/proc/self/fd")), before)

    def test_not_utf8(self) -> None:
        self.path.write_bytes(b"\xff\xfe{}")
        self.path.chmod(0o600)
        self.fault("is not UTF-8 text")

    def test_not_json_names_the_place_and_no_text(self) -> None:
        self.write('{"schema_version": SYNTHETIC-TEXT')
        self.fault("is not valid JSON (line 1 column", "SYNTHETIC-TEXT")


class TheKeys(Base):
    def test_not_an_object(self) -> None:
        for data in (["x"], "x", 7, None):
            with self.subTest(data):
                self.write(json.dumps(data))
                self.fault("does not hold an object")

    def test_a_repeated_key_at_either_level(self) -> None:
        self.write('{"schema_version": "host-fingerprint/1", "schema_version": "host-fingerprint/1", "volume_roots": {}}')
        self.fault("repeats a key")
        self.write('{"schema_version": "host-fingerprint/1", "volume_roots": {"working": "/a", "working": "/b", "archive": "/c"}}')
        self.fault("repeats a key")

    def test_a_missing_key(self) -> None:
        for key in GOOD:
            with self.subTest(key):
                self.write({k: v for k, v in GOOD.items() if k != key})
                self.fault("must have exactly the keys")

    def test_an_extra_key_names_no_value(self) -> None:
        self.write({**GOOD, "user_name": "synthetic-user"})
        self.fault("must have exactly the keys", "synthetic-user", "user_name")

    def test_another_schema(self) -> None:
        for value in ("host-fingerprint/2", "", None, 1):
            with self.subTest(value):
                self.write({**GOOD, "schema_version": value})
                self.fault("is not schema host-fingerprint/1")

    def test_the_roots_of_another_shape(self) -> None:
        for roots in (["/a"], "/a", None, {}, {"working": WORKING}, {"archive": ARCHIVE}, {"working": WORKING, "archive": ARCHIVE, "other": "/c"}):
            with self.subTest(roots):
                self.write({**GOOD, "volume_roots": roots})
                self.fault("must have exactly the volume roots")

    def test_each_root_of_a_bad_value(self) -> None:
        for name in ("working", "archive"):
            for value in (None, 7, "", "relative/path", "two\nlines", "/with space", "/caf\u00e9", "/a;b"):
                with self.subTest(name=name, value=value):
                    self.write({**GOOD, "volume_roots": {**GOOD["volume_roots"], name: value}})
                    self.fault(f"has a volume root {name} that is not an absolute path of plain characters", *([value] if isinstance(value, str) and value else []))

    def test_each_root_not_in_its_plain_form(self) -> None:
        for name in ("working", "archive"):
            for value in ("/", "/a/", "/a//b", "/a/../b", "/a/./b"):
                with self.subTest(name=name, value=value):
                    self.write({**GOOD, "volume_roots": {**GOOD["volume_roots"], name: value}})
                    self.fault(f"has a volume root {name} that is not in its plain form", value)


class TheRefusal(Base):
    def test_the_one_message(self) -> None:
        exit_ = fingerprint.refuse("a-tool", self.path, fingerprint.FingerprintError("does not exist"))
        self.assertIsInstance(exit_, SystemExit)
        self.assertEqual(exit_.code, f"a-tool refuses: the host fingerprint file {self.path} does not exist. Nothing else was read or written.")

    def run_main(self, path: Path, *argv: str) -> tuple[int, str]:
        out = io.StringIO()
        with mock.patch.object(fingerprint, "FILE", path), contextlib.redirect_stdout(out):
            try:
                return fingerprint.main(list(argv)), out.getvalue()
            except SystemExit as exc:
                return exc.code, out.getvalue()

    def test_main_refuses_with_one_message_and_a_string_exit(self) -> None:
        code, out = self.run_main(self.path)
        self.assertEqual(code, f"fingerprint.py refuses: the host fingerprint file {self.path} does not exist. Nothing else was read or written.")
        self.assertEqual(out, "")

    def test_main_prints_no_value(self) -> None:
        self.write()
        code, out = self.run_main(self.path)
        self.assertEqual(code, 0)
        self.assertEqual(out, f"the host fingerprint file {self.path} reads whole\n")
        self.assertNotIn(WORKING, out)
        self.assertNotIn(ARCHIVE, out)

    def test_main_takes_no_argument(self) -> None:
        self.write()
        code, out = self.run_main(self.path, "--print")
        self.assertIn("it takes no argument", code)
        self.assertEqual(out, "")

    def test_nothing_is_written_on_a_refusal(self) -> None:
        self.write(mode=0o644)
        before = self.path.read_bytes(), self.path.stat().st_mode, sorted(os.listdir(self.root))
        self.fault("is not private")
        self.assertEqual((self.path.read_bytes(), self.path.stat().st_mode, sorted(os.listdir(self.root))), before)

    def test_the_command_line_exits_nonzero_where_the_file_is_absent(self) -> None:
        """A copy in a temporary room, so that the room's own ignored file is not the one asked for."""
        tool = self.root / "room" / "ops" / "lib" / "scripts" / "fingerprint.py"
        tool.parent.mkdir(parents=True)
        tool.write_bytes(TOOL.read_bytes())
        done = subprocess.run([sys.executable, "-I", "-B", str(tool)], capture_output=True, text=True, stdin=subprocess.DEVNULL)
        self.assertEqual(done.returncode, 1, done.stderr)
        self.assertIn("refuses: the host fingerprint file", done.stderr)
        self.assertEqual(done.stdout, "")



SCRIPTS = TOOL.parent


def shared_fingerprint():
    """The module each consumer loads for itself, by the key its loader uses, so that a test can point it at a file."""
    key = f"fingerprint@{TOOL.resolve()}"
    if key not in sys.modules:
        spec = importlib.util.spec_from_file_location(key, TOOL.resolve())
        module = importlib.util.module_from_spec(spec)
        sys.modules[key] = module
        spec.loader.exec_module(module)
    return sys.modules[key]


def consumer(name: str):
    spec = importlib.util.spec_from_file_location(f"{name}_under_fingerprint_test", SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)   # importing reads no fingerprint: the suites run with ops/etc empty
    return module


class TheVolumeRoot(Base):
    def test_each_root_by_name(self) -> None:
        self.write()
        with mock.patch.object(fingerprint, "FILE", self.path):
            self.assertEqual(fingerprint.volume_root("t.py", "working"), Path(WORKING))
            self.assertEqual(fingerprint.volume_root("t.py", "archive"), Path(ARCHIVE))

    def test_a_fault_refuses_for_the_tool_and_names_no_value(self) -> None:
        self.write(mode=0o644)
        with mock.patch.object(fingerprint, "FILE", self.path), self.assertRaises(SystemExit) as caught:
            fingerprint.volume_root("t.py", "working")
        text = str(caught.exception.code)
        self.assertTrue(text.startswith(f"t.py refuses: the host fingerprint file {self.path} is not private"), text)
        self.assertNotIn(WORKING, text)

    def test_an_unknown_root_is_a_programming_error_not_a_refusal(self) -> None:
        self.write()
        with mock.patch.object(fingerprint, "FILE", self.path), self.assertRaises(ValueError):
            fingerprint.volume_root("t.py", "home")


class TheConsumers(Base):
    """The 4 volume-rooted lines in this room's own code read the file where the path is used, through volume_root, under their own names."""
    CASES = (
        ("alerts", lambda m: m.extra_codex_roots(), [Path(WORKING) / "VMs/Shared/Workbench/sessions"]),
        ("telemetry", lambda m: m.default_roots()[1:], [Path(WORKING) / "VMs/Shared/Workbench/sessions"]),
        ("watch", lambda m: m.default_sessions_roots()[1:], [Path(WORKING) / "VMs/Shared/Workbench/sessions"]),
        ("retention", lambda m: [m._volume_root("archive")], [Path(ARCHIVE)]),
    )

    def test_each_derives_its_path_from_the_file(self) -> None:
        self.write()
        with mock.patch.object(shared_fingerprint(), "FILE", self.path):
            for name, call, expected in self.CASES:
                with self.subTest(name):
                    self.assertEqual(call(consumer(name)), expected)

    def test_each_refuses_under_its_own_name_without_the_file(self) -> None:
        with mock.patch.object(shared_fingerprint(), "FILE", self.path):
            for name, call, _ in self.CASES:
                with self.subTest(name), self.assertRaises(SystemExit) as caught:
                    call(consumer(name))
                self.assertTrue(str(caught.exception.code).startswith(f"{name}.py refuses: the host fingerprint file"))

    def test_alerts_keeps_a_callers_roots(self) -> None:
        alerts = consumer("alerts")
        with mock.patch.object(shared_fingerprint(), "FILE", self.path), \
                mock.patch.object(alerts, "EXTRA_CODEX_ROOTS", [Path("/media/example/vm")]):
            self.assertEqual(alerts.extra_codex_roots(), [Path("/media/example/vm")])


if __name__ == "__main__":
    unittest.main()
