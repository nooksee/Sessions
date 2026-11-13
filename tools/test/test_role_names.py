#!/usr/bin/env python3
"""Three role names the policy no longer uses stand in no tracked file outside the kept records.

The room's roles once carried three other names. The policy, the tools, the tests and the
documents were renamed in one packet, and this suite keeps those names out: the required
check runs it, so a change that brings one back does not land. A record is never rewritten
(PoT 1.2.13). The ledger and the archives are therefore not read, and they keep the names
their events used (CONSTRAINTS C04).

The names are held as digests, never as text: a literal here would be a hit on itself. A
line is cut into runs of letters, and a whole run is compared. Two of the names are refused
in any case of letters. The third is also the provider's own word for the author of a reply,
which the transcript tools must use, so it is refused only when it begins with a capital and
continues in small letters. Each is refused alone and as a plural. A file's own path is cut
and compared like a line. A name glued inside a longer run of letters, or built at run time,
is not seen. A failure prints a path and a line number, never the line; a hit in the path
itself is line 0.

Scope: every file git tracks or would add, by git ls-files in a tree with .git: the tracked
files and the untracked ones that are not ignored, so that a new file is read in a packet's
worktree before it is committed. A tree without .git is walked, so a checkout and an export
read alike. A failing git stops the test and never falls back to the walk. Run:

    python3 -I -B tools/test/test_role_names.py
"""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RECORDS = ("archives/",)             # kept records: not read
LEDGER = "RoR.md"                    # the ledger: not read, and the proof that the digests still match their names
RUN = re.compile(r"[A-Za-z]+")

# name -> the digests of its singular and its plural. ANY is compared with the run in small letters; CAPITAL with the run as it stands.
ANY = {
    "first name": ("6ee4a469cd4e91053847f5d3fcb61dbcc91e8f0ef10be7748da4c4a1ba382d17",
                   "e6ef1856e376fff10d5159f5f6f5a8d35cb7032a3954c32a616ab9b91e7d19d3"),
    "third name": ("042b8f64044ee7990f5272525e9c63a93559a5bf2078bc2bcda05f2b148ecc91",
                   "5b07d052328131e36971390c85e9a19adee1575bda1a87d57e8aa36dc82fae79"),
}
CAPITAL = {
    "second name": ("391e405152779acc6b0f9429f3a4e27baf2af0deab2c37ba792311efa767d676",
                    "913101023d6a833008346268868589eed4a838d0758124d7bddc57514f91eda8"),
}


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def needles(word: str) -> tuple[str, str]:
    """The pair of digests for a name and its plural, as the tables hold them."""
    return sha(word), sha(word + "s")


class Finder:
    """One pair of tables, with a cache by run. The room's own tables and the invented ones both go through it."""

    def __init__(self, any_case: dict[str, tuple[str, ...]], capital: dict[str, tuple[str, ...]]) -> None:
        self.any_case = {digest: name for name, digests in any_case.items() for digest in digests}
        self.capital = {digest: name for name, digests in capital.items() for digest in digests}
        self.cache: dict[str, frozenset[str]] = {}

    def in_run(self, run: str) -> frozenset[str]:
        hit = self.cache.get(run)
        if hit is None:
            found = {self.any_case.get(sha(run.lower())), self.capital.get(sha(run))}
            hit = self.cache[run] = frozenset(name for name in found if name)
        return hit

    def in_line(self, line: str) -> set[str]:
        found: set[str] = set()
        for run in RUN.findall(line):
            found |= self.in_run(run)
        return found


def read(name: str) -> bool:
    return name != LEDGER and not name.startswith(RECORDS) and "__pycache__" not in name.split("/")


def tracked_files(root: Path) -> list[str]:
    """Every relative path to consider: what git tracks or would add, and otherwise a walk of a tree that has no .git."""
    if (root / ".git").exists():
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        done = subprocess.run(["git", "-C", str(root), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                              capture_output=True, stdin=subprocess.DEVNULL, timeout=60, env=env)
        if done.returncode != 0:
            raise RuntimeError("git ls-files failed in a tree that has .git; this test does not fall back to a walk")
        return sorted({name.decode("utf-8") for name in done.stdout.split(b"\0") if name})
    names = []
    for folder, _, files in os.walk(root):
        rel = Path(folder).relative_to(root).as_posix()
        names += [f if rel == "." else f"{rel}/{f}" for f in files]
    return sorted(names)


def hits(root: Path, finder: Finder, names: list[str]) -> list[tuple[str, int, str]]:
    """(path, line number, name) for every hit in the given files and in their own paths, which are line 0.

    A link is not followed, since its target may be anywhere; its own path is still compared.
    """
    found = []
    for name in names:
        found += [(name, 0, hit) for hit in sorted(finder.in_line(name))]
        path = root / name
        if path.is_symlink() or not path.is_file():
            continue
        for number, line in enumerate(path.read_bytes().decode("utf-8", "replace").splitlines(), 1):
            found += [(name, number, hit) for hit in sorted(finder.in_line(line))]
    return found


class RoomTest(unittest.TestCase):
    """The tree under test."""

    def setUp(self) -> None:
        self.finder = Finder(ANY, CAPITAL)

    def test_no_file_outside_the_records_holds_one_of_the_names(self) -> None:
        names = [name for name in tracked_files(ROOT) if read(name)]
        for expected in ("PoT.md", "NOW.md", "ops/lib/manifests/CONSTRAINTS.md", "docs/MANUAL.md", "tools/test/test_role_names.py"):
            self.assertIn(expected, names, "the file list is not the tree")
        found = hits(ROOT, self.finder, names)
        self.assertEqual([], [f"{path}:{number}: the {name}" for path, number, name in found],
                         "a role name the policy no longer uses; name the role as PoT 4.1 names it, or reword")

    def test_the_ledger_still_holds_each_name(self) -> None:
        """The digests are live: the ledger's own entries carry all three names, and a record is never rewritten."""
        found = {name for _, _, name in hits(ROOT, self.finder, [LEDGER])}
        self.assertEqual({"first name", "second name", "third name"}, found)

    def test_the_tables_hold_digests_and_no_text(self) -> None:
        digests = [digest for table in (ANY, CAPITAL) for pair in table.values() for digest in pair]
        self.assertEqual(6, len(set(digests)))
        for digest in digests:
            self.assertRegex(digest, r"\A[0-9a-f]{64}\Z")
        own = Path(__file__).read_text(encoding="utf-8")
        self.assertEqual(set(), Finder(ANY, CAPITAL).in_line(own.replace("\n", " ")))

    def test_the_ledger_and_the_archives_are_not_read_and_nothing_else_is_spared(self) -> None:
        self.assertFalse(read("RoR.md"))
        self.assertFalse(read("archives/packets/DP-SES-0001.md"))
        self.assertFalse(read("tools/test/__pycache__/x.pyc"))
        for name in ("PoT.md", "NOW.md", "docs/RoR.md", "docs/archives/x.md", "archives.md", "ops/lib/manifests/CONSTRAINTS.md",
                     "tools/test/test_role_names.py", ".github/workflows/sessions-gates.yml"):
            self.assertTrue(read(name), name)


class FinderTest(unittest.TestCase):
    """The cutting and the two rules, proved on invented names."""

    def setUp(self) -> None:
        self.finder = Finder({"any": needles("warden")}, {"capital": needles("Helper")})

    def test_a_whole_run_of_letters_is_compared(self) -> None:
        for line in ("the warden said", "WARDEN_ROLE = 1", "Warden's desk", "a-warden-two", "two wardens", "Wardens.", "(warden)", "warden9"):
            self.assertEqual({"any"}, self.finder.in_line(line), line)
        for line in ("the wardenship", "churchwarden", "contextwarden", "war den", "wardenz", ""):
            self.assertEqual(set(), self.finder.in_line(line), line)

    def test_the_capital_rule_spares_the_small_and_the_all_capital_forms(self) -> None:
        for line in ("the Helper said", "Helper's desk", "Helpers,", "GitHub Helper (x)"):
            self.assertEqual({"capital"}, self.finder.in_line(line), line)
        for line in ('"role": "helper"', "the helper's reply", "CLAUDE_HELPER", "helpers", "HelperThing", "hElper"):
            self.assertEqual(set(), self.finder.in_line(line), line)

    def test_both_rules_are_found_in_one_line(self) -> None:
        self.assertEqual({"any", "capital"}, self.finder.in_line("The Helper and the WARDEN"))


class TreeTest(unittest.TestCase):
    """A planted name is found by path and line in both routes, and a record is not read."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="role-names-")
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.finder = Finder({"any": needles("warden")}, {})
        for name, text in (("docs/a.md", "clean\nthe warden\n"), ("archives/b.md", "the warden\n"), ("RoR.md", "the warden\n"),
                           ("ops/c.py", "x = 1\n"), ("deep/er/d.txt", "one\ntwo\nWardens here\n"),
                           ("docs/the-warden-guide.md", "clean\n"), ("archives/warden/e.md", "clean\n")):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        (self.root / "docs/link.md").symlink_to(self.root / "archives/b.md")

    def planted(self) -> list[tuple[str, int, str]]:
        return hits(self.root, self.finder, [name for name in tracked_files(self.root) if read(name)])

    def test_the_walk_finds_the_planted_lines_and_reads_no_record(self) -> None:
        self.assertEqual([("deep/er/d.txt", 3, "any"), ("docs/a.md", 2, "any"), ("docs/the-warden-guide.md", 0, "any")], self.planted())

    def test_git_lists_what_it_tracks_or_would_add_and_nothing_it_ignores(self) -> None:
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull)

        def git(*args: str) -> None:
            subprocess.run(["git", "-C", str(self.root), "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args],
                           check=True, capture_output=True, stdin=subprocess.DEVNULL, timeout=60, env=env)
        git("init", "-q")
        (self.root / ".gitignore").write_text("deep/\n", encoding="utf-8")
        git("add", "docs/a.md", "archives/b.md", "RoR.md", ".gitignore")
        names = tracked_files(self.root)
        self.assertIn("ops/c.py", names)                                        # not tracked yet, and not ignored: read
        self.assertNotIn("deep/er/d.txt", names)                                # ignored: not read
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual([("docs/a.md", 2, "any"), ("docs/the-warden-guide.md", 0, "any")], self.planted())
        git("add", "-A")
        git("commit", "-q", "-m", "all")
        self.assertEqual([("docs/a.md", 2, "any"), ("docs/the-warden-guide.md", 0, "any")], self.planted())
        (self.root / "docs/a.md").unlink()                                      # deleted and still in the index: passed over
        self.assertEqual([("docs/the-warden-guide.md", 0, "any")], self.planted())

    def test_a_failing_git_stops_the_test(self) -> None:
        (self.root / ".git").write_text("not a repository\n", encoding="utf-8")
        with self.assertRaises(RuntimeError):
            tracked_files(self.root)


if __name__ == "__main__":
    unittest.main(verbosity=1)
