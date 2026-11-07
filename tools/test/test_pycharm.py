#!/usr/bin/env python3
"""Tests for ops/lib/scripts/pycharm.py, ported from Scripts/reconcile_pycharm_ai_surfaces.py on 2026-11-01.

The legacy script came without a test suite. The smoke cases prove that the
ported copy is present and compiles. The chats-file cases (2026-11-02) write a
synthetic chats file of 0000-namespace identifiers in a temporary directory.
They prove that the file loads, that the derived retired order holds, and that
an absent or malformed file is refused with one message and a nonzero exit
before anything else is read or written. Two cases run the tool in its default
read-only mode against a synthetic workspace and task history in a temporary
directory. No case reads the IDE's own state, a session body, or the room's own
chats file, and no case runs --preview-dir or --apply. Behavior cases for
--preview-dir and --apply: [PLACEHOLDER: synthetic cases for the two writing
modes, owner: the writer the Session Continuity Manager names for pycharm]. Run:

    python3 -I -B tools/test/test_pycharm.py
"""
import importlib.util
import json
import os
import py_compile
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

TOOL = Path(__file__).resolve().parents[2] / "ops" / "lib" / "scripts" / "pycharm.py"
SPEC = importlib.util.spec_from_file_location("pycharm_under_test", TOOL)
assert SPEC is not None and SPEC.loader is not None
pycharm = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = pycharm
SPEC.loader.exec_module(pycharm)


def cid(n):
    return f"00000000-0000-0000-0000-{n:012x}"


GEORGE = cid(0x1)
TEMP = cid(0x2)
LEGACY = cid(0x3)
STUBS = [cid(0x20), cid(0x11), cid(0x1F), cid(0x12), cid(0x10)]   # deliberately not sorted
OSAI = "osai-synthetic.xml"


def good():
    return {
        "george_vi_chat": GEORGE,
        "temp_osai_chat": TEMP,
        "legacy_claude_chat": LEGACY,
        "shell_only_stubs": list(STUBS),
    }


def changed(**fields):
    doc = good()
    for key, value in fields.items():
        if value is KeyError:
            del doc[key]
        else:
            doc[key] = value
    return json.dumps(doc, indent=2)


def malformed_cases():
    """(label, file bytes, a fragment the refusal must contain)."""
    good_text = json.dumps(good(), indent=2)
    cases = []
    for key in pycharm.CHAT_KEYS:
        cases.append((f"missing {key}", changed(**{key: KeyError}), f"lacks the key(s) {key}"))
    cases += [
        ("extra key", changed(note="x"), "unexpected key(s) 'note'"),
        ("top level is a list", json.dumps([good()]), "holds a list, not an object"),
        ("empty file", "", "is not valid JSON"),
        ("truncated JSON", good_text[:-2], "is not valid JSON"),
        ("duplicate key", good_text.replace(
            '"temp_osai_chat"', f'"george_vi_chat": "{GEORGE}",\n  "temp_osai_chat"', 1),
         "repeats the key 'george_vi_chat'"),
        ("george as a number", changed(george_vi_chat=1), "gives george_vi_chat as a number"),
        ("george as a boolean", changed(george_vi_chat=True), "gives george_vi_chat as a boolean"),
        ("temp as null", changed(temp_osai_chat=None), "gives temp_osai_chat as null"),
        ("legacy as a list", changed(legacy_claude_chat=[LEGACY]), "gives legacy_claude_chat as a list"),
        ("stubs as a string", changed(shell_only_stubs=STUBS[0]), "gives shell_only_stubs as a string"),
        ("stubs as an object", changed(shell_only_stubs={"a": STUBS[0]}), "gives shell_only_stubs as an object"),
        ("stub as a number", changed(shell_only_stubs=[*STUBS[:2], 7]), "gives shell_only_stubs[2] as a number"),
        ("stub repeated", changed(shell_only_stubs=[*STUBS, STUBS[1]]),
         "repeats one identifier at shell_only_stubs[1] and shell_only_stubs[5]"),
        ("george equals temp", changed(temp_osai_chat=GEORGE),
         "repeats one identifier at george_vi_chat and temp_osai_chat"),
        ("stub equals legacy", changed(shell_only_stubs=[*STUBS, LEGACY]),
         "repeats one identifier at legacy_claude_chat and shell_only_stubs[5]"),
        ("stub equals george", changed(shell_only_stubs=[GEORGE]),
         "repeats one identifier at george_vi_chat and shell_only_stubs[0]"),
    ]
    not_an_id = {
        "uppercase": cid(0xA).upper(),
        "braces": "{" + cid(0xA) + "}",
        "35 characters": cid(0xA)[:-1],
        "37 characters": cid(0xA) + "0",
        "no hyphens": cid(0xA).replace("-", "") + "0000",
        "hyphen misplaced": cid(0xA)[:7] + "-0" + cid(0xA)[9:],
        "not hex": cid(0xA)[:-1] + "g",
        "trailing newline": cid(0xA) + "\n",
        "leading space": " " + cid(0xA)[1:],
        "empty": "",
        "urn prefix": "urn:uuid:" + cid(0xA),
    }
    message = "a value that is not a 36-character lowercase hyphenated hex identifier"
    for label, value in not_an_id.items():
        cases.append((f"george {label}", changed(george_vi_chat=value), f"gives george_vi_chat {message}"))
        cases.append((f"stub {label}", changed(shell_only_stubs=[*STUBS[:3], value]),
                      f"gives shell_only_stubs[3] {message}"))
    return [(label, text.encode("utf-8"), fragment) for label, text, fragment in cases] + [
        ("not UTF-8", b'{"george_vi_chat": "\xff"}', "is not UTF-8 text"),
    ]


class SmokeTest(unittest.TestCase):
    def test_tool_exists(self):
        self.assertTrue(TOOL.is_file(), TOOL)

    def test_tool_compiles(self):
        with tempfile.TemporaryDirectory() as tmp:
            py_compile.compile(str(TOOL), cfile=str(Path(tmp) / "compiled.pyc"), doraise=True)


class ChatsFileTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, data, name="pycharm-chats.json"):
        path = self.tmp / name
        path.write_bytes(data if isinstance(data, bytes) else data.encode("utf-8"))
        return path

    def test_loads(self):
        chats = pycharm.load_chats(self.write(json.dumps(good(), indent=2)))
        self.assertEqual(chats.george_vi_chat, GEORGE)
        self.assertEqual(chats.temp_osai_chat, TEMP)
        self.assertEqual(chats.legacy_claude_chat, LEGACY)
        self.assertEqual(chats.shell_only_stubs, tuple(STUBS))

    def test_derived_order_holds(self):
        chats = pycharm.load_chats(self.write(json.dumps(good())))
        self.assertEqual(chats.retired_task_ids, (*STUBS, TEMP, LEGACY))
        self.assertNotEqual(list(chats.retired_task_ids), sorted(chats.retired_task_ids))
        self.assertNotIn(GEORGE, chats.retired_task_ids)

    def test_default_path_and_option(self):
        self.assertEqual(pycharm.CHATS, TOOL.parents[3] / "ops" / "etc" / "pycharm-chats.json")
        with mock.patch.object(sys, "argv", ["pycharm.py"]):
            self.assertEqual(pycharm.parse_args().chats, pycharm.CHATS)
        chosen = self.tmp / "elsewhere.json"
        with mock.patch.object(sys, "argv", ["pycharm.py", "--chats", str(chosen)]):
            self.assertEqual(pycharm.parse_args().chats, chosen)

    def test_refuses_absent_file(self):
        with self.assertRaises(pycharm.ChatsError) as caught:
            pycharm.load_chats(self.tmp / "absent.json")
        self.assertEqual(str(caught.exception), "does not exist")
        with self.assertRaises(pycharm.ChatsError) as caught:
            pycharm.load_chats(self.tmp)
        self.assertIn("cannot be read", str(caught.exception))

    def test_refuses_absent_file_as_a_process(self):
        absent = self.tmp / "absent.json"
        run = subprocess.run(
            [sys.executable, "-I", "-B", str(TOOL), "--chats", str(absent),
             "--workspace-dir", str(self.tmp / "workspace"), "--task-history", str(self.tmp / "history")],
            capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(run.returncode, 1)
        self.assertEqual(run.stdout, "")
        self.assertEqual(run.stderr.count("\n"), 1, run.stderr)
        self.assertEqual(
            run.stderr,
            f"pycharm.py refuses: the chats file {absent} does not exist. Nothing else was read or written.\n",
        )
        self.assertEqual(sorted(p.name for p in self.tmp.iterdir()), [])

    def test_refuses_each_malformed_form(self):
        cases = malformed_cases()
        self.assertGreaterEqual(len(cases), 40)
        for label, data, fragment in cases:
            with self.subTest(label):
                path = self.write(data)
                with self.assertRaises(pycharm.ChatsError) as caught:
                    pycharm.load_chats(path)
                self.assertIn(fragment, str(caught.exception))
                self.assertNotIn("\n", str(caught.exception))

    def test_refusal_comes_before_any_other_read_or_write(self):
        def tripwire(*_args, **_kwargs):
            raise AssertionError("read or wrote past a refused chats file")

        custody = self.tmp / "custody"
        workspace = self.tmp / "workspace"
        workspace.mkdir()
        cases = [("absent", None, "does not exist")] + malformed_cases()
        for label, data, fragment in cases:
            with self.subTest(label):
                chats = self.tmp / "absent.json" if data is None else self.write(data)
                argv = ["pycharm.py", "--chats", str(chats), "--workspace-dir", str(workspace),
                        "--task-history", str(self.tmp / "history"), "--apply", "--custody-dir", str(custody)]
                with mock.patch.object(sys, "argv", argv), \
                        mock.patch.object(pycharm, "pycharm_processes", tripwire), \
                        mock.patch.object(pycharm, "inspect_task_history", tripwire), \
                        mock.patch.object(pycharm, "transform_workspace", tripwire), \
                        mock.patch.object(pycharm, "atomic_write", tripwire), \
                        mock.patch.object(pycharm, "move_task_history", tripwire):
                    with self.assertRaises(SystemExit) as caught:
                        pycharm.main()
                message = caught.exception.code
                self.assertIsInstance(message, str)   # a string exit code exits with status 1
                self.assertTrue(message.startswith(f"pycharm.py refuses: the chats file {chats} "), message)
                self.assertIn(fragment, message)
                self.assertTrue(message.endswith(". Nothing else was read or written."), message)
                self.assertFalse(custody.exists())
                self.assertEqual(list(workspace.iterdir()), [])


def chat_block(uid, *options):
    lines = ["    <SerializedChat>\n", f'      <option name="uid" value="{uid}" />\n']
    lines += [f"      {option}\n" for option in options]
    return "".join(lines) + "    </SerializedChat>\n"


def pending_workspace():
    return (
        "<project>\n"
        + chat_block(GEORGE, '<option name="model" value="agent_acp.registry.claude-acp" />',
                     '<option name="text" value="OSAI" />')
        + chat_block(TEMP, '<option name="text" value="temporary" />')
        + chat_block(LEGACY, '<option name="text" value="legacy" />')
        + "".join(f'    <entry key="{uid}" value="1" />\n' for uid in [*STUBS, TEMP])
        + "</project>\n"
    )


class RunningIdeGuardTest(unittest.TestCase):
    """The guard before an apply knows the IDE by its executable, with no version in the rule. Every process here is synthetic."""

    def proc(self, *rows):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        for pid, exe, cmdline in rows:
            folder = root / str(pid)
            folder.mkdir()
            if exe is not None:
                os.symlink(exe, folder / "exe")
            if cmdline is not None:
                (folder / "cmdline").write_bytes(cmdline)
        return root

    def test_the_ide_of_any_version_or_folder_is_found(self):
        for exe in ("/opt/example/apps/pycharm-2027.2.1/bin/pycharm", "/opt/pycharm/bin/pycharm", "/home/example/pycharm-9/bin/pycharm.sh",
                    "/opt/example/apps/pycharm-2026.1.4/bin/pycharm"):
            with self.subTest(exe):
                self.assertEqual(pycharm.pycharm_processes(self.proc((41, exe, b"anything\0"))), [41])

    def test_an_ide_updated_in_place_reads_as_deleted_and_is_still_found(self):
        self.assertEqual(pycharm.pycharm_processes(self.proc((41, "/opt/example/bin/pycharm (deleted)", b"x\0"))), [41])

    def test_the_jvm_of_an_older_launcher_is_found(self):
        cmd = b"/opt/example/jbr/bin/java\0-Xmx1g\0com.intellij.idea.Main\0"
        self.assertEqual(pycharm.pycharm_processes(self.proc((41, "/opt/example/jbr/bin/java", cmd))), [41])
        self.assertEqual(pycharm.pycharm_processes(self.proc((41, "/opt/example/jbr/bin/java (deleted)", cmd))), [41])

    def test_a_process_that_only_mentions_the_ide_is_not(self):
        for exe, cmd in (("/usr/bin/python3", b"python3\0ops/lib/scripts/pycharm.py\0--apply\0"),
                         ("/usr/bin/bash", b"bash\0-c\0cd /opt/example/apps/pycharm-2026.1.4; com.intellij.idea.Main\0"),
                         ("/opt/example/apps/pycharm-2026.1.4/bin/fsnotifier", b"fsnotifier\0"),
                         ("/usr/bin/java", b"java\0-jar\0something-else.jar\0pycharm\0"),
                         ("/usr/bin/notify-send", b"notify-send\0pycharm\0")):
            with self.subTest(exe):
                self.assertEqual(pycharm.pycharm_processes(self.proc((41, exe, cmd))), [])

    def test_a_process_that_has_gone_is_passed_over_and_the_list_is_sorted(self):
        root = self.proc((50, "/opt/example/bin/pycharm", b"x\0"), (41, "/opt/example/bin/pycharm", b"x\0"),
                         (43, "/opt/example/bin/pycharm", None))
        (root / "not-a-pid").mkdir()
        self.assertEqual(pycharm.pycharm_processes(root), [41, 50])

    def test_an_executable_it_cannot_read_fails_closed_when_the_command_names_the_ide(self):
        self.assertEqual(pycharm.pycharm_processes(self.proc((41, None, b"/opt/example/bin/PyCharm\0"))), [41])
        self.assertEqual(pycharm.pycharm_processes(self.proc((41, None, b"/usr/bin/other\0"), (42, None, b""))), [])

    def test_its_own_process_is_not_counted(self):
        root = self.proc((os.getpid(), "/opt/example/bin/pycharm", b"x\0"))
        self.assertEqual(pycharm.pycharm_processes(root), [])

    def test_the_default_reads_the_real_table_and_finds_no_stand_in(self):
        self.assertIsInstance(pycharm.pycharm_processes(), list)

    def apply(self, *argv, processes=()):
        """main() as far as the guard, with every later act a tripwire, and what stopped it."""
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        chats = root / "chats.json"
        chats.write_text(json.dumps(good()))
        (root / "workspace").mkdir()
        (root / "history").mkdir()
        class Reached(Exception):
            pass
        def tripwire(*a, **k):
            raise Reached
        argv = ["pycharm.py", "--chats", str(chats), "--workspace-dir", str(root / "workspace"), "--task-history", str(root / "history"), "--apply", *argv]
        with mock.patch.object(sys, "argv", argv), mock.patch.object(pycharm, "pycharm_processes", lambda: list(processes)), \
                mock.patch.object(pycharm, "inspect_task_history", tripwire), mock.patch.object(pycharm, "atomic_write", tripwire), \
                mock.patch.object(pycharm, "move_task_history", tripwire):
            try:
                pycharm.main()
            except Reached:
                return "went on"
            except SystemExit as exc:
                return exc.code
        return "returned"

    def test_an_apply_refuses_while_the_ide_runs(self):
        self.assertEqual(self.apply("--custody-dir", "/nonexistent/custody", processes=[41, 50]), "PyCharm must be closed; matching process IDs: [41, 50]")

    def test_an_apply_goes_on_when_it_does_not(self):
        self.assertEqual(self.apply("--custody-dir", "/nonexistent/custody"), "went on")

    def test_an_apply_with_no_custody_folder_refuses(self):
        self.assertEqual(self.apply(processes=[41]), "--apply requires --custody-dir")


class LiveFolderTest(unittest.TestCase):
    """No pin: the folders default to the live settings folder, by identity.py's rule, in a temporary home."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.home = Path(self._tmp.name)
        self.chats = self.home / "chats.json"
        self.chats.write_text(json.dumps(good(), indent=2), encoding="utf-8")

    def seed(self, workspace, history, extra=0):
        """A sound pending state, with a number of extra workspace files that tells which folder was read."""
        workspace.mkdir(parents=True, exist_ok=True)
        history.mkdir(parents=True, exist_ok=True)
        (workspace / OSAI).write_text(pending_workspace(), encoding="utf-8")
        for i in range(extra):
            (workspace / f"other{i}.xml").write_text("<project />\n", encoding="utf-8")
        for uid in STUBS:
            (history / f"{uid}.agentsession").write_text("", encoding="utf-8")
        for uid in (TEMP, LEGACY):
            for suffix in (".agentsession", ".events", ".lastid", ".usage"):
                (history / f"{uid}{suffix}").write_text("", encoding="utf-8")

    def folder(self, name, extra=0):
        root = self.home / ".config/JetBrains" / name
        self.seed(root / "workspace", root / "aia-task-history", extra)
        return root

    def scanned(self, *extra):
        run = self.tool(*extra)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        return json.loads(run.stdout)["workspace_files_scanned"]

    def tool(self, *extra):
        env = {"PATH": "/usr/bin:/bin", "HOME": str(self.home), "LANG": "C.UTF-8"}
        return subprocess.run([sys.executable, "-I", "-B", str(TOOL), "--chats", str(self.chats), "--osai-workspace", OSAI, *map(str, extra)],
                              capture_output=True, text=True, timeout=60, env=env)

    def test_no_version_is_pinned_in_the_tool(self):
        self.assertIsNone(re.search(r"pycharm[-_ ]?20\d\d\.\d", TOOL.read_text(encoding="utf-8"), re.IGNORECASE))

    def test_the_highest_version_is_read_by_number(self):
        self.folder("PyCharm2026.1", extra=4)
        self.folder("PyCharm2026.3", extra=2)
        self.folder("PyCharm2026.10", extra=1)
        self.assertEqual(self.scanned(), 2)

    def test_no_folder_refuses(self):
        run = self.tool()
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("pycharm.py refuses: no PyCharm<year>.<n> folder", run.stderr)
        self.assertIn("Nothing else was read or written.", run.stderr)
        self.assertEqual(run.stdout, "")

    def test_two_folders_of_one_version_refuse(self):
        self.folder("PyCharm2026.3")
        self.folder("PyCharm2026.03")
        run = self.tool()
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("pycharm.py refuses: 2 folders of the same version", run.stderr)

    def test_a_link_counts_for_nothing(self):
        self.folder("PyCharm2026.1")
        elsewhere = self.home / "elsewhere"
        self.seed(elsewhere / "workspace", elsewhere / "aia-task-history", extra=5)
        (self.home / ".config/JetBrains/PyCharm2027.1").symlink_to(elsewhere)
        self.assertEqual(self.scanned(), 1)

    def test_both_folders_given_need_no_live_folder(self):
        given = self.home / "given"
        self.seed(given / "workspace", given / "history", extra=3)
        self.assertEqual(self.scanned("--workspace-dir", given / "workspace", "--task-history", given / "history"), 4)

    def test_both_folders_given_read_no_live_folder_even_when_two_tie(self):
        self.folder("PyCharm2026.3")
        self.folder("PyCharm2026.03")
        given = self.home / "given"
        self.seed(given / "workspace", given / "history", extra=3)
        self.assertEqual(self.scanned("--workspace-dir", given / "workspace", "--task-history", given / "history"), 4)

    def test_one_folder_given_takes_the_other_from_the_live_folder_or_refuses(self):
        given = self.home / "given"
        self.seed(given / "workspace", given / "history", extra=2)
        run = self.tool("--workspace-dir", given / "workspace")
        self.assertIn("pycharm.py refuses: no PyCharm<year>.<n> folder", run.stderr)
        self.folder("PyCharm2026.3", extra=5)
        self.assertEqual(self.scanned("--workspace-dir", given / "workspace"), 3)
        self.assertEqual(self.scanned("--task-history", given / "history"), 6)

    def test_a_given_task_history_is_the_one_read(self):
        self.folder("PyCharm2026.3")
        bad = self.home / "bad-history"
        bad.mkdir()
        (bad / f"{TEMP}.events").write_text("", encoding="utf-8")
        run = self.tool("--task-history", bad)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn('"task_history_deviations": 1', run.stderr)

    def test_the_chats_file_is_still_refused_first(self):
        self.chats.unlink()
        with mock.patch.object(pycharm, "live_root", side_effect=AssertionError("read a folder before the chats file")), \
                mock.patch.object(sys, "argv", ["pycharm.py", "--chats", str(self.chats)]), \
                self.assertRaises(SystemExit) as caught:
            pycharm.main()
        self.assertIn("the chats file", str(caught.exception.code))

    def test_apply_does_not_get_past_a_refusal(self):
        custody = self.home / "custody"
        run = self.tool("--apply", "--custody-dir", custody)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("refuses", run.stderr)
        self.assertFalse(custody.exists())

    def test_parsing_reads_no_folder(self):
        with mock.patch.object(pycharm, "live_root", side_effect=AssertionError), mock.patch.object(sys, "argv", ["pycharm.py"]):
            args = pycharm.parse_args()
        self.assertIsNone(args.workspace_dir)
        self.assertIsNone(args.task_history)


class ReadOnlyBehaviorTest(unittest.TestCase):
    """The default mode on synthetic state: the loaded values drive the same reconciliation."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.chats_path = self.tmp / "pycharm-chats.json"
        self.chats_path.write_text(json.dumps(good(), indent=2), encoding="utf-8")
        self.workspace = self.tmp / "workspace"
        self.history = self.tmp / "aia-task-history"
        self.workspace.mkdir()
        self.history.mkdir()

    def tearDown(self):
        self._tmp.cleanup()

    def snapshot(self):
        return {str(p.relative_to(self.tmp)): p.read_bytes() for p in sorted(self.tmp.rglob("*")) if p.is_file()}

    def run_tool(self):
        run = subprocess.run(
            [sys.executable, "-I", "-B", str(TOOL), "--chats", str(self.chats_path),
             "--workspace-dir", str(self.workspace), "--task-history", str(self.history),
             "--osai-workspace", OSAI],
            capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(run.returncode, 0, run.stderr)
        return json.loads(run.stdout)

    def test_pending_state_is_measured_and_nothing_is_written(self):
        (self.workspace / OSAI).write_text(pending_workspace(), encoding="utf-8")
        for uid in STUBS:
            (self.history / f"{uid}.agentsession").write_text("", encoding="utf-8")
        for uid in (TEMP, LEGACY):
            for suffix in (".agentsession", ".events", ".lastid", ".usage"):
                (self.history / f"{uid}{suffix}").write_text("", encoding="utf-8")
        before = self.snapshot()
        report = self.run_tool()
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(report["reconciliation_state"], "pending")
        self.assertEqual(report["task_ids_pending"], len(STUBS) + 2)
        self.assertEqual(report["shell_only_files"], len(STUBS))
        self.assertEqual(report["retired_full_files"], 8)
        self.assertEqual(report["removed_chats"], 2)
        self.assertEqual(report["removed_map_entries"], len(STUBS) + 1)
        self.assertEqual(report["model_repairs"], 1)
        self.assertEqual(report["title_repairs"], 1)
        self.assertEqual(report["george_vi_verified"], 1)
        self.assertEqual(report["workspace_files_changed"], 1)
        self.assertEqual(report["task_history_files_moved"], 0)
        self.assertEqual(report["protocol_deviations"], 0)

    def test_reconciled_state_after_the_transform(self):
        chats = pycharm.load_chats(self.chats_path)
        transformed, counts = pycharm.transform_workspace(
            pending_workspace(), chats=chats, remove_chat_ids={TEMP, LEGACY}, repair_george_vi=True,
        )
        self.assertEqual(counts["removed_chats"], 2)
        self.assertIn('value="agent_acp.registry.codex-acp"', transformed)
        self.assertIn('<option name="text" value="George VI \u2014 OSAI" />', transformed)
        for uid in chats.retired_task_ids:
            self.assertNotIn(uid, transformed)
        (self.workspace / OSAI).write_text(transformed, encoding="utf-8")
        before = self.snapshot()
        report = self.run_tool()
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(report["reconciliation_state"], "reconciled")
        self.assertEqual(report["task_ids_retired"], len(STUBS) + 2)
        self.assertEqual(report["workspace_files_changed"], 0)


if __name__ == "__main__":
    unittest.main()
