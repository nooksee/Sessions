#!/usr/bin/env python3
"""Tests for ops/bin/open, in synthetic rooms only. Standard library only.

Every case builds its own room, with a law of its own on `main`, and a registry
of invented residents in a temporary directory. Where a case needs an open
packet it makes a real packet worktree whose leaf is rendered by the packet
tool itself, so the caller's functions are read exactly as they are in the
room. The packet tool's status and the gauge are stood in for, except in the
cases that say they run the real ones. Three cases read the room's own read-in
table and law, as files, to prove that the table cites only clauses in force
and has a row for each delivery function and for nothing else. No real
registry, body, mind or record is read or written. Run:

    python3 -I -B tools/test/test_open.py
"""
import contextlib
import datetime as dt
import importlib.machinery
import importlib.util
import io
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
OPEN = ROOT / "ops" / "bin" / "open"
sys.dont_write_bytecode = True
_loader = importlib.machinery.SourceFileLoader("open_under_test", str(OPEN))
_spec = importlib.util.spec_from_loader("open_under_test", _loader)
opn = importlib.util.module_from_spec(_spec)
sys.modules["open_under_test"] = opn
_loader.exec_module(opn)
packet = opn.sibling("packet")                      # the packet tool, loaded as the tool under test loads it

SESSION = "0000f00d-0000-4000-8000-00000000000{}"   # rotate's synthetic convention: the first four are zeros
T0 = dt.datetime(2026, 11, 12, 10, 0, tzinfo=dt.timezone.utc)
IDENTITY = {"GIT_AUTHOR_NAME": "Synthetic Room", "GIT_AUTHOR_EMAIL": "synthetic@example.invalid",
            "GIT_COMMITTER_NAME": "Synthetic Room", "GIT_COMMITTER_EMAIL": "synthetic@example.invalid"}
FOUR = ("Integrator", "Contractor", "Auditor", "Orchestrator")
KEYS = ("itg", "con", "aud", "orc", "out")          # four who may carry a function, and one more resident
# What the registry says of each resident's role. It is a function's name with a mark, and never the function the
# packet gives that resident: the tool must print none of it and decide nothing by it.
ROLES = {"itg": "Auditor QX0", "con": "Orchestrator QX1", "aud": "Integrator QX2", "orc": "Contractor QX3", "out": "Auditor QX4"}
PACKET_ID = "DP-SES-0001"

POLICY = """# Policy of Truth (PoT)

Not part of the preamble.

## Preamble
The system prevents action that violates policy.
A second line of the preamble.

## 1. Laws
- **1.1** A two-part clause for every reader.
- **1.2** [Retired]
- **1.2.1 Precedence.** A titled clause, with **bold** inside it.

## 2. Work

### 2.1 Stations
Words the law sets under this heading,
in two lines.
- **2.1.1** The clause for whoever integrates.
- **2.1.2 Auditor:** the clause for whoever audits.
A sentence the law sets between two clauses, which is no word of the heading.
- **2.1.3** The clause for whoever contracts.
- **2.1.4** The clause for whoever ships.
- **2.1.10** A clause whose number ends in two digits.
"""
CONTEXT = """# Context

## X01
Read in order.

## X04

Words before the table.

| Reader | Policy clauses | Constraints |
| --- | --- | --- |
| every reader | Preamble, 1.1, 1.2.1 | C01 |
| Integrator | 2.1.1, 1.1 | C02 |
| Contractor | 2.1.3, 2.1.1 | |
| Auditor | 2.1.2 | |
| Orchestrator | 2.1.4 | |
"""
CONSTRAINTS = """# Constraints

Opening words.

## C01

Filing. The first section,
in two lines.

## C02

Records. The second section.
"""
BOARD = """# Board

Updated: now.

## Now

- **Repository:** a synthetic room.

## Tracks

- A track line that an OPEN does not repeat.

## Open

- One open item.
"""
DECISIONS = "# Ledger\n\n### RoR-1: decision\n\n- an entry\n\n### RoR-2: standing direction\n\n- an entry\n"
STATUS = ["room: main at 000000000000, clean, level with origin/main as last fetched", "you: itg",
          "packet: none active; the next is DP-SES-0001"]
CLAUSE = {"Integrator": "The clause for whoever integrates.", "Contractor": "The clause for whoever contracts.",
          "Auditor": "the clause for whoever audits.", "Orchestrator": "The clause for whoever ships."}
STATIONS = ["### 2.1 Stations", "Words the law sets under this heading,", "in two lines."]   # a heading and its words


def git(cwd, *args) -> str:
    done = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True,
                          env=dict(opn.git_env(), **IDENTITY))
    if done.returncode:
        raise AssertionError(f"git {' '.join(args)} failed: {done.stderr}")
    return done.stdout.strip()


class Result:
    def __init__(self, code, out, err):
        self.code, self.out, self.err, self.text = code, out, err, out + err


class Room:
    """One synthetic room: a checkout on main that holds a small law, and a registry of invented residents."""

    def __init__(self, base: Path, policy: str = POLICY, context: str = CONTEXT, constraints: str = CONSTRAINTS):
        self.base = base.resolve()
        self.room = self.base / "room"
        self.room.mkdir()
        git(self.room, "-c", "init.templateDir=", "init", "-q", "-b", "main", ".")
        git(self.room, "config", "commit.gpgsign", "false")
        self.commit({opn.POLICY: policy, opn.CONTEXT: context, opn.CONSTRAINTS: constraints, opn.BOARD: BOARD,
                     opn.DECISIONS: DECISIONS, ".gitignore": "/logs/\n/var/tmp/\n"})
        self.registry = self.base / "registry.json"
        self.sessions = {key: SESSION.format(n) for n, key in enumerate(KEYS)}
        self.write_registry()
        self.tick = 0

    def write_registry(self) -> None:
        rows = [{"key": key, "person": f"Person {key}", "role": ROLES[key], "provider": "claude", "room": str(self.room),
                 "session_id": self.sessions[key]} for key in KEYS]
        rows.append({"key": "far", "person": "Person far", "role": "Auditor QX9", "provider": "claude",
                     "room": str(self.base / "elsewhere"), "session_id": SESSION.format(9)})
        self.registry.write_text(json.dumps({"identities": rows}))

    def commit(self, files: dict, message: str = "synthetic") -> str:
        for rel, text in files.items():
            path = self.room / rel
            if text is None:
                path.unlink()
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        git(self.room, "add", "-A")
        git(self.room, "commit", "-q", "-m", message)
        return git(self.room, "rev-parse", "HEAD")

    def open_packet(self, number: int = 1, **functions) -> Path:
        """A real packet worktree on a packet branch, with a leaf the packet tool renders. Keys default to the four
        residents named for them; a keyword gives one function to another key."""
        name, branch = f"DP-SES-{number:04d}", f"agent/dp-ses-{number:04d}-2026-11-12"
        head = {"Packet": name, "Branch": branch, "Base": "commit " + git(self.room, "rev-parse", "HEAD"),
                "Opened": "2026-11-12T10:01:00Z", "Integrator": "itg", "Contractor": "con", "Auditor": "aud",
                "Orchestrator": "orc", "Authority": "RoR-2"}
        head.update(functions)
        leaf = {"title": "Say more in the docs", "head": head, "objective": "Make the first page say more.",
                "scope": ["docs/"], "gates": ["ok"], "amendments": [], "results": None, "audit": None}
        worktree = self.room / packet.WORKTREE
        git(self.room, "worktree", "add", "-q", str(worktree), "-b", branch)
        path = worktree / packet.LEAVES / f"{name}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(packet.render_leaf(leaf))
        self.head = head
        return path

    def end_packet(self) -> None:
        """The open packet is gone, as after a landing: its worktree and its branch."""
        branch = git(self.room / packet.WORKTREE, "rev-parse", "--abbrev-ref", "HEAD")
        git(self.room, "worktree", "remove", "--force", str(self.room / packet.WORKTREE))
        git(self.room, "branch", "-D", branch)

    def packet_ledger(self, line: dict) -> None:
        """One line in the packet tool's own private ledger, as that tool would have written it."""
        path = self.room / packet.LEDGER
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a") as handle:
            handle.write(json.dumps(line) + "\n")

    def moment(self, minutes: int | None = None) -> str:
        if minutes is None:
            self.tick += 1
            minutes = self.tick
        return opn.iso(T0 + dt.timedelta(minutes=minutes))

    def run(self, *argv, who="itg", now=None) -> Result:
        full = ["--room", str(self.room), "--registry", str(self.registry), "--now", now or self.moment(), *argv]
        environ = {k: v for k, v in os.environ.items() if k != opn.SEAM}
        if who:
            environ[opn.SEAM] = who
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.dict(os.environ, environ, clear=True), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = opn.main(full)
        return Result(code, out.getvalue(), err.getvalue())

    def finish(self, first: Result, who="itg", now=None) -> list[Result]:
        """Every part from the one given to the last. Each must exit 0, and the OPEN must end."""
        results = [first]
        while results[-1].code == 0 and "END SESSIONS OPEN" not in results[-1].out and len(results) <= 80:
            results.append(self.run("--next", who=who, now=now))
        for result in results:
            if result.code:
                raise AssertionError(f"a part ended {result.code}: {result.text}")
        if "END SESSIONS OPEN" not in results[-1].out:
            raise AssertionError("the OPEN did not end")
        return results

    def open(self, who="itg", intent="a synthetic shift", now=None) -> list[Result]:
        """A whole OPEN: the first part and every next one."""
        return self.finish(self.run("--intent", intent, who=who, now=now), who=who, now=now)

    def ledger(self) -> list[dict]:
        path = self.room / opn.LEDGER
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


class Case(unittest.TestCase):
    policy, context, constraints = POLICY, CONTEXT, CONSTRAINTS

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="open-test-")
        self.addCleanup(self._tmp.cleanup)
        self.r = Room(Path(self._tmp.name), self.policy, self.context, self.constraints)
        self.addCleanup(mock.patch.stopall)
        for name, value in (("packet_status", list(STATUS)), ("fullness", "unknown (a stand-in)")):
            mock.patch.object(opn, name, return_value=value).start()

    def args(self):
        return types.SimpleNamespace(room=self.r.room, registry=self.r.registry)

    def refused(self, result: Result, *words: str) -> None:
        self.assertEqual(2, result.code, result.text)
        for word in words:
            self.assertIn(word, result.text)


def long_policy(clauses: int = 220) -> str:
    return POLICY + "".join(f"- **9.{n}** " + ("A clause that is long enough to fill a line of the law. " * 2).strip() + "\n"
                            for n in range(1, clauses + 1))


def trace_of(text: str) -> str:
    return re.search(r"^- trace: (\S+)$", text, re.MULTILINE).group(1)


def closing_of(text: str) -> str:
    return text[text.index("[EVERY READER"):]


# --------------------------------------------------------------------------
# Reading the law.
# --------------------------------------------------------------------------
class ReadingTheLaw(unittest.TestCase):
    def test_clauses_are_read_by_number_with_or_without_a_title(self):
        clauses = opn.policy_clauses(POLICY.splitlines())
        self.assertEqual("- **1.1** A two-part clause for every reader.", clauses["1.1"])
        self.assertTrue(clauses["1.2.1"].startswith("- **1.2.1 Precedence.** A titled clause, with **bold**"))
        self.assertTrue(clauses["2.1.2"].startswith("- **2.1.2 Auditor:**"))
        self.assertEqual("- **2.1.1** The clause for whoever integrates.", clauses["2.1.1"])
        self.assertEqual("- **2.1.10** A clause whose number ends in two digits.", clauses["2.1.10"])

    def test_the_preamble_is_the_text_under_its_own_heading_and_nothing_else(self):
        preamble = opn.policy_clauses(POLICY.splitlines())[opn.PREAMBLE]
        self.assertEqual("The system prevents action that violates policy.\nA second line of the preamble.", preamble)

    def test_a_clause_is_known_by_the_heading_it_stands_under_with_the_words_set_there(self):
        heads = opn.clause_heads(POLICY.splitlines())
        self.assertEqual(("## Preamble",), heads[opn.PREAMBLE])
        self.assertEqual(("## 1. Laws",), heads["1.1"])
        self.assertEqual(("## 1. Laws",), heads["1.2.1"])
        for number in ("2.1.1", "2.1.2", "2.1.3", "2.1.10"):
            self.assertEqual(tuple(STATIONS), heads[number])
        self.assertEqual(sorted(opn.policy_clauses(POLICY.splitlines())), sorted(heads))

    def test_clauses_are_shown_under_their_heading_once_for_the_clauses_that_follow_it(self):
        text = POLICY.splitlines()
        clauses, heads = opn.policy_clauses(text), opn.clause_heads(text)
        lines, cited = opn.shown(("a row", ["Preamble", "1.1", "2.1.1", "2.1.3", "1.2.1"], []), clauses, {}, set(), heads)
        self.assertEqual(["Preamble", "1.1", "2.1.1", "2.1.3", "1.2.1"], cited)
        self.assertEqual(["## Preamble", "The system prevents action that violates policy.", "A second line of the preamble.",
                          "## 1. Laws", clauses["1.1"], *STATIONS, clauses["2.1.1"], clauses["2.1.3"],
                          "## 1. Laws", clauses["1.2.1"]], lines)
        bare, _ = opn.shown(("a row", ["1.1", "2.1.1"], []), clauses, {}, set())
        self.assertEqual([clauses["1.1"], clauses["2.1.1"]], bare)

    def test_a_retired_clause_is_known_as_retired(self):
        clauses = opn.policy_clauses(POLICY.splitlines())
        self.assertTrue(opn.retired(clauses["1.2"]))
        self.assertFalse(opn.retired(clauses["1.1"]))

    def test_constraint_sections_are_split_at_their_headings_without_edge_blanks(self):
        sections = opn.constraint_sections(CONSTRAINTS.splitlines())
        self.assertEqual(["C01", "C02"], sorted(sections))
        self.assertEqual(["Filing. The first section,", "in two lines."], sections["C01"])

    def test_the_function_names_are_the_packet_tools_own(self):
        self.assertEqual(packet.FUNCTIONS, opn.function_names())
        self.assertEqual(FOUR, opn.function_names())
        with mock.patch.object(packet, "FUNCTIONS", ("Integrator", "Clerk")):
            self.assertEqual(("Integrator", "Clerk"), opn.function_names())
        for broken in ((), ["Integrator"], ("Integrator", ""), None):
            with self.subTest(broken=broken), mock.patch.object(packet, "FUNCTIONS", broken), self.assertRaises(opn.Refused):
                opn.function_names()

    def test_the_table_is_read_as_every_reader_and_the_four_functions(self):
        rows = opn.read_table(CONTEXT.splitlines(), FOUR)
        self.assertEqual(("every reader", ["Preamble", "1.1", "1.2.1"], ["C01"]), rows[0])
        self.assertEqual(list(FOUR), [row[0] for row in rows[1:]])
        self.assertEqual(("Auditor", ["2.1.2"], []), rows[3])

    def test_a_table_that_cannot_be_read_exactly_is_refused(self):
        broken = {
            "missing": CONTEXT.replace("## X04", "## X05"),
            "first row is not for every reader": CONTEXT.replace("| every reader | Preamble, 1.1, 1.2.1 | C01 |\n", ""),
            "4 cells": CONTEXT.replace("| Auditor | 2.1.2 | |", "| Auditor | 2.1.2 | | |"),
            "not a clause number": CONTEXT.replace("2.1.2", "the second"),
            "not a section of the constraints": CONTEXT.replace("| C02 |", "| Chapter 2 |"),
            "names a reader twice": CONTEXT + "| auditor | 1.1 | |\n",
        }
        for words, text in broken.items():
            with self.subTest(words), self.assertRaises(opn.Refused) as caught:
                opn.read_table(text.splitlines(), FOUR)
            self.assertIn(words, str(caught.exception))

    def test_a_row_that_is_not_a_delivery_function_is_refused_and_so_is_a_function_without_a_row(self):
        with self.assertRaises(opn.Refused) as caught:
            opn.read_table((CONTEXT + "| Clerk | 1.1 | |\n").splitlines(), FOUR)
        self.assertIn("has a row for 'Clerk', which is not a delivery function", str(caught.exception))
        self.assertIn("every reader, Integrator, Contractor, Auditor, Orchestrator", str(caught.exception))
        with self.assertRaises(opn.Refused) as caught:
            opn.read_table(CONTEXT.replace("| Auditor | 2.1.2 | |\n", "").splitlines(), FOUR)
        self.assertIn("has no row for the Auditor function", str(caught.exception))
        with self.assertRaises(opn.Refused) as caught:
            opn.read_table(CONTEXT.replace("| Auditor |", "| auditors |").splitlines(), FOUR)
        self.assertIn("which is not a delivery function", str(caught.exception))

    def test_a_citation_of_a_clause_that_is_absent_or_retired_is_a_problem(self):
        clauses = opn.policy_clauses(POLICY.splitlines())
        sections = opn.constraint_sections(CONSTRAINTS.splitlines())
        rows = [("every reader", ["1.1", "7.7", "1.2"], ["C09"])]
        problems = opn.table_problems(rows, clauses, sections)
        self.assertEqual(3, len(problems), problems)
        self.assertIn("7.7, which the policy does not hold", problems[0])
        self.assertIn("1.2, which is retired", problems[1])
        self.assertIn("C09, which the constraints do not hold", problems[2])
        self.assertEqual([], opn.table_problems(opn.read_table(CONTEXT.splitlines(), FOUR), clauses, sections))

    def test_the_rows_shown_are_the_functions_carried_and_all_four_when_none_is(self):
        rows = opn.read_table(CONTEXT.splitlines(), FOUR)
        self.assertEqual(["Contractor"], [row[0] for row in opn.function_rows(rows, FOUR, ["Contractor"])])
        self.assertEqual(["Integrator", "Auditor"], [row[0] for row in opn.function_rows(rows, FOUR, ["Auditor", "Integrator"])])
        self.assertEqual(list(FOUR), [row[0] for row in opn.function_rows(rows, FOUR, [])])

    def test_a_duty_is_said_in_one_line(self):
        def said(functions, packet_id=PACKET_ID, note=None):
            return opn.duty_text({"packet": packet_id, "functions": functions, "note": note})

        self.assertEqual("Contractor in DP-SES-0001", said(["Contractor"]))
        self.assertEqual("Integrator and Contractor in DP-SES-0001", said(["Integrator", "Contractor"]))
        self.assertEqual("Integrator, Contractor and Orchestrator in DP-SES-0001", said(["Integrator", "Contractor", "Orchestrator"]))
        self.assertEqual("none in DP-SES-0001", said([]))
        self.assertEqual("none; no packet is open", said([], packet_id=None))
        self.assertEqual("unknown (the worktree is not a packet)", said([], packet_id=None, note="the worktree is not a packet"))

    def test_sections_share_a_part_where_they_fit_and_a_large_one_begins_its_own_and_is_cut_between_lines(self):
        small = [["a", "b"], ["c"]]
        self.assertEqual([["a", "b", "c"]], opn.pack(small))
        many = [f"line {n}" for n in range(opn.PART_LINES + 5)]
        large = [["head"], many, ["tail one", "tail two"]]
        self.assertEqual([["head"], many[:opn.PART_LINES], [*many[opn.PART_LINES:], "tail one", "tail two"]], opn.pack(large))
        most = [f"line {n}" for n in range(opn.PART_LINES - 1)]
        self.assertEqual([["head", *most], ["tail one", "tail two"]], opn.pack([["head"], most, ["tail one", "tail two"]]))
        heavy = ["x" * (opn.PART_BYTES // 2)]
        self.assertEqual([["head", *heavy], heavy], opn.pack([["head"], heavy, heavy]))

    def test_a_section_that_begins_a_part_drops_its_opening_blank_lines_and_one_that_joins_a_part_keeps_them(self):
        heavy = "x" * (opn.PART_BYTES * 2 // 3)
        self.assertEqual([["head", "", heavy], ["[NEXT]", "", heavy]],
                         opn.pack([["head"], ["", heavy], ["", "", "[NEXT]", "", heavy]]))
        self.assertEqual([["head", "", "[NEXT]"]], opn.pack([["head"], ["", "[NEXT]"]]))

    def test_a_line_longer_than_a_part_stays_whole_in_a_part_of_its_own(self):
        giant = "x" * (opn.PART_BYTES + 100)
        self.assertEqual([["before"], [giant], ["after"]], opn.pack([["before"], [giant], ["after"]]))


# --------------------------------------------------------------------------
# The room's own table and law, read as files: what the required check proves
# about a change before it lands.
# --------------------------------------------------------------------------
class TheRoomsOwnTable(unittest.TestCase):
    def setUp(self):
        policy = (ROOT / opn.POLICY).read_text(encoding="utf-8").splitlines()
        self.clauses, self.heads = opn.policy_clauses(policy), opn.clause_heads(policy)
        self.sections = opn.constraint_sections((ROOT / opn.CONSTRAINTS).read_text(encoding="utf-8").splitlines())
        self.rows = opn.read_table((ROOT / opn.CONTEXT).read_text(encoding="utf-8").splitlines(), opn.function_names())

    def test_the_rooms_table_has_a_row_for_every_reader_and_for_each_function_and_for_nothing_else(self):
        self.assertEqual([opn.EVERY, *packet.FUNCTIONS], [row[0] for row in self.rows])

    def test_every_citation_of_the_rooms_table_is_a_clause_in_force(self):
        self.assertEqual([], opn.table_problems(self.rows, self.clauses, self.sections))
        for row in self.rows:
            self.assertTrue(row[1] or row[2], f"the row for {row[0]} cites nothing")
            for number in row[1]:
                self.assertTrue(self.heads.get(number), f"{number} stands under no heading of the law")

    def test_what_every_open_repeats_stays_short_enough_for_one_part(self):
        """The freshness lines, the clauses for every reader and the clauses for all the functions are read as one
        part: an eighth of a part is left for the freshness lines and the labels."""
        seen: set = set()
        weight = count = 0
        for row in self.rows:
            lines, _ = opn.shown(row, self.clauses, self.sections, seen, self.heads)
            weight += sum(len(line.encode("utf-8")) + 1 for line in lines)
            count += len(lines)
        self.assertLessEqual(weight, opn.PART_BYTES * 7 // 8)
        self.assertLessEqual(count, opn.PART_LINES * 7 // 8)


# --------------------------------------------------------------------------
# An OPEN, from its first part to its record.
# --------------------------------------------------------------------------
class AnOpen(Case):
    def test_a_first_open_shows_the_law_whole_then_the_clauses_and_is_recorded(self):
        parts = self.r.open()
        self.assertEqual(1, len(parts))
        text = parts[0].out
        for path in opn.LAW:
            self.assertIn(f"[THE LAW, WHOLE: {path}", text)
        self.assertIn("because this body has not been shown it", text)
        self.assertIn("Not part of the preamble.", text)
        self.assertLess(text.index("[THE LAW, WHOLE"), text.index("[EVERY READER"))
        self.assertLess(text.index("[EVERY READER"), text.index("[THE FUNCTIONS"))
        self.assertLess(text.index("[THE FUNCTIONS"), text.index("[PRESENT STATE"))
        self.assertIn("END SESSIONS OPEN: complete and recorded", text)
        record, = self.r.ledger()
        self.assertEqual(("open", "itg", "a synthetic shift"), (record["action"], record["key"], record["intent"]))
        self.assertEqual(list(opn.LAW), record["whole"])
        self.assertEqual((None, [], list(FOUR)), (record["packet"], record["functions"], record["rows"]))
        self.assertEqual(["Preamble", "1.1", "1.2.1", "C01", "2.1.1", "C02", "2.1.3", "2.1.2", "2.1.4"], record["clauses"])
        self.assertEqual(opn.sha256(text.encode("utf-8")), record["output"])
        self.assertEqual(git(self.r.room, "rev-parse", "HEAD"), record["main"])
        self.assertEqual({path: opn.sha256((self.r.room / path).read_bytes()) for path in opn.LAW}, record["law"])

    def test_a_second_open_in_the_same_body_repeats_the_clauses_and_no_whole_file(self):
        self.r.open()
        text = self.r.open()[0].out
        self.assertNotIn("[THE LAW, WHOLE", text)
        self.assertIn("- **1.1** A two-part clause for every reader.", text)
        self.assertEqual([], self.r.ledger()[-1]["whole"])

    def test_with_no_packet_open_all_four_functions_are_shown_and_the_reader_is_told_why(self):
        text = self.r.open()[0].out
        self.assertIn("- function: none; no packet is open", text)
        self.assertIn("[THE FUNCTIONS: all 4 are shown, because no packet is open; a packet's leaf says who carries each]", text)
        closing = closing_of(text)
        for name in FOUR:
            self.assertIn(f"\n{name}:\n", closing)
            self.assertIn(CLAUSE[name], closing)
        self.assertNotIn("[YOUR FUNCTION", text)

    def test_a_resident_is_shown_the_function_the_open_packets_leaf_gives_it_and_no_other(self):
        self.r.open_packet()
        for key, name in zip(KEYS, FOUR):
            with self.subTest(key=key, function=name):
                text = self.r.open(who=key)[0].out
                closing = closing_of(text)
                self.assertIn(f"- function: {name} in {PACKET_ID}", text)
                self.assertIn(f"[YOUR FUNCTION IN {PACKET_ID}: {name}]", closing)
                self.assertIn(CLAUSE[name], closing)
                for other in FOUR:
                    if other != name:
                        self.assertNotIn(f"{PACKET_ID}: {other}]", closing)
                self.assertNotIn("[THE FUNCTIONS", text)
                record = self.r.ledger()[-1]
                self.assertEqual((PACKET_ID, [name], [name]), (record["packet"], record["functions"], record["rows"]))
        auditor = closing_of(self.r.open(who="aud")[0].out)
        self.assertNotIn(CLAUSE["Integrator"], auditor)
        self.assertNotIn(CLAUSE["Contractor"], auditor)
        self.assertNotIn(CLAUSE["Orchestrator"], auditor)

    def test_a_resident_who_carries_two_functions_is_shown_both_and_a_shared_clause_once(self):
        self.r.open_packet(Contractor="itg")
        text = self.r.open(who="itg")[0].out
        closing = closing_of(text)
        self.assertIn(f"- function: Integrator and Contractor in {PACKET_ID}", text)
        self.assertLess(closing.index(f"[YOUR FUNCTION IN {PACKET_ID}: Integrator]"),
                        closing.index(f"[YOUR FUNCTION IN {PACKET_ID}: Contractor]"))
        self.assertEqual(1, closing.count(CLAUSE["Integrator"]))
        self.assertEqual(1, closing.count("- **1.1** A two-part clause for every reader."))
        self.assertIn(CLAUSE["Contractor"], closing)
        self.assertNotIn(CLAUSE["Auditor"], closing)
        self.assertEqual(["Integrator", "Contractor"], self.r.ledger()[-1]["functions"])

    def test_a_resident_the_open_packet_does_not_name_is_shown_all_four(self):
        self.r.open_packet()
        text = self.r.open(who="out")[0].out
        self.assertIn(f"- function: none in {PACKET_ID}", text)
        self.assertIn(f"[THE FUNCTIONS: all 4 are shown, because the leaf of {PACKET_ID} gives you none;", text)
        for name in FOUR:
            self.assertIn(CLAUSE[name], closing_of(text))
        record = self.r.ledger()[-1]
        self.assertEqual((PACKET_ID, [], list(FOUR)), (record["packet"], record["functions"], record["rows"]))

    def test_a_function_is_read_from_the_leaf_and_never_from_the_registry(self):
        """The registry calls itg an auditor. The leaf makes itg the Integrator. The leaf decides, and nothing of the
        registry's role is printed or kept."""
        self.r.open_packet()
        parts = self.r.open(who="itg")
        said = "".join(part.text for part in parts) + self.r.run("--check").text + self.r.run("--roster").text
        closing = closing_of(parts[0].out)
        self.assertIn(f"[YOUR FUNCTION IN {PACKET_ID}: Integrator]", closing)
        self.assertNotIn(CLAUSE["Auditor"], closing)
        self.assertNotIn("QX", said)
        self.assertNotIn("QX", (self.r.room / opn.LEDGER).read_text())
        self.assertNotIn("role", self.r.ledger()[-1])

    def test_a_leaf_that_cannot_be_read_gives_no_function_whatever_the_packet_tools_ledger_remembers(self):
        path = self.r.open_packet()
        self.r.packet_ledger({"packet": PACKET_ID, "action": "open", "actor": "itg", "functions": self.r.head})
        path.write_text(path.read_text() + "a line the tool did not write\n")
        lenient = packet.Active(self.args(), lenient=True)
        self.assertTrue(lenient.damage)
        self.assertEqual("aud", lenient.head["Auditor"])      # the packet tool falls back on its ledger; an OPEN does not
        text = self.r.open(who="aud")[0].out
        self.assertIn(f"- function: unknown (the leaf of {PACKET_ID} cannot be read)", text)
        self.assertIn("[THE FUNCTIONS: all 4 are shown, because the open packet could not be read;", text)
        self.assertNotIn("[YOUR FUNCTION", text)
        record = self.r.ledger()[-1]
        self.assertEqual((PACKET_ID, [], list(FOUR)), (record["packet"], record["functions"], record["rows"]))

    def test_a_fault_of_the_packet_tool_is_said_and_all_four_are_shown(self):
        self.r.open_packet()
        with mock.patch.object(packet, "Active", side_effect=RuntimeError("a fault")):
            text = self.r.open(who="aud")[0].out
        self.assertIn("- function: unknown (the packet tool could not read the open packet (RuntimeError))", text)
        self.assertNotIn("[YOUR FUNCTION", text)
        for name in FOUR:
            self.assertIn(CLAUSE[name], closing_of(text))
        self.assertEqual((None, []), (self.r.ledger()[-1]["packet"], self.r.ledger()[-1]["functions"]))

    def test_a_function_stands_under_its_heading_of_the_law_with_the_words_set_there(self):
        self.r.open_packet()
        closing = closing_of(self.r.open(who="orc")[0].out).splitlines()
        at = closing.index(f"[YOUR FUNCTION IN {PACKET_ID}: Orchestrator]")
        self.assertEqual([*STATIONS, "- **2.1.4** The clause for whoever ships.", ""], closing[at + 1:at + 6])
        every = closing[:at]
        self.assertEqual(["## Preamble", "The system prevents action that violates policy."], every[1:3])
        self.assertEqual(1, every.count("## 1. Laws"))

    def test_a_worktree_that_is_not_a_packet_is_said_so_and_all_four_are_shown(self):
        (self.r.room / packet.WORKTREE).mkdir(parents=True)
        text = self.r.open()[0].out
        self.assertIn("- function: unknown (", text)
        self.assertIn("is not this room's packet worktree", text)
        for name in FOUR:
            self.assertIn(CLAUSE[name], closing_of(text))
        self.assertEqual((None, []), (self.r.ledger()[-1]["packet"], self.r.ledger()[-1]["functions"]))

    def test_a_constraint_section_is_shown_whole_under_its_name(self):
        text = self.r.open()[0].out
        self.assertIn("C01 (constraints):\nFiling. The first section,\nin two lines.", text)

    def test_the_law_is_read_from_main_and_never_from_an_uncommitted_edit(self):
        (self.r.room / opn.POLICY).write_text(POLICY.replace("A two-part clause", "A forged clause"))
        text = self.r.open()[0].out
        self.assertNotIn("forged", text)
        self.assertIn("A two-part clause for every reader.", text)

    def test_the_present_state_is_the_packet_status_the_ledger_head_the_fullness_and_two_board_sections(self):
        text = self.r.open()[0].out
        state = text[text.index("[PRESENT STATE"):]
        for line in STATUS:
            self.assertIn(line, state)
        self.assertIn("ledger: the newest entry is RoR-2 (standing direction)", state)
        self.assertIn("fullness: unknown (a stand-in)", state)
        self.assertIn("## Now\n- **Repository:** a synthetic room.\n## Open\n- One open item.", state)
        self.assertNotIn("A track line", state)

    def test_a_board_without_the_named_sections_is_shown_by_its_first_lines(self):
        self.assertEqual(["# Board", "one", "two"], opn.board_lines(["# Board", "", "one", "two"]))

    def test_the_report_names_the_caller_its_function_the_trace_and_the_law(self):
        self.r.open_packet()
        text = self.r.open(who="con")[0].out
        record = self.r.ledger()[-1]
        report = text[text.index("[REPORT"):]
        self.assertIn("- identity: Person con, registry key con", report)
        self.assertIn(f"- function: Contractor in {PACKET_ID}", report)
        self.assertIn("- parent authority: Control", report)
        self.assertIn(f"- read-in: OPEN {record['trace']}, the law on main at {record['main'][:12]}, good until {record['until']}", report)
        self.assertIn("- fullness: unknown (a stand-in)", report)
        self.assertIn("- caller: con (Person con)", text)

    def test_what_landed_since_the_last_open_is_named(self):
        self.r.open()
        self.r.commit({"archives/packets/DP-SES-0002.md": "a leaf\n", "docs/a.md": "alpha\n"}, "DP-SES-0002: a landing")
        text = self.r.open()[0].out
        self.assertRegex(text, r"since your OPEN of \S+: main moved by 1 commit\(s\), landing DP-SES-0002")

    def test_an_open_needs_one_plain_line_of_intent(self):
        self.refused(self.r.run(), "states what the shift is for")
        self.refused(self.r.run("--intent", "   "), "states what the shift is for")
        self.refused(self.r.run("--intent", "x" * (opn.INTENT_LIMIT + 1)), "one plain line")
        self.refused(self.r.run("--intent", "a bell \x07 rings"), "one plain line")
        self.assertEqual([], self.r.ledger())
        self.r.open(intent="two lines\n  made   one")
        self.assertEqual("two lines made one", self.r.ledger()[-1]["intent"])

    def test_no_output_and_no_record_holds_a_session_identifier(self):
        parts = self.r.open()
        said = "".join(part.text for part in parts) + self.r.run("--check").text + self.r.run("--roster").text
        kept = (self.r.room / opn.LEDGER).read_text()
        for session in self.r.sessions.values():
            self.assertNotIn(session, said)
            self.assertNotIn(session, kept)
        self.assertEqual(opn.sha256(self.r.sessions["itg"].encode())[:16], self.r.ledger()[-1]["body"])

    def test_the_ledger_and_its_folder_are_private(self):
        self.r.open()
        folder = self.r.room / opn.LEDGER.parent
        self.assertEqual(0o700, stat.S_IMODE(folder.stat().st_mode))
        self.assertEqual(0o600, stat.S_IMODE((self.r.room / opn.LEDGER).stat().st_mode))
        self.assertEqual("", git(self.r.room, "status", "--porcelain"))


class InParts(Case):
    policy = long_policy()

    def test_a_long_law_is_printed_in_parts_and_recorded_only_at_the_last(self):
        first = self.r.run("--intent", "a long read")
        self.assertEqual(0, first.code, first.text)
        self.assertRegex(first.out, r"^===== SESSIONS OPEN, part 1 of (\d+) \(\d+ lines\) =====\n")
        self.assertIn(f"The read-in is not complete. Run: {opn.NEXT} =====", first.out)
        self.assertEqual([], self.r.ledger())
        self.refused(self.r.run("--check"), "no good OPEN: none is on record")
        parts = self.r.finish(first)
        self.assertGreater(len(parts), 2)
        record, = self.r.ledger()
        self.assertEqual(len(parts), record["parts"])
        self.assertEqual(opn.sha256("".join(part.out for part in parts).encode("utf-8")), record["output"])
        self.assertEqual(0, self.r.run("--check").code)

    def test_no_part_is_larger_than_a_shell_tool_passes_and_no_line_of_the_law_is_lost(self):
        parts = [part.out for part in self.r.open()]
        for number, text in enumerate(parts, 1):
            lines = text.splitlines()
            self.assertLessEqual(len(lines), opn.PART_LINES + 2)
            self.assertLessEqual(len(text.encode("utf-8")), opn.PART_BYTES + 400)
            self.assertIn(f"part {number} of {len(parts)}", lines[0])
            self.assertTrue(lines[-1].startswith("====="))
        body = [line for text in parts for line in text.splitlines()[1:-1]]
        start = body.index(next(line for line in body if line.startswith(f"[THE LAW, WHOLE: {opn.POLICY}")))
        law = self.policy.splitlines()
        self.assertEqual(law, body[start + 1:start + 1 + len(law)])

    def test_the_clauses_stay_together_in_one_part_and_so_does_the_present_state(self):
        parts = [part.out for part in self.r.open()]
        clauses, = [text for text in parts if "[EVERY READER" in text]
        self.assertIn("[THE FUNCTIONS", clauses)
        self.assertIn(CLAUSE["Orchestrator"], clauses)
        state, = [text for text in parts if "[PRESENT STATE" in text]
        for heading in ("[THE BOARD", "[REPORT", "- fullness:"):
            self.assertIn(heading, state)
        self.assertEqual(parts[-1], state)

    def test_the_whole_law_the_clauses_and_the_present_state_are_three_runs_of_lines(self):
        """What is packed: with a file printed whole, three runs, so the clauses and the present state each move to a
        new part before they are cut; with none, two runs, and the first begins with the freshness lines, so an
        ordinary OPEN never begins with a part of a few lines."""
        packed = []
        real = opn.pack

        def watch(sections):
            packed.append(sections)
            return real(sections)

        with mock.patch.object(opn, "pack", side_effect=watch):
            self.r.open()
            self.r.open()
        first, ordinary = packed
        self.assertEqual(3, len(first))
        self.assertEqual("[FRESHNESS]", first[0][0])
        self.assertTrue(any(line.startswith("[THE LAW, WHOLE") for line in first[0]))
        self.assertFalse(any(line.startswith("[EVERY READER") for line in first[0]))
        self.assertTrue(first[1][1].startswith("[EVERY READER"))
        self.assertFalse(any(line.startswith("[PRESENT STATE") for line in first[1]))
        self.assertTrue(first[2][1].startswith("[PRESENT STATE"))
        self.assertTrue(first[2][-1].startswith("- fullness:"))
        self.assertEqual(2, len(ordinary))
        self.assertEqual("[FRESHNESS]", ordinary[0][0])
        self.assertTrue(any(line.startswith("[EVERY READER") for line in ordinary[0]))
        self.assertEqual(first[1], ordinary[0][-len(first[1]):])
        self.assertTrue(ordinary[1][1].startswith("[PRESENT STATE"))

    def test_an_ordinary_open_too_long_for_one_part_is_cut_between_the_clauses_and_the_present_state(self):
        self.r.open()
        board = BOARD.replace("- One open item.\n", "".join(f"- Open item {n}, which is long enough to fill a line of the board.\n"
                                                              for n in range(120)))
        self.r.commit({opn.BOARD: board}, "a long board")
        parts = [part.out for part in self.r.open()]
        self.assertEqual(2, len(parts))
        self.assertIn("[FRESHNESS]", parts[0])
        self.assertIn("[EVERY READER", parts[0])
        self.assertIn("[THE FUNCTIONS", parts[0])
        self.assertNotIn("[PRESENT STATE", parts[0])
        self.assertEqual("[PRESENT STATE: read now, never remembered]", parts[1].splitlines()[1])
        self.assertIn("[REPORT", parts[1])

    def test_next_without_an_unfinished_open_is_refused(self):
        self.refused(self.r.run("--next"), "you have no unfinished OPEN")
        self.r.open()
        self.refused(self.r.run("--next"), "you have no unfinished OPEN")

    def test_an_unfinished_open_is_dropped_when_the_law_changes_while_it_is_read(self):
        self.r.run("--intent", "interrupted")
        self.r.commit({opn.CONSTRAINTS: CONSTRAINTS + "\n## C03\n\nA new section.\n"}, "the law moved")
        self.refused(self.r.run("--next"), "the law changed while you were reading", "begin again")
        self.refused(self.r.run("--next"), "you have no unfinished OPEN")
        self.assertEqual([], self.r.ledger())

    def test_an_unfinished_open_is_dropped_in_another_body_or_after_an_hour(self):
        self.r.run("--intent", "interrupted")
        self.r.sessions["itg"] = SESSION.format(7)
        self.r.write_registry()
        self.refused(self.r.run("--next"), "it was begun in another body")
        self.r.run("--intent", "slow", now=self.r.moment(100))
        self.refused(self.r.run("--next", now=self.r.moment(100 + opn.PENDING_LIFE // 60 + 1)), "it waited too long")

    def test_a_new_open_replaces_an_unfinished_one_and_says_so(self):
        first = self.r.run("--intent", "the first")
        second = self.r.run("--intent", "the second")
        self.assertEqual(0, second.code, second.text)
        self.assertIn("is dropped; this one replaces it", second.err)
        self.assertNotEqual(trace_of(first.out), trace_of(second.out))
        self.r.finish(second)
        self.assertEqual(["the second"], [record["intent"] for record in self.r.ledger()])

    def test_each_caller_reads_its_own_unfinished_open(self):
        self.r.run("--intent", "one resident reads", who="itg")
        self.refused(self.r.run("--next", who="aud"), "you have no unfinished OPEN")
        self.assertEqual(0, self.r.run("--next", who="itg").code)


# --------------------------------------------------------------------------
# Standing: one body, one text of the law, one shift.
# --------------------------------------------------------------------------
class Standing(Case):
    def test_a_good_open_is_said_good_with_its_trace_and_intent(self):
        self.r.open(intent="keep the rotations going")
        result = self.r.run("--check")
        self.assertEqual(0, result.code, result.text)
        self.assertIn(f"OPEN good: itg, trace {self.r.ledger()[-1]['trace']}", result.out)
        self.assertIn("intent: keep the rotations going", result.out)

    def test_without_an_open_the_check_refuses_and_names_the_command(self):
        self.refused(self.r.run("--check"), "no good OPEN: none is on record", f"python3 -I -B {opn.TOOL} --intent TEXT")

    def test_a_change_to_any_file_of_the_law_ends_every_open_and_only_that_file_is_shown_whole_again(self):
        self.r.open()
        self.r.commit({opn.POLICY: POLICY + "- **2.1.11** A clause added by an amendment.\n"}, "an amendment lands")
        self.refused(self.r.run("--check"), f"the law changed since it was made: {opn.POLICY}")
        text = self.r.open()[0].out
        self.assertIn(f"[THE LAW, WHOLE: {opn.POLICY}", text)
        self.assertIn("because it changed since your last OPEN", text)
        self.assertIn("A clause added by an amendment.", text)
        self.assertNotIn(f"[THE LAW, WHOLE: {opn.CONTEXT}", text)
        self.assertEqual([opn.POLICY], self.r.ledger()[-1]["whole"])
        self.assertEqual(0, self.r.run("--check").code)

    def test_a_commit_that_leaves_the_law_alone_ends_no_open(self):
        self.r.open()
        self.r.commit({"docs/a.md": "alpha\n"}, "a landing that is not law")
        self.assertEqual(0, self.r.run("--check").code)

    def test_a_new_body_holds_no_open_and_is_shown_the_whole_law(self):
        self.r.open()
        self.r.sessions["itg"] = SESSION.format(7)
        self.r.write_registry()
        self.refused(self.r.run("--check"), "the last one was made in another body")
        text = self.r.open()[0].out
        for path in opn.LAW:
            self.assertIn(f"[THE LAW, WHOLE: {path}", text)
        self.assertEqual(0, self.r.run("--check").code)

    def test_an_open_ends_with_its_shift(self):
        self.r.open(now=self.r.moment(0))
        last = opn.SHIFT // 60
        self.assertEqual(0, self.r.run("--check", now=self.r.moment(last - 1)).code)
        self.refused(self.r.run("--check", now=self.r.moment(last)), "its shift ended at")

    def test_an_open_that_showed_every_function_stays_good_when_a_packet_names_the_caller(self):
        self.r.open(who="aud")                              # no packet is open, so all four were shown
        self.r.open_packet()
        self.assertEqual(0, self.r.run("--check", who="aud").code)

    def test_an_open_ends_when_a_packet_gives_the_caller_a_function_it_did_not_show(self):
        self.r.open_packet()
        self.r.open(who="aud")                              # shown: the Auditor's clauses and no other function's
        self.assertEqual(["Auditor"], self.r.ledger()[-1]["rows"])
        self.assertEqual(0, self.r.run("--check", who="aud").code)
        self.r.end_packet()
        self.assertEqual(0, self.r.run("--check", who="aud").code)
        self.r.open_packet(2, Contractor="aud", Auditor="con")
        self.refused(self.r.run("--check", who="aud"), "no good OPEN: it did not show the clauses for Contractor in DP-SES-0002",
                     f"python3 -I -B {opn.TOOL} --intent TEXT")
        roster = {line.split()[0]: line for line in self.r.run("--roster", who=None).out.splitlines()[1:]}
        self.assertIn("no OPEN: it did not show the clauses for Contractor in DP-SES-0002; last OPEN", roster["aud"])
        text = self.r.open(who="aud")[0].out
        self.assertIn("[YOUR FUNCTION IN DP-SES-0002: Contractor]", text)
        self.assertNotIn("[THE LAW, WHOLE", text)
        self.assertEqual(0, self.r.run("--check", who="aud").code)

    def test_every_function_the_packet_gives_must_have_been_shown(self):
        self.r.open_packet()
        self.r.open(who="aud")
        self.r.end_packet()
        self.r.open_packet(2, Integrator="aud", Contractor="aud", Auditor="con")
        self.refused(self.r.run("--check", who="aud"), "it did not show the clauses for Integrator and Contractor in DP-SES-0002")
        self.r.end_packet()
        self.r.open_packet(3, Orchestrator="aud")
        self.refused(self.r.run("--check", who="aud"), "it did not show the clauses for Orchestrator in DP-SES-0003")

    def test_one_residents_open_is_not_anothers(self):
        self.r.open(who="itg")
        self.refused(self.r.run("--check", who="aud"), "none is on record")

    def test_the_standing_function_answers_for_a_tool_that_would_require_an_open(self):
        self.r.open(now=self.r.moment(0))
        commit = git(self.r.room, "rev-parse", "HEAD")
        law = opn.hashes(opn.read_law(self.r.room, commit))
        body = opn.sha256(self.r.sessions["itg"].encode())[:16]
        record, reason = opn.standing(self.r.room, "itg", body, law, T0 + dt.timedelta(minutes=5))
        self.assertEqual(self.r.ledger()[-1]["trace"], record["trace"])
        self.assertTrue(reason.startswith("good until "))
        self.assertEqual((None, "none is on record"), opn.standing(self.r.room, "aud", body, law, T0))
        soon = T0 + dt.timedelta(minutes=5)
        asked = {"packet": "DP-SES-0009", "functions": ["Auditor"], "note": None}
        self.assertEqual(record, opn.standing(self.r.room, "itg", body, law, soon, asked)[0])      # all four were shown
        self.r.open_packet()
        self.r.open(now=self.r.moment(1))                   # shown: the Integrator's clauses only
        self.assertEqual(["Integrator"], self.r.ledger()[-1]["rows"])
        self.assertEqual((None, "it did not show the clauses for Auditor in DP-SES-0009"),
                         opn.standing(self.r.room, "itg", body, law, soon, asked))
        self.assertEqual((None, "it did not show the clauses for Auditor"),
                         opn.standing(self.r.room, "itg", body, law, soon, {"functions": ["Auditor"]}))
        self.assertIsNotNone(opn.standing(self.r.room, "itg", body, law, soon, {"functions": ["Integrator"]})[0])
        self.assertIsNotNone(opn.standing(self.r.room, "itg", body, law, soon)[0])

    def test_a_line_of_the_ledger_that_is_not_a_record_is_passed_over(self):
        self.r.open()
        with (self.r.room / opn.LEDGER).open("a") as handle:
            handle.write("not json\n[1, 2]\n{\"action\": \"other\"}\n")
        self.assertEqual(0, self.r.run("--check").code)
        self.assertEqual(1, len(opn.ledger_rows(self.r.room)))


# --------------------------------------------------------------------------
# Who may open, and what is refused.
# --------------------------------------------------------------------------
class Refusals(Case):
    def test_an_unverified_reader_is_shown_the_common_read_in_and_nothing_is_recorded(self):
        result = self.r.run("--intent", "a visit", who="ghost")
        self.assertEqual(2, result.code, result.text)
        self.assertIn("- caller: unverified (", result.out)
        self.assertIn("- **1.1** A two-part clause for every reader.", result.out)
        self.assertNotIn("[YOUR FUNCTION", result.out)
        self.assertNotIn("[THE FUNCTIONS", result.out)
        self.assertNotIn("- function:", result.out)
        self.assertNotIn("[THE LAW, WHOLE", result.out)
        self.assertIn("nothing was recorded. An unverified reader says so and waits for the operator.", result.out)
        self.assertFalse((self.r.room / "logs").exists())

    def test_a_resident_of_another_room_is_unverified_here(self):
        result = self.r.run("--intent", "a visit", who="far")
        self.assertEqual(2, result.code, result.text)
        self.assertIn("registered to another room", result.out)
        self.refused(self.r.run("--check", who="far"), "the caller is not verified")

    def test_another_registry_serves_tests_only(self):
        result = self.r.run("--intent", "no seam", who=None)
        self.refused(result, "the caller is verified through the room's canonical registry; another registry serves tests only")
        self.assertEqual("", result.out)
        self.refused(self.r.run("--check", who=None), "another registry serves tests only")

    def test_a_table_that_cites_a_missing_clause_opens_nothing(self):
        self.r.commit({opn.CONTEXT: CONTEXT.replace("| Auditor | 2.1.2 | |", "| Auditor | 2.1.2, 8.8 | |")}, "a bad table")
        result = self.r.run("--intent", "blocked")
        self.refused(result, "cites 8.8, which the policy does not hold", "Nothing is opened", "mended by a packet")
        self.assertEqual("", result.out)
        self.assertEqual([], self.r.ledger())

    def test_a_table_with_a_row_that_is_not_a_function_opens_nothing_for_anyone(self):
        self.r.commit({opn.CONTEXT: CONTEXT + "| Clerk | 1.1 | |\n"}, "a row that is not a function")
        for who in ("itg", "ghost"):
            result = self.r.run("--intent", "blocked", who=who)
            self.refused(result, "has a row for 'Clerk', which is not a delivery function")
            self.assertEqual("", result.out)
        self.assertEqual([], self.r.ledger())

    def test_a_file_of_the_law_missing_from_main_opens_nothing(self):
        self.r.commit({opn.CONSTRAINTS: None}, "the constraints are gone")
        self.refused(self.r.run("--intent", "blocked"), f"{opn.CONSTRAINTS} is not on main")

    def test_a_room_without_main_or_without_git_is_refused(self):
        git(self.r.room, "branch", "-m", "main", "trunk")
        self.refused(self.r.run("--intent", "blocked"), "the room has no branch main")
        bare = self.r.base / "plain"
        bare.mkdir()
        with mock.patch.object(self.r, "room", bare):
            self.refused(self.r.run("--intent", "blocked"), "not the root of a Git checkout")

    def test_the_copy_inside_a_linked_worktree_is_refused(self):
        linked = self.r.base / "linked"
        git(self.r.room, "worktree", "add", "-q", str(linked), "-b", "side")
        with mock.patch.object(self.r, "room", linked):
            self.refused(self.r.run("--intent", "blocked"), "linked Git worktree", "run the room's own copy")

    def test_a_time_that_is_not_a_time_is_refused(self):
        self.refused(self.r.run("--check", now="tomorrow"), "--now is not a time")


# --------------------------------------------------------------------------
# The roster, and the two programs an OPEN asks.
# --------------------------------------------------------------------------
class RosterAndSides(Case):
    def test_the_roster_lists_this_rooms_residents_and_what_each_holds(self):
        self.r.open(who="itg", intent="keep the rotations going")
        self.r.open(who="aud", intent="audit", now=self.r.moment(-opn.SHIFT // 60 - 5))
        result = self.r.run("--roster", who=None)
        self.assertEqual(0, result.code, result.text)
        lines = {line.split()[0]: line for line in result.out.splitlines()[1:]}
        self.assertEqual(sorted(KEYS), sorted(lines))
        self.assertIn("OPEN: good until", lines["itg"])
        self.assertIn("intent: keep the rotations going", lines["itg"])
        self.assertIn("no OPEN: its shift ended at", lines["aud"])
        self.assertIn("no OPEN: none is on record", lines["out"])
        self.assertIn("a shift is 12 hours", result.out.splitlines()[0])
        self.assertNotIn("QX", result.out)

    def test_the_real_packet_status_is_asked_and_its_lines_are_shown(self):
        mock.patch.stopall()
        with mock.patch.object(opn, "fullness", return_value="unknown (a stand-in)"):
            text = self.r.open()[0].out
        state = text[text.index("[PRESENT STATE"):]
        self.assertIn("room: main at ", state)
        self.assertIn("you: itg", state)
        self.assertIn("packet: none active", state)

    def test_a_packet_tool_that_does_not_answer_is_said_so(self):
        mock.patch.stopall()
        with mock.patch.object(opn, "side", return_value=(2, ["refused: something is wrong"])):
            self.assertEqual(["packet: unknown (the packet tool did not answer: refused: something is wrong)"],
                             opn.packet_status(self.args()))

    def test_fullness_is_the_gauges_figures_and_never_its_body_or_session(self):
        mock.patch.stopall()
        row = {"key": "itg", "percent": 61.25, "tokens": 122500, "window": 200000, "state": "last observed", "reason": None,
               "age_seconds": 240, "session_id": self.r.sessions["itg"], "body": "/a/private/path.jsonl"}
        with mock.patch.object(opn, "side", return_value=(0, [json.dumps(row)])):
            line = opn.fullness(self.args(), "itg")
        self.assertEqual("61.2 percent of the window (122,500 of 200,000 tokens), read 4 minutes ago, state last observed", line)
        self.assertNotIn("private", line)

    def test_fullness_is_unknown_when_the_gauge_has_no_figure_or_no_answer(self):
        mock.patch.stopall()
        row = {"key": "itg", "percent": None, "tokens": None, "window": None, "state": "unknown", "reason": "body not found"}
        with mock.patch.object(opn, "side", return_value=(0, [json.dumps(row)])):
            self.assertEqual("unknown (body not found)", opn.fullness(self.args(), "itg"))
        with mock.patch.object(opn, "side", return_value=(2, ["gauge: registry unreadable"])):
            self.assertEqual("unknown (the gauge gave no reading)", opn.fullness(self.args(), "itg"))
        with mock.patch.object(opn, "side", return_value=(0, [json.dumps(dict(row, key="another"))])):
            self.assertEqual("unknown (the gauge gave no reading)", opn.fullness(self.args(), "itg"))

    def test_an_age_is_said_in_the_largest_whole_unit(self):
        self.assertEqual("45 seconds ago", opn.age_text(45))
        self.assertEqual("4 minutes ago", opn.age_text(240))
        self.assertEqual("3 hours ago", opn.age_text(3 * 3600 + 5))
        self.assertEqual("at an unknown time", opn.age_text(None))


if __name__ == "__main__":
    unittest.main()
