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
import re
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2] / "ops" / "lib" / "scripts"
ALAN = "0000a1a0-0000-4000-8000-00000000a1a0"
GEORGE = "0000e0e0-0000-4000-8000-00000000e0e0"
HELPER = "0000c1c1-0000-4000-8000-00000000c1c1"
GRANDCHILD = "0000b4b4-0000-4000-8000-00000000b4b4"
CHILD = "0000b5b5-0000-4000-8000-00000000b5b5"
SHANNON = "0000e1e1-0000-4000-8000-00000000e1e1"


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
        pid = "claude:Sessions (me) / 0000e1e1-0000-4000-8"
        self.assertEqual(diff.describe(pid, self.names, self.home),
                         ("Session Continuity Manager (Claude Shannon)", None))

    def test_an_unknown_patient_keeps_its_raw_label(self):
        pid = "claude:Projects-STELA / 0000abc2"
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
        s = "claude:Sessions (me) / 0000e1e1-0000-4000-8"
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
            ran = root / "fixture-detector-ran"
            (scripts / "drift.py").write_text(
                f"open({str(ran)!r}, 'w').close()\n"
                "print('STATE=aligned SEVERITY=normal SHOULD_ALERT=0')\n")
            rounds = scripts / "rounds.sh"
            # The wrapper names the live detector by absolute path, and running it writes Control's drift state.
            # The copy under test must not reach it, or a run on this host consumes a real transition.
            text = self.ROUNDS.read_text()
            detector = re.search(r'"(/[^"]+/check_resident_center_drift\.py)"', text)
            self.assertIsNotNone(detector, "the wrapper no longer names its detector this way")
            remainder = text.replace(detector.group(1), "")  # checked before the fixture's own path goes in
            for host_root in ("/media/", "/home/"):
                self.assertNotIn(host_root, remainder)
            rounds.write_text(text.replace(detector.group(1), str(scripts / "drift.py")))
            log = rec / "calls.log"
            stub = rec / "notify-send"
            stub.write_text(f'#!/bin/sh\nfor a in "$@"; do echo "ARG:$a"; done >> {log}\n')
            stub.chmod(0o755)
            env = {**os.environ, "PATH": f"{rec}:{os.environ.get('PATH', '')}"}
            env.pop("SESSION_ROUNDS_NOTIFY", None)
            subprocess.run(["bash", str(rounds)], capture_output=True, env=env)
            calls = log.read_text()
            self.assertTrue(ran.exists(), "the wrapper did not run the fixture's detector")
        self.assertIn("ARG:-u", calls)
        self.assertIn("ARG:critical", calls)
        self.assertIn("ARG:🩺 Critical: Desktop Continuity Manager (George Friend)", calls)
        self.assertIn("ARG:Desktop Continuity Manager (George Friend): critical", calls)
        self.assertNotIn("rollout-x", calls)


class PanelTests(unittest.TestCase):
    """W3: the private active panel beside the alert state (2026-11-05). Synthetic room, registry and bodies;
    every binding state and inventory class; the aggregate and the state are byte for byte what they were."""

    IDS = {name: f"0000{n:04x}-0000-4000-8000-0000000{n:05x}" for n, name in enumerate(
        ("alpha", "gamma", "sigma", "rho", "mu", "tau", "unreg", "helper", "pi", "nu", "dup", "twin1", "twin2"), 1)}

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.saved = (diff.STATE_FILE, diff.AGGREGATE_FILE, diff.REGISTRY, diff.CODEX_HOME,
                      diff.EXTRA_CODEX_ROOTS, diff.CLAUDE_PROJECTS)
        (self.root / "logs").mkdir()
        diff.STATE_FILE = self.root / "logs" / "clinic-alert-state.json"
        diff.AGGREGATE_FILE = self.root / "logs" / "clinic-aggregate.json"
        diff.REGISTRY = self.root / "registry.json"
        diff.CODEX_HOME = self.root / "codex"
        diff.EXTRA_CODEX_ROOTS = [self.root / "vm"]
        diff.CLAUDE_PROJECTS = self.root / "claude"
        self.panel_file = self.root / "logs" / "clinic-panel.json"
        i = self.IDS
        rows = [("alpha-codex", "codex", i["alpha"]), ("gamma-codex", "codex", i["gamma"]),
                ("sigma-claude", "claude", i["sigma"]), ("rho-codex", "codex", i["rho"]),
                ("mu-codex", "codex", i["mu"]), ("tau-codex", "codex", i["tau"]),
                ("pi-copilot", "copilot", i["pi"]), ("nu-codex", "codex", ""),
                ("dup-key", "codex", i["dup"]), ("dup-key", "claude", i["dup"])]
        self.registry = [{"key": k, "provider": p, "session_id": s, "role": "Role", "person": f"Person {k}",
                          "room": str(self.root)} for k, p, s in rows]
        diff.REGISTRY.write_text(json.dumps({"identities": self.registry}))
        self.codex_rows, self.claude_rows = [], []
        self.body("host", i["alpha"], "compact-treadmill")
        self.body("vm", i["gamma"], "healthy")
        self.body("archive", i["rho"], None)                  # the real Codex ward never reports the archive
        self.body("host", i["tau"], "CRITICAL")
        self.body("vm", i["tau"], None)                       # the same file name in a second live root
        self.body("host", i["unreg"], "rotate-soon")
        self.body("host", i["helper"], "compact-treadmill", parent=i["alpha"])
        self.claude_body("-synthetic-room", i["sigma"], "CRITICAL")
        self.codex = self.root / "codex.txt"
        self.claude = self.root / "claude.txt"
        self.write_reports()

    def tearDown(self):
        (diff.STATE_FILE, diff.AGGREGATE_FILE, diff.REGISTRY, diff.CODEX_HOME,
         diff.EXTRA_CODEX_ROOTS, diff.CLAUDE_PROJECTS) = self.saved
        self._tmp.cleanup()

    def body(self, where, tid, verdict, parent=None):
        folder = {"host": self.root / "codex/sessions/2026/11/05", "vm": self.root / "vm/2026/11/05",
                  "archive": self.root / "codex/archived_sessions"}[where]
        folder.mkdir(parents=True, exist_ok=True)
        name = f"rollout-2026-11-05T10-00-00-{tid}.jsonl"
        payload = {"id": tid, **({"parent_thread_id": parent, "agent_nickname": "Helper"} if parent else {})}
        (folder / name).write_text(json.dumps({"type": "session_meta", "payload": payload}) + "\n")
        if verdict:
            self.codex_rows.append(f"   1.0MB  12  x  {name}\n    verdict: {verdict}\n")

    def claude_body(self, project, sid, verdict, name=None):
        folder = self.root / "claude" / project
        folder.mkdir(parents=True, exist_ok=True)
        (folder / (name or f"{sid}.jsonl")).write_text("{}\n")
        if verdict:
            self.claude_rows.append(f"   10MB    100    0.0     0     1/2  50.0%  {verdict:<26}  {project} / {sid[:20]}\n")

    def write_reports(self):
        self.codex.write_text("".join(self.codex_rows))
        self.claude.write_text("".join(self.claude_rows))

    def run_main(self):
        import contextlib
        import io
        import sys
        out = io.StringIO()
        argv = sys.argv
        sys.argv = ["alerts.py", str(self.codex), str(self.claude)]
        try:
            with contextlib.redirect_stdout(out):
                code = diff.main()
        finally:
            sys.argv = argv
        return code, out.getvalue()

    def panel(self):
        return json.loads(self.panel_file.read_text())

    def test_each_registered_resident_has_one_binding_state(self):
        code, out = self.run_main()
        self.assertEqual(code, 0)
        self.assertEqual(stat.S_IMODE(self.panel_file.stat().st_mode), 0o600)
        panel = self.panel()
        self.assertEqual((panel["schema"], panel["status"]), ("clinic-panel/1", "ok"))
        r = panel["residents"]
        expect = {"alpha-codex": ("one-live-body", "compact-treadmill", "codex-host-live"),
                  "gamma-codex": ("one-live-body", "healthy", "codex-vm-live"),
                  "sigma-claude": ("one-live-body", "CRITICAL", "claude-live-store"),
                  "rho-codex": ("archived", None, None), "mu-codex": ("missing", None, None),
                  "tau-codex": ("ambiguous", None, None), "pi-copilot": ("unknown", None, None),
                  "nu-codex": ("unknown", None, None), "dup-key": ("ambiguous", None, None)}
        self.assertEqual({k: (v["binding"], v["verdict"], v["ward"]) for k, v in r.items()}, expect)
        self.assertIn("archived", r["rho-codex"]["reason"])
        self.assertIn("no body is found", r["mu-codex"]["reason"])
        self.assertIn("no clinic ward", r["pi-copilot"]["reason"])
        self.assertIn("names no session", r["nu-codex"]["reason"])
        self.assertIn("more than one registry row", r["dup-key"]["reason"])
        self.assertEqual(panel["bindings"], {"one-live-body": 3, "missing": 1, "ambiguous": 2, "unknown": 2, "archived": 1})
        signal = r["alpha-codex"]["signals"]["clinic_verdict"]
        self.assertEqual((signal["value"], signal["evidence"]), ("compact-treadmill", "clinic codex ward report"))
        self.assertIsInstance(signal["age_seconds"], int)
        self.assertEqual(r["mu-codex"]["signals"], {})
        self.assertEqual([e["domain"] for e in panel["evidence"]],
                         ["clinic claude ward report", "clinic codex ward report", "resident registry"])
        self.assertIn("residents 9, active 8: one-live-body 3, missing 1, ambiguous 2, unknown 2, archived 1", out)

    def test_inventories_are_counted_apart_from_resident_health(self):
        self.run_main()
        inv = self.panel()["inventories"]
        self.assertEqual(inv["orphan_and_helper"], {"unregistered": {"rotate-soon": 1}, "helper": {"compact-treadmill": 1}})
        self.assertEqual(inv["lifecycle"], {"archived": 1, "archived_registered": 1, "operator_recorded_retired": None})
        self.assertEqual(inv["unresolved"], {"missing": {}, "ambiguous": {"CRITICAL": 1}})
        self.assertEqual(set(self.panel()["residents"]), {row["key"] for row in self.registry})

    def test_a_claude_label_shared_by_two_bodies_is_ambiguous(self):
        sid = self.IDS["twin1"]
        self.registry.append({"key": "twin-claude", "provider": "claude", "session_id": sid, "role": "R", "person": "P"})
        diff.REGISTRY.write_text(json.dumps({"identities": self.registry}))
        self.claude_body("-synthetic-room", sid, "healthy")
        self.claude_body("-synthetic-room", sid, None, name=sid[:20] + "ffff-ffff-ffffffffffff.jsonl")
        self.write_reports()
        self.run_main()
        row = self.panel()["residents"]["twin-claude"]
        self.assertEqual(row["binding"], "ambiguous")
        self.assertEqual(self.panel()["residents"]["sigma-claude"]["binding"], "one-live-body")

    def test_a_ward_report_found_in_the_store_but_gone_is_missing(self):
        gone = self.root / "codex/sessions/2026/11/05" / f"rollout-2026-11-05T10-00-00-{self.IDS['alpha']}.jsonl"
        gone.unlink()
        self.run_main()
        row = self.panel()["residents"]["alpha-codex"]
        self.assertEqual(row["binding"], "missing")
        self.assertIn("not found", row["reason"])
        self.assertEqual(self.panel()["inventories"]["unresolved"]["missing"], {"compact-treadmill": 1})

    def test_a_ward_without_rows_leaves_its_residents_unknown(self):
        self.claude_rows = []
        self.write_reports()
        self.run_main()
        row = self.panel()["residents"]["sigma-claude"]
        self.assertEqual((row["binding"], row["reason"]), ("unknown", "the claude ward report has no rows"))

    def test_the_panel_never_carries_identifiers_or_paths(self):
        code, out = self.run_main()
        text = self.panel_file.read_text()
        section = "\n".join(line for line in out.splitlines() if line.startswith("PANEL"))
        for value in list(self.IDS.values()) + [str(self.root), "rollout-", ".jsonl", " / ", "-synthetic-room"]:
            self.assertNotIn(value, text)
            self.assertNotIn(value, section)
        for value in [f"Person {row['key']}" for row in self.registry]:
            self.assertNotIn(value, text)

    def test_the_aggregate_state_and_exit_are_unchanged_by_the_panel(self):
        import datetime as real
        fixed = real.datetime(2026, 11, 5, 19, 0, 0, tzinfo=real.timezone.utc)

        class Clock(real.datetime):
            @classmethod
            def now(cls, tz=None):
                return fixed

        fake = type("FakeDatetimeModule", (), {"datetime": Clock, "timezone": real.timezone})
        results = []
        for with_panel in (False, True):
            diff.STATE_FILE.unlink(missing_ok=True)
            with mock.patch.object(diff, "datetime", fake):
                if with_panel:
                    code, out = self.run_main()
                else:
                    with mock.patch.object(diff, "publish_panel", lambda *a: None):
                        code, out = self.run_main()
            results.append((code, out, diff.AGGREGATE_FILE.read_bytes(), diff.STATE_FILE.read_bytes()))
        (c0, o0, a0, s0), (c1, o1, a1, s1) = results
        self.assertEqual((c0, a0, s0), (c1, a1, s1))
        panel_lines = [line for line in o1.splitlines() if line.startswith("PANEL")]
        self.assertEqual([line for line in o1.splitlines() if not line.startswith("PANEL")], o0.splitlines())
        self.assertEqual(len(panel_lines), 1)
        self.assertEqual(o1.splitlines()[0], o0.splitlines()[0])            # rounds reads chronic from line 1
        for line in panel_lines:
            for token in ("SHOULD_ALERT=", "ANY_CRITICAL=", "HEADLINE=", "SAY:", "NEW:", "WORSE:"):
                self.assertNotIn(token, line)
        self.assertEqual(set(json.loads(a1)), {"schema_version", "generated_at", "counts", "worst_verdict", "next_action"})

    def test_an_unreadable_registry_is_stated_not_guessed(self):
        for raw in ("{not json", '{"identities": {}}', '{"other": []}'):
            with self.subTest(raw=raw):
                diff.REGISTRY.write_text(raw)
                code, out = self.run_main()
                self.assertEqual(code, 0)
                panel = self.panel()
                self.assertEqual((panel["status"], panel["residents"], panel["inventories"]),
                                 ("registry unavailable", {}, None))
                self.assertIn("status registry unavailable", out)
                self.assertTrue(diff.AGGREGATE_FILE.exists())

    def test_two_live_bodies_for_one_session_are_ambiguous(self):
        folder = self.root / "codex/sessions/2026/11/05"
        name = f"rollout-2026-11-05T11-00-00-{self.IDS['alpha']}.jsonl"
        (folder / name).write_text("{}\n")
        self.codex_rows.append(f"   1.0MB  12  x  {name}\n    verdict: healthy\n")
        self.write_reports()
        self.run_main()
        self.assertEqual(self.panel()["residents"]["alpha-codex"]["binding"], "ambiguous")

    def test_one_live_body_beside_a_vanished_one_is_ambiguous(self):
        name = f"rollout-2026-11-05T11-00-00-{self.IDS['alpha']}.jsonl"
        self.codex_rows.append(f"   1.0MB  12  x  {name}\n    verdict: healthy\n")
        self.write_reports()
        self.run_main()
        self.assertEqual(self.panel()["residents"]["alpha-codex"]["binding"], "ambiguous")

    def test_a_session_bound_to_two_keys_is_ambiguous(self):
        self.registry.append({"key": "alpha-twin", "provider": "codex", "session_id": self.IDS["alpha"],
                              "role": "R", "person": "P"})
        diff.REGISTRY.write_text(json.dumps({"identities": self.registry}))
        self.run_main()
        r = self.panel()["residents"]
        for key in ("alpha-codex", "alpha-twin"):
            self.assertEqual((r[key]["binding"], r[key]["reason"]),
                             ("ambiguous", "the session is bound to more than one registry row"))
        self.assertEqual(self.panel()["inventories"]["orphan_and_helper"]["unregistered"], {"rotate-soon": 1})

    def register(self, key, provider, sid):
        self.registry.append({"key": key, "provider": provider, "session_id": sid, "role": "R", "person": "P"})
        diff.REGISTRY.write_text(json.dumps({"identities": self.registry}))

    def test_an_archived_body_no_ward_reports_binds_archived(self):
        rho = self.IDS["rho"]
        self.assertNotIn(rho, self.codex.read_text())
        self.assertTrue((self.root / f"codex/archived_sessions/rollout-2026-11-05T10-00-00-{rho}.jsonl").is_file())
        self.run_main()
        panel = self.panel()
        row = panel["residents"]["rho-codex"]
        self.assertEqual((row["binding"], row["verdict"], row["ward"], row["signals"], row["reason"]),
                         ("archived", None, None, {}, "only an archived body carries this session"))
        self.assertEqual((panel["registered"], panel["active"], panel["bindings"]["archived"]), (9, 8, 1))
        self.assertEqual(panel["inventories"]["lifecycle"]["archived_registered"], 1)

    def test_a_resident_with_no_body_anywhere_is_missing(self):
        self.run_main()
        row = self.panel()["residents"]["mu-codex"]
        self.assertEqual((row["binding"], row["reason"]),
                         ("missing", "no body is found under the live or archive roots"))

    def test_the_archive_is_counted_from_its_files_not_from_ward_rows(self):
        self.body("archive", self.IDS["twin2"], None)         # not registered
        self.run_main()
        inv = self.panel()["inventories"]
        self.assertEqual(inv["lifecycle"], {"archived": 2, "archived_registered": 1, "operator_recorded_retired": None})
        self.assertEqual(inv["orphan_and_helper"]["unregistered"], {"rotate-soon": 1})

    def test_a_ward_row_naming_an_archived_body_is_counted_once(self):
        self.body("archive", self.IDS["rho"], "rotate-soon")  # a report made by pointing the ward at the archive
        self.body("archive", self.IDS["twin2"], "healthy")
        self.write_reports()
        self.run_main()
        panel = self.panel()
        row = panel["residents"]["rho-codex"]
        self.assertEqual((row["binding"], row["verdict"]), ("archived", None))
        self.assertEqual(panel["inventories"]["lifecycle"]["archived"], 2)
        self.assertEqual(panel["inventories"]["lifecycle"]["archived_registered"], 1)
        self.assertEqual(panel["inventories"]["orphan_and_helper"]["unregistered"], {"rotate-soon": 1})

    def test_two_archived_bodies_for_one_session_are_ambiguous(self):
        name = f"rollout-2026-11-05T11-00-00-{self.IDS['rho']}.jsonl"
        (self.root / "codex/archived_sessions" / name).write_text("{}\n")
        self.run_main()
        panel = self.panel()
        self.assertEqual(panel["residents"]["rho-codex"]["binding"], "ambiguous")
        self.assertEqual(panel["inventories"]["lifecycle"]["archived"], 2)
        self.assertEqual(panel["inventories"]["lifecycle"]["archived_registered"], 2)

    def test_a_session_both_live_and_archived_with_no_ward_row_is_ambiguous(self):
        self.body("host", self.IDS["rho"], None)
        self.run_main()
        self.assertEqual(self.panel()["residents"]["rho-codex"]["binding"], "ambiguous")

    def test_a_live_body_without_a_ward_row_is_unknown_not_missing(self):
        self.body("host", self.IDS["mu"], None)
        self.register("kappa-claude", "claude", self.IDS["twin1"])
        self.claude_body("-synthetic-room", self.IDS["twin1"], None)
        self.run_main()
        for key in ("mu-codex", "kappa-claude"):
            row = self.panel()["residents"][key]
            self.assertEqual((row["binding"], row["verdict"], row["reason"]),
                             ("unknown", None, "one live body carries this session, but no ward row measures it"))

    def test_a_duplicate_key_with_a_live_body_is_not_counted_as_unregistered(self):
        self.body("host", self.IDS["dup"], "healthy")
        self.write_reports()
        self.run_main()
        panel = self.panel()
        self.assertEqual(panel["residents"]["dup-key"]["binding"], "ambiguous")
        self.assertEqual(panel["inventories"]["orphan_and_helper"]["unregistered"], {"rotate-soon": 1})

    def test_an_ambiguous_row_still_counts_its_archived_body_as_registered(self):
        self.register("rho-twin", "codex", self.IDS["rho"])
        self.run_main()
        panel = self.panel()
        self.assertEqual(panel["residents"]["rho-codex"]["binding"], "ambiguous")
        self.assertEqual(panel["inventories"]["lifecycle"]["archived_registered"], 1)

    def test_the_rounds_log_gets_one_line_and_no_rows(self):
        code, out = self.run_main()
        lines = [line for line in out.splitlines() if line.startswith("PANEL")]
        self.assertEqual(len(lines), 1)
        self.assertEqual(out.splitlines()[-1], lines[0])
        for row in self.registry:
            self.assertNotIn(row["key"], lines[0])
        self.assertIn("residents 9, active 8: one-live-body 3, missing 1, ambiguous 2, unknown 2, archived 1", lines[0])
        self.assertIn("not resident health: unregistered 1, helpers 1, unresolved 1, archived 1, archived registered 1",
                      lines[0])

    def test_a_panel_failure_changes_nothing_else(self):
        with mock.patch.object(diff, "build_panel", side_effect=RuntimeError("synthetic")):
            code, out = self.run_main()
        self.assertEqual(code, 0)
        self.assertEqual(self.panel()["status"], "unavailable (RuntimeError)")
        self.assertIn("SHOULD_ALERT=", out)
        self.assertTrue(diff.AGGREGATE_FILE.exists())


if __name__ == "__main__":
    unittest.main()
