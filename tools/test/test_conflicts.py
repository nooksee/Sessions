#!/usr/bin/env python3
"""Focused tests for exact Codex thread-writer holder classification and reading."""

from __future__ import annotations

import contextlib
import fcntl
import importlib.util
import io
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[2] / "ops" / "lib" / "scripts" / "conflicts.py"
SPEC = importlib.util.spec_from_file_location("writer_conflicts", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
conflicts = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(conflicts)

THREAD_A = "00000000-0000-0000-0000-00000000000a"
THREAD_B = "00000000-0000-0000-0000-00000000000b"
EDITOR_EXE = "/opt/PyCharm/acp-agents/codex-acp"
DAEMON_EXE = "/opt/codex/standalone/codex"
OTHER_EXE = "/usr/bin/python3"


class HolderClassificationTests(unittest.TestCase):
    def test_editor_bridge(self) -> None:
        self.assertEqual(
            conflicts.classify_holder(
                "/home/example/.cache/JetBrains/PyCharm/acp-agents/codex-acp",
                "codex-acp",
            ),
            "editor-bridge",
        )

    def test_remote_daemon(self) -> None:
        self.assertEqual(
            conflicts.classify_holder(
                "/home/example/.codex/packages/standalone/current/codex",
                "codex app-server --remote-control --listen unix://",
            ),
            "background-daemon",
        )

    def test_visible_resume_console(self) -> None:
        self.assertEqual(
            conflicts.classify_holder(
                "/home/example/.codex/packages/standalone/current/codex",
                "codex resume 00000000-0000-0000-0000-000000000000",
            ),
            "terminal-cli",
        )

    def test_ordinary_terminal_cli(self) -> None:
        self.assertEqual(
            conflicts.classify_holder(
                "/home/example/.local/bin/codex",
                "codex",
            ),
            "terminal-cli",
        )

    def test_unrelated_process(self) -> None:
        self.assertEqual(
            conflicts.classify_holder("/usr/bin/python3", "python3 worker.py"),
            "unknown",
        )


class HomeSelectionTests(unittest.TestCase):
    def test_provider_variable_wins(self) -> None:
        self.assertEqual(
            conflicts.codex_home({"CODEX_HOME": "/elsewhere/home"}),
            (Path("/elsewhere/home"), "CODEX_HOME"),
        )

    def test_empty_variable_is_the_default(self) -> None:
        self.assertEqual(
            conflicts.codex_home({"CODEX_HOME": ""}),
            (Path.home() / ".codex", "default"),
        )

    def test_absent_variable_is_the_default(self) -> None:
        self.assertEqual(conflicts.codex_home({}), (Path.home() / ".codex", "default"))


class FakeHost:
    """A process table and a Codex home in a temporary folder."""

    def __init__(self, root: Path) -> None:
        self.proc = root / "proc"
        self.proc.mkdir()
        self.home = root / "home" / ".codex"
        self.locks = self.home / "thread-writer-locks"
        self.locks.mkdir(parents=True)

    def lock(self, thread: str = THREAD_A) -> Path:
        path = self.locks / f"{thread}.lock"
        path.write_text("", encoding="ascii")
        return path

    def process(self, pid: int, exe: str, cmd: str, *fds: Path) -> Path:
        entry = self.proc / str(pid)
        (entry / "fd").mkdir(parents=True)
        (entry / "exe").symlink_to(exe)
        (entry / "cmdline").write_bytes(cmd.encode("ascii").replace(b" ", b"\0"))
        for number, target in enumerate(fds, start=3):
            (entry / "fd" / str(number)).symlink_to(target)
        return entry

    def table(self, *rows: str) -> None:
        (self.proc / "locks").write_text("".join(f"{row}\n" for row in rows), encoding="ascii")

    def row(self, path: Path, pid: int = 7, number: int = 1) -> str:
        seen = path.stat()
        return (
            f"{number}: FLOCK  ADVISORY  WRITE {pid} "
            f"{os.major(seen.st_dev):02x}:{os.minor(seen.st_dev):02x}:{seen.st_ino} 0 EOF"
        )


class ReadingTests(unittest.TestCase):
    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.host = FakeHost(Path(folder.name))
        for name, value in (
            ("PROC", self.host.proc),
            ("CODEX", self.host.home),
            ("CODEX_SOURCE", "default"),
            ("LOCKS", self.host.locks),
            ("STATE", self.host.home / "state_5.sqlite"),
        ):
            patcher = mock.patch.object(conflicts, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = mock.patch.object(conflicts, "registry", lambda: {})
        patcher.start()
        self.addCleanup(patcher.stop)

    def in_order(self, *rows: tuple[int, str]) -> None:
        """Set the order the process walk meets these; a fake folder gives no order of its own."""
        procs = {pid: {"exe": "", "cmd": "", "kind": kind} for pid, kind in rows}
        patcher = mock.patch.object(conflicts, "holders", lambda: (procs, 0))
        patcher.start()
        self.addCleanup(patcher.stop)

    def one(self) -> dict:
        findings = conflicts.collect()["findings"]
        self.assertEqual(len(findings), 1)
        return findings[0]

    def run_main(self, *argv: str) -> tuple[int, str]:
        out = io.StringIO()
        code = 0
        with mock.patch.object(sys, "argv", ["conflicts.py", *argv]), contextlib.redirect_stdout(out):
            try:
                conflicts.main()
            except SystemExit as stop:
                code = stop.code
        return code, out.getvalue()

    def test_one_editor_holder_with_the_kernel_lock(self) -> None:
        lock = self.host.lock()
        self.host.process(7, EDITOR_EXE, "codex-acp", lock)
        self.host.table(self.host.row(lock, 7))
        finding = self.one()
        self.assertEqual(finding["thread"], THREAD_A)
        self.assertEqual(finding["holder_pid"], 7)
        self.assertEqual(finding["holder_kind"], "editor-bridge")
        self.assertEqual(finding["holder_count"], 1)
        self.assertEqual(finding["holders"], [{"pid": 7, "kind": "editor-bridge"}])
        self.assertEqual(finding["holder_state"], "held")
        self.assertEqual(finding["kernel_lock"], "locked")
        self.assertEqual(finding["kernel_lock_pids"], [7])
        self.assertFalse(finding["blocks_editor"])
        self.assertTrue(finding["blocks_other_writer"])
        self.assertFalse(finding["stale"])

    def test_every_holder_is_listed_and_any_blocker_blocks(self) -> None:
        lock = self.host.lock()
        self.host.process(7, EDITOR_EXE, "codex-acp", lock)
        self.host.process(8, DAEMON_EXE, "codex app-server --remote-control", lock)
        self.host.table(self.host.row(lock, 7))
        finding = self.one()
        self.assertEqual(finding["holder_count"], 2)
        self.assertEqual(
            sorted(h["kind"] for h in finding["holders"]),
            ["background-daemon", "editor-bridge"],
        )
        self.assertEqual(finding["holder_pid"], finding["holders"][0]["pid"])
        self.assertEqual(finding["holder_kind"], finding["holders"][0]["kind"])
        self.assertTrue(finding["blocks_editor"])

    def test_one_process_with_two_descriptors_is_one_holder(self) -> None:
        lock = self.host.lock()
        self.host.process(7, EDITOR_EXE, "codex-acp", lock, lock)
        self.host.table(self.host.row(lock, 7))
        self.assertEqual(self.one()["holder_count"], 1)

    def test_daemon_holder_keeps_the_field_the_janitor_reads(self) -> None:
        lock = self.host.lock()
        self.host.process(8, DAEMON_EXE, "codex app-server --remote-control", lock)
        self.host.table(self.host.row(lock, 8))
        finding = self.one()
        self.assertEqual(finding["holder_kind"], "background-daemon")
        self.assertEqual(finding["holder_pid"], 8)

    def test_holder_outside_the_codex_processes_is_unknown(self) -> None:
        lock = self.host.lock()
        self.host.process(9, OTHER_EXE, "python3 worker.py", lock)
        self.host.table(self.host.row(lock, 9))
        finding = self.one()
        self.assertEqual(finding["holder_kind"], "unknown")
        self.assertEqual(finding["holder_pid"], 9)
        self.assertTrue(finding["blocks_editor"])

    def test_locked_with_no_visible_holder_is_not_gone(self) -> None:
        lock = self.host.lock()
        self.host.table(self.host.row(lock, 41))
        finding = self.one()
        self.assertEqual(finding["holder_state"], "held-unseen")
        self.assertEqual(finding["holder_kind"], "unknown")
        self.assertIsNone(finding["holder_pid"])
        self.assertEqual(finding["kernel_lock_pids"], [41])
        self.assertFalse(finding["stale"])
        self.assertTrue(finding["blocks_editor"])
        self.assertTrue(finding["blocks_other_writer"])

    def test_stale_needs_the_kernel_table_to_agree(self) -> None:
        self.host.lock()
        self.host.table()
        finding = self.one()
        self.assertEqual(finding["holder_state"], "stale")
        self.assertEqual(finding["holder_kind"], "gone")
        self.assertIsNone(finding["holder_pid"])
        self.assertTrue(finding["stale"])
        self.assertFalse(finding["blocks_editor"])
        self.assertFalse(finding["blocks_other_writer"])

    def test_no_table_and_no_holder_is_unknown_and_never_stale(self) -> None:
        self.host.lock()
        finding = self.one()
        self.assertEqual(finding["holder_state"], "unknown")
        self.assertEqual(finding["kernel_lock"], "unknown")
        self.assertEqual(finding["holder_kind"], "unknown")
        self.assertFalse(finding["stale"])
        self.assertTrue(finding["blocks_editor"])
        self.assertTrue(finding["blocks_other_writer"])
        self.assertFalse(conflicts.collect()["coverage"]["lock_table_read"])

    def test_a_row_that_cannot_be_parsed_makes_the_table_unread(self) -> None:
        self.host.lock()
        self.host.table("1: a format nobody has seen")
        finding = self.one()
        self.assertEqual(finding["kernel_lock"], "unknown")
        self.assertFalse(finding["stale"])

    def test_a_good_row_does_not_excuse_a_bad_one(self) -> None:
        lock = self.host.lock()
        self.host.table(self.host.row(lock, 7), "2: a format nobody has seen")
        self.assertEqual(self.one()["kernel_lock"], "unknown")

    def test_a_byte_that_is_not_ascii_makes_the_table_unread(self) -> None:
        self.host.lock()
        (self.host.proc / "locks").write_bytes(b"1: FLOCK \xff\n")
        self.assertEqual(conflicts.kernel_locks(), ({}, False))
        self.assertEqual(self.one()["kernel_lock"], "unknown")

    def test_a_device_number_with_letters_reads_in_hex(self) -> None:
        self.host.table("1: FLOCK  ADVISORY  WRITE 7 fd:2f:123 0 EOF")
        table, read = conflicts.kernel_locks()
        self.assertTrue(read)
        self.assertEqual(table, {(0xfd, 0x2f, 123): [7]})
        identity = (os.makedev(0xfd, 0x2f), 123)
        self.assertEqual(conflicts.kernel_state(identity, table, True), ("locked", [7]))

    def test_a_lock_file_gone_before_its_stat_is_unknown_and_never_stale(self) -> None:
        (self.host.locks / f"{THREAD_A}.lock").symlink_to(self.host.home / "nowhere")
        self.host.table()
        finding = self.one()
        self.assertEqual(finding["kernel_lock"], "unknown")
        self.assertEqual(finding["holder_state"], "unknown")
        self.assertFalse(finding["stale"])
        self.assertEqual(conflicts.kernel_state(None, {}, True), ("unknown", []))

    def test_a_blank_line_is_not_a_bad_row(self) -> None:
        self.host.lock()
        self.host.table("")
        self.assertEqual(self.one()["kernel_lock"], "not-locked")

    def test_a_waiter_is_no_holder(self) -> None:
        lock = self.host.lock()
        seen = lock.stat()
        self.host.table(
            f"1: -> FLOCK  ADVISORY  WRITE 7 "
            f"{os.major(seen.st_dev):02x}:{os.minor(seen.st_dev):02x}:{seen.st_ino} 0 EOF"
        )
        self.assertEqual(self.one()["kernel_lock"], "not-locked")

    def test_the_same_inode_on_another_device_is_unknown(self) -> None:
        lock = self.host.lock()
        seen = lock.stat()
        self.host.table(f"1: FLOCK  ADVISORY  WRITE 7 ff:fe:{seen.st_ino} 0 EOF")
        self.assertEqual(self.one()["kernel_lock"], "unknown")

    def test_another_file_on_the_table_leaves_this_one_not_locked(self) -> None:
        lock = self.host.lock()
        seen = lock.stat()
        self.host.table(
            f"1: FLOCK  ADVISORY  WRITE 7 "
            f"{os.major(seen.st_dev):02x}:{os.minor(seen.st_dev):02x}:{seen.st_ino + 1} 0 EOF"
        )
        self.assertEqual(self.one()["kernel_lock"], "not-locked")

    def test_the_kernel_pids_come_back_sorted(self) -> None:
        lock = self.host.lock()
        self.host.table(self.host.row(lock, 9, 1), self.host.row(lock, 4, 2))
        self.assertEqual(self.one()["kernel_lock_pids"], [4, 9])

    def test_open_without_a_lock_is_said(self) -> None:
        lock = self.host.lock()
        self.host.process(7, EDITOR_EXE, "codex-acp", lock)
        self.host.table()
        finding = self.one()
        self.assertEqual(finding["holder_state"], "open-not-locked")
        self.assertEqual(finding["holder_kind"], "editor-bridge")
        self.assertTrue(finding["blocks_other_writer"])

    def test_an_open_holder_with_no_table_stays_held(self) -> None:
        lock = self.host.lock()
        self.host.process(7, EDITOR_EXE, "codex-acp", lock)
        finding = self.one()
        self.assertEqual(finding["holder_state"], "held")
        self.assertEqual(finding["kernel_lock"], "unknown")

    def test_a_descriptor_in_another_home_is_counted_and_holds_nothing(self) -> None:
        self.host.lock()
        other = self.host.home.parent / "other" / "thread-writer-locks"
        other.mkdir(parents=True)
        foreign = other / f"{THREAD_A}.lock"
        foreign.write_text("", encoding="ascii")
        self.host.process(7, EDITOR_EXE, "codex-acp", foreign)
        self.host.table()
        result = conflicts.collect()
        self.assertEqual(result["coverage"]["lock_fds_other_home"], 1)
        self.assertEqual(result["coverage"]["lock_fds_unlisted"], 0)
        self.assertEqual(result["findings"][0]["holder_count"], 0)

    def test_an_unrelated_descriptor_is_not_read_as_a_lock(self) -> None:
        self.host.lock()
        ordinary = self.host.home / "ordinary.log"
        ordinary.write_text("", encoding="ascii")
        self.host.process(7, EDITOR_EXE, "codex-acp", ordinary)
        self.host.table()
        coverage = conflicts.collect()["coverage"]
        self.assertEqual(coverage["lock_fds_other_home"], 0)
        self.assertEqual(coverage["lock_fds_unlisted"], 0)

    def test_the_same_file_by_another_path_is_a_holder(self) -> None:
        lock = self.host.lock()
        alias = self.host.home.parent / "alias"
        alias.symlink_to(self.host.home)
        self.host.process(7, EDITOR_EXE, "codex-acp", alias / "thread-writer-locks" / lock.name)
        self.host.table(self.host.row(lock, 7))
        result = conflicts.collect()
        self.assertEqual(result["findings"][0]["holder_pid"], 7)
        self.assertEqual(result["coverage"]["lock_fds_other_home"], 0)

    def test_a_descriptor_on_a_replaced_file_holds_only_the_old_file(self) -> None:
        lock = self.host.lock()
        keep = lock.with_name(f"{THREAD_A}.lock.old")
        lock.rename(keep)
        self.host.lock()
        self.host.process(7, EDITOR_EXE, "codex-acp", keep)
        self.host.table()
        result = conflicts.collect()
        self.assertEqual(result["findings"][0]["holder_count"], 0)
        self.assertEqual(result["coverage"]["lock_fds_unlisted"], 1)
        self.assertEqual(result["coverage"]["lock_fds_other_home"], 0)

    def test_codex_processes_come_first_whatever_the_pid_order(self) -> None:
        lock = self.host.lock()
        self.host.process(5, OTHER_EXE, "python3 worker.py", lock)
        self.host.process(8, DAEMON_EXE, "codex app-server --remote-control", lock)
        self.host.table(self.host.row(lock, 8))
        with mock.patch.object(conflicts, "_all_pids", lambda: [5, 8]):
            finding = self.one()
        self.assertEqual(finding["holder_pid"], 8)
        self.assertEqual(finding["holder_kind"], "background-daemon")
        self.assertEqual([h["pid"] for h in finding["holders"]], [8, 5])

    def test_equal_text_on_another_inode_holds_nothing(self) -> None:
        lock = self.host.lock()
        row = {"pid": 7, "path": str(lock.resolve()), "identity": (1, 2)}
        self.host.table()
        with mock.patch.object(conflicts, "scan_lock_fds", lambda order, targets: ([row], 0)):
            result = conflicts.collect()
        self.assertEqual(result["findings"][0]["holder_count"], 0)
        self.assertEqual(result["findings"][0]["holder_state"], "stale")
        self.assertEqual(result["coverage"]["lock_fds_unlisted"], 1)

    def test_a_listed_lock_that_resolves_elsewhere_keeps_its_descriptor(self) -> None:
        outside = self.host.home / "outside-file"
        outside.write_text("", encoding="ascii")
        (self.host.locks / f"{THREAD_A}.lock").symlink_to(outside)
        self.host.process(7, EDITOR_EXE, "codex-acp", outside)
        self.host.table(self.host.row(outside, 7))
        finding = self.one()
        self.assertEqual(finding["holder_pid"], 7)
        self.assertEqual(finding["holder_state"], "held")

    def test_a_link_that_cannot_be_followed_falls_back_to_its_text(self) -> None:
        lock = self.host.lock()
        entry = self.host.process(7, EDITOR_EXE, "codex-acp")
        (entry / "fd" / "3").symlink_to(str(lock.resolve()))
        self.host.table()
        real_stat = os.stat

        def refusing(path, *args, **kwargs):
            if str(path).endswith("/fd/3"):
                raise PermissionError(13, "refused")
            return real_stat(path, *args, **kwargs)

        with mock.patch.object(conflicts.os, "stat", refusing):
            self.assertEqual(self.one()["holder_pid"], 7)

    def test_unreadable_descriptor_tables_are_counted(self) -> None:
        lock = self.host.lock()
        self.host.process(7, EDITOR_EXE, "codex-acp", lock)
        entry = self.host.process(8, OTHER_EXE, "python3 other")
        os.chmod(entry / "fd", 0)
        self.addCleanup(os.chmod, entry / "fd", stat.S_IRWXU)
        self.host.table(self.host.row(lock, 7))
        if os.geteuid() == 0:
            self.skipTest("root reads every mode")
        self.assertEqual(conflicts.collect()["coverage"]["fd_tables_unreadable"], 1)

    def test_a_process_that_ended_is_not_a_refusal(self) -> None:
        self.assertEqual(conflicts.scan_lock_fds([4242]), ([], 0))

    def test_refused_processes_are_counted_and_ended_ones_are_not(self) -> None:
        self.host.process(7, DAEMON_EXE, "codex app-server")
        self.host.process(8, OTHER_EXE, "python3 x")
        self.host.process(9, OTHER_EXE, "python3 y")
        real = os.readlink

        def refusing(path, *args, **kwargs):
            text = str(path)
            if text.endswith("8/exe"):
                raise PermissionError(13, "refused")
            if text.endswith("9/exe"):
                raise FileNotFoundError(2, "ended")
            return real(path, *args, **kwargs)

        with mock.patch.object(conflicts.os, "readlink", refusing):
            procs, refused = conflicts.holders()
        self.assertEqual(refused, 1)
        self.assertEqual(sorted(procs), [7])

    def test_refused_processes_reach_the_reading(self) -> None:
        self.host.process(8, OTHER_EXE, "python3 x")
        self.host.table()
        real = os.readlink

        def refusing(path, *args, **kwargs):
            if str(path).endswith("8/exe"):
                raise PermissionError(13, "refused")
            return real(path, *args, **kwargs)

        with mock.patch.object(conflicts.os, "readlink", refusing):
            self.assertEqual(conflicts.collect()["coverage"]["processes_unreadable"], 1)

    def test_a_lock_file_with_no_thread_name_is_counted(self) -> None:
        (self.host.locks / "not-a-thread.lock").write_text("", encoding="ascii")
        self.host.table()
        result = conflicts.collect()
        self.assertEqual(result["findings"], [])
        self.assertEqual(result["coverage"]["lock_files_skipped"], 1)

    def test_coverage_names_the_home_and_its_rule(self) -> None:
        self.host.table()
        coverage = conflicts.collect()["coverage"]
        self.assertEqual(coverage["codex_home"], str(self.host.home))
        self.assertEqual(coverage["home_source"], "default")

    def test_json_exits_zero_and_carries_the_limit(self) -> None:
        lock = self.host.lock()
        self.host.process(8, DAEMON_EXE, "codex app-server --remote-control", lock)
        self.host.table(self.host.row(lock, 8))
        code, text = self.run_main("--json")
        self.assertEqual(code, 0)
        document = json.loads(text)
        self.assertEqual(document["limit"], conflicts.LIMIT)
        self.assertEqual(document["findings"][0]["holder_kind"], "background-daemon")
        self.assertIn("coverage", document)

    def test_text_empty_home_clears_nothing(self) -> None:
        self.host.table()
        code, text = self.run_main()
        self.assertEqual(code, 0)
        self.assertTrue(text.startswith("LIMIT:"))
        self.assertIn("that clears no chat", text)
        self.assertNotIn("can open", text)
        self.assertIn("lock table read", text)

    def test_text_says_when_the_table_was_not_read(self) -> None:
        _, text = self.run_main()
        self.assertIn("lock table NOT read", text)

    def test_text_editor_holder_warns_of_a_second_window_and_exits_zero(self) -> None:
        lock = self.host.lock()
        self.host.process(7, EDITOR_EXE, "codex-acp", lock)
        self.host.table(self.host.row(lock, 7))
        code, text = self.run_main()
        self.assertEqual(code, 0)
        self.assertIn("pid 7 (editor-bridge); kernel lock: locked", text)
        self.assertIn("1 thread(s) are open in an editor", text)
        self.assertNotIn("not the editor", text)
        self.assertNotIn("the editor cannot open this", text)

    def test_text_daemon_holder_gives_the_command_and_exits_one(self) -> None:
        lock = self.host.lock()
        self.host.process(8, DAEMON_EXE, "codex app-server --remote-control", lock)
        self.host.table(self.host.row(lock, 8))
        code, text = self.run_main()
        self.assertEqual(code, 1)
        self.assertIn("the editor cannot open this", text)
        self.assertIn("systemctl --user stop codex-remote-control.service", text)
        self.assertNotIn("open in an editor", text)

    def test_text_terminal_holder(self) -> None:
        lock = self.host.lock()
        self.host.process(8, DAEMON_EXE, "codex resume x", lock)
        self.host.table(self.host.row(lock, 8))
        code, text = self.run_main()
        self.assertEqual(code, 1)
        self.assertIn("Terminal claim", text)
        self.assertNotIn("Remote daemon claim", text)

    def test_text_second_holder_that_is_a_daemon_still_gets_its_command(self) -> None:
        lock = self.host.lock()
        self.host.process(7, EDITOR_EXE, "codex-acp", lock)
        self.host.process(8, DAEMON_EXE, "codex app-server --remote-control", lock)
        self.host.table(self.host.row(lock, 7))
        self.in_order((7, "editor-bridge"), (8, "background-daemon"))
        code, text = self.run_main()
        self.assertEqual(code, 1)
        self.assertIn("systemctl --user stop codex-remote-control.service", text)
        self.assertIn("(editor-bridge), pid", text)

    def test_text_second_holder_that_is_a_terminal_gets_its_advice(self) -> None:
        lock = self.host.lock()
        self.host.process(7, EDITOR_EXE, "codex-acp", lock)
        self.host.process(8, DAEMON_EXE, "codex resume x", lock)
        self.host.table(self.host.row(lock, 7))
        self.in_order((7, "editor-bridge"), (8, "terminal-cli"))
        code, text = self.run_main()
        self.assertEqual(code, 1)
        self.assertIn("Terminal claim", text)

    def test_text_second_holder_that_is_unknown_gets_its_advice(self) -> None:
        lock = self.host.lock()
        self.host.process(7, EDITOR_EXE, "codex-acp", lock)
        self.host.process(9, OTHER_EXE, "python3 worker.py", lock)
        self.host.table(self.host.row(lock, 7))
        self.in_order((7, "editor-bridge"))
        code, text = self.run_main()
        self.assertEqual(code, 1)
        self.assertIn("Unknown claim", text)

    def test_text_each_state_has_its_own_words(self) -> None:
        unseen = self.host.lock(THREAD_A)
        self.host.lock(THREAD_B)
        self.host.table(self.host.row(unseen, 41))
        code, text = self.run_main()
        self.assertEqual(code, 1)
        self.assertIn("locked with no visible holder; the kernel names pid 41", text)
        self.assertIn("STALE, no visible holder and no kernel lock", text)
        self.assertIn("Unknown claim", text)

    def test_text_unknown_state(self) -> None:
        self.host.lock()
        code, text = self.run_main()
        self.assertEqual(code, 1)
        self.assertIn("UNKNOWN, no visible holder", text)

    def test_text_open_without_a_lock(self) -> None:
        lock = self.host.lock()
        self.host.process(7, EDITOR_EXE, "codex-acp", lock)
        self.host.table()
        _, text = self.run_main()
        self.assertIn("open, and not locked, in pid 7 (editor-bridge)", text)


class RealKernelTests(unittest.TestCase):
    """The kernel's table and this process's own descriptors, with no fake in between."""

    def setUp(self) -> None:
        if not (Path("/proc/locks")).exists():
            self.skipTest("no kernel lock table on this host")
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.home = Path(folder.name) / ".codex"
        self.locks = self.home / "thread-writer-locks"
        self.locks.mkdir(parents=True)
        self.path = self.locks / f"{THREAD_A}.lock"
        self.path.write_text("", encoding="ascii")
        for name, value in (
            ("CODEX", self.home),
            ("LOCKS", self.locks),
            ("STATE", self.home / "state_5.sqlite"),
        ):
            patcher = mock.patch.object(conflicts, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = mock.patch.object(conflicts, "registry", lambda: {})
        patcher.start()
        self.addCleanup(patcher.stop)

    def finding(self) -> dict:
        return conflicts.collect()["findings"][0]

    def test_the_table_is_read_and_a_real_lock_is_found(self) -> None:
        with self.path.open("r") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            finding = self.finding()
            self.assertEqual(finding["kernel_lock"], "locked")
            self.assertIn(os.getpid(), finding["kernel_lock_pids"])
            self.assertEqual(finding["holder_state"], "held")
            self.assertIn(os.getpid(), [h["pid"] for h in finding["holders"]])

            fcntl.flock(handle, fcntl.LOCK_UN)
            finding = self.finding()
            self.assertEqual(finding["kernel_lock"], "not-locked")
            self.assertEqual(finding["holder_state"], "open-not-locked")
        finding = self.finding()
        self.assertEqual(finding["holder_state"], "stale")
        self.assertTrue(finding["stale"])

    def test_a_lock_folder_symlinked_to_another_name_keeps_its_holder(self) -> None:
        real_folder = self.home / "under-another-name"
        real_folder.mkdir()
        name = self.path.name
        self.path.unlink()
        self.locks.rmdir()
        self.locks.symlink_to(real_folder)
        (real_folder / name).write_text("", encoding="ascii")
        with (self.locks / name).open("r") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            finding = self.finding()
        self.assertEqual(finding["holder_state"], "held")
        self.assertIn(os.getpid(), [h["pid"] for h in finding["holders"]])

    def test_a_lock_file_symlinked_out_of_the_folder_keeps_its_holder(self) -> None:
        outside = self.home / "outside-file"
        outside.write_text("", encoding="ascii")
        self.path.unlink()
        self.path.symlink_to(outside)
        with self.path.open("r") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            finding = self.finding()
        self.assertEqual(finding["holder_state"], "held")
        self.assertIn(os.getpid(), [h["pid"] for h in finding["holders"]])

    def test_a_deleted_file_held_open_is_not_the_new_file(self) -> None:
        with self.path.open("r") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            self.path.unlink()
            self.path.write_text("", encoding="ascii")
            result = conflicts.collect()
            self.assertEqual(result["findings"][0]["holder_count"], 0)
            self.assertEqual(result["findings"][0]["kernel_lock"], "not-locked")
            self.assertEqual(result["coverage"]["lock_fds_unlisted"], 1)


class CommandLineTests(unittest.TestCase):
    """The janitor's route: a child process, its own home, the fields it reads."""

    def test_the_janitor_route_keeps_its_fields(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            locks = Path(folder) / ".codex" / "thread-writer-locks"
            locks.mkdir(parents=True)
            (locks / f"{THREAD_A}.lock").write_text("", encoding="ascii")
            environ = {k: v for k, v in os.environ.items() if k != "CODEX_HOME"}
            environ["HOME"] = folder
            done = subprocess.run(
                [sys.executable, "-I", "-B", str(MODULE_PATH), "--json"],
                capture_output=True, text=True, timeout=60, env=environ,
            )
        self.assertEqual(done.returncode, 0, done.stderr)
        finding = json.loads(done.stdout)["findings"][0]
        for key in ("thread", "resident", "room", "holder_pid", "holder_kind", "blocks_editor", "stale"):
            self.assertIn(key, finding)
        self.assertEqual(finding["thread"], THREAD_A)

    def test_the_provider_variable_reaches_the_reading(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder) / "chosen"
            (home / "thread-writer-locks").mkdir(parents=True)
            environ = dict(os.environ)
            environ["CODEX_HOME"] = str(home)
            done = subprocess.run(
                [sys.executable, "-I", "-B", str(MODULE_PATH), "--json"],
                capture_output=True, text=True, timeout=60, env=environ,
            )
        self.assertEqual(done.returncode, 0, done.stderr)
        coverage = json.loads(done.stdout)["coverage"]
        self.assertEqual(coverage["codex_home"], str(home))
        self.assertEqual(coverage["home_source"], "CODEX_HOME")


if __name__ == "__main__":
    unittest.main()
