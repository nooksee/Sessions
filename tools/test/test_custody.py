#!/usr/bin/env python3
"""Custody by day, on roots this suite makes in a temporary folder. The live host's custody roots are never read."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parents[2] / "ops" / "lib" / "scripts" / "custody.py"
SPEC = importlib.util.spec_from_file_location("custody_under_test", TOOL)
custody = importlib.util.module_from_spec(SPEC)
sys.modules["custody_under_test"] = custody
SPEC.loader.exec_module(custody)


class Base(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name)
        self.roots = []
        for n in ("one", "two", "three"):
            r = self.base / n
            r.mkdir(mode=0o700)
            self.roots.append(r)
        self.src = self.base / "src"
        self.src.mkdir()

    def item(self, name: str, data: bytes) -> Path:
        p = self.src / name
        p.write_bytes(data)
        return p

    def run_tool(self, *args: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        argv = list(args)
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = custody.main(argv)
        return rc, out.getvalue(), err.getvalue()

    def roots_args(self) -> list[str]:
        args = []
        for r in self.roots:
            args += ["--root", str(r)]
        return args + ["--same-device-ok"]

    def add(self, *files: Path, writer: str = "session-doctor", date: str = "20261108") -> tuple[int, str, str]:
        return self.run_tool("add", *self.roots_args(), "--writer", writer, "--date", date, *map(str, files))

    def close(self, readme: str = "Test batch.") -> tuple[int, str, str]:
        return self.run_tool("close", *self.roots_args(), "--writer", "session-doctor", "--date", "20261108", "--readme", readme)

    def batch(self, r: Path) -> Path:
        return r / "sessions-session-doctor-20261108"


class TestCustody(Base):
    def test_add_writes_every_root_private_and_equal(self) -> None:
        rc, out, err = self.add(self.item("a.txt", b"alpha\n"), self.item("b.txt", b"beta\n"))
        self.assertEqual(rc, 0, err)
        for r in self.roots:
            b = self.batch(r)
            self.assertEqual(b.stat().st_mode & 0o777, 0o700)
            self.assertEqual((b / "a.txt").read_bytes(), b"alpha\n")
            self.assertEqual((b / "a.txt").stat().st_mode & 0o777, 0o600)
            self.assertEqual((b / "MANIFEST").stat().st_mode & 0o777, 0o600)
            self.assertEqual(len((b / "MANIFEST").read_text().splitlines()), 2)
            self.assertFalse(any(p.name.endswith(".part") for p in b.iterdir()))

    def test_second_add_appends_and_keeps_earlier_rows(self) -> None:
        self.assertEqual(self.add(self.item("a.txt", b"a"))[0], 0)
        first = (self.batch(self.roots[0]) / "MANIFEST").read_text()
        self.assertEqual(self.add(self.item("b.txt", b"b"))[0], 0)
        second = (self.batch(self.roots[0]) / "MANIFEST").read_text()
        self.assertTrue(second.startswith(first))
        self.assertEqual(len(second.splitlines()), 2)

    def test_duplicate_reserved_and_bad_names_refused(self) -> None:
        self.assertEqual(self.add(self.item("a.txt", b"a"))[0], 0)
        self.assertEqual(self.add(self.item("a.txt", b"again"))[0], 2)
        self.assertEqual(self.add(self.item("MANIFEST", b"x"))[0], 2)
        self.assertEqual(self.add(self.item(".hidden", b"x"))[0], 2)
        self.assertEqual(self.add(self.item("ok.txt", b"x"), writer="Bad Key")[0], 2)
        self.assertEqual(self.add(self.item("ok2.txt", b"x"), date="20261332")[0], 2)

    def test_links_and_directories_are_not_items(self) -> None:
        link = self.src / "link.txt"
        link.symlink_to(self.item("t.txt", b"t"))
        self.assertEqual(self.add(link)[0], 2)
        self.assertEqual(self.add(self.src)[0], 2)

    def test_close_writes_sums_and_refuses_later_adds(self) -> None:
        self.add(self.item("a.txt", b"a"), self.item("b.txt", b"b"))
        rc, out, err = self.close()
        self.assertEqual(rc, 0, err)
        for r in self.roots:
            b = self.batch(r)
            sums = (b / "SHA256SUMS").read_text().splitlines()
            self.assertEqual([s.split("  ")[1] for s in sums], ["a.txt", "b.txt"])
            for n in ("SHA256SUMS", "README.txt", "CLOSED"):
                self.assertEqual((b / n).stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.add(self.item("c.txt", b"c"))[0], 2)
        self.assertEqual(self.close()[0], 2)

    def test_close_refuses_non_ascii_readme(self) -> None:
        self.add(self.item("a.txt", b"a"))
        self.assertEqual(self.close("caf" + chr(233))[0], 2)

    def test_verify_clean_then_finds_mismatch_missing_and_unlisted(self) -> None:
        self.add(self.item("a.txt", b"a"), self.item("b.txt", b"b"))
        self.close()
        name = "sessions-session-doctor-20261108"
        self.assertEqual(self.run_tool("verify", *self.roots_args(), name)[0], 0)
        b = self.batch(self.roots[1])
        (b / "a.txt").chmod(0o600)
        (b / "a.txt").write_bytes(b"changed")
        self.assertEqual(self.run_tool("verify", *self.roots_args(), name)[0], 1)
        (b / "a.txt").write_bytes(b"a")
        (b / "extra.txt").write_bytes(b"x")
        self.assertEqual(self.run_tool("verify", *self.roots_args(), name)[0], 1)
        (b / "extra.txt").unlink()
        (b / "b.txt").unlink()
        self.assertEqual(self.run_tool("verify", *self.roots_args(), name)[0], 1)

    def test_roots_that_disagree_are_refused(self) -> None:
        self.add(self.item("a.txt", b"a"))
        other = self.base / "four"
        other.mkdir()
        rc, out, err = self.run_tool("add", "--root", str(self.roots[0]), "--root", str(other), "--same-device-ok",
                                     "--writer", "session-doctor", "--date", "20261108", str(self.item("b.txt", b"b")))
        self.assertEqual(rc, 2)
        self.assertIn("disagree", err)

    def test_root_rules(self) -> None:
        f = self.item("a.txt", b"a")
        self.assertEqual(self.run_tool("add", "--root", str(self.roots[0]), "--same-device-ok", "--writer", "w", "--date", "20261108", str(f))[0], 2)
        self.assertEqual(self.run_tool("add", "--root", str(self.roots[0]), "--root", str(self.roots[0]), "--same-device-ok", "--writer", "w", "--date", "20261108", str(f))[0], 2)
        self.assertEqual(self.run_tool("add", "--root", "relative", "--root", str(self.roots[1]), "--same-device-ok", "--writer", "w", "--date", "20261108", str(f))[0], 2)
        rc, out, err = self.run_tool("add", "--root", str(self.roots[0]), "--root", str(self.roots[1]), "--writer", "w", "--date", "20261108", str(f))
        self.assertEqual(rc, 2)
        self.assertIn("share a device", err)
        self.assertFalse(os.path.lexists(self.roots[0] / "sessions-w-20261108"))

    def test_nothing_is_written_when_one_item_is_refused(self) -> None:
        rc, out, err = self.add(self.item("good.txt", b"g"), self.src)
        self.assertEqual(rc, 2)
        for r in self.roots:
            self.assertFalse(os.path.lexists(self.batch(r)))

    def test_a_corrupt_copy_is_refused_and_not_recorded(self) -> None:
        real = custody.shutil.copyfile

        def bad_copy(src, dst):
            real(src, dst)
            with open(dst, "ab") as f:
                f.write(b"corrupt")
        f = self.item("a.txt", b"a")
        from unittest import mock
        with mock.patch.object(custody.shutil, "copyfile", bad_copy):
            rc, out, err = self.add(f)
        self.assertEqual(rc, 2)
        self.assertIn("does not match its source", err)
        for r in self.roots:
            b = self.batch(r)
            self.assertFalse((b / "a.txt").exists())
            self.assertFalse((b / "MANIFEST").exists())

    def test_a_failure_on_a_later_root_removes_earlier_copies(self) -> None:
        real = custody.shutil.copyfile
        calls = []

        def second_bad(src, dst):
            real(src, dst)
            calls.append(dst)
            if len(calls) == 2:
                with open(dst, "ab") as f:
                    f.write(b"corrupt")
        from unittest import mock
        with mock.patch.object(custody.shutil, "copyfile", second_bad):
            rc, out, err = self.add(self.item("a.txt", b"a"))
        self.assertEqual(rc, 2)
        for r in self.roots:
            b = self.batch(r)
            self.assertFalse((b / "a.txt").exists())
            self.assertFalse(any(p.name.endswith(".part") for p in b.iterdir()))

    def test_an_os_error_is_a_refusal_not_a_traceback(self) -> None:
        def full(src, dst):
            raise OSError(28, "No space left on device", str(dst))
        from unittest import mock
        with mock.patch.object(custody.shutil, "copyfile", full):
            rc, out, err = self.add(self.item("a.txt", b"a"))
        self.assertEqual(rc, 2)
        self.assertIn("No space left", err)

    def test_direct_must_name_a_root(self) -> None:
        f = self.item("a.txt", b"a")
        rc, out, err = self.run_tool("add", *self.roots_args(), "--direct", str(self.base / "elsewhere"),
                                     "--writer", "session-doctor", "--date", "20261108", str(f))
        self.assertEqual(rc, 2)
        self.assertIn("names no --root", err)
        rc, out, err = self.run_tool("add", *self.roots_args(), "--direct", str(self.roots[1]) + "/",
                                     "--writer", "session-doctor", "--date", "20261108", str(f))
        self.assertEqual(rc, 0, err)

    def test_verify_refuses_a_name_outside_the_form(self) -> None:
        for bad in ("../x", "sessions-x", "other-20261108"):
            rc, out, err = self.run_tool("verify", *self.roots_args(), bad)
            self.assertEqual(rc, 2)
            self.assertIn("is not sessions-", err)

    def test_as_names_one_file(self) -> None:
        f = self.item("a.txt", b"a")
        rc, out, err = self.run_tool("add", *self.roots_args(), "--writer", "session-doctor", "--date", "20261108", "--as", "renamed.txt", str(f))
        self.assertEqual(rc, 0, err)
        self.assertTrue((self.batch(self.roots[2]) / "renamed.txt").is_file())


if __name__ == "__main__":
    unittest.main()
