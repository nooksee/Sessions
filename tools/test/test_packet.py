#!/usr/bin/env python3
"""Tests for ops/lib/scripts/packet.py, in synthetic rooms only. Standard library only.

Every case builds its own room, bare origin and registry in a temporary
directory. GitHub is a small program named gh that the test puts first on
PATH; it keeps its state in a file and merges by rewriting commits in the bare
origin, as a rebase merge does. No real room, registry, remote or account is
read or written. Run:

    python3 -I -B tools/test/test_packet.py
"""
import contextlib
import datetime as dt
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

PACKET = Path(__file__).resolve().parents[2] / "ops" / "lib" / "scripts" / "packet.py"
_spec = importlib.util.spec_from_file_location("packet", PACKET)
packet = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(packet)

KEYS = ("itg", "con", "aud", "orc", "out")          # integrator, contractor, auditor, orchestrator, one more resident
SESSION = "0000f00d-0000-4000-8000-00000000000{}"   # rotate's synthetic convention: the first four are zeros
T0 = dt.datetime(2026, 11, 12, 10, 0, tzinfo=dt.timezone.utc)
IDENTITY = {"GIT_AUTHOR_NAME": "Synthetic Room", "GIT_AUTHOR_EMAIL": "synthetic@example.invalid",
            "GIT_COMMITTER_NAME": "Synthetic Room", "GIT_COMMITTER_EMAIL": "synthetic@example.invalid"}
TEMPLATE = None                                     # built once by setUpModule: origin.git, room, bin/gh

IGNORE = "/var/tmp/*\n!/var/tmp/.gitkeep\n/logs/\n/storage/handoff/*\n!/storage/handoff/.gitkeep\n__pycache__/\n"
SUITE_OK = "print('ok')\n"
SUITE_ENV = ("import os, sys\n"
             "mask = os.umask(0)\n"
             "print('umask=' + oct(mask))\n"
             "sys.exit(1 if 'MIND_TEST_CALLER' in os.environ else 0)\n")
SUITE_FLAG = ("import pathlib, sys\n"
              "if pathlib.Path('var/tmp/stray').exists():\n"
              "    pathlib.Path('stray.txt').write_text('made by a gate')\n"
              "sys.exit(1 if pathlib.Path('var/tmp/fail').exists() else 0)\n")
SELF_TEST = "#!/usr/bin/env bash\n[ \"$1\" = \"--test\" ] && echo ok\n"

FAKE_GH = r'''
import json, os, subprocess, sys, urllib.parse

path = os.environ["FAKE_GH_STATE"]
state = json.load(open(path))
argv = sys.argv[1:]
state["calls"].append(argv)


def finish(code, text, stream):
    json.dump(state, open(path, "w"))
    print(text, file=stream)
    sys.exit(code)


def out(value):
    finish(0, json.dumps(value), sys.stdout)


def fail(message):
    finish(1, message, sys.stderr)


def git(*args, env=None):
    done = subprocess.run(["git", "-C", state["origin"], *args], capture_output=True, text=True, env=env)
    if done.returncode:
        fail("fake gh: git " + args[0] + ": " + done.stderr.strip())
    return done.stdout.strip()


if argv[:2] != ["api", "-X"]:
    fail("fake gh: only `gh api -X METHOD ENDPOINT` is known")
method, endpoint = argv[2], argv[3]
fields = {}
for flag, pair in zip(argv[4::2], argv[5::2]):
    key, _, value = pair.partition("=")
    fields[key] = open(value[1:]).read() if flag == "-F" and value.startswith("@") else value
if method in state["fail"]:
    fail(state["fail"][method])
if state.get("raw"):
    finish(0, state["raw"], sys.stdout)
route, _, query = endpoint.partition("?")
query = dict(urllib.parse.parse_qsl(query))
rest = route.split("/")[3:]
pulls = state["pulls"]


def pull(number):
    return next(p for p in pulls if p["number"] == int(number))


if method == "GET" and rest == ["pulls"]:
    out([p for p in pulls if p["head"]["ref"] == query["head"].split(":", 1)[1]])
if method == "POST" and rest == ["pulls"]:
    made = {"number": state["next"], "state": "open", "merged_at": None, "title": fields["title"], "body": fields["body"],
            "base": {"ref": fields["base"]}, "user": {"login": "room-account"}, "created_at": state.get("opened", "2026-11-12T09:00:00Z"),
            "head": {"ref": fields["head"], "sha": git("rev-parse", "refs/heads/" + fields["head"])}}
    state["next"] += 1
    pulls.append(made)
    out(made)
if method == "GET" and rest[0] == "commits" and rest[2:] == ["check-runs"]:
    out({"check_runs": state["checks"]})
if method == "GET" and rest[0] == "pulls" and len(rest) == 2:
    if state.get("pull_answer"):
        out(state["pull_answer"]["is"])
    out(dict(pull(rest[1]), requested_reviewers=state.get("asked", []), requested_teams=state.get("teams", [])))
if method == "GET" and rest[0] == "pulls" and rest[2:] == ["reviews"]:
    reviews = state.get("reviews", [])
    if not isinstance(reviews, list):
        out(reviews)
    page, per = int(query.get("page", 1)), int(query.get("per_page", 30))
    out(reviews[(page - 1) * per:page * per])
if method == "GET" and rest[0] == "pulls" and rest[2:] == ["comments"]:
    if not isinstance(state["comments"], list):
        out(state["comments"])
    page, per = int(query.get("page", 1)), int(query.get("per_page", 30))
    out(state["comments"][(page - 1) * per:page * per])
if method == "PUT" and rest[0] == "pulls" and rest[2:] == ["merge"]:
    found = pull(rest[1])
    head, base = git("rev-parse", "refs/heads/" + found["head"]["ref"]), git("rev-parse", "refs/heads/main")
    if fields.get("sha") != head or fields.get("merge_method") != "rebase":
        fail("Head branch was modified. Review and try the merge again.")
    env = dict(os.environ, GIT_AUTHOR_NAME="Synthetic Room", GIT_AUTHOR_EMAIL="synthetic@example.invalid",
               GIT_COMMITTER_NAME="Fake Host", GIT_COMMITTER_EMAIL="host@example.invalid")
    parent = base
    for commit in git("rev-list", "--reverse", base + ".." + head).split():
        parent = git("commit-tree", git("rev-parse", commit + "^{tree}"), "-p", parent,
                     "-m", git("log", "-1", "--format=%B", commit), env=env)
    git("update-ref", "refs/heads/main", parent)
    found.update(state="closed", merged_at="2026-11-12T12:00:00Z")
    out({"merged": True, "sha": parent})
if method == "PATCH" and rest[0] == "pulls":
    pull(rest[1])["state"] = fields["state"]
    out(pull(rest[1]))
if method == "GET" and rest[0] == "issues" and rest[2:] == ["comments"]:
    if not isinstance(state["talk"], list):
        out(state["talk"])
    page, per = int(query.get("page", 1)), int(query.get("per_page", 30))
    out(state["talk"][(page - 1) * per:page * per])
if method == "GET" and rest[0] == "issues" and rest[2:] == ["timeline"]:
    if state.get("no_events"):
        fail(state["no_events"])
    events = state.get("events", [])
    if not isinstance(events, list):
        out(events)
    page, per = int(query.get("page", 1)), int(query.get("per_page", 30))
    out(events[(page - 1) * per:page * per])
if method == "POST" and rest[0] == "issues" and rest[2:] == ["comments"]:
    state["notes"].append({"number": int(rest[1]), "body": fields["body"]})
    out({"id": len(state["notes"])})
fail("fake gh: unexpected call " + method + " " + route)
'''


def git(cwd, *args, env=None, check=True) -> str:
    done = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True,
                          env=dict(os.environ, **IDENTITY, **(env or {})))
    if check and done.returncode:
        raise AssertionError(f"git {' '.join(args)} failed: {done.stderr}")
    return done.stdout.strip()


def derive(repo, parent: str, changes: dict, message: str = "derived") -> str:
    """A new commit on parent with files written (text) or removed (None), by plumbing; no ref or checkout moves."""
    with tempfile.TemporaryDirectory() as tmp:
        env = {"GIT_INDEX_FILE": str(Path(tmp) / "index")}
        git(repo, "read-tree", parent, env=env)
        for path, content in changes.items():
            if content is None:
                git(repo, "update-index", "--force-remove", "--", path, env=env)
            else:
                blob = subprocess.run(["git", "-C", str(repo), "hash-object", "-w", "--stdin"], input=content,
                                      capture_output=True, text=True, check=True).stdout.strip()
                git(repo, "update-index", "--add", "--cacheinfo", f"100644,{blob},{path}", env=env)
        return git(repo, "commit-tree", git(repo, "write-tree", env=env), "-p", parent, "-m", message)


def build_template(root: Path) -> None:
    origin, room = root / "origin.git", root / "room"
    git(root, "-c", "init.templateDir=", "init", "-q", "--bare", "-b", "main", str(origin))
    git(root, "-c", "init.templateDir=", "init", "-q", "-b", "main", str(room))
    for key, value in (("user.name", "Synthetic Room"), ("user.email", "synthetic@example.invalid"),
                       ("commit.gpgsign", "false"), ("push.negotiate", "false")):
        git(room, "config", key, value)
    files = {".gitignore": IGNORE, "PoT.md": "The law of a synthetic room.\n", "docs/a.md": "alpha\n", "docs/b.md": "beta\n",
             "tools/test/test_ok.py": SUITE_OK, "tools/test/test_env.py": SUITE_ENV, "tools/test/test_flag.py": SUITE_FLAG,
             "ops/bin/help": SELF_TEST, "ops/bin/template": SELF_TEST, "storage/handoff/.gitkeep": "", "var/tmp/.gitkeep": "",
             packet.TOOL: "# a stand-in, so the gate's bootstrap rule sees a base that holds the packet tool\n"}
    for rel, text in files.items():
        (room / rel).parent.mkdir(parents=True, exist_ok=True)
        (room / rel).write_text(text)
    for word in ("help", "template"):
        (room / "ops" / "bin" / word).chmod(0o755)
    git(room, "add", "-A")
    git(room, "commit", "-q", "-m", "synthetic main")
    git(room, "remote", "add", "origin", str(origin))
    git(room, "push", "-q", "-u", "origin", "main")
    (root / "bin").mkdir()
    (root / "bin" / "gh").write_text(f"#!{sys.executable}\n{FAKE_GH}")
    (root / "bin" / "gh").chmod(0o755)


def setUpModule():
    global TEMPLATE
    TEMPLATE = Path(tempfile.mkdtemp(prefix="packet-template-")).resolve()
    build_template(TEMPLATE)


def tearDownModule():
    shutil.rmtree(TEMPLATE, ignore_errors=True)


class Result:
    def __init__(self, code, out, err):
        self.code, self.out, self.err, self.text = code, out, err, out + err


class Room:
    """One synthetic room: a clone on main, its bare origin, a registry of invented residents, and a fake gh."""

    def __init__(self, base: Path):
        self.base = base.resolve()
        shutil.copytree(TEMPLATE, self.base, dirs_exist_ok=True)
        self.room, self.origin, self.wt = self.base / "room", self.base / "origin.git", self.base / "room" / packet.WORKTREE
        git(self.room, "remote", "set-url", "origin", str(self.origin))
        rows = [{"key": key, "person": f"Person {key}", "role": "Role", "provider": "claude", "room": str(self.room),
                 "session_id": SESSION.format(n)} for n, key in enumerate(KEYS)]
        rows.append(dict(rows[0], key="far", room=str(self.base / "elsewhere"), session_id=SESSION.format(9)))
        self.registry = self.base / "registry.json"
        self.registry.write_text(json.dumps({"identities": rows}))
        self.state = self.base / "gh.json"
        self.gh(origin=str(self.origin), pulls=[], next=7, comments=[], notes=[], talk=[], calls=[], fail={}, raw="",
                checks=[{"name": packet.REQUIRED_CHECK, "status": "completed", "conclusion": "success",
                         "started_at": "2026-11-12T09:00:00Z"}])
        self.tick, self.said = 0, []

    def gh(self, **change) -> dict:
        state = json.loads(self.state.read_text()) if self.state.exists() else {}
        if change:
            state.update(change)
            self.state.write_text(json.dumps(state))
        return state

    def run(self, *argv, who=None, stdin="", env=None, now=None) -> Result:
        self.tick += 1
        when = now or packet.iso(T0 + dt.timedelta(minutes=self.tick))
        full = ["--room", str(self.room), "--registry", str(self.registry), "--now", when, *argv]
        environ = {k: v for k, v in os.environ.items() if k != packet.SEAM}
        environ.update(PATH=f"{self.base / 'bin'}{os.pathsep}{os.environ['PATH']}", FAKE_GH_STATE=str(self.state))
        if who:
            environ[packet.SEAM] = who
        environ.update(env or {})
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.dict(os.environ, environ, clear=True), mock.patch.object(sys, "stdin", io.StringIO(stdin)), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = packet.main(full)
        result = Result(code, out.getvalue(), err.getvalue())
        self.said.append(result.text)
        return result

    def note(self, text: str) -> str:
        self.tick += 1
        path = self.base / f"text-{self.tick}.md"
        path.write_text(text)
        return str(path)

    def draft(self, title="Say more in the docs", contractor="con", auditor="aud", orchestrator="orc", authority="RoR-25",
              scope=("docs/",), gates=("ok",), objective="Make the first page say more than one word.") -> Result:
        argv = ["draft", "--title", title, "--contractor", contractor, "--auditor", auditor, "--orchestrator", orchestrator,
                "--authority", authority, "--objective", "-"]
        for entry in scope:
            argv += ["--scope", entry]
        for gate in gates:
            argv += ["--gate", gate]
        return self.run(*argv, stdin=objective)

    def open(self, who="itg", **draft) -> Result:
        self.draft(**draft)
        return self.run("open", who=who)

    def edit(self, rel="docs/a.md", text="alpha, and more\n") -> None:
        (self.wt / rel).parent.mkdir(parents=True, exist_ok=True)
        (self.wt / rel).write_text(text)

    def close(self, who="con", deviations="0", narrative="One page changed. Nothing else was touched.") -> Result:
        return self.run("close", "--deviations", deviations, "--narrative", self.note(narrative), who=who)

    def audit(self, verdict="pass", who="aud", note="Read the change against the objective. It does what it says.") -> Result:
        return self.run("audit", "--verdict", verdict, "--note", self.note(note), who=who)

    def ship(self, *flags, who="orc", **more) -> Result:
        return self.run("ship", *flags, who=who, **more)

    def through(self, station: str, text="alpha, and more\n", **draft) -> "Room":
        """Run the stations up to and including the one named; each must succeed."""
        steps = [("open", lambda: self.open(**draft)), ("edit", lambda: self.edit(text=text)), ("close", self.close),
                 ("audit", self.audit), ("hold", lambda: self.ship("--hold")), ("ship", self.ship)]
        for name, step in steps:
            result = step()
            want = 3 if name == "hold" else 0
            if result is not None and result.code != want:
                raise AssertionError(f"{name} ended {result.code}: {result.text}")
            if name == station:
                return self
        raise AssertionError(f"no station named {station}")

    def leaf_path(self, number=1) -> Path:
        return self.wt / packet.LEAVES / f"DP-SES-{number:04d}.md"

    def leaf(self, number=1) -> dict:
        return packet.parse_leaf(self.leaf_path(number).read_text())

    def ledger(self) -> list[dict]:
        path = self.room / packet.LEDGER
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    def head(self, ref="main", where=None) -> str:
        return git(where or self.room, "rev-parse", ref)

    def advance_origin(self, text="moved\n") -> str:
        """Another landing on origin's main, made behind the room's back."""
        commit = derive(self.origin, self.head("refs/heads/main", self.origin), {"docs/b.md": text}, "another landing")
        git(self.origin, "update-ref", "refs/heads/main", commit)
        return commit

    def merge_outside(self) -> None:
        """The pull request is merged on the host's own page, not by the tool."""
        number = self.gh()["pulls"][-1]["number"]
        env = dict(os.environ, PATH=f"{self.base / 'bin'}{os.pathsep}{os.environ['PATH']}", FAKE_GH_STATE=str(self.state))
        branch = git(self.wt, "rev-parse", "--abbrev-ref", "HEAD")
        subprocess.run(["gh", "api", "-X", "PUT", f"repos/o/r/pulls/{number}/merge", "-f", "merge_method=rebase",
                        "-f", f"sha={self.head(branch, self.origin)}"], env=env, check=True, capture_output=True)


class Case(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="packet-test-")
        self.addCleanup(self._tmp.cleanup)
        self.r = Room(Path(self._tmp.name))

    def refused(self, result: Result, *words: str, code: int = 2) -> None:
        self.assertEqual(code, result.code, result.text)
        for word in words:
            self.assertIn(word, result.text)


def sample_leaf(**head) -> dict:
    base = {"Packet": "DP-SES-0001", "Branch": "agent/dp-ses-0001-2026-11-12", "Base": "commit " + "a" * 40,
            "Opened": "2026-11-12T10:01:00Z", "Integrator": "itg", "Contractor": "con", "Auditor": "aud", "Orchestrator": "orc",
            "Authority": "RoR-25"}
    return {"title": "Say more in the docs", "head": dict(base, **head), "objective": "Make the first page say more.",
            "scope": ["docs/"], "gates": ["ok"], "amendments": [], "results": None, "audit": None}


def closed(leaf: dict, **results) -> dict:
    head = {"Closed": "2026-11-12T10:05:00Z", "Contractor": leaf["head"]["Contractor"], "Paths changed": "1", "Deviations": "0",
            "Tree": "tree " + "b" * 40}
    return dict(leaf, results={"head": dict(head, **results), "gates": [(0, 1, "tools/test/test_ok.py")],
                               "narrative": "One page changed."})


def audited(leaf: dict, **audit) -> dict:
    head = {"Verdict": "PASS", "Auditor": leaf["head"]["Auditor"], "Audited": "2026-11-12T10:06:00Z",
            "Tree": leaf["results"]["head"]["Tree"]}
    return dict(leaf, audit={"head": dict(head, **audit), "note": "Read against the objective."})


# --------------------------------------------------------------------------
class LeafFormat(unittest.TestCase):
    def test_a_leaf_round_trips_at_every_station(self):
        contract = sample_leaf()
        full = audited(closed(dict(contract, amendments=["2026-11-12T10:03:00Z itg added docs/: wider than first drawn"])))
        for leaf in (contract, closed(contract), full):
            text = packet.render_leaf(leaf)
            self.assertEqual(leaf, packet.parse_leaf(text))
            self.assertEqual([], packet.leaf_problems(leaf))
            self.assertTrue(text.endswith("\n") and not text.endswith("\n\n"))

    def test_an_objective_of_several_paragraphs_round_trips(self):
        leaf = dict(sample_leaf(), objective="First paragraph.\n\nSecond paragraph.\n- a list line")
        self.assertEqual(leaf, packet.parse_leaf(packet.render_leaf(leaf)))

    def test_anything_but_canonical_form_is_refused(self):
        text = packet.render_leaf(audited(closed(sample_leaf())))
        broken = {"a trailing space": text.replace("- Contractor: con\n", "- Contractor: con \n", 1),
                  "header out of order": text.replace("- Integrator: itg\n- Contractor: con\n", "- Contractor: con\n- Integrator: itg\n"),
                  "an unknown section": text + "## Extra\n\nwords\n",
                  "text before the first section": text.replace("## Objective", "stray\n\n## Objective"),
                  "sections out of order": text.replace("## Scope\n\n- docs/\n\n## Gates\n\n- ok\n", "## Gates\n\n- ok\n\n## Scope\n\n- docs/\n"),
                  "no blank line after a heading": text.replace("## Scope\n\n", "## Scope\n"),
                  "a results line that is no gate": text.replace("- Gate: exit 0", "- Note: exit 0"),
                  "an audit of five lines": text.replace("- Verdict: PASS\n", "- Verdict: PASS\n- Verdict: PASS\n"),
                  "an audit without results": packet.render_leaf(dict(audited(closed(sample_leaf())), results=None)),
                  "another id in the title": text.replace("# DP-SES-0001:", "# DP-SES-0002:"),
                  "no final newline": text.rstrip("\n"), "empty": ""}
        for name, value in broken.items():
            with self.subTest(name), self.assertRaises(packet.Refused):
                packet.parse_leaf(value)

    def test_every_rule_of_a_valid_leaf(self):
        cases = [(sample_leaf(Auditor="con"), "no one audits their own work"),
                 (sample_leaf(Packet="DP-SES-1"), "not DP-SES-NNNN"),
                 (sample_leaf(Branch="agent/dp-ses-0002-2026-11-12"), "Branch:"),
                 (sample_leaf(Branch="feature/x"), "Branch:"),
                 (sample_leaf(Base="commit abc"), "Base:"),
                 (sample_leaf(Opened="yesterday"), "Opened:"),
                 (sample_leaf(Contractor="Con Tractor"), "Contractor: not a registry key"),
                 (sample_leaf(Authority=""), "Authority: empty"),
                 (dict(sample_leaf(), title="t" * 59), "Title: 59 characters"),
                 (dict(sample_leaf(), objective="x" * 801), "Objective: 801 characters"),
                 (dict(sample_leaf(), objective="fine\n# a heading"), "would read as a heading"),
                 (dict(sample_leaf(), objective="an em dash \u2014 here"), "EM DASH"),
                 (dict(sample_leaf(), scope=["docs/", "docs/"]), "each once"),
                 (dict(sample_leaf(), scope=[f"p{n}" for n in range(61)]), "at most 60"),
                 (dict(sample_leaf(), gates=["full", "ok"]), "Gates:"),
                 (dict(sample_leaf(), gates=["Ok"]), "Gates:"),
                 (dict(sample_leaf(), gates=["ok", "ok"]), "Gates:"),
                 (dict(sample_leaf(), amendments=["sometime itg added docs/: why"]), "Amendments:"),
                 (dict(sample_leaf(), amendments=["2026-11-12T10:03:00Z itg added tools/: why"]), "Amendments:"),
                 (closed(sample_leaf(), Contractor="out"), "Results: Closed"),
                 (closed(sample_leaf(), **{"Paths changed": "0"}), "count of at least 1"),
                 (closed(sample_leaf(), Deviations="none"), "Deviations is a count"),
                 (closed(sample_leaf(), Tree="tree short"), "Results: Tree"),
                 (audited(closed(sample_leaf()), Verdict="MAYBE"), "PASS or FAIL"),
                 (audited(closed(sample_leaf()), Auditor="out"), "by the packet's Auditor"),
                 (audited(closed(sample_leaf()), Tree="b" * 40), "Audit: Tree")]
        for leaf, expected in cases:
            with self.subTest(expected):
                self.assertIn(expected, "; ".join(packet.leaf_problems(leaf)))

    def test_results_must_hold_passing_gates_that_the_contract_names(self):
        leaf = closed(sample_leaf())
        failing = dict(leaf, results=dict(leaf["results"], gates=[(1, 2, "tools/test/test_ok.py")]))
        self.assertIn("1 gate(s) did not exit 0", "; ".join(packet.leaf_problems(failing)))
        none = dict(leaf, results=dict(leaf["results"], gates=[]))
        self.assertIn("no gate was run", "; ".join(packet.leaf_problems(none)))
        other = dict(leaf, results=dict(leaf["results"], gates=[(0, 1, "tools/test/test_env.py")]))
        self.assertIn("not the gates the contract names", "; ".join(packet.leaf_problems(other)))
        full = dict(leaf, gates=["full"], results=dict(leaf["results"], gates=[(0, 1, "tools/test/test_env.py")]))
        self.assertEqual([], packet.leaf_problems(full))
        self.assertEqual(["tools/test/test_ok.py", "ops/bin/help --test"], packet.gate_names(["ok", "help"]))

    def test_scope_entries_are_plain_paths_and_never_a_leaf(self):
        good = ["docs/", "docs/a.md", ".github/workflows/sessions-gates.yml", "archives/packets/README.md", "RoR.md"]
        bad = ["", "/", "/etc/passwd", "~/x", "../x", "..", ".", "./docs", "docs//a.md", "docs/../x", ".git/config", "a b",
               "docs/*.md", "docs/[a].md", "-rf", "a\"b", "caf\u00e9/", "archives/", "archives/packets/",
               "archives/packets/DP-SES-0001.md", "archives/packets/DP-SES-9999.md"]
        for entry in good:
            self.assertIsNone(packet.scope_problem(entry), entry)
        for entry in bad:
            self.assertIsNotNone(packet.scope_problem(entry), entry)

    def test_scope_matches_an_exact_path_or_a_folder_prefix_only(self):
        scope = ["docs/", "README.md"]
        self.assertTrue(packet.in_scope("docs/a.md", scope) and packet.in_scope("README.md", scope))
        for path in ("docs", "docsx/a.md", "README.md.bak", "x/README.md", "tools/docs/a.md"):
            self.assertFalse(packet.in_scope(path, scope), path)

    def test_a_leaf_holds_nothing_a_public_record_may_not(self):
        clean = packet.render_leaf(audited(closed(sample_leaf())))
        self.assertEqual([], packet.public_problems(clean))
        held = {"a quotation": 'He said "do it now" and so it was done.',
                "a host path": "The file is at /home/someone/Sessions/RoR.md today.",
                "a session identifier": "The session 0b9e4d1c-52aa-4c1f-9d2e-3f6a7b8c9d0e was rotated.",
                "a bare short hash": "It was fixed in 5468ce4b42 last week."}
        for name, sentence in held.items():
            with self.subTest(name):
                self.assertTrue(packet.public_problems(clean.replace("One page changed.", sentence)))
        self.assertEqual([], packet.public_problems(clean.replace("One page changed.", "It is commit 5468ce4b42 on main.")))
        for path in ("archives/PoT-0a1b2c3d.md", "archives/PoT-authority-0a1b2c3d.md"):      # the policy's own snapshots
            self.assertEqual([], packet.public_problems(clean.replace("One page changed.", f"The snapshot is {path} now.")), path)
        for near in ("archives/PoT-0a1b2c3d.txt", "archives/PoT-0a1b2c3d4.md", "storage/archives/PoT-0a1b2c3d.md", "PoT-0a1b2c3d.md"):
            self.assertTrue(packet.public_problems(clean.replace("One page changed.", f"The file is {near} now.")), near)

    def test_text_rules(self):
        self.assertEqual([], packet.text_problems("A plain line.", "x", 50, one_line=True))
        self.assertTrue(packet.text_problems(" padded", "x", 50, one_line=True))
        self.assertTrue(packet.text_problems("two\nlines", "x", 50, one_line=True))
        self.assertTrue(packet.text_problems("a tab\there", "x", 50))
        self.assertTrue(packet.text_problems("trailing \nspace", "x", 50))
        self.assertEqual(["x: empty"], packet.text_problems("  \n", "x", 50))
        self.assertEqual("a\n\nb", packet.clean_text("\r\n a\r\n\r\nb  \n\n".replace(" a", "a")))

    def test_a_draft_round_trips_and_an_unfilled_one_names_what_is_missing(self):
        fields = {"Title": "T", "Contractor": "con", "Auditor": "aud", "Orchestrator": "orc", "Authority": "RoR-25"}
        text = packet.render_draft(fields, "Do the thing.\n\nThen stop.", ["docs/", "README.md"], ["full"])
        self.assertEqual({"fields": fields, "objective": "Do the thing.\n\nThen stop.", "scope": ["docs/", "README.md"],
                          "gates": ["full"]}, packet.parse_draft(text))
        with self.assertRaises(packet.Refused) as caught:
            packet.parse_draft(packet.render_draft({"Title": "T"}, "", [], ["full"]))
        for missing in ("Contractor", "Auditor", "Orchestrator", "Authority", "## Objective", "## Scope"):
            self.assertIn(missing, str(caught.exception))
        with self.assertRaises(packet.Refused):
            packet.parse_draft(text.replace("- docs/", "docs/"))

    def test_small_helpers(self):
        self.assertEqual(packet.SEAM, packet.sibling("mind").SEAM)
        told = packet.telling_line("To https://someone:secret-token@host.example/o/r\n ! [rejected]\nerror: failed to push\n")
        self.assertEqual("error: failed to push", told)
        self.assertNotIn("secret-token", packet.telling_line("fatal: unable to access 'https://someone:secret-token@host.example/o/r'"))
        self.assertEqual("no message", packet.telling_line("\n"))


# --------------------------------------------------------------------------
class DraftAndOpen(Case):
    def test_draft_writes_a_private_form_and_keeps_the_one_it_replaces(self):
        first = self.r.run("draft", "--title", "First")
        self.assertEqual(0, first.code, first.text)
        form = self.r.room / packet.DRAFT
        self.assertEqual(0o600, stat.S_IMODE(form.stat().st_mode))
        self.assertIn("Title: First", form.read_text())
        self.assertIn("- full", form.read_text())
        self.r.run("draft", "--title", "Second")
        self.assertIn("Title: Second", form.read_text())
        self.assertIn("Title: First", (self.r.room / packet.DRAFT_PREVIOUS).read_text())
        self.assertEqual("", git(self.r.room, "status", "--porcelain"))
        self.refused(self.r.run("open", who="itg"), "the draft is not filled", "Contractor")

    def test_open_makes_the_one_packet_from_clean_main(self):
        base = self.r.head()
        result = self.r.open()
        self.assertEqual(0, result.code, result.text)
        self.assertIn("DP-SES-0001 is open on agent/dp-ses-0001-2026-11-12", result.out)
        leaf = self.r.leaf()
        self.assertEqual({"Packet": "DP-SES-0001", "Branch": "agent/dp-ses-0001-2026-11-12", "Base": f"commit {base}",
                          "Integrator": "itg", "Contractor": "con", "Auditor": "aud", "Orchestrator": "orc", "Authority": "RoR-25"},
                         {k: v for k, v in leaf["head"].items() if k != "Opened"})
        self.assertEqual((["docs/"], ["ok"], None, None), (leaf["scope"], leaf["gates"], leaf["results"], leaf["audit"]))
        self.assertEqual("agent/dp-ses-0001-2026-11-12", git(self.r.wt, "rev-parse", "--abbrev-ref", "HEAD"))
        self.assertEqual(("main", ""), (git(self.r.room, "rev-parse", "--abbrev-ref", "HEAD"), git(self.r.room, "status", "--porcelain")))
        self.assertFalse((self.r.room / packet.DRAFT).exists())
        line = self.r.ledger()[-1]
        self.assertEqual(("open", "itg", "DP-SES-0001", base), (line["action"], line["actor"], line["packet"], line["base"]))
        self.assertEqual(packet.contract_digest(leaf), line["contract"])
        self.assertEqual({"Integrator": "itg", "Contractor": "con", "Auditor": "aud", "Orchestrator": "orc"}, line["functions"])
        ledger = self.r.room / packet.LEDGER
        self.assertEqual((0o600, 0o700), (stat.S_IMODE(ledger.stat().st_mode), stat.S_IMODE(ledger.parent.stat().st_mode)))
        self.assertEqual("", git(self.r.origin, "for-each-ref", "refs/heads/agent"))

    def test_only_one_packet_is_active_at_a_time(self):
        self.r.through("open")
        self.refused(self.r.open(), "already active", "one packet at a time")

    def test_open_refuses_a_room_that_is_not_clean_main_level_with_origin(self):
        git(self.r.room, "checkout", "-q", "-b", "side")
        self.refused(self.r.open(), "the room is on side, not main")
        git(self.r.room, "checkout", "-q", "main")
        (self.r.room / "docs" / "a.md").write_text("edited in the room\n")
        self.refused(self.r.open(), "1 uncommitted path(s)", "docs/a.md")
        git(self.r.room, "checkout", "-q", "--", "docs/a.md")
        self.r.advance_origin()
        self.refused(self.r.open(), "behind origin/main", "packet.py sync")
        self.assertFalse(self.r.wt.exists())

    def test_open_refuses_a_main_that_holds_commits_origin_does_not(self):
        (self.r.room / "docs" / "a.md").write_text("committed in the room\n")
        git(self.r.room, "commit", "-q", "-am", "a commit made on main by hand")
        self.refused(self.r.open(), "holds commits origin/main does not", "never force")
        self.refused(self.r.run("sync", who="out"), "holds commits origin/main does not", "never force")

    def test_open_accepts_the_paths_of_a_policy_snapshot_in_scope(self):
        scope = ("PoT.md", "archives/PoT-0a1b2c3d.md", "archives/PoT-authority-0a1b2c3d.md")
        self.assertEqual(0, self.r.open(scope=scope).code, self.r.said[-1])
        self.assertEqual(list(scope), self.r.leaf()["scope"])

    def test_open_refuses_bad_function_keys(self):
        self.refused(self.r.open(auditor="con"), "no one audits their own work")
        self.refused(self.r.open(contractor="ghost"), "Contractor:", "'ghost' is registered 0 times")
        self.refused(self.r.open(orchestrator="far"), "Orchestrator:", "registered to another room")
        self.refused(self.r.open(who="ghost"), "Integrator:", "registered 0 times")
        self.assertFalse(self.r.wt.exists())
        self.assertTrue((self.r.room / packet.DRAFT).exists())

    def test_open_refuses_a_malformed_or_unpublishable_contract(self):
        self.refused(self.r.open(scope=("/etc/",)), "not a plain path relative to the room")
        self.refused(self.r.open(scope=("archives/packets/",)), "packet leaves are never in scope")
        self.refused(self.r.open(gates=("full", "ok")), "Gates:")
        self.refused(self.r.open(objective='Do what he said: "ship it".'), "holds what a public record may not", "quotations")
        self.refused(self.r.open(authority="The note at /home/someone/notes.md"), "host paths")
        self.assertEqual([], self.r.ledger())

    def test_open_needs_a_verified_caller_and_a_draft(self):
        self.r.draft()
        self.refused(self.r.run("open"), "canonical registry")
        (self.r.room / packet.DRAFT).unlink()
        self.refused(self.r.run("open", who="itg"), "no readable draft")
        self.r.draft()
        git(self.r.room, "remote", "set-url", "origin", str(self.r.base / "no-such-origin.git"))
        self.refused(self.r.run("open", who="itg"), "git fetch --quiet failed")
        self.assertFalse(self.r.wt.exists())
        shutil.rmtree(self.r.room / "storage" / "handoff")
        self.refused(self.r.run("draft"), "storage/handoff/ does not exist")

    def test_open_refuses_a_number_whose_branch_already_exists(self):
        git(self.r.origin, "update-ref", "refs/heads/agent/dp-ses-0001-2026-11-01", self.r.head())
        self.refused(self.r.open(), "a branch for DP-SES-0001 already exists: agent/dp-ses-0001-2026-11-01 on origin",
                     "git push origin --delete NAME")
        git(self.r.origin, "update-ref", "-d", "refs/heads/agent/dp-ses-0001-2026-11-01")
        git(self.r.room, "branch", "agent/dp-ses-0001-2026-10-01", "main")
        self.refused(self.r.run("open", who="itg"), "a branch for DP-SES-0001 already exists: agent/dp-ses-0001-2026-10-01 here")
        git(self.r.room, "branch", "-D", "agent/dp-ses-0001-2026-10-01")
        self.assertEqual(0, self.r.run("open", who="itg").code, self.r.said[-1])

    def test_a_failed_open_leaves_no_worktree_and_no_branch(self):
        self.r.draft()
        with mock.patch.object(packet, "record", side_effect=OSError(28, "No space left on device")):
            self.refused(self.r.run("open", who="itg"), "No space left")
        self.assertFalse(self.r.wt.exists())
        self.assertEqual("", git(self.r.room, "for-each-ref", "refs/heads/agent"))
        self.assertEqual(0, self.r.run("open", who="itg").code)

    def test_the_tool_refuses_a_linked_worktree_as_its_room(self):
        other = self.r.base / "other"
        git(self.r.room, "worktree", "add", "-q", "-b", "other", str(other), "main")
        result = self.r.run("status")
        self.assertEqual(0, result.code)
        with mock.patch.object(self.r, "room", other):
            self.refused(self.r.run("status"), "linked Git worktree")
        with mock.patch.object(self.r, "room", self.r.base):
            self.refused(self.r.run("status"), "not the root of a Git checkout")


# --------------------------------------------------------------------------
class Work(Case):
    def test_status_names_each_station_and_whose_turn_it_is(self):
        first = self.r.run("status", who="itg")
        self.assertIn("room: main at", first.out)
        self.assertIn("clean, level with origin/main", first.out)
        self.assertIn("you: itg", first.out)
        self.assertIn("packet: none active; the next is DP-SES-0001", first.out)
        self.assertIn("station: draft:", first.out)
        self.assertIn("you: unverified", self.r.run("status").out)
        self.r.draft()
        self.assertIn("station: open: a draft waits", self.r.run("status").out)
        self.r.run("open", who="itg")
        refs = git(self.r.room, "for-each-ref")
        at_work = self.r.run("status", who="con")
        self.assertIn("packet: DP-SES-0001: Say more in the docs", at_work.out)
        self.assertIn("functions: Integrator itg, Contractor con, Auditor aud, Orchestrator orc", at_work.out)
        self.assertIn("work: 0 path(s) changed, 0 outside scope", at_work.out)
        self.assertIn("station: work:", at_work.out)
        self.assertIn("(con, which is you)", at_work.out)
        self.r.edit()
        self.r.edit("tools/extra.py", "x = 1\n")
        outside = self.r.run("status", who="itg")
        self.assertIn("work: 2 path(s) changed, 1 outside scope", outside.out)
        self.assertIn("work: outside scope: tools/extra.py", outside.out)
        self.assertIn("(con)", outside.out)
        (self.r.wt / "tools" / "extra.py").unlink()
        self.r.close()
        self.assertIn("station: audit:", self.r.run("status", who="aud").out)
        self.r.edit(text="alpha, changed after close\n")
        self.assertIn("changed after close", self.r.run("status").out)
        self.r.close()
        self.r.audit("fail")
        self.assertIn("station: rework:", self.r.run("status").out)
        self.r.audit("pass")
        self.assertIn("station: ship:", self.r.run("status", who="orc").out)
        self.assertEqual(refs, git(self.r.room, "for-each-ref"))
        self.assertEqual("", git(self.r.wt, "diff", "--cached", "--name-only"))

    def test_diff_shows_the_exact_change_the_audit_binds(self):
        self.refused(self.r.run("diff"), "no packet is active")
        self.r.through("edit")
        self.r.edit("docs/new page.md", "a page Git does not track yet\n")
        (self.r.wt / "docs" / "b.md").unlink()
        self.r.close()
        tree = self.r.leaf()["results"]["head"]["Tree"]
        whole = self.r.run("diff")
        self.assertEqual(0, whole.code, whole.text)
        self.assertIn(f"# DP-SES-0001: the change since base {self.r.head()[:12]}, without the leaf; {tree}", whole.out)
        for line in ("+alpha, and more", "+a page Git does not track yet", "-beta", "+++ b/docs/new page.md", "deleted file mode"):
            self.assertIn(line, whole.out)
        self.assertNotIn("archives/packets", whole.out)
        self.assertEqual(["M\tdocs/a.md", "D\tdocs/b.md", "A\tdocs/new page.md"], self.r.run("diff", "names").out.splitlines()[1:])
        self.assertIn("3 files changed", self.r.run("diff", "stat").out)
        self.assertEqual("", git(self.r.wt, "diff", "--cached", "--name-only"))

    def test_status_says_stop_when_the_room_is_not_clean_main(self):
        (self.r.room / "loose.txt").write_text("x")
        self.assertIn("room: STOP", self.r.run("status").out)

    def test_close_measures_the_work_and_writes_the_results(self):
        self.r.through("edit")
        result = self.r.close(deviations="2")
        self.assertEqual(0, result.code, result.text)
        self.assertIn("gate: exit 0 in", result.out)
        self.assertIn("1 path(s), 1 of 1 gates passed, deviations 2", result.out)
        leaf = self.r.leaf()
        results = leaf["results"]
        self.assertEqual(("con", "1", "2"), (results["head"]["Contractor"], results["head"]["Paths changed"], results["head"]["Deviations"]))
        self.assertEqual([(0, "tools/test/test_ok.py")], [(code, name) for code, _, name in results["gates"]])
        self.assertEqual("One page changed. Nothing else was touched.", results["narrative"])
        independent = derive(self.r.room, self.r.head(), {"docs/a.md": "alpha, and more\n"})
        self.assertEqual("tree " + git(self.r.room, "rev-parse", independent + "^{tree}"), results["head"]["Tree"])
        log = self.r.room / packet.RESULTS
        self.assertEqual(0o600, stat.S_IMODE(log.stat().st_mode))
        self.assertIn("## exit 0", log.read_text())
        line = self.r.ledger()[-1]
        self.assertEqual(("close", "con", 1, 1, 2), (line["action"], line["actor"], line["gates"], line["paths"], line["deviations"]))
        self.assertEqual("", git(self.r.room, "status", "--porcelain"))

    def test_close_is_only_the_contractors(self):
        self.r.through("edit")
        for who in ("itg", "aud", "orc", "out"):
            self.refused(self.r.close(who=who), "only the packet's Contractor (con)")
        self.refused(self.r.run("close", "--deviations", "0", "--narrative", self.r.note("x")), "canonical registry")
        self.assertIsNone(self.r.leaf()["results"])

    def test_close_refuses_a_path_outside_scope_and_names_it(self):
        self.r.through("edit")
        self.r.edit("tools/test/test_ok.py", "print('changed')\n")
        self.r.edit("odd name \u00e9.txt", "new\n")
        self.r.edit("docs/also odd \u00e9.md", "in scope, whatever its name\n")
        result = self.r.close()
        self.refused(result, "2 changed path(s) are outside the packet's scope before the gates", "odd name \u00e9.txt", "tools/test/test_ok.py")
        self.assertNotIn("also odd", result.text)
        self.assertNotIn("gate:", result.out)
        self.assertIsNone(self.r.leaf()["results"])

    def test_close_refuses_when_nothing_in_scope_changed(self):
        self.r.through("open")
        self.refused(self.r.close(), "nothing in scope has changed")

    def test_a_failing_gate_fails_the_close_and_keeps_the_log(self):
        self.r.through("edit", gates=("ok", "flag"))
        (self.r.wt / "var" / "tmp" / "fail").write_text("")
        result = self.r.close()
        self.refused(result, "FAILED", "1 of 2 gate(s) did not exit 0", "tools/test/test_flag.py", code=1)
        self.assertIn("gate: exit 1 in", result.out)
        self.assertIsNone(self.r.leaf()["results"])
        self.assertIn("## exit 1", (self.r.room / packet.RESULTS).read_text())
        (self.r.wt / "var" / "tmp" / "fail").unlink()
        self.assertEqual(0, self.r.close().code)

    def test_a_close_that_fails_voids_the_earlier_close_and_its_verdict(self):
        self.r.through("audit", gates=("ok", "flag"))
        tree = self.r.leaf()["audit"]["head"]["Tree"]
        self.assertIn("station: ship:", self.r.run("status").out)
        (self.r.wt / "var" / "tmp" / "fail").write_text("")            # ignored by Git: the tree is the one that passed
        self.refused(self.r.close(), "FAILED", "1 of 2 gate(s) did not exit 0", code=1)
        leaf = self.r.leaf()
        self.assertEqual((None, None), (leaf["results"], leaf["audit"]))
        self.assertEqual(tree, "tree " + packet.tree_of_worktree(self.r.wt, "archives/packets/DP-SES-0001.md", self.r.head())[0])
        self.assertIn("station: work:", self.r.run("status").out)
        self.refused(self.r.ship(), "no PASS from its Auditor; nothing ships")
        self.refused(self.r.audit(), "not closed")
        self.assertEqual(("close-failed", 2, 1), tuple(self.r.ledger()[-1][k] for k in ("action", "gates", "failed")))
        self.assertEqual("", git(self.r.origin, "for-each-ref", "refs/heads/agent"))
        (self.r.wt / "var" / "tmp" / "fail").unlink()
        self.r.close()
        self.assertIsNone(self.r.leaf()["audit"])
        self.r.audit()
        self.assertEqual(0, self.r.ship().code, self.r.said[-1])

    def test_a_gate_that_writes_outside_scope_is_caught_after_the_gates(self):
        self.r.through("edit", gates=("flag",))
        (self.r.wt / "var" / "tmp" / "stray").write_text("")
        self.refused(self.r.close(), "outside the packet's scope after the gates", "stray.txt")
        self.assertIsNone(self.r.leaf()["results"])

    def test_gates_run_at_umask_0002_without_the_test_seam(self):
        self.r.through("edit", gates=("env",))
        previous = os.umask(0o077)
        try:
            result = self.r.close()
        finally:
            os.umask(previous)
        self.assertEqual(0, result.code, result.text)
        self.assertIn("umask=0o2", (self.r.room / packet.RESULTS).read_text())

    def test_full_runs_every_suite_and_both_self_tests(self):
        self.r.through("edit", gates=("full",))
        result = self.r.close()
        self.assertEqual(0, result.code, result.text)
        self.assertEqual(["tools/test/test_env.py", "tools/test/test_flag.py", "tools/test/test_ok.py", "ops/bin/help --test",
                          "ops/bin/template --test"], [name for _, _, name in self.r.leaf()["results"]["gates"]])

    def test_close_refuses_a_gate_that_names_nothing(self):
        self.r.through("edit", gates=("nosuch",))
        self.refused(self.r.close(), "tools/test/test_nosuch.py, which is not in the worktree")

    def test_the_narrative_is_checked_before_any_gate_runs(self):
        self.r.through("edit")
        for narrative, word in (('The operator said "go".', "quoted words"), ('Someone wrote "go".', "quotations"),
                                ("x" * 2001, "2001 characters"),
                                ("See /home/someone/log.txt", "host paths"), ("", "empty")):
            result = self.r.close(narrative=narrative)
            self.refused(result, word)
            self.assertNotIn("gate:", result.out)
        self.refused(self.r.run("close", "--deviations", "0", "--narrative", str(self.r.base / "absent.md"), who="con"), "unreadable")
        self.refused(self.r.close(deviations="-1"), "neither can be negative")
        self.assertEqual(0, self.r.run("close", "--deviations", "0", "--narrative", "-", who="con", stdin="From standard input.").code)
        self.assertEqual("From standard input.", self.r.leaf()["results"]["narrative"])

    def test_close_refuses_while_the_rooms_own_checkout_is_dirty(self):
        self.r.through("edit")
        (self.r.room / "docs" / "a.md").write_text("edited in the room by habit\n")
        self.refused(self.r.close(), "the room's own checkout has 1 uncommitted path(s)", "var/tmp/packet/")

    def test_a_contract_edited_by_hand_stops_every_station(self):
        self.r.through("edit")
        path = self.r.leaf_path()
        path.write_text(path.read_text().replace("- docs/\n", "- docs/\n- tools/\n"))
        self.assertEqual(["docs/", "tools/"], self.r.leaf()["scope"])
        self.refused(self.r.close(), "packet hash failure")
        self.refused(self.r.run("amend", "--add", "x", "--reason", "y", who="itg"), "packet hash failure")
        path.write_text(path.read_text().replace("- docs/\n- tools/\n", "- docs/\n"))
        self.r.close()
        self.r.audit()
        path.write_text(path.read_text().replace("- Authority: RoR-25", "- Authority: RoR-26"))
        self.refused(self.r.audit(), "packet hash failure")
        self.refused(self.r.ship(), "packet hash failure")

    def test_amend_is_the_integrators_and_voids_an_earlier_close(self):
        self.r.through("close")
        self.refused(self.r.run("amend", "--add", "README.md", "--reason", "needed", who="con"), "only the packet's Integrator (itg)")
        self.refused(self.r.run("amend", "--add", "docs/", "--reason", "needed", who="itg"), "already in scope")
        self.refused(self.r.run("amend", "--add", "../x", "--reason", "needed", who="itg"), "not a normal path")
        self.refused(self.r.run("amend", "--add", "README.md", "--reason", "two\nlines", who="itg"), "one line")
        self.assertIsNotNone(self.r.leaf()["results"])
        result = self.r.run("amend", "--add", "README.md", "--add", "tools/", "--reason", "the change needs both", who="itg")
        self.assertEqual(0, result.code, result.text)
        leaf = self.r.leaf()
        self.assertEqual(["docs/", "README.md", "tools/"], leaf["scope"])
        self.assertEqual(2, len(leaf["amendments"]))
        self.assertTrue(leaf["amendments"][0].endswith("itg added README.md: the change needs both"))
        self.assertIsNone(leaf["results"])
        self.assertEqual(packet.contract_digest(leaf), self.r.ledger()[-1]["contract"])
        self.r.edit("README.md", "now in scope\n")
        self.assertEqual(0, self.r.close().code)
        self.assertEqual("2", self.r.leaf()["results"]["head"]["Paths changed"])

    def test_audit_is_only_the_auditors_and_binds_the_exact_tree(self):
        self.r.through("edit")
        self.refused(self.r.audit(), "not closed")
        self.r.close()
        for who in ("itg", "con", "orc", "out"):
            self.refused(self.r.audit(who=who), "only the packet's Auditor (aud)")
        self.refused(self.r.audit(note="He wrote \"fine\" in the margin."), "quotations")
        self.refused(self.r.audit(note="n" * 1501), "1501 characters")
        self.r.edit(text="alpha, changed after close\n")
        self.refused(self.r.audit(), "the worktree changed after close")
        self.r.close()
        failed = self.r.audit("fail", note="The page still says too little.")
        self.assertEqual(0, failed.code, failed.text)
        self.assertIn("the Contractor (con) reworks", failed.out)
        self.assertEqual("FAIL", self.r.leaf()["audit"]["head"]["Verdict"])
        self.refused(self.r.ship(), "no PASS from its Auditor")
        self.r.edit(text="alpha, and a good deal more\n")
        self.r.close()
        self.assertIsNone(self.r.leaf()["audit"])
        self.refused(self.r.ship(), "no PASS from its Auditor")
        passed = self.r.audit("PASS")
        self.assertEqual(0, passed.code, passed.text)
        leaf = self.r.leaf()
        self.assertEqual(("PASS", "aud", leaf["results"]["head"]["Tree"]),
                         (leaf["audit"]["head"]["Verdict"], leaf["audit"]["head"]["Auditor"], leaf["audit"]["head"]["Tree"]))
        self.assertEqual(("audit", "PASS"), (self.r.ledger()[-1]["action"], self.r.ledger()[-1]["verdict"]))

    def test_a_damaged_leaf_stops_the_stations_until_its_integrator_restores_it(self):
        self.r.through("close")
        kept = self.r.leaf_path().read_text()
        self.r.leaf_path().write_text("not a leaf\n")
        self.assertIn("station: STOP", self.r.run("status").out)
        self.assertIn("packet.py restore", self.r.said[-1])
        self.refused(self.r.close(), "the leaf is damaged", "packet.py restore")
        self.refused(self.r.audit(), "the leaf is damaged")
        self.refused(self.r.run("restore", who="con"), "only the packet's Integrator (itg) restores its leaf")
        self.refused(self.r.run("restore"), "canonical registry")
        restored = self.r.run("restore", who="itg")
        self.assertEqual(0, restored.code, restored.text)
        self.assertIn("restored as the close station left it", restored.out)
        self.assertEqual(kept, self.r.leaf_path().read_text())
        self.assertIn("nothing to restore", self.r.run("restore", who="itg").out)
        self.assertIn("station: audit:", self.r.run("status").out)
        self.assertEqual("restore", self.r.ledger()[-1]["action"])
        self.r.leaf_path().unlink()
        self.assertEqual(0, self.r.run("restore", who="itg").code)
        self.assertEqual(0, self.r.audit().code, self.r.said[-1])
        self.assertEqual(0, self.r.ship().code, self.r.said[-1])

    def test_a_verdict_or_a_result_written_by_hand_is_refused(self):
        self.r.through("close")
        leaf = self.r.leaf()
        forged = dict(leaf, audit={"head": {"Verdict": "PASS", "Auditor": "aud", "Audited": "2026-11-12T10:30:00Z",
                                            "Tree": leaf["results"]["head"]["Tree"]}, "note": "Looks fine to me."})
        self.assertEqual([], packet.leaf_problems(forged))
        self.r.leaf_path().write_text(packet.render_leaf(forged))
        said = self.r.run("status", who="orc").out
        self.assertIn("station: STOP: the leaf is not the one the tool last wrote (packet hash failure)", said)
        self.assertNotIn("station: ship", said)
        self.refused(self.r.ship(), "packet hash failure", "packet.py restore")
        self.refused(self.r.audit(), "packet hash failure")
        self.assertEqual("", git(self.r.origin, "for-each-ref", "refs/heads/agent"))
        self.assertEqual(0, self.r.run("restore", who="itg").code)
        self.assertIsNone(self.r.leaf()["audit"])
        path = self.r.leaf_path()
        path.write_text(path.read_text().replace("- Deviations: 0", "- Deviations: 7"))
        self.assertEqual("7", self.r.leaf()["results"]["head"]["Deviations"])
        self.refused(self.r.audit(), "packet hash failure")
        self.assertEqual(0, self.r.run("restore", who="itg").code)
        self.assertEqual(0, self.r.audit().code, self.r.said[-1])
        self.assertEqual(0, self.r.ship().code, self.r.said[-1])

    def test_with_the_ledger_gone_nothing_is_restored_and_the_integrator_abandons_by_hand(self):
        self.r.through("edit")
        (self.r.room / packet.LEDGER).unlink()
        self.assertIn("packet hash failure", self.r.run("status").out)
        self.refused(self.r.close(), "packet hash failure")
        self.refused(self.r.run("restore", who="itg"), "the ledger holds no leaf to restore", "abandons the packet")
        self.assertEqual(0, self.r.run("abandon", "--reason", "the ledger was lost", who="itg").code, self.r.said[-1])
        self.assertIn("alpha, and more", (self.r.room / packet.ABANDONED).read_text())

    def test_a_damaged_leaf_can_still_be_abandoned_by_its_integrator_with_the_work_kept(self):
        self.r.through("edit")
        self.r.leaf_path().write_text("not a leaf\n")
        self.refused(self.r.run("abandon", "--reason", "damaged", who="con"), "only the packet's Integrator (itg)")
        result = self.r.run("abandon", "--reason", "the leaf was overwritten", who="itg")
        self.assertEqual(0, result.code, result.text)
        self.assertFalse(self.r.wt.exists())
        self.assertIn("alpha, and more", (self.r.room / packet.ABANDONED).read_text())


# --------------------------------------------------------------------------
def argparse_like(now):
    """The two fields of the parsed arguments that the review functions read: a fixed time for the test."""
    import types
    return types.SimpleNamespace(now=now, fixed_now=True)


class Ship(Case):
    def test_ship_lands_the_packet_end_to_end(self):
        self.r.through("audit")
        base, tree = self.r.head(), self.r.leaf()["audit"]["head"]["Tree"][5:]
        (self.r.wt / "var" / "tmp" / "scratch.txt").write_text("ignored scratch inside the worktree")
        result = self.r.ship()
        self.assertEqual(0, result.code, result.text)
        for line in ("commit: ", "push: origin/agent/dp-ses-0001-2026-11-12", "pull request: #7", "gates: sessions-gates success",
                     "findings: none unanswered", "merge: #7 by rebase", "sync: main ", "LANDED: DP-SES-0001"):
            self.assertIn(line, result.out)
        main, origin_main = self.r.head(), self.r.head("refs/heads/main", self.r.origin)
        self.assertEqual(main, origin_main)
        self.assertNotEqual(base, main)
        self.assertEqual(base, self.r.head("main~1"))
        self.assertEqual(("main", ""), (git(self.r.room, "rev-parse", "--abbrev-ref", "HEAD"), git(self.r.room, "status", "--porcelain")))
        self.assertEqual(["A\tarchives/packets/DP-SES-0001.md", "M\tdocs/a.md"],
                         git(self.r.room, "diff", "--name-status", base, main).splitlines())
        self.assertEqual("alpha, and more\n", (self.r.room / "docs" / "a.md").read_text())
        landed = packet.parse_leaf((self.r.room / packet.LEAVES / "DP-SES-0001.md").read_text())
        self.assertEqual("PASS", landed["audit"]["head"]["Verdict"])
        self.assertEqual(tree, packet.tree_of_commit(self.r.room, main, "archives/packets/DP-SES-0001.md"))
        message = git(self.r.room, "log", "-1", "--format=%B", "main")
        for line in ("DP-SES-0001: Say more in the docs", "Packet: archives/packets/DP-SES-0001.md", "Contractor: con",
                     f"Auditor: aud (PASS on tree {tree})", "Orchestrator: orc"):
            self.assertIn(line, message)
        self.assertNotIn("Shipped-by", message)
        self.assertFalse(self.r.wt.exists())
        self.assertEqual("", git(self.r.room, "for-each-ref", "refs/heads/agent", "refs/remotes/origin/agent"))
        self.assertEqual("", git(self.r.origin, "for-each-ref", "refs/heads/agent"))
        self.assertEqual(1, git(self.r.room, "worktree", "list", "--porcelain").count("worktree "))
        state = self.r.gh()
        pull = state["pulls"][0]
        self.assertEqual(("DP-SES-0001: Say more in the docs", "main", "closed"), (pull["title"], pull["base"]["ref"], pull["state"]))
        for line in ("Dispatch packet DP-SES-0001", "Make the first page say more", "Gates: 1 of 1 exit 0", "Deviations: 0",
                     "Audit: PASS by aud", "Functions: Integrator itg, Contractor con, Auditor aud, Orchestrator orc"):
            self.assertIn(line, pull["body"])
        self.assertIn(f"main is commit {main}", state["notes"][0]["body"])
        self.assertEqual(["open", "close", "audit", "commit", "pull-request", "merge", "landed"], [l["action"] for l in self.r.ledger()])
        self.assertEqual((main, 7), (self.r.ledger()[-1]["main"], self.r.ledger()[-1]["number"]))
        self.assertEqual(0, self.r.run("status", who="itg").code)
        self.assertIn("the next is DP-SES-0002", self.r.said[-1])

    def test_the_next_packet_takes_the_next_number_and_carries_two_functions_into_the_form(self):
        self.r.through("ship")
        self.r.run("draft", "--title", "Second")
        form = (self.r.room / packet.DRAFT).read_text()
        self.assertIn("Auditor: aud\n", form)
        self.assertIn("Orchestrator: orc\n", form)
        self.assertIn("Contractor:\n", form)
        opened = self.r.open(title="Say more again")
        self.assertIn("DP-SES-0002 is open on agent/dp-ses-0002-2026-11-12", opened.out)
        (self.r.wt / "docs" / "b.md").unlink()
        self.r.edit("docs/c.md", "gamma\n")
        self.r.close()
        self.assertEqual("2", self.r.leaf(2)["results"]["head"]["Paths changed"])
        self.r.audit()
        self.assertEqual(0, self.r.ship().code, self.r.said[-1])
        self.assertEqual(["A\tarchives/packets/DP-SES-0002.md", "D\tdocs/b.md", "A\tdocs/c.md"],
                         git(self.r.room, "diff", "--name-status", "main~1", "main").splitlines())
        self.assertEqual([1, 2], packet.leaf_numbers(self.r.room, "main"))
        self.assertEqual([], packet.chain_failures(self.r.room, self.r.head()))

    def test_ship_is_pending_while_the_check_runs_and_resumes_without_repeating_a_step(self):
        self.r.through("audit")
        self.r.gh(checks=[])
        first = self.r.ship()
        self.refused(first, "PENDING", "has not started", "run `packet.py ship` again", code=3)
        commit = self.r.head("HEAD", self.r.wt)
        self.r.gh(checks=[{"name": packet.REQUIRED_CHECK, "status": "in_progress", "conclusion": None, "started_at": "2026-11-12T09:00:00Z"}])
        self.refused(self.r.ship(), "PENDING", "is running", code=3)
        self.assertEqual(commit, self.r.head("HEAD", self.r.wt))
        self.assertEqual(1, len(self.r.gh()["pulls"]))
        self.assertEqual(["open", "close", "audit", "commit", "pull-request"], [l["action"] for l in self.r.ledger()])
        self.r.gh(checks=[{"name": "another-check", "status": "completed", "conclusion": "failure", "started_at": "2026-11-12T09:30:00Z"},
                          {"name": packet.REQUIRED_CHECK, "status": "completed", "conclusion": "success", "started_at": "2026-11-12T09:00:00Z"}])
        self.assertEqual(0, self.r.ship().code, self.r.said[-1])
        self.assertEqual(1, len([call for call in self.r.gh()["calls"] if call[2] == "POST" and call[3].endswith("/pulls")]))
        self.assertEqual(1, int(git(self.r.room, "rev-list", "--count", "main~1..main")))

    def test_wait_polls_the_check_until_it_completes(self):
        self.r.through("audit")
        self.r.gh(checks=[])
        naps, real = [], packet.time.sleep

        def nap(seconds):
            if seconds < 1:                 # the standard library's own short polls while a child runs
                return real(seconds)
            naps.append(seconds)
            self.r.gh(checks=[{"name": packet.REQUIRED_CHECK, "status": "completed", "conclusion": "success",
                               "started_at": "2026-11-12T09:00:00Z"}])

        with mock.patch.object(packet.time, "sleep", nap):
            result = self.r.ship("--wait", "30")
        self.assertEqual(0, result.code, result.text)
        self.assertEqual(1, len(naps))
        self.assertTrue(1 <= naps[0] <= 20)
        self.refused(self.r.run("ship", "--wait", "-1", who="orc"), "neither can be negative")

    def test_a_red_check_fails_the_ship_and_returns_the_packet_to_the_contractor(self):
        self.r.through("audit")
        self.r.gh(checks=[{"name": packet.REQUIRED_CHECK, "status": "completed", "conclusion": "failure", "started_at": "2026-11-12T09:00:00Z"}])
        self.refused(self.r.ship(), "FAILED", "ended failure", "returns to the Contractor", code=1)
        self.assertTrue(self.r.wt.exists())
        self.r.edit(text="alpha, mended\n")
        self.refused(self.r.ship(), "not the tree the Auditor passed")
        self.r.close()
        self.r.audit()
        self.r.gh(checks=[{"name": packet.REQUIRED_CHECK, "status": "completed", "conclusion": "success", "started_at": "2026-11-12T09:00:00Z"}])
        self.assertEqual(0, self.r.ship().code, self.r.said[-1])
        self.assertEqual(2, int(git(self.r.room, "rev-list", "--count", "main~2..main")))
        self.assertEqual("alpha, mended\n", (self.r.room / "docs" / "a.md").read_text())

    def test_the_head_rests_before_it_merges(self):
        self.r.through("audit")
        self.r.gh(checks=[{"name": packet.REQUIRED_CHECK, "status": "completed", "conclusion": "success", "started_at": "2026-11-12T10:58:00Z"}])
        self.refused(self.r.ship(now="2026-11-12T11:00:00Z"), "PENDING", "rests 300 seconds", "181 remain", code=3)
        self.assertEqual(0, self.r.ship(now="2026-11-12T11:03:00Z").code, self.r.said[-1])

    def test_a_review_that_says_it_is_running_holds_the_merge(self):
        def says(status, when="2026-11-12T10:50:00Z"):
            state = {"code_review": {"commit_sha": None, "has_any_findings": None, "status": status},
                     "security_review": {"commit_sha": None, "status": None}}
            return {"user": {"login": "review-bot", "type": "Bot"}, "updated_at": when,
                    "body": f"<!-- a summary -->\n<!-- codex-review-state:v1 {json.dumps(state)} -->\n\nwords"}

        self.r.through("audit")
        self.r.gh(talk=[{"user": {"login": "someone"}, "body": "an ordinary comment", "updated_at": "2026-11-12T10:00:00Z"},
                        says("running")])
        held = self.r.ship(now="2026-11-12T11:00:00Z")
        self.refused(held, "PENDING", "a review is still running on pull request #7", code=3)
        self.assertEqual([], [call for call in self.r.gh()["calls"] if call[2] == "PUT"])
        for unreadable in ({}, None, False, "words"):                      # an answer that cannot be read does not say that none is running
            self.r.gh(talk=unreadable)
            self.refused(self.r.ship(now="2026-11-12T11:00:30Z"), "GitHub's answer to GET repos/", "/issues/7/comments is not a list")
            self.assertEqual([], [call for call in self.r.gh()["calls"] if call[2] == "PUT"], repr(unreadable))
        passer_by = dict(says("running"), user={"login": "someone", "type": "User"})
        self.r.gh(talk=[{"user": {"login": "review-bot", "type": "Bot"}, "body": "<!-- codex-review-state:v1 {not json} -->"},
                        passer_by, says("completed")])
        self.assertEqual(0, self.r.ship(now="2026-11-12T11:01:00Z").code, self.r.said[-1])
        self.r.through("audit", text="alpha, a second time\n", title="A second one")
        self.r.gh(talk=[says("running", when="2026-11-12T10:00:00Z")])
        stale = self.r.ship(now="2026-11-12T11:00:00Z")
        self.assertEqual(0, stale.code, stale.text)
        self.assertIn("taken as stopped", stale.out)

    def test_a_reviewer_github_asked_is_waited_for_and_not_for_ever(self):
        """As GitHub gives it for an application that reviews every pull request by itself: the request stands in the
        pull request's events and never in its list of requested reviewers, and the review carries another name."""
        asked = {"event": "review_requested", "requested_reviewer": {"login": "Copilot", "type": "Bot", "id": 41}}
        self.r.through("audit")
        self.r.gh(opened="2026-11-12T10:50:00Z", asked=[], events=[{"event": "committed"}, asked], teams=[{"slug": "readers"}])
        held = self.r.ship(now="2026-11-12T11:00:00Z")                         # ten minutes after it opened
        self.refused(held, "PENDING", "a review that GitHub asked for has not arrived (Copilot, team readers) on pull request #7", code=3)
        self.assertEqual([], [call for call in self.r.gh()["calls"] if call[2] == "PUT"])
        self.r.gh(teams=[], events=[asked, {"event": "copilot_work_started"},
                                    {"event": "reviewed", "state": "commented", "user": {"login": "Copilot", "type": "Bot", "id": 41}}],
                  reviews=[{"user": {"login": "copilot-pull-request-reviewer[bot]", "type": "Bot", "id": 41}, "state": "COMMENTED"}])
        landed = self.r.ship(now="2026-11-12T11:01:00Z")                       # it answered, under its other name
        self.assertEqual(0, landed.code, landed.text)
        self.assertIn("LANDED: DP-SES-0001; reviews: copilot-pull-request-reviewer[bot] no findings; the room is clean main", landed.out)
        self.r.through("audit", text="alpha, a second time\n", title="A second one")
        self.r.gh(opened="2026-11-12T10:50:00Z", events=[asked], reviews=[], pulls=[])
        self.refused(self.r.ship(now="2026-11-12T11:04:59Z"), "PENDING", "has not arrived (Copilot)", code=3)
        silent = self.r.ship(now="2026-11-12T11:05:00Z")                       # fifteen minutes: a reviewer that is down holds no packet
        self.assertEqual(0, silent.code, silent.text)
        self.assertIn("reviews: Copilot asked and silent 900 seconds after the pull request opened; not waited for longer", silent.out)
        self.assertIn("LANDED: DP-SES-0002; reviews: Copilot asked, no answer; the room is clean main", silent.out)

    def test_the_events_are_read_in_order_and_a_reviewer_is_known_by_its_account_number(self):
        def asks(login, number=None):
            return {"event": "review_requested", "requested_reviewer": dict({"login": login}, **({"id": number} if number else {}))}

        def answers(login, number=None, kind="reviewed"):
            who = dict({"login": login}, **({"id": number} if number else {}))
            return dict({"event": kind}, **({"user": who} if kind == "reviewed" else {"requested_reviewer": who}))

        def waited(events, asked=()):
            self.r.gh(events=events, asked=list(asked))
            return packet.asked_reviewers(self.r.room, "o/r", {"number": 7})

        self.r.through("audit")
        self.refused(self.r.ship("--hold"), "PENDING", "held before the merge", code=3)       # the pull request exists
        with mock.patch.dict(os.environ, PATH=f"{self.r.base / 'bin'}{os.pathsep}{os.environ['PATH']}", FAKE_GH_STATE=str(self.r.state)):
            self.assertEqual(([], "2026-11-12T09:00:00Z", True), waited([]))
            self.assertEqual(["Copilot"], waited([asks("Copilot", 41)])[0])
            self.assertEqual([], waited([asks("Copilot", 41), answers("copilot-other-name", 41)])[0])          # the number, not the name
            self.assertEqual(["Copilot"], waited([asks("Copilot", 41), answers("Copilot", 42)])[0])            # another account's review
            self.assertEqual(["Copilot"], waited([asks("Copilot", 41), answers("Copilot", 41), asks("Copilot", 41)])[0])   # asked again
            self.assertEqual(["Copilot"], waited([answers("Copilot", 41), asks("Copilot", 41)])[0])            # a review before the request
            self.assertEqual([], waited([asks("Copilot", 41), answers("Copilot", 41, "review_request_removed")])[0])
            self.assertEqual(["ada"], waited([asks("ada"), asks("bo"), answers("bo")])[0])                     # no number: by name
            self.assertEqual(["ada", "bo"], waited([asks("bo", 43)], asked=[{"login": "ada", "id": 44}, {"login": "bo", "id": 43}])[0])
            self.assertEqual([], waited([{"event": "review_requested"}, {"event": "review_requested", "requested_reviewer": "x"},
                                         {"event": "review_requested", "requested_reviewer": {"id": 45}},
                                         {"event": "reviewed", "user": None}, "not an event", {"event": "closed"}])[0])
            late = [{"event": "labeled"}] * 100 + [asks("Copilot", 41)]
            self.assertEqual(["Copilot"], waited(late)[0])                                                     # on the second page
            self.assertEqual([], waited(late + [{"event": "labeled"}] * 99 + [answers("Copilot", 41)])[0])     # and on the third
            mine = {"number": 7, "user": {"login": "room-account"}}
            self.r.gh(events=[asks("ada", 44), answers("ada", 44)], asked=[], reviews=[{"user": {"login": "ada", "id": 44}, "state": "COMMENTED"}])
            self.assertEqual("ada no findings", packet.review_record(self.r.room, "o/r", mine))
            self.r.gh(events=[asks("ada", 44), answers("ada", 44), asks("ada", 44)])
            self.assertEqual("ada no findings; ada asked, no answer", packet.review_record(self.r.room, "o/r", mine))   # asked again
            for unreadable in ({}, None, False, [], "words"):                                                  # no pull request: refused, in both reads
                self.r.gh(pull_answer={"is": unreadable})
                with self.assertRaises(packet.Refused, msg=repr(unreadable)):
                    packet.asked_reviewers(self.r.room, "o/r", {"number": 7})
                with self.assertRaises(packet.Refused, msg=repr(unreadable)):
                    packet.review_record(self.r.room, "o/r", mine)
            self.r.gh(pull_answer=None)

    def test_events_that_cannot_be_read_stop_no_landing(self):
        self.r.through("audit")
        self.r.gh(opened="2026-11-12T10:50:00Z", no_events="Not Found", asked=[{"login": "ada", "id": 44}])
        held = self.r.ship(now="2026-11-12T11:00:00Z")
        self.refused(held, "PENDING", "has not arrived (ada)", code=3)                         # GitHub's own list is still waited on
        self.assertIn("reviews: the pull request's events could not be read; only GitHub's own list of requested reviewers is waited on", held.out)
        self.r.gh(asked=[])
        landed = self.r.ship(now="2026-11-12T11:01:00Z")
        self.assertEqual(0, landed.code, landed.text)
        self.assertIn("LANDED: DP-SES-0001; reviews: events not read; the room is clean main", landed.out)
        self.r.through("audit", text="alpha, a second time\n", title="A second one")
        self.r.gh(no_events="", events={"message": "an answer that is no list"}, pulls=[])
        other = self.r.ship()
        self.assertEqual(0, other.code, other.text)
        self.assertIn("LANDED: DP-SES-0002; reviews: events not read; the room is clean main", other.out)
        with mock.patch.dict(os.environ, PATH=f"{self.r.base / 'bin'}{os.pathsep}{os.environ['PATH']}", FAKE_GH_STATE=str(self.r.state)):
            last = {"number": self.r.gh()["pulls"][-1]["number"]}
            for unreadable in ({}, None, False, 0, "", "words", {"message": "no list"}):      # an empty or null answer is no event history
                self.r.gh(events=unreadable)
                self.assertIsNone(packet.pull_events(self.r.room, "o/r", last), repr(unreadable))
                asked, _, read = packet.asked_reviewers(self.r.room, "o/r", last)
                self.assertEqual(([], False), (asked, read), repr(unreadable))
            self.r.gh(events=[])
            self.assertEqual([], packet.pull_events(self.r.room, "o/r", last))                # an empty list is one: read, and empty
            asked, _, read = packet.asked_reviewers(self.r.room, "o/r", last)
            self.assertEqual(([], True), (asked, read))

    def test_an_asked_reviewer_is_asked_after_the_rest_and_an_opening_time_that_cannot_be_read_is_long_ago(self):
        def asking():
            return [call[3] for call in self.r.gh()["calls"]
                    if call[2] == "GET" and call[3].endswith(("/pulls/7", "/issues/7/timeline?per_page=100&page=1"))]

        self.r.through("audit")
        self.r.gh(opened="2026-11-12T10:58:00Z", asked=[{"login": "Copilot", "type": "Bot"}],
                  checks=[{"name": packet.REQUIRED_CHECK, "status": "completed", "conclusion": "success", "started_at": "2026-11-12T10:58:00Z"}])
        self.refused(self.r.ship(now="2026-11-12T11:00:00Z"), "PENDING", "rests 300 seconds", code=3)      # the rest first
        self.assertEqual([], asking())
        self.refused(self.r.ship(now="2026-11-12T11:03:00Z"), "PENDING", "has not arrived (Copilot)", code=3)
        self.assertEqual(2, len(asking()), asking())                           # the pull request and its events, once each
        for unreadable in ({}, None, False, [], [1], "words"):                 # no pull request is not one that nobody was asked to review
            self.r.gh(pull_answer={"is": unreadable})
            self.refused(self.r.ship(now="2026-11-12T11:03:10Z"), "GitHub's answer to GET repos/", "/pulls/7 is not a pull request")
            self.assertNotIn("Traceback", self.r.said[-1], repr(unreadable))
            self.assertEqual([], [call for call in self.r.gh()["calls"] if call[2] == "PUT"], repr(unreadable))
        self.r.gh(pull_answer=None)
        self.r.gh(opened="not a time", pulls=[dict(self.r.gh()["pulls"][0], created_at="not a time")])
        landed = self.r.ship(now="2026-11-12T11:03:30Z")
        self.assertEqual(0, landed.code, landed.text)
        self.assertIn("Copilot asked; the pull request's opening time could not be read and is taken as long ago; not waited for longer", landed.out)
        self.assertNotIn("silent 900 seconds", landed.out)                     # a count of seconds that was not measured is not said

    def test_the_landing_names_who_reviewed_and_what_each_left(self):
        def marker(status):
            state = {"code_review": {"commit_sha": None, "has_any_findings": False, "status": status}, "security_review": {"status": None}}
            return {"user": {"login": "review-bot[bot]", "type": "Bot"}, "updated_at": "2026-11-12T09:30:00Z",
                    "body": f"<!-- codex-review-state:v1 {json.dumps(state)} -->"}

        self.r.through("audit")
        nothing = self.r.ship()
        self.assertIn("LANDED: DP-SES-0001; reviews: none arrived; the room is clean main", nothing.out)
        self.assertEqual("none arrived", self.r.ledger()[-1]["reviews"])
        self.assertIn("Shipped by orc. Reviews: none arrived.", self.r.gh()["notes"][-1]["body"])
        self.r.through("audit", text="alpha, a second time\n", title="A second one")
        finding = lambda n, who, **more: dict({"id": n, "user": {"login": who}, "path": "docs/a.md", "line": 1}, **more)
        self.r.gh(talk=[marker("completed"), {"user": {"login": "someone", "type": "User"}, "body": marker("completed")["body"]}],
                  reviews=[{"user": {"login": "second-reviewer[bot]"}, "state": "COMMENTED"}, {"user": {"login": "room-account"}, "state": "COMMENTED"},
                           {"user": {"login": "quiet-reviewer"}, "state": "APPROVED"}, {"user": None}],
                  comments=[finding(1, "second-reviewer[bot]"), finding(2, "second-reviewer[bot]"), finding(3, "room-account"),
                            finding(4, "room-account", in_reply_to_id=1), finding(5, "room-account", in_reply_to_id=2),
                            finding(6, "second-reviewer[bot]", in_reply_to_id=1)])
        landed = self.r.ship()
        self.assertEqual(0, landed.code, landed.text)
        want = "quiet-reviewer no findings; review-bot[bot] no findings; second-reviewer[bot] 2 finding(s), answered, 2 without a change"
        self.assertIn(f"LANDED: DP-SES-0002; reviews: {want}; the room is clean main", landed.out)
        self.assertEqual(want, self.r.ledger()[-1]["reviews"])
        self.assertIn(f"Reviews: {want}.", self.r.gh()["notes"][-1]["body"])
        mine, broken = {"number": 8, "user": {"login": "room-account"}}, dict(marker("completed"), body="<!-- codex-review-state:v1 {not json} -->")
        with mock.patch.dict(os.environ, PATH=f"{self.r.base / 'bin'}{os.pathsep}{os.environ['PATH']}", FAKE_GH_STATE=str(self.r.state)):
            self.r.gh(talk=[broken], reviews=[], comments=[])                # a marker that cannot be read names no reviewer
            self.assertEqual("none arrived", packet.review_record(self.r.room, "o/r", mine))
            self.r.gh(talk=[dict(broken, body="<!-- codex-review-state:v1 {} -->")])           # one that reads, and says nothing, does
            self.assertEqual("review-bot[bot] no findings", packet.review_record(self.r.room, "o/r", mine))
            self.r.gh(talk=[broken, marker("running")])
            self.assertEqual("review-bot[bot] still running", packet.review_record(self.r.room, "o/r", mine))
            for unreadable in ({}, None, False, "words"):                    # an empty or null answer is no list of reviews or comments
                self.r.gh(talk=[], reviews=unreadable)
                with self.assertRaises(packet.Refused, msg=repr(unreadable)):
                    packet.review_record(self.r.room, "o/r", mine)
                self.r.gh(talk=unreadable, reviews=[])
                with self.assertRaises(packet.Refused, msg=repr(unreadable)):
                    packet.review_record(self.r.room, "o/r", mine)

    def host(self):
        """The stand-in host for a function of the tool called by itself, once a pull request stands."""
        self.r.through("audit")
        self.refused(self.r.ship("--hold"), "PENDING", "held before the merge", code=3)
        return mock.patch.dict(os.environ, PATH=f"{self.r.base / 'bin'}{os.pathsep}{os.environ['PATH']}", FAKE_GH_STATE=str(self.r.state))

    @staticmethod
    def finding(number, login, account=None, outdated=True, **more):
        """A review comment as GitHub gives it: one whose line was changed afterwards keeps its first line only."""
        who = dict({"login": login}, **({"id": account} if account else {}))
        return dict({"id": number, "user": who, "path": "docs/a.md", "line": None if outdated else 4, "original_line": 4}, **more)

    def test_a_reviewer_is_one_account_and_is_named_once_by_the_login_on_its_review(self):
        """As GitHub gave it on a real pull request: one application signs its finding with one login and its review
        with another, under one account number."""
        mine = {"number": 7, "user": {"login": "room-account", "id": 5}}
        marker = {"user": {"login": "review-bot[bot]", "type": "Bot", "id": 99}, "body": "<!-- codex-review-state:v1 {} -->"}
        review = {"user": {"login": "copilot-pull-request-reviewer[bot]", "type": "Bot", "id": 41}, "state": "COMMENTED"}
        answer = self.finding(2, "room-account", 5, in_reply_to_id=1)
        with self.host():
            self.r.gh(talk=[marker], reviews=[review, dict(review), {"user": {"login": "room-account", "id": 5}}],
                      comments=[self.finding(1, "Copilot", 41), answer])
            self.assertEqual("copilot-pull-request-reviewer[bot] 1 finding(s), answered; review-bot[bot] no findings",
                             packet.review_record(self.r.room, "o/r", mine))
            self.r.gh(reviews=[], comments=[self.finding(1, "Copilot", 41), answer, review | {"id": 3, "in_reply_to_id": 1}])
            self.assertEqual("Copilot 1 finding(s), answered; review-bot[bot] no findings",                    # no review: the login it has
                             packet.review_record(self.r.room, "o/r", mine))
            self.r.gh(reviews=[review], comments=[self.finding(1, "Copilot", 41), answer], talk=[dict(marker, user=dict(marker["user"], id=41))])
            self.assertEqual("copilot-pull-request-reviewer[bot] 1 finding(s), answered",                      # its marker is the same account too
                             packet.review_record(self.r.room, "o/r", mine))
            self.r.gh(talk=[], reviews=[{"user": {"login": "copilot-pull-request-reviewer[bot]"}}], comments=[self.finding(1, "Copilot"), answer])
            self.assertEqual("Copilot 1 finding(s), answered; copilot-pull-request-reviewer[bot] no findings", # no number: a login is all there is
                             packet.review_record(self.r.room, "o/r", mine))
            self.r.gh(reviews=[{"user": {"login": "renamed-account", "id": 5}}], comments=[self.finding(1, "another-name", 5)])
            self.assertEqual("none arrived", packet.review_record(self.r.room, "o/r", mine))                   # the pull request's own account, by number

    def test_the_landing_counts_findings_answered_without_a_change(self):
        mine = {"number": 7, "user": {"login": "room-account"}}
        answers = [self.finding(10 + n, "room-account", in_reply_to_id=n) for n in (1, 2, 3)]
        with self.host():
            self.r.gh(talk=[], reviews=[], comments=[self.finding(1, "ada"), self.finding(2, "ada", outdated=False), *answers[:2]])
            self.assertEqual("ada 2 finding(s), answered, 1 without a change", packet.review_record(self.r.room, "o/r", mine))
            self.r.gh(comments=[self.finding(1, "ada"), self.finding(2, "ada"), *answers[:2]])
            self.assertEqual("ada 2 finding(s), answered", packet.review_record(self.r.room, "o/r", mine))  # each line was changed
            self.r.gh(comments=[self.finding(1, "ada", outdated=False), self.finding(2, "ada", outdated=False), self.finding(3, "ada"), answers[0], answers[2]])
            self.assertEqual("ada 3 finding(s), 1 unanswered, 1 answered without a change", packet.review_record(self.r.room, "o/r", mine))
            self.r.gh(comments=[self.finding(1, "ada", outdated=False)])
            self.assertEqual("ada 1 finding(s), 1 unanswered", packet.review_record(self.r.room, "o/r", mine))  # unanswered is not "without a change"
            self.assertNotIn("declined", packet.review_record(self.r.room, "o/r", mine))
        self.r.gh(comments=[self.finding(1, "ada", outdated=False), answers[0]])
        landed = self.r.ship()                                                 # a pointer for the operator: it stops nothing
        self.assertEqual(0, landed.code, landed.text)
        self.assertIn("LANDED: DP-SES-0001; reviews: ada 1 finding(s), answered, 1 without a change; the room is clean main", landed.out)

    def test_the_reviews_and_the_comments_are_read_across_every_page(self):
        mine = {"number": 7, "user": {"login": "room-account"}}
        filler = [{"user": {"login": "someone", "type": "User"}, "body": "a remark"}] * 100
        running = {"user": {"login": "review-bot[bot]", "type": "Bot"}, "updated_at": "2026-11-12T10:59:00Z",
                   "body": '<!-- codex-review-state:v1 {"code_review": {"status": "running"}} -->'}
        at = argparse_like(now=dt.datetime(2026, 11, 12, 11, 0, tzinfo=dt.timezone.utc))
        with self.host():
            self.r.gh(talk=filler + [running], reviews=[{"user": {"login": "ada"}}] * 100 + [{"user": {"login": "zed"}}], comments=[])
            self.assertEqual("ada no findings; review-bot[bot] still running; zed no findings", packet.review_record(self.r.room, "o/r", mine))
            self.assertTrue(packet.review_running(at, self.r.room, "o/r", mine))                               # on the second page
            self.r.gh(talk=filler * 2 + [running])
            self.assertTrue(packet.review_running(at, self.r.room, "o/r", mine))                               # and on the third
            self.r.gh(talk=filler)
            self.assertFalse(packet.review_running(at, self.r.room, "o/r", mine))
            calls = [call[3] for call in self.r.gh()["calls"] if "/issues/7/comments" in call[3]]
            self.assertEqual(["page=1", "page=2"], [call.rsplit("&", 1)[1] for call in calls[-2:]])           # a full page asks for the next

    def test_an_item_that_is_no_object_is_refused_plainly(self):
        mine = {"number": 7, "user": {"login": "room-account"}}
        at = argparse_like(now=dt.datetime(2026, 11, 12, 11, 0, tzinfo=dt.timezone.utc))
        good = {"user": {"login": "ada"}, "body": "a remark"}
        with self.host():
            for strange in (None, 7, "words", [good]):
                with self.subTest(item=strange):
                    for where in ("reviews", "talk", "comments"):
                        self.r.gh(**dict({"reviews": [], "talk": [], "comments": []}, **{where: [good, strange]}))
                        with self.assertRaises(packet.Refused) as caught:
                            packet.review_record(self.r.room, "o/r", mine)
                        self.assertIn("holds an item that is no object", str(caught.exception))
                    self.r.gh(reviews=[], comments=[], talk=[good, strange])
                    with self.assertRaises(packet.Refused):
                        packet.review_running(at, self.r.room, "o/r", mine)
                    self.r.gh(talk=[], comments=[strange])
                    with self.assertRaises(packet.Refused):
                        packet.unanswered_findings(self.r.room, "o/r", mine)
            for strange in ("words", 7, ["ada"], True):                        # an object whose user is no object
                with self.subTest(user=strange):
                    odd = dict(good, user=strange)
                    for where in ("reviews", "talk", "comments"):
                        self.r.gh(**dict({"reviews": [], "talk": [], "comments": []}, **{where: [good, odd]}))
                        with self.assertRaises(packet.Refused) as caught:
                            packet.review_record(self.r.room, "o/r", mine)
                        self.assertIn("holds an item whose user is no object", str(caught.exception))
                    self.r.gh(reviews=[], comments=[], talk=[odd])
                    with self.assertRaises(packet.Refused):
                        packet.review_running(at, self.r.room, "o/r", mine)
                    self.r.gh(talk=[], comments=[odd])
                    with self.assertRaises(packet.Refused):
                        packet.unanswered_findings(self.r.room, "o/r", mine)
            self.r.gh(reviews=[dict(good, user=None)], talk=[dict(good, user=None)], comments=[])   # no user at all is read, and names nobody
            self.assertEqual("none arrived", packet.review_record(self.r.room, "o/r", mine))
        for where in ("talk", "comments"):                                     # at the station: refused, no traceback, no merge
            for item, why in ((None, "holds an item that is no object"), ({"user": "words", "body": "x"}, "holds an item whose user is no object")):
                self.r.gh(**dict({"talk": [], "comments": []}, **{where: [item]}))
                self.refused(self.r.ship(), "GitHub's answer to GET repos/", why)
                self.assertNotIn("Traceback", self.r.said[-1])
                self.assertEqual([], [call for call in self.r.gh()["calls"] if call[2] == "PUT"])

    def test_a_reviewer_asked_again_is_waited_for_from_that_request(self):
        def asks(when):
            return dict({"event": "review_requested", "requested_reviewer": {"login": "Copilot", "type": "Bot", "id": 41}},
                        **({"created_at": when} if when else {}))

        def waited(now):
            said = io.StringIO()
            with contextlib.redirect_stdout(said):
                still = packet.awaited_reviewers(argparse_like(now=dt.datetime.fromisoformat(now)), self.r.room, "o/r", {"number": 7})
            return still, said.getvalue()

        reviewed = {"event": "reviewed", "user": {"login": "Copilot", "type": "Bot", "id": 41}}
        with self.host():
            self.r.gh(opened="2026-11-12T09:00:00Z", pulls=[dict(self.r.gh()["pulls"][0], created_at="2026-11-12T09:00:00Z")],
                      events=[asks("2026-11-12T09:00:02Z"), reviewed, asks("2026-11-12T12:00:00Z")], asked=[], teams=[])
            self.assertEqual(({"Copilot": "2026-11-12T12:00:00Z"}, "2026-11-12T09:00:00Z", True),
                             packet.asked_requests(self.r.room, "o/r", {"number": 7}))
            self.assertEqual((["Copilot"], ""), waited("2026-11-12T12:14:59+00:00"))       # hours after the opening, and still waited for
            still, said = waited("2026-11-12T12:15:00+00:00")
            self.assertEqual([], still)
            self.assertIn("reviews: Copilot asked and silent 900 seconds after the request; not waited for longer", said)
            self.r.gh(events=[asks(None)], asked=[{"login": "ada", "id": 44}], teams=[{"slug": "readers"}])   # no time of its own: from the opening
            self.assertEqual((["Copilot", "ada", "team readers"], ""), waited("2026-11-12T09:14:59+00:00"))
            still, said = waited("2026-11-12T09:15:00+00:00")
            self.assertEqual([], still)
            self.assertIn("reviews: Copilot, ada, team readers asked and silent 900 seconds after the pull request opened; not waited for longer", said)
            self.r.gh(events=[asks("2026-11-12T09:10:00Z")], asked=[{"login": "ada", "id": 44}], teams=[])    # one late, one not
            still, said = waited("2026-11-12T09:16:00+00:00")
            self.assertEqual(["Copilot"], still)
            self.assertIn("reviews: ada asked and silent 900 seconds after the pull request opened", said)
            self.r.gh(events=[asks("not a time")], asked=[], pulls=[dict(self.r.gh()["pulls"][0], created_at="not a time")], opened="not a time")
            still, said = waited("2026-11-12T09:16:00+00:00")
            self.assertEqual([], still)
            self.assertIn("Copilot asked; the pull request's opening time could not be read and is taken as long ago", said)

    def test_a_finding_that_arrives_after_the_merge_is_named_and_a_review_that_cannot_be_read_stops_nothing(self):
        self.r.through("hold")
        self.r.merge_outside()
        self.r.gh(comments=[{"id": 9, "user": {"login": "late-reviewer"}, "path": "docs/a.md", "line": 1}],
                  talk=[{"user": {"login": "review-bot[bot]", "type": "Bot"}, "body": '<!-- codex-review-state:v1 {"code_review": {"status": "running"}} -->'}])
        landed = self.r.ship()
        self.assertEqual(0, landed.code, landed.text)
        self.assertIn("reviews: late-reviewer 1 finding(s), 1 unanswered; review-bot[bot] still running; the room", landed.out)
        self.r.through("hold", text="alpha, a second time\n", title="A second one")
        self.r.merge_outside()
        self.r.gh(reviews={}, comments=[], talk=[])                        # an empty object where the reviews should be a list
        unread = self.r.ship()
        self.assertEqual(0, unread.code, unread.text)
        self.assertIn("LANDED: DP-SES-0002; reviews: not read; the room is clean main", unread.out)

    def test_an_unanswered_review_finding_stops_the_merge(self):
        self.r.through("audit")
        finding = {"id": 11, "user": {"login": "reviewer"}, "path": "docs/a.md", "line": 1, "body": "This is wrong.",
                   "html_url": "https://host.example/o/r/pull/7#discussion_r11"}
        own = {"id": 12, "user": {"login": "room-account"}, "path": "docs/a.md", "line": 1, "body": "A note to self."}
        self.r.gh(comments=[finding, own])
        self.refused(self.r.ship(), "1 review finding(s) are unanswered on pull request #7",
                     "docs/a.md:1 https://host.example/o/r/pull/7#discussion_r11")
        self.assertIsNone(self.r.gh()["pulls"][0]["merged_at"])
        other = {"id": 13, "in_reply_to_id": 11, "user": {"login": "bystander"}, "path": "docs/a.md", "line": 1, "body": "Agreed."}
        self.r.gh(comments=[finding, own, other])
        self.refused(self.r.ship(), "1 review finding(s) are unanswered")
        for unreadable in ({}, None, False, "words"):                      # an answer that cannot be read is not "no finding"
            self.r.gh(comments=unreadable)
            self.refused(self.r.ship(), "GitHub's answer to GET repos/", "/pulls/7/comments is not a list")
            self.assertEqual([], [call for call in self.r.gh()["calls"] if call[2] == "PUT"], repr(unreadable))
        answer = {"id": 14, "in_reply_to_id": 11, "user": {"login": "room-account"}, "path": "docs/a.md", "line": 1, "body": "Declined: out of scope."}
        self.r.gh(comments=[finding, own, other, answer])
        self.assertEqual(0, self.r.ship().code, self.r.said[-1])

    def test_findings_are_read_across_every_page(self):
        self.r.through("audit")
        filler = [{"id": n, "user": {"login": "room-account"}, "path": "docs/a.md", "line": 1} for n in range(100, 200)]
        late = {"id": 300, "user": {"login": "reviewer"}, "path": "docs/b.md", "original_line": 4}
        self.r.gh(comments=filler + [late])
        self.refused(self.r.ship(), "1 review finding(s) are unanswered", "docs/b.md:4")

    def test_hold_stops_before_the_merge(self):
        self.r.through("audit")
        held = self.r.ship("--hold")
        self.refused(held, "PENDING", "held before the merge", "pull request #7 is ready", code=3)
        self.assertIn("findings: none unanswered", held.out)
        state = self.r.gh()
        self.assertEqual([], [call for call in state["calls"] if call[2] == "PUT"])
        self.assertEqual("open", state["pulls"][0]["state"])
        self.assertEqual(self.r.head("HEAD", self.r.wt), self.r.head("refs/heads/agent/dp-ses-0001-2026-11-12", self.r.origin))
        self.assertEqual(self.r.head(), self.r.head("refs/heads/main", self.r.origin))
        self.assertEqual(0, self.r.ship().code, self.r.said[-1])

    def test_ship_is_the_orchestrators_or_a_recorded_fallback(self):
        self.r.through("audit")
        for who in ("itg", "con", "aud", "out"):
            self.refused(self.r.ship(who=who), "not the packet's Orchestrator (orc)", "--fallback", "CONSTRAINTS C16")
        self.refused(self.r.ship("--fallback", "no reason at all"), "the caller is the packet's Orchestrator; no fallback applies")
        self.refused(self.r.ship("--fallback", 'he said "go"', who="itg"), "the fallback reason holds what a public record may not")
        self.refused(self.r.ship("--fallback", "two\nlines", who="itg"), "one line")
        self.refused(self.r.ship("--fallback", "the seat is away", who="ghost"), "registered 0 times")
        self.assertEqual("", git(self.r.origin, "for-each-ref", "refs/heads/agent"))
        result = self.r.ship("--fallback", "the Orchestrator seat is away today", who="itg")
        self.assertEqual(0, result.code, result.text)
        self.assertIn("Shipped-by: itg (fallback)", git(self.r.room, "log", "-1", "--format=%B", "main"))
        self.assertIn("Shipped by itg in place of the Orchestrator: the Orchestrator seat is away today", self.r.gh()["pulls"][0]["body"])
        self.assertEqual(("landed", "itg", "the Orchestrator seat is away today"),
                         tuple(self.r.ledger()[-1][k] for k in ("action", "actor", "fallback")))

    def test_ship_refuses_when_origin_main_moved(self):
        self.r.through("audit")
        self.r.advance_origin()
        self.refused(self.r.ship(), "origin/main moved since this packet opened", "abandons it")
        self.assertEqual("", git(self.r.origin, "for-each-ref", "refs/heads/agent"))

    def test_ship_refuses_content_the_auditor_did_not_pass(self):
        self.r.through("audit")
        self.r.edit("docs/b.md", "beta, slipped in after the audit\n")
        self.refused(self.r.ship(), "not the tree the Auditor passed")
        git(self.r.wt, "checkout", "-q", "--", "docs/b.md")
        (self.r.room / "loose.txt").write_text("x")
        self.refused(self.r.ship(), "the room's own checkout has 1 uncommitted path(s)")
        self.assertEqual("", git(self.r.origin, "for-each-ref", "refs/heads/agent"))

    def test_ship_finishes_a_merge_made_outside_the_tool(self):
        self.r.through("hold")
        self.r.merge_outside()
        result = self.r.ship()
        self.assertEqual(0, result.code, result.text)
        self.assertNotIn("commit:", result.out)
        self.assertIn("LANDED", result.out)
        self.assertEqual(self.r.head(), self.r.head("refs/heads/main", self.r.origin))
        self.assertFalse(self.r.wt.exists())

    def test_ship_stops_when_the_worktree_changed_after_the_merge(self):
        self.r.through("hold")
        self.r.merge_outside()
        self.r.edit(text="alpha, edited after the merge\n")
        self.refused(self.r.ship(), "uncommitted paths after the merge", "stop and report")
        self.assertTrue(self.r.wt.exists())

    def test_ship_never_forces_a_push(self):
        self.r.through("hold")
        branch = "refs/heads/agent/dp-ses-0001-2026-11-12"
        stranger = derive(self.r.origin, self.r.head(branch, self.r.origin), {"docs/b.md": "pushed by another hand\n"})
        git(self.r.origin, "update-ref", branch, stranger)
        self.r.edit(text="alpha, reworked\n")
        self.r.close()
        self.r.audit()
        self.refused(self.r.ship(), "git push failed")
        self.assertEqual(stranger, self.r.head(branch, self.r.origin))

    def test_a_push_is_plain_and_switches_push_negotiation_off(self):
        calls = []

        def answer(cwd, *args, **more):
            calls.append(args)
            return subprocess.CompletedProcess(args, 1, "", "fatal: --negotiate-only needs one or more --negotiation-tip=*\n")

        with mock.patch.object(packet, "git_try", answer):
            told = packet.push(self.r.room, "--delete", "agent/x")
        self.assertEqual([("-c", "push.negotiate=false", "push", "--quiet", "origin", "--delete", "agent/x")], calls)
        self.assertEqual("git push failed (exit 1): fatal: --negotiate-only needs one or more --negotiation-tip=*", told)
        git(self.r.room, "config", "push.negotiate", "true")
        self.r.through("ship")
        self.assertEqual("", git(self.r.origin, "for-each-ref", "refs/heads/agent"))
        self.assertNotIn("force", " ".join(" ".join(call) for call in calls))

    def test_a_branch_that_cannot_be_removed_from_origin_keeps_the_packet_until_it_can(self):
        self.r.through("hold")
        self.r.merge_outside()
        with mock.patch.object(packet, "push", return_value="git push failed (exit 1): remote: refusing to delete"):
            self.refused(self.r.ship(), "origin still holds agent/dp-ses-0001-2026-11-12", "refusing to delete", "run the same command again")
        self.assertTrue(self.r.wt.exists())
        self.assertEqual(self.r.head(), self.r.head("refs/heads/main", self.r.origin))
        self.assertEqual(0, self.r.ship().code, self.r.said[-1])
        self.assertFalse(self.r.wt.exists())
        self.assertEqual("", git(self.r.origin, "for-each-ref", "refs/heads/agent"))

    def test_the_leaf_ships_even_where_an_ignore_rule_hides_it(self):
        (self.r.room / ".git" / "info").mkdir(exist_ok=True)
        (self.r.room / ".git" / "info" / "exclude").write_text("/archives/\n")
        self.r.through("ship")
        self.assertEqual([1], packet.leaf_numbers(self.r.room, "main"))
        self.assertEqual("", git(self.r.room, "status", "--porcelain"))

    def test_the_authorization_gate_runs_before_anything_is_pushed(self):
        self.r.through("open", scope=("docs/", "PoT.md"))
        self.r.edit("PoT.md", "A law changed with no decision recorded.\n")
        self.r.close()
        self.r.audit()
        self.refused(self.r.ship(), "the PoT authorization gate refuses this commit")
        self.assertEqual("", git(self.r.origin, "for-each-ref", "refs/heads/agent"))
        self.assertEqual([], self.r.gh()["pulls"])

    def test_what_the_host_says_is_relayed_and_nothing_is_guessed(self):
        self.r.through("audit")
        self.r.gh(fail={"POST": "gh: Validation Failed (HTTP 422)"})
        self.refused(self.r.ship(), "GitHub refused POST repos/", "Validation Failed")
        self.r.gh(fail={"PUT": "gh: Required status check is expected (HTTP 405)"})
        self.refused(self.r.ship(), "GitHub refused PUT", "Required status check")
        self.assertEqual(self.r.head(), self.r.head("refs/heads/main", self.r.origin))
        self.r.gh(fail={}, raw="<html>not json</html>")
        self.refused(self.r.ship(), "is not JSON")
        self.r.gh(raw="")
        with tempfile.TemporaryDirectory() as empty, mock.patch.dict(os.environ, {"PATH": empty}):
            with self.assertRaises(packet.Refused) as caught:
                packet.gh(self.r.room, "GET", "repos/o/r/pulls")
        self.assertIn("gh is not installed", str(caught.exception))
        self.assertEqual(0, self.r.ship().code, self.r.said[-1])

    def test_the_owner_and_repository_come_from_the_origin_address(self):
        for address, slug in (("https://host.example/owner/name", "owner/name"), ("https://host.example/owner/Name.git", "owner/Name"),
                              ("git@host.example:owner/name.git", "owner/name"), ("https://user@host.example/owner/name/", "owner/name")):
            git(self.r.room, "remote", "set-url", "origin", address)
            self.assertEqual(slug, packet.repo_slug(self.r.room))

    def test_no_output_ledger_line_or_leaf_carries_a_session_identifier(self):
        self.r.through("ship")
        self.r.run("status", who="itg")
        self.r.run("open")
        everything = "\n".join(self.r.said) + (self.r.room / packet.LEDGER).read_text() \
            + (self.r.room / packet.LEAVES / "DP-SES-0001.md").read_text() + json.dumps(self.r.gh())
        self.assertNotIn("0000f00d", everything)


# --------------------------------------------------------------------------
class AbandonAndSync(Case):
    def test_the_integrator_abandons_a_packet_that_never_reached_origin_and_the_work_is_kept(self):
        self.r.through("edit")
        self.r.edit("docs/new.md", "a new page\n")
        for who in ("con", "aud", "orc", "out"):
            self.refused(self.r.run("abandon", "--reason", "wrong scope", who=who), "only the packet's Integrator (itg)")
        result = self.r.run("abandon", "--reason", "the scope was drawn wrong", who="itg")
        self.assertEqual(0, result.code, result.text)
        self.assertIn("its number is free again", result.out)
        self.assertFalse(self.r.wt.exists())
        self.assertEqual("", git(self.r.room, "for-each-ref", "refs/heads/agent"))
        patch = self.r.room / packet.ABANDONED
        self.assertEqual(0o600, stat.S_IMODE(patch.stat().st_mode))
        self.assertIn("alpha, and more", patch.read_text())
        self.assertIn("docs/new.md", patch.read_text())
        self.assertNotIn("DP-SES-0001", patch.read_text())
        self.assertEqual(("abandon", "the scope was drawn wrong", True), tuple(self.r.ledger()[-1][k] for k in ("action", "reason", "kept")))
        self.assertIn("DP-SES-0001 is open", self.r.open(scope=("docs/",)).out)
        git(self.r.wt, "apply", str(patch))
        self.assertEqual("a new page\n", (self.r.wt / "docs" / "new.md").read_text())
        self.assertEqual(0, self.r.close().code)

    def test_a_packet_on_origin_is_abandoned_by_the_orchestrator_who_closes_its_pull_request(self):
        self.r.through("hold")
        self.refused(self.r.run("abandon", "--reason", "superseded", who="itg"), "not the packet's Orchestrator (orc)", "--fallback")
        result = self.r.run("abandon", "--reason", "superseded by a wider packet", who="orc")
        self.assertEqual(0, result.code, result.text)
        self.assertEqual("closed", self.r.gh()["pulls"][0]["state"])
        self.assertIsNone(self.r.gh()["pulls"][0]["merged_at"])
        self.assertEqual("", git(self.r.origin, "for-each-ref", "refs/heads/agent"))
        self.assertFalse(self.r.wt.exists())
        self.assertEqual(self.r.head(), self.r.head("refs/heads/main", self.r.origin))

    def test_a_fallback_may_abandon_on_origin_and_a_merged_packet_is_never_abandoned(self):
        self.r.through("hold")
        self.r.merge_outside()
        self.refused(self.r.run("abandon", "--reason", "too late", who="orc"), "the pull request is merged", "packet.py ship")
        self.assertTrue(self.r.wt.exists())
        self.assertEqual(0, self.r.ship().code)
        self.r.through("hold", text="alpha, a second time\n", title="A second one")
        result = self.r.run("abandon", "--reason", "not wanted", "--fallback", "the Orchestrator seat is away", who="itg")
        self.assertEqual(0, result.code, result.text)
        self.assertEqual("the Orchestrator seat is away", self.r.ledger()[-1]["fallback"])

    def test_sync_brings_a_clean_room_level_and_nothing_else(self):
        moved = self.r.advance_origin()
        self.refused(self.r.run("sync"), "canonical registry")
        result = self.r.run("sync", who="out")
        self.assertEqual(0, result.code, result.text)
        self.assertEqual(moved, self.r.head())
        self.assertEqual(("sync", "out", moved), tuple(self.r.ledger()[-1][k] for k in ("action", "actor", "main")))
        (self.r.room / "loose.txt").write_text("x")
        self.refused(self.r.run("sync", who="out"), "uncommitted path(s)")

    def test_a_folder_that_is_not_the_packet_worktree_stops_everything(self):
        self.r.wt.mkdir(parents=True)
        self.refused(self.r.run("status"), "is not this room's packet worktree", "stop and report")
        self.refused(self.r.open(), "already active")


# --------------------------------------------------------------------------
class Gate(unittest.TestCase):
    """The required check, on real Git objects. One valid packet is built once; each case derives a commit from it."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory(prefix="packet-gate-")
        cls.r = Room(Path(cls._tmp.name)).through("hold")
        cls.repo, cls.branch = cls.r.room, "agent/dp-ses-0001-2026-11-12"
        cls.base, cls.head = cls.r.head(), cls.r.head("HEAD", cls.r.wt)
        cls.rel = "archives/packets/DP-SES-0001.md"
        cls.text = git(cls.repo, "show", f"{cls.head}:{cls.rel}") + "\n"
        cls.leaf = packet.parse_leaf(cls.text)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def judge(self, head=None, base=None, branch=None) -> str:
        failures, notices = packet.gate_failures(self.repo, base or self.base, head or self.head,
                                                 self.branch if branch is None else branch)
        return "\n".join(failures + [f"NOTICE {n}" for n in notices])

    def with_leaf(self, leaf: dict) -> str:
        return derive(self.repo, self.head, {self.rel: packet.render_leaf(leaf)})

    def command(self, *argv) -> Result:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = packet.main(["gate", "--root", str(self.repo), *argv])
        return Result(code, out.getvalue(), err.getvalue())

    def test_a_valid_packet_passes_and_the_gate_moves_nothing(self):
        before = (git(self.repo, "for-each-ref"), git(self.repo, "status", "--porcelain"), git(self.r.wt, "status", "--porcelain"))
        self.assertEqual("", self.judge())
        result = self.command("--base", self.base, "--head", self.head, "--branch", self.branch)
        self.assertEqual(0, result.code, result.text)
        self.assertIn(f"packet gate: {self.branch} at {self.head[:12]}: PASS", result.out)
        self.assertEqual(before, (git(self.repo, "for-each-ref"), git(self.repo, "status", "--porcelain"),
                                  git(self.r.wt, "status", "--porcelain")))

    def test_the_gate_does_not_apply_while_the_base_holds_no_packet_tool(self):
        old_base = derive(self.repo, self.base, {packet.TOOL: None})
        anything = derive(self.repo, old_base, {"README.md": "no packet at all\n", packet.TOOL: "the tool arrives\n"})
        result = self.command("--base", old_base, "--head", anything, "--branch", "agent/any-name")
        self.assertEqual(0, result.code, result.text)
        self.assertIn("bootstrap", result.out)
        after = self.command("--base", anything, "--head", derive(self.repo, anything, {"README.md": "next\n"}), "--branch", "agent/any-name")
        self.assertEqual(1, after.code)
        self.assertIn("FAIL the branch 'agent/any-name' is not agent/dp-ses-NNNN-YYYY-MM-DD", after.out)

    def test_the_gate_does_not_apply_on_the_first_tool_while_the_base_holds_no_leaf(self):
        first = git(self.repo, "rev-parse", f"{self.base}:{packet.TOOL}")
        corrected = derive(self.repo, self.base, {"README.md": "no packet at all\n", packet.TOOL: "the tool, corrected\n"})
        argv = ("--base", self.base, "--head", corrected, "--branch", "agent/any-name")
        self.assertEqual(1, self.command(*argv).code)                       # this base's tool is not the first one
        with mock.patch.object(packet, "FIRST_TOOL", first):
            result = self.command(*argv)
            self.assertEqual(0, result.code, result.text)
            self.assertIn("bootstrap: the base holds the first packet tool", result.out)
            for base in (corrected, self.head):                             # another tool on the base; a leaf on the base
                after = self.command("--base", base, "--head", derive(self.repo, base, {"README.md": "next\n"}),
                                     "--branch", "agent/any-name")
                self.assertEqual(1, after.code, after.text)
                self.assertIn("FAIL the branch 'agent/any-name' is not agent/dp-ses-NNNN-YYYY-MM-DD", after.out)

    def test_broken_a_path_outside_scope(self):
        self.assertIn("1 changed path(s) are outside the packet's scope: other.txt", self.judge(derive(self.repo, self.head, {"other.txt": "x\n"})))

    def test_broken_no_leaf(self):
        said = self.judge(derive(self.repo, self.head, {self.rel: None}))
        self.assertIn("must add exactly one leaf, archives/packets/DP-SES-0001.md, and change no other; it has none", said)

    def test_broken_the_wrong_number(self):
        leaf = dict(self.leaf, head=dict(self.leaf["head"], Packet="DP-SES-0003", Branch="agent/dp-ses-0003-2026-11-12"))
        head = derive(self.repo, self.head, {self.rel: None, "archives/packets/DP-SES-0003.md": packet.render_leaf(leaf)})
        said = self.judge(head, branch="agent/dp-ses-0003-2026-11-12")
        self.assertEqual("DP-SES-0003 is not the next number; main holds up to 0000, so the next packet is 0001", said)

    def test_broken_content_changed_after_the_audit(self):
        said = self.judge(derive(self.repo, self.head, {"docs/a.md": "alpha, changed after the audit\n"}))
        self.assertEqual("the tree the Auditor passed is not the tree of this pull request without its leaf; content changed after the audit", said)

    def test_broken_the_contractor_is_the_auditor(self):
        leaf = dict(self.leaf, head=dict(self.leaf["head"], Contractor="aud"))
        leaf["results"] = dict(leaf["results"], head=dict(leaf["results"]["head"], Contractor="aud"))
        self.assertEqual(f"{self.rel}: Contractor and Auditor are the same key; no one audits their own work (PoT 4.2.2)",
                         self.judge(self.with_leaf(leaf)))

    def test_broken_an_earlier_leaf_is_edited(self):
        landed = self.head                                    # as if the first packet had landed: main holds leaf 0001
        second = dict(self.leaf, head=dict(self.leaf["head"], Packet="DP-SES-0002", Branch="agent/dp-ses-0002-2026-11-13",
                                           Base=f"commit {landed}"))
        tree = packet.tree_of_commit(self.repo, derive(self.repo, landed, {"docs/b.md": "beta, more\n"}), self.rel)
        fair = derive(self.repo, landed, {"docs/b.md": "beta, more\n", "archives/packets/DP-SES-0002.md": "placeholder\n"})
        tree = "tree " + packet.tree_of_commit(self.repo, fair, "archives/packets/DP-SES-0002.md")
        second["results"] = dict(second["results"], head=dict(second["results"]["head"], Tree=tree))
        second["audit"] = dict(second["audit"], head=dict(second["audit"]["head"], Tree=tree))
        changes = {"docs/b.md": "beta, more\n", "archives/packets/DP-SES-0002.md": packet.render_leaf(second)}
        self.assertEqual("", self.judge(derive(self.repo, landed, changes), base=landed, branch="agent/dp-ses-0002-2026-11-13"))
        edited = derive(self.repo, landed, dict(changes, **{self.rel: self.text.replace("PASS", "FAIL")}))
        said = self.judge(edited, base=landed, branch="agent/dp-ses-0002-2026-11-13")
        self.assertIn("and change no other; it has M archives/packets/DP-SES-0001.md, A archives/packets/DP-SES-0002.md", said)
        removed = derive(self.repo, landed, dict(changes, **{self.rel: None}))
        self.assertIn("it has D archives/packets/DP-SES-0001.md", self.judge(removed, base=landed, branch="agent/dp-ses-0002-2026-11-13"))

    def test_broken_two_leaves(self):
        head = derive(self.repo, self.head, {"archives/packets/DP-SES-0002.md": self.text})
        self.assertIn("it has A archives/packets/DP-SES-0001.md, A archives/packets/DP-SES-0002.md", self.judge(head))

    def test_broken_a_branch_that_is_not_a_packet_branch(self):
        for branch in ("agent/packet-workflow-20261112", "main", "agent/dp-ses-1-2026-11-12", "agent/DP-SES-0001-2026-11-12", ""):
            self.assertIn("a change reaches main only as a packet", self.judge(branch=branch))
        self.assertIn("names another packet or branch", self.judge(branch="agent/dp-ses-0001-2026-11-13"))

    def test_broken_a_leaf_out_of_canonical_form(self):
        head = derive(self.repo, self.head, {self.rel: self.text + "\n"})
        self.assertEqual(f"{self.rel}: the leaf's Audit note section is not set between two single blank lines", self.judge(head))
        spaced = derive(self.repo, self.head, {self.rel: self.text.replace("- Contractor: con\n", "- Contractor: con \n", 1)})
        self.assertEqual(f"{self.rel}: the leaf is not in canonical form: a line ends in a space", self.judge(spaced))

    def test_broken_a_leaf_that_records_a_failed_gate_no_audit_or_a_fail(self):
        results = self.leaf["results"]
        red = dict(self.leaf, results=dict(results, gates=[(1, 3, "tools/test/test_ok.py")]))
        self.assertIn("1 gate(s) did not exit 0", self.judge(self.with_leaf(red)))
        self.assertIn("holds no Results or no Audit", self.judge(self.with_leaf(dict(self.leaf, audit=None))))
        self.assertIn("holds no Results or no Audit", self.judge(self.with_leaf(dict(self.leaf, audit=None, results=None))))
        failed = dict(self.leaf, audit=dict(self.leaf["audit"], head=dict(self.leaf["audit"]["head"], Verdict="FAIL")))
        self.assertEqual("the audit verdict is not PASS", self.judge(self.with_leaf(failed)))
        counted = dict(self.leaf, results=dict(results, head=dict(results["head"], Deviations="a few")))
        self.assertIn("Deviations is a count", self.judge(self.with_leaf(counted)))

    def test_broken_a_leaf_that_quotes_or_names_a_host_path(self):
        quoted = dict(self.leaf, results=dict(self.leaf["results"], narrative='He said "ship it" and so it shipped.'))
        self.assertIn("holds what a public record may not: 1 quotations", self.judge(self.with_leaf(quoted)))
        pathed = dict(self.leaf, audit=dict(self.leaf["audit"], note="Compared with /home/someone/copy.md by eye."))
        self.assertIn("1 host paths", self.judge(self.with_leaf(pathed)))

    def test_broken_main_moved_or_the_leaf_names_another_base(self):
        moved = derive(self.repo, self.base, {"docs/b.md": "another landing\n"})
        self.assertIn("main moved since this packet opened", self.judge(base=moved))
        other = dict(self.leaf, head=dict(self.leaf["head"], Base="commit " + "c" * 40))
        self.assertEqual("the leaf's Base is not the commit this branch was cut from", self.judge(self.with_leaf(other)))

    def test_a_pull_request_that_changes_the_gate_itself_is_named(self):
        said = self.judge(derive(self.repo, self.head, {packet.TOOL: "print('always pass')\n"}))
        self.assertIn("NOTICE this pull request changes the gate that judges it: ops/lib/scripts/packet.py", said)
        self.assertIn("outside the packet's scope", said)
        result = self.command("--base", self.base, "--head", derive(self.repo, self.head, {packet.TOOL: "x\n"}), "--branch", self.branch)
        self.assertEqual(1, result.code)
        self.assertIn("NOTICE this pull request changes the gate", result.out)
        self.assertIn("failure(s)", result.out)

    def test_the_leaf_chain_is_numbered_without_a_gap(self):
        self.assertEqual([], packet.chain_failures(self.repo, self.base))
        self.assertEqual([], packet.chain_failures(self.repo, self.head))
        gap = derive(self.repo, self.head, {"archives/packets/DP-SES-0003.md": self.text.replace("0001", "0003")})
        self.assertIn("not numbered 0001 upward without a gap: 0001, 0003", "\n".join(packet.chain_failures(self.repo, gap)))
        wrong = derive(self.repo, self.head, {"archives/packets/DP-SES-0002.md": self.text})
        self.assertEqual(["archives/packets/DP-SES-0002.md does not open with its own packet id"], packet.chain_failures(self.repo, wrong))
        self.assertEqual(0, self.command("--head", self.head, "--chain").code)
        failed = self.command("--head", gap, "--chain")
        self.assertEqual(1, failed.code)
        self.assertIn("packet gate: leaf chain at", failed.out)

    def test_the_gate_command_needs_its_arguments(self):
        self.assertEqual(2, self.command("--head", self.head).code)
        self.assertEqual(2, self.command("--head", self.head, "--base", self.base).code)
        self.assertEqual(2, self.command("--head", "no-such-commit", "--chain").code)


if __name__ == "__main__":
    unittest.main(verbosity=1)
