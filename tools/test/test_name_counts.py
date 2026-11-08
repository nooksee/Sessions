#!/usr/bin/env python3
"""The count of host and operator names in tracked code and tests cannot climb, and cannot fall unrecorded.

The repository is public. This holds the names as digests, never as text: a literal
here would be a hit on itself, and reading them from the private binding would read
the live host and run blank in CI. Lines are lowercased and cut into runs of [a-z0-9];
a one-word name is sought in every window of its length inside each token, so one glued
inside a longer token is seen; a two-word name is sought across each adjacent pair of
tokens, so its underscore, hyphen and slash forms are seen, and also run together.
A name split by anything else, or built at run time, is not seen.

Scope: the files git tracks under ops/, tools/ and .github/, by git ls-files in a tree
with .git and otherwise by a walk, so a checkout and a git archive export read alike.
ops/etc/ is out of both routes: the live room's ignored files there hold these values.
ops/lib/manifests/ is out too: those are documents. A failing git stops the test and
never falls back to the walk. A failure prints path and count, never a line.

The table is exact: a rise fails, and a fall fails until the table is lowered in the
same commit, so a broken tokeniser that finds nothing fails too. A row's reason marks a
count meant to stay; a row with none is not yet driven down. Registry heads are not here
and never will be: a digest of 32 bits falls to a search.
"""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCOPE = ("ops", "tools", ".github")
NOT_SCANNED = ("ops/etc/", "ops/lib/manifests/")
TOKEN = re.compile(r"[a-z0-9]+")

# A form is (length, digest) for a window inside a token, or (left, right, digest) across two adjacent tokens.
NEEDLES = {
    'user name': [(6, 'ffedb64588af0f827058ce3aaf4f7e2805a98bf7f91a65281be39ccd85e54190')],
    'working volume': [(4, 3, '268ab12e70cdaabb146a395522f090d4c047e8cc68c1f43b450be180ae4b2388'), (7, '42dcb8310759e9d3aeb92fcaadb57456c09b93f27e201b724a663bbaabc3ab35')],
    'archive volume': [(4, 4, '38bc1aaffcc3a292cad26e1364436611422b8f21f5e37314a27188ab897e3dcb'), (8, 'c70bdf532d004b3763f4a825ffdd9b61eeecdc4b73bb7f360be9f2f4d19ca2ea')],
    "operator's first name": [(5, '85f5e10431f69bc2a14046a13aabaefc660103b6de7a84f75c4b96181d03f0b5')],
}

KEEP_REDACT_RULE = "the redact rule's key word"
KEEP_REDACT_FIXTURES = "the redact rule's key word: its fixtures must keep it"

# (path, {needle: lines}, the reason a count is meant to stay, or "")
TABLE = [
    ('ops/lib/scripts/alerts.py', {"operator's first name": 1, 'user name': 1, 'working volume': 1}, ""),
    ('ops/lib/scripts/closeout.py', {"operator's first name": 7}, ""),
    ('ops/lib/scripts/conflicts.py', {"operator's first name": 1}, ""),
    ('ops/lib/scripts/gauge.py', {'user name': 1, 'working volume': 1}, ""),
    ('ops/lib/scripts/mind.py', {"operator's first name": 20}, ""),
    ('ops/lib/scripts/redact.py', {"operator's first name": 2}, KEEP_REDACT_RULE),
    ('ops/lib/scripts/retention.py', {'archive volume': 1, "operator's first name": 2, 'user name': 1}, ""),
    ('ops/lib/scripts/rounds.sh', {'user name': 1, 'working volume': 1}, ""),
    ('ops/lib/scripts/telemetry.py', {'user name': 1, 'working volume': 1}, ""),
    ('ops/lib/scripts/vitals.py', {'user name': 6, 'working volume': 5}, ""),
    ('ops/lib/scripts/watch.py', {'user name': 1, 'working volume': 1}, ""),
    ('tools/test/test_alerts.py', {"operator's first name": 1}, ""),
    ('tools/test/test_alerts_arity.py', {'archive volume': 1}, ""),
    ('tools/test/test_closeout.py', {"operator's first name": 4}, ""),
    ('tools/test/test_media.py', {"operator's first name": 1}, ""),
    ('tools/test/test_mind.py', {"operator's first name": 6}, ""),
    ('tools/test/test_redact.py', {"operator's first name": 40, 'working volume': 1}, KEEP_REDACT_FIXTURES),
]


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def forms_of(word: str) -> list[tuple]:
    """The forms for a name of one word or two, as NEEDLES holds them."""
    parts = word.split()
    if len(parts) == 1:
        return [(len(word), sha(word))]
    left, right = parts
    return [(len(left), len(right), sha(f"{left} {right}")), (len(left) + len(right), sha(left + right))]


class Finder:
    """One set of needles, with a cache by token. The function the table and the synthetic proofs both go through."""

    def __init__(self, needles: dict[str, list[tuple]]) -> None:
        self.windows = [(name, form) for name, forms in needles.items() for form in forms if len(form) == 2]
        self.across = [(name, form) for name, forms in needles.items() for form in forms if len(form) == 3]
        self.cache: dict[str, frozenset[str]] = {}

    def in_token(self, token: str) -> frozenset[str]:
        hit = self.cache.get(token)
        if hit is None:
            hit = frozenset(name for name, (length, digest) in self.windows
                            if any(sha(token[i:i + length]) == digest for i in range(len(token) - length + 1)))
            self.cache[token] = hit
        return hit

    def in_line(self, line: str) -> set[str]:
        tokens = TOKEN.findall(line.lower())
        found: set[str] = set()
        for token in tokens:
            found |= self.in_token(token)
        for a, b in zip(tokens, tokens[1:]):
            for name, (left, right, digest) in self.across:
                if sha(f"{a[-left:]} {b[:right]}") == digest:      # a shorter token cannot match, being too short for the digest
                    found.add(name)
        return found


def scanned(name: str) -> bool:
    return not name.startswith(NOT_SCANNED) and "__pycache__" not in name.split("/")


def tracked_files(root: Path) -> list[str]:
    """The relative paths to read. git where the tree has it, and otherwise a walk that never enters the excluded folders."""
    if (root / ".git").exists():
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        done = subprocess.run(["git", "-C", str(root), "ls-files", "-z", "--", *SCOPE], capture_output=True, stdin=subprocess.DEVNULL, timeout=60, env=env)
        if done.returncode != 0:
            raise RuntimeError("git ls-files failed in a tree that has .git; this test does not fall back to a walk")
        names = [name.decode("utf-8") for name in done.stdout.split(b"\0") if name]
    else:
        names = []
        for top in SCOPE:
            for folder, subfolders, files in os.walk(root / top):
                rel = Path(folder).relative_to(root).as_posix() + "/"
                subfolders[:] = [s for s in subfolders if scanned(f"{rel}{s}/")]
                names += [f"{rel}{f}" for f in files]
    return sorted(name for name in names if scanned(name))


def count_tree(root: Path, needles: dict[str, list[tuple]]) -> dict[str, dict[str, int]]:
    """{path: {needle: lines}} for every file with a hit. A link is not followed, since its target may be anywhere."""
    finder = Finder(needles)
    counts: dict[str, dict[str, int]] = {}
    for name in tracked_files(root):
        path = root / name
        if path.is_symlink() or not path.is_file():
            continue
        for line in path.read_bytes().decode("utf-8", "replace").splitlines():
            for needle in finder.in_line(line):
                file_counts = counts.setdefault(name, {})
                file_counts[needle] = file_counts.get(needle, 0) + 1
    return counts


def differences(measured: dict[str, dict[str, int]], table: list[tuple], needles: dict[str, list[tuple]]) -> list[str]:
    """One sentence for each count that differs, naming path, needle and counts, and never a line."""
    wanted = {path: dict(row) for path, row, _ in table}
    problems = []
    for path in sorted(set(measured) | set(wanted)):
        for needle in needles:
            have, want = measured.get(path, {}).get(needle, 0), wanted.get(path, {}).get(needle, 0)
            if have != want:
                problems.append(f"{path}: {needle}: the table says {want}, the tree has {have}. A rise is a name added; a fall lowers this row in the same commit.")
    return problems


class TheComparison(unittest.TestCase):
    NEEDLES = {"one": [], "two": []}
    TABLE = [("a.py", {"one": 2}, ""), ("b.py", {"one": 1, "two": 1}, "kept")]

    def test_equal_counts_say_nothing(self) -> None:
        self.assertEqual(differences({"a.py": {"one": 2}, "b.py": {"one": 1, "two": 1}}, self.TABLE, self.NEEDLES), [])

    def test_a_rise_a_fall_and_a_new_file_each_fail_and_name_only_path_and_counts(self) -> None:
        said = differences({"a.py": {"one": 3}, "b.py": {"one": 1}, "new.py": {"two": 1}}, self.TABLE, self.NEEDLES)
        self.assertEqual([s.split(". A rise")[0] for s in said], [
            "a.py: one: the table says 2, the tree has 3",
            "b.py: two: the table says 1, the tree has 0",
            "new.py: two: the table says 0, the tree has 1"])

    def test_a_file_gone_from_the_tree_fails(self) -> None:
        said = differences({"a.py": {"one": 2}}, self.TABLE, self.NEEDLES)
        self.assertEqual(len(said), 2)
        self.assertTrue(all(s.startswith("b.py: ") for s in said))


class TheTable(unittest.TestCase):
    def test_the_counts_are_exactly_the_table(self) -> None:
        problems = differences(count_tree(ROOT, NEEDLES), TABLE, NEEDLES)
        self.assertEqual(problems, [], "\n".join(problems))

    def test_every_needle_has_a_count_so_none_can_go_blank_unseen(self) -> None:
        for needle in NEEDLES:
            self.assertGreater(sum(row.get(needle, 0) for _, row, _ in TABLE), 0, needle)

    def test_the_table_has_one_row_per_path_and_no_empty_row(self) -> None:
        paths = [path for path, _, _ in TABLE]
        self.assertEqual(len(paths), len(set(paths)))
        for path, row, _ in TABLE:
            self.assertTrue(row and all(count > 0 for count in row.values()), path)
            self.assertLessEqual(set(row), set(NEEDLES), path)

    def test_the_kept_rows_are_the_redact_rule_and_its_fixtures(self) -> None:
        kept = {path: reason for path, _, reason in TABLE if reason}
        self.assertEqual(kept, {"ops/lib/scripts/redact.py": KEEP_REDACT_RULE, "tools/test/test_redact.py": KEEP_REDACT_FIXTURES})

    def test_no_needle_is_a_short_digest(self) -> None:
        for forms in NEEDLES.values():
            for form in forms:
                self.assertRegex(form[-1], r"^[0-9a-f]{64}$")


class TheTokeniser(unittest.TestCase):
    """Through the same function as the table, with invented names."""
    NEEDLES = {"one word": forms_of("zebra"), "two words": forms_of("quartz vault")}

    def setUp(self) -> None:
        self.finder = Finder(self.NEEDLES)

    def test_a_one_word_name_in_each_form(self) -> None:
        for line in ("zebra", "ZEBRA", "Zebra said", "xzebray", "the_zebra_here", "the-zebra-here", "/home/zebra/x", "zebra's", 'event="zebra-notice"', "test_needs_zebras_words"):
            with self.subTest(line):
                self.assertEqual(self.finder.in_line(line), {"one word"})

    def test_a_two_word_name_in_each_form(self) -> None:
        for line in ("quartz vault", "quartz_vault", "quartz-vault", "quartz/vault", "QUARTZ_VAULT", "/media/x/quartz_vault/y", "-media-x-quartz-vault-Sessions", "xquartz_vaulty", "xquartz-vaulty", "quartz__vault", "quartzvault", "xquartzvaulty"):
            with self.subTest(line):
                self.assertEqual(self.finder.in_line(line), {"two words"})

    def test_what_is_not_the_name(self) -> None:
        for line in ("", "zebr", "ebra", "z e b r a", "quartz", "vault", "quartz and vault", "vault quartz", "quart vault", "quartz vaul"):
            with self.subTest(line):
                self.assertEqual(self.finder.in_line(line), set())

    def test_both_on_one_line(self) -> None:
        self.assertEqual(self.finder.in_line("zebra at quartz_vault"), {"one word", "two words"})

    def test_a_token_shorter_than_a_side_is_passed_over(self) -> None:
        self.assertEqual(self.finder.in_line("q v"), set())

    def test_the_cache_does_not_change_an_answer(self) -> None:
        self.assertEqual(self.finder.in_line("zebra"), {"one word"})
        self.assertEqual(self.finder.in_line("zebra"), {"one word"})
        self.assertEqual(self.finder.in_line("other"), set())

    def test_a_file_through_the_counter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tools").mkdir()
            (root / "tools" / "named.py").write_text("zebra\nxzebray and zebra again\nthe quartz_vault\nthe quartz-vault\nclean line\n")
            (root / "tools" / "clean.py").write_text("nothing here\nat all\n")
            (root / "tools" / "binary.bin").write_bytes(b"\xff\xfe zebra \xff\n")
            self.assertEqual(count_tree(root, self.NEEDLES), {"tools/named.py": {"one word": 2, "two words": 2}, "tools/binary.bin": {"one word": 1}})

    def test_a_clean_tree_gives_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tools").mkdir()
            (root / "tools" / "clean.py").write_text("nothing here\n")
            self.assertEqual(count_tree(root, self.NEEDLES), {})


class TheFiles(unittest.TestCase):
    NEEDLES = {"one word": forms_of("zebra")}
    GIT = ["-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid", "-c", "commit.gpgsign=false"]

    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name)
        self.root = self.base / "tree"
        self.root.mkdir()

    def write(self, name: str, text: str = "zebra\n") -> Path:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def tree(self) -> None:
        self.write("ops/lib/scripts/a.py")
        self.write("tools/test/b.py")
        self.write(".github/workflows/c.yml")

    def git(self, *args: str) -> None:
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        subprocess.run(["git", "-C", str(self.root), *self.GIT, *args], check=True, capture_output=True, stdin=subprocess.DEVNULL, env=env)

    def test_the_walk_takes_the_scope_and_nothing_else(self) -> None:
        self.tree()
        self.write("docs/d.md")
        self.write("storage/e.md")
        self.write("top.py")
        self.assertEqual(sorted(count_tree(self.root, self.NEEDLES)), [".github/workflows/c.yml", "ops/lib/scripts/a.py", "tools/test/b.py"])

    def test_the_walk_never_reads_the_private_folder(self) -> None:
        self.tree()
        self.write("ops/etc/resident-identities.json")
        self.write("ops/etc/deeper/x.json")
        self.write("ops/lib/manifests/CONTEXT.md")
        self.write("ops/lib/scripts/__pycache__/a.pyc")
        read = []
        real = Path.read_bytes
        def spying(path):
            read.append(path.relative_to(self.root).as_posix())
            return real(path)
        with mock.patch.object(Path, "read_bytes", spying):
            count_tree(self.root, self.NEEDLES)
        self.assertEqual(sorted(read), [".github/workflows/c.yml", "ops/lib/scripts/a.py", "tools/test/b.py"])

    def test_the_walk_does_not_even_enter_the_private_folder(self) -> None:
        self.tree()
        self.write("ops/etc/x.json")
        entered = []
        real = os.walk
        def spying(top, *a, **k):
            for folder, subs, files in real(top, *a, **k):
                entered.append(Path(folder).relative_to(self.root).as_posix())
                yield folder, subs, files
        with mock.patch.object(os, "walk", spying):
            tracked_files(self.root)
        self.assertNotIn("ops/etc", entered)

    def test_a_link_is_not_followed(self) -> None:
        outside = self.base / "outside.txt"
        outside.write_text("zebra\n")
        (self.root / "tools").mkdir()
        os.symlink(outside, self.root / "tools" / "link.py")
        self.assertEqual(count_tree(self.root, self.NEEDLES), {})
        self.git("init", "-q")
        self.git("add", "tools/link.py")
        self.assertEqual(count_tree(self.root, self.NEEDLES), {})

    def test_git_lists_what_is_tracked_and_nothing_untracked_or_ignored(self) -> None:
        self.tree()
        self.write(".gitignore", "/ops/etc/*\n")
        self.git("init", "-q")
        self.git("add", ".")
        self.write("ops/etc/resident-identities.json")
        self.write("tools/untracked.py")
        self.assertEqual(sorted(count_tree(self.root, self.NEEDLES)), [".github/workflows/c.yml", "ops/lib/scripts/a.py", "tools/test/b.py"])

    def test_git_tracking_the_private_folder_does_not_bring_it_in(self) -> None:
        self.tree()
        self.write("ops/etc/x.json")
        self.write("ops/lib/manifests/y.md")
        self.git("init", "-q")
        self.git("add", "-f", ".")
        self.assertEqual(sorted(count_tree(self.root, self.NEEDLES)), [".github/workflows/c.yml", "ops/lib/scripts/a.py", "tools/test/b.py"])

    def test_a_checkout_and_an_export_read_alike(self) -> None:
        self.tree()
        self.write("ops/lib/scripts/two.py", "zebra\nzebra\n")
        self.write(".gitignore", "/ops/etc/*\n")
        self.git("init", "-q")
        self.git("add", ".")
        self.git("commit", "-q", "-m", "fixture")
        self.write("ops/etc/private.json")
        checkout = count_tree(self.root, self.NEEDLES)
        export = self.base / "export"
        export.mkdir()
        tar = subprocess.run(["git", "-C", str(self.root), "archive", "HEAD"], check=True, capture_output=True)
        subprocess.run(["tar", "-x", "-C", str(export)], input=tar.stdout, check=True)
        self.assertFalse((export / ".git").exists())
        self.assertEqual(count_tree(export, self.NEEDLES), checkout)
        self.assertEqual(checkout["ops/lib/scripts/two.py"], {"one word": 2})

    def test_a_failing_git_stops_and_does_not_fall_back(self) -> None:
        self.tree()
        (self.root / ".git").write_text("gitdir: /nonexistent/place\n")
        with self.assertRaises(RuntimeError) as caught:
            count_tree(self.root, self.NEEDLES)
        self.assertIn("does not fall back", str(caught.exception))

    def test_a_git_environment_does_not_point_it_elsewhere(self) -> None:
        self.tree()
        self.git("init", "-q")
        self.git("add", ".")
        with mock.patch.dict(os.environ, {"GIT_DIR": str(self.base / "nowhere"), "GIT_WORK_TREE": str(self.base)}):
            self.assertEqual(len(count_tree(self.root, self.NEEDLES)), 3)

    def test_this_file_holds_no_name(self) -> None:
        self.assertEqual(count_tree(ROOT, NEEDLES).get("tools/test/test_name_counts.py", {}), {})


if __name__ == "__main__":
    unittest.main()
