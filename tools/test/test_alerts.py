#!/usr/bin/env python3
"""The clinic popup names residents the way Kevin knows them.

Until 2026-10-19 a clinic popup named a raw patient: a Codex rollout file name
or a Claude room plus twenty characters of a session id. Every popup since the
previous day concerned a helper thread, not a resident, and one of them called
a thread that had become healthy "WORSE". These tests pin the three repairs:
names come from the resident registry as Role (Person); helper threads roll up
under their resident and pop only when critical; and a move to healthy is never
a worsening. The state keys and the log keep the raw identifiers.
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "ops" / "lib" / "scripts"
ALAN = "0000a1a0-0000-4000-8000-00000000a1a0"
GEORGE = "0000e0e0-0000-4000-8000-00000000e0e0"
HELPER = "0000c1c1-0000-4000-8000-00000000c1c1"
GRANDCHILD = "000074a8-0000-4000-8000-0000000074a8"
CHILD = "0000cd5d-0000-4000-8000-00000000cd5d"
SHANNON = "00009feb-0000-4000-8000-000000009feb"


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace(".py", "") + "_names", ROOT / name)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


diff = load("alerts.py")


def rollout(home: Path, tid: str, parent: str | None, nickname: str | None) -> str:
    day = home / "sessions/2026/10/17"
    day.mkdir(parents=True, exist_ok=True)
    name = f"rollout-2026-10-17T23-54-21-{tid}.jsonl"
    payload = {"id": tid}
    if parent:
        payload.update({"parent_thread_id": parent, "agent_nickname": nickname})
    (day / name).write_text(json.dumps({"type": "session_meta", "payload": payload}) + "\n")
    return f"codex:{name}"


class NamingTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.home = self.root / "codex"
        registry = self.root / "identities.json"
        registry.write_text(json.dumps({"identities": [
            {"key": "alan-codex", "role": "Desktop Software and Maintenance",
             "person": "Alan Codex", "session_id": ALAN},
            {"key": "george-x", "role": "Desktop Continuity Manager",
             "person": "George Friend", "session_id": GEORGE},
            {"key": "session-doctor", "role": "Session Continuity Manager",
             "person": "Claude Shannon", "session_id": SHANNON},
        ]}))
        self.names = diff.load_names(registry)

    def tearDown(self):
        self._tmp.cleanup()

    def test_registry_names_are_role_and_person(self):
        self.assertEqual(self.names[GEORGE], "Desktop Continuity Manager (George Friend)")

    def test_a_registered_codex_body_is_named(self):
        pid = rollout(self.home, GEORGE, None, None)
        self.assertEqual(diff.describe(pid, self.names, self.home),
                         ("Desktop Continuity Manager (George Friend)", None))

    def test_a_helper_names_its_resident_and_itself(self):
        pid = rollout(self.home, HELPER, ALAN, "Maxwell")
        self.assertEqual(diff.describe(pid, self.names, self.home),
                         ("Desktop Software and Maintenance (Alan Codex)", "Maxwell"))

    def test_a_helper_of_a_helper_climbs_to_the_resident(self):
        rollout(self.home, CHILD, GEORGE, "Einstein")
        pid = rollout(self.home, GRANDCHILD, CHILD, "Poincare")
        self.assertEqual(diff.describe(pid, self.names, self.home),
                         ("Desktop Continuity Manager (George Friend)", "Poincare"))

    def test_a_helper_with_only_the_nested_spawn_record_is_named(self):
        day = self.home / "sessions/2026/10/17"
        day.mkdir(parents=True, exist_ok=True)
        name = f"rollout-2026-10-17T23-54-21-{HELPER}.jsonl"
        spawn = {"subagent": {"thread_spawn": {"parent_thread_id": ALAN,
                                               "agent_nickname": "Hubble"}}}
        (day / name).write_text(json.dumps(
            {"type": "session_meta", "payload": {"id": HELPER, "source": spawn}}) + "\n")
        self.assertEqual(diff.describe(f"codex:{name}", self.names, self.home),
                         ("Desktop Software and Maintenance (Alan Codex)", "Hubble"))

    def test_a_helper_in_the_workbench_root_is_named(self):
        workbench = self.root / "workbench"
        rollout(workbench, HELPER, GEORGE, "Galileo")
        pid = f"codex:rollout-2026-10-17T23-54-21-{HELPER}.jsonl"
        self.assertEqual(diff.describe(pid, self.names, self.home, [workbench]),
                         ("Desktop Continuity Manager (George Friend)", "Galileo"))

    def test_a_claude_label_resolves_by_its_session_prefix(self):
        pid = "claude:Sessions (me) / 00009feb-0000-4000-8"
        self.assertEqual(diff.describe(pid, self.names, self.home),
                         ("Session Continuity Manager (Claude Shannon)", None))

    def test_an_unknown_patient_keeps_its_raw_label(self):
        pid = "claude:Projects-STELA / 5efc0b08"
        self.assertEqual(diff.describe(pid, self.names, self.home), (pid, None))

    def test_a_missing_registry_names_nobody(self):
        self.assertEqual(diff.load_names(self.root / "absent.json"), {})


class PopupTests(NamingTests):
    def test_one_critical_resident_is_the_headline(self):
        pid = rollout(self.home, GEORGE, None, None)
        a = diff.build_alert([(pid, "CRITICAL")], self.names, self.home)
        self.assertEqual(a["headline"], "Critical: Desktop Continuity Manager (George Friend)")
        self.assertEqual(a["lines"], ["Desktop Continuity Manager (George Friend): critical"])
        self.assertTrue(a["alert"] and a["critical"])

    def test_helpers_below_critical_stay_quiet(self):
        one = rollout(self.home, HELPER, ALAN, "Maxwell")
        two = rollout(self.home, CHILD, ALAN, "Herschel")
        a = diff.build_alert([(one, "compact-treadmill"), (two, "compact-treadmill")],
                             self.names, self.home)
        self.assertFalse(a["alert"])
        self.assertEqual(a["quiet_helpers"], 2)
        self.assertEqual(a["headline"], "")

    def test_critical_helpers_roll_up_under_their_resident(self):
        one = rollout(self.home, HELPER, ALAN, "Maxwell")
        two = rollout(self.home, CHILD, ALAN, "Herschel")
        a = diff.build_alert([(one, "CRITICAL"), (two, "CRITICAL")], self.names, self.home)
        self.assertEqual(a["lines"], [
            "Desktop Software and Maintenance (Alan Codex): helpers Maxwell, Herschel critical"])
        self.assertEqual(a["headline"], "Critical: Desktop Software and Maintenance (Alan Codex)")

    def test_a_resident_and_its_helpers_share_one_line(self):
        body = rollout(self.home, ALAN, None, None)
        one = rollout(self.home, HELPER, ALAN, "Maxwell")
        two = rollout(self.home, CHILD, ALAN, "Herschel")
        a = diff.build_alert([(body, "CRITICAL"), (one, "CRITICAL"),
                              (two, "CRITICAL-window-exhausted")], self.names, self.home)
        self.assertEqual(a["lines"], [
            "Desktop Software and Maintenance (Alan Codex): critical; helper Maxwell critical; "
            "helper Herschel critical, context window exhausted"])
        self.assertEqual(a["headline"], "Critical: Desktop Software and Maintenance (Alan Codex)")

    def test_several_residents_are_counted(self):
        g = rollout(self.home, GEORGE, None, None)
        s = "claude:Sessions (me) / 00009feb-0000-4000-8"
        a = diff.build_alert([(g, "rotate-soon"), (s, "rotate-soon")], self.names, self.home)
        self.assertEqual(a["headline"], "2 residents need attention")
        self.assertFalse(a["critical"])


class WorseningTests(unittest.TestCase):
    """A thread that becomes healthy has not worsened (2026-10-19, 13:15)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        self.saved = (diff.STATE_FILE, diff.AGGREGATE_FILE, diff.REGISTRY, diff.CODEX_HOME)
        diff.STATE_FILE = root / "state.json"
        diff.AGGREGATE_FILE = root / "aggregate.json"
        diff.REGISTRY = root / "absent.json"
        diff.CODEX_HOME = root / "codex"
        self.name = f"rollout-2026-10-19T12-59-54-{HELPER}.jsonl"
        self.codex = root / "codex.txt"
        self.claude = root / "claude.txt"
        self.claude.write_text("")

    def tearDown(self):
        diff.STATE_FILE, diff.AGGREGATE_FILE, diff.REGISTRY, diff.CODEX_HOME = self.saved
        self._tmp.cleanup()

    def run_diff(self, previous: str, verdict: str) -> str:
        diff.STATE_FILE.write_text(json.dumps({f"codex:{self.name}": previous}))
        self.codex.write_text(f"   1.0MB  12  x  {self.name}\n    verdict: {verdict}\n")
        import contextlib
        import io
        import sys
        out = io.StringIO()
        argv = sys.argv
        sys.argv = ["alerts.py", str(self.codex), str(self.claude)]
        try:
            with contextlib.redirect_stdout(out):
                diff.main()
        finally:
            sys.argv = argv
        return out.getvalue()

    def test_no_telemetry_to_healthy_is_not_worse(self):
        out = self.run_diff("no-telemetry", "healthy")
        self.assertNotIn("WORSE", out)
        self.assertIn("SHOULD_ALERT=0", out)

    def test_no_telemetry_to_flagged_is_still_worse(self):
        out = self.run_diff("no-telemetry", "rotate-soon")
        self.assertIn("WORSE", out)


class WrapperPopupTests(unittest.TestCase):
    """The rounds wrapper puts the headline in the title and the names in the body."""

    ROUNDS = ROOT / "rounds.sh"

    def test_named_popup(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evid, scripts, rec = root / "logs", root / "ops" / "lib" / "scripts", root / "bin"
            for d in (evid, scripts, rec):                # the room's own layout: rounds.sh finds logs/ from its place
                d.mkdir(parents=True)
            for stub in ("telemetry.py", "vitals.py"):
                (scripts / stub).write_text("print('')\n")
            (scripts / "alerts.py").write_text(
                "print('chronic_flagged=1 new=1 worsened=0 resolved=0')\n"
                "print('  NEW: codex:rollout-x.jsonl -> CRITICAL')\n"
                "print('  SAY: Desktop Continuity Manager (George Friend): critical')\n"
                "print('QUIET_HELPERS=0')\n"
                "print('HEADLINE=Critical: Desktop Continuity Manager (George Friend)')\n"
                "print('SHOULD_ALERT=1 ANY_CRITICAL=1')\n")
            (scripts / "drift.py").write_text(
                "print('STATE=aligned SEVERITY=normal SHOULD_ALERT=0')\n")
            rounds = scripts / "rounds.sh"
            rounds.write_text(self.ROUNDS.read_text())
            log = rec / "calls.log"
            stub = rec / "notify-send"
            stub.write_text(f'#!/bin/sh\nfor a in "$@"; do echo "ARG:$a"; done >> {log}\n')
            stub.chmod(0o755)
            env = {**os.environ, "PATH": f"{rec}:{os.environ.get('PATH', '')}"}
            env.pop("SESSION_ROUNDS_NOTIFY", None)
            subprocess.run(["bash", str(rounds)], capture_output=True, env=env)
            calls = log.read_text()
        self.assertIn("ARG:-u", calls)
        self.assertIn("ARG:critical", calls)
        self.assertIn("ARG:🩺 Critical: Desktop Continuity Manager (George Friend)", calls)
        self.assertIn("ARG:Desktop Continuity Manager (George Friend): critical", calls)
        self.assertNotIn("rollout-x", calls)


if __name__ == "__main__":
    unittest.main()
