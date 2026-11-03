#!/usr/bin/env python3
"""Synthetic Git tests for the PoT authorization gate; no private data is used."""
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "ops" / "lib" / "scripts" / "constitution.py"
SCRATCH = ROOT / "var" / "tmp"


def git(root, *args):
    return subprocess.run(
        ["git", "-C", str(root), "-c", "core.hooksPath=/dev/null", *args],
        check=True, capture_output=True, text=True,
    ).stdout.strip()


class Fixture:
    def __init__(self, root):
        self.root = root
        git(root, "-c", "init.templateDir=", "init", "-q")
        git(root, "config", "user.name", "Synthetic Test")
        git(root, "config", "user.email", "synthetic@example.invalid")
        self.base_law = b"synthetic constitutional baseline\n"
        self.write("PoT.md", self.base_law)
        self.write("RoR.md", b"# Synthetic decision ledger\n")
        self.write("README.md", b"baseline\n")
        self.base = self.commit("baseline")

    def write(self, relative, content):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def commit(self, message):
        git(self.root, "add", "--all")
        git(self.root, "commit", "-m", message, "-q")
        return git(self.root, "rev-parse", "HEAD")

    def authorize_change(self, *, scope="PoT.md", target_hash=None,
                         snapshot=True, authority=True, include_decision=True,
                         decision="Operator", hash_suffix="", duplicate_act=False,
                         act_suffix=""):
        candidate_law = b"synthetic constitutional successor\n"
        actual_hash = hashlib.sha256(candidate_law).hexdigest()
        target_hash = target_hash or actual_hash
        short = actual_hash[:8]
        self.write("PoT.md", candidate_law)
        if snapshot:
            self.write(f"archives/PoT-{short}.md", candidate_law)
        words_hash = hashlib.sha256(b"synthetic private operator words").hexdigest()
        authority_path = f"archives/PoT-authority-{short}.md"
        if authority:
            self.write(
                authority_path,
                (
                    "# Sanitized constitutional authority\n"
                    "Authority: Operator decision (protected provenance; not authenticated by this checker)\n"
                    f"Scope: {scope}\n"
                    f"Target policy SHA-256: {target_hash}\n"
                    f"Words SHA-256: {words_hash}\n"
                    f"Record: RoR.md#RoR-1; archives/PoT-{short}.md; "
                    f"{authority_path}; Words SHA-256: {words_hash}\n"
                ).encode(),
            )
        if include_decision:
            act = (
                f"Decision: {decision}. Scope: {scope}. "
                f"Target policy SHA-256: {target_hash}{hash_suffix}. "
                f"Apply the synthetic policy change.{act_suffix}"
            )
            record = (
                f"PoT.md; archives/PoT-{short}.md; {authority_path}; "
                f"private words source archives/RoR-words.md; Words SHA-256: {words_hash}"
            )
            entry = (
                "\n### RoR-1: operator direction\n"
                "- **Given:** synthetic test fixture\n"
                f'- **Words:** "[words sha256={words_hash}]"\n'
                f"- **Act:** {act}\n"
            )
            if duplicate_act:
                entry += f"- **Act:** {act}\n"
            entry += f"- **Record:** {record}\n- **Entered by:** synthetic test writer\n"
            with (self.root / "RoR.md").open("ab") as handle:
                handle.write(entry.encode())
        self.head = self.commit("candidate")
        return actual_hash

    def run(self, base=None, head=None):
        return subprocess.run(
            [sys.executable, "-I", "-B", str(TOOL),
             "--root", str(self.root),
             "--base", base or self.base,
             "--head", head or self.head],
            capture_output=True, text=True, timeout=30,
        )


class ConstitutionTest(unittest.TestCase):
    def setUp(self):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="constitution-test-", dir=SCRATCH)
        self.root = Path(self.temp.name)
        self.fixture = Fixture(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def test_unchanged_policy_is_an_ordinary_pass(self):
        self.fixture.write("README.md", b"candidate documentation\n")
        head = self.fixture.commit("documentation only")
        result = self.fixture.run(head=head)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PoT unchanged", result.stdout)

    def test_unauthorized_policy_change_fails_closed(self):
        self.fixture.authorize_change(include_decision=False)
        result = self.fixture.run()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("RoR.md must be appended", result.stderr)

    def test_valid_scoped_operator_decision_passes(self):
        self.fixture.authorize_change()
        result = self.fixture.run()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("snapshot, and ledger", result.stdout)

    def test_unrelated_decision_does_not_authorize_policy(self):
        self.fixture.authorize_change(scope="README.md")
        result = self.fixture.run()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("exact operator decision", result.stderr)

    def test_suffixed_scope_does_not_authorize_policy(self):
        self.fixture.authorize_change(scope="PoT.md.bak")
        result = self.fixture.run()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("exact operator decision", result.stderr)

    def test_suffixed_decision_does_not_authorize_policy(self):
        self.fixture.authorize_change(decision="Operator-denied")
        result = self.fixture.run()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("exact operator decision", result.stderr)

    def test_wrong_target_hash_fails(self):
        self.fixture.authorize_change(target_hash="0" * 64)
        result = self.fixture.run()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("exact operator decision", result.stderr)

    def test_suffixed_target_hash_fails(self):
        self.fixture.authorize_change(hash_suffix="0")
        result = self.fixture.run()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("exact operator decision", result.stderr)

    def test_duplicate_authorization_fields_fail(self):
        self.fixture.authorize_change(duplicate_act=True)
        result = self.fixture.run()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate 'Act' fields", result.stderr)

    def test_repeated_scope_inside_act_fails(self):
        self.fixture.authorize_change(act_suffix=" Scope: README.md.")
        result = self.fixture.run()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("exact operator decision", result.stderr)

    def test_later_unrelated_ledger_entry_cannot_be_ignored(self):
        self.fixture.authorize_change()
        with (self.root / "RoR.md").open("ab") as handle:
            handle.write(
                b"\n### RoR-2: unrelated later entry\n"
                b"- **Given:** synthetic unrelated event\n"
            )
        self.fixture.head = self.fixture.commit("append unrelated later entry")
        result = self.fixture.run()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("exactly one new RoR decision entry", result.stderr)

    def test_duplicate_or_lower_new_entry_number_fails(self):
        self.fixture.authorize_change()
        with (self.root / "RoR.md").open("ab") as handle:
            handle.write(
                b"\n### RoR-1: duplicate numbered entry\n"
                b"- **Given:** synthetic unrelated event\n"
            )
        self.fixture.head = self.fixture.commit("append duplicate-number entry")
        result = self.fixture.run()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unique and strictly increasing", result.stderr)

    def test_new_entry_number_cannot_go_backwards(self):
        self.fixture.authorize_change()
        with (self.root / "RoR.md").open("ab") as handle:
            handle.write(
                b"\n### RoR-0: lower numbered entry\n"
                b"- **Given:** synthetic unrelated event\n"
            )
        self.fixture.head = self.fixture.commit("append lower-number entry")
        result = self.fixture.run()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unique and strictly increasing", result.stderr)

    def test_duplicate_authority_fields_fail(self):
        self.fixture.authorize_change()
        authority_path = next(self.root.glob("archives/PoT-authority-*.md"))
        with authority_path.open("a") as handle:
            handle.write("Scope: PoT.md.bak\n")
        self.fixture.head = self.fixture.commit("append contradictory authority scope")
        result = self.fixture.run()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate 'Scope' fields", result.stderr)

    def test_missing_immutable_snapshot_fails(self):
        self.fixture.authorize_change(snapshot=False)
        result = self.fixture.run()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("snapshot and authority leaf", result.stderr)

    def test_missing_authority_leaf_fails(self):
        self.fixture.authorize_change(authority=False)
        result = self.fixture.run()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("snapshot and authority leaf", result.stderr)

    def test_changed_policy_must_be_modified_not_deleted_or_renamed(self):
        (self.root / "PoT.md").unlink()
        (self.root / "constitution.md").write_bytes(b"renamed law\n")
        self.fixture.head = self.fixture.commit("rename constitution")
        result = self.fixture.run()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("deletes or renames PoT.md", result.stderr)

    def test_policy_must_remain_a_regular_file(self):
        (self.root / "PoT.md").unlink()
        (self.root / "PoT.md").symlink_to("README.md")
        self.fixture.head = self.fixture.commit("replace policy with symlink")
        result = self.fixture.run()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("regular, non-executable file", result.stderr)

    def test_candidate_checkout_must_be_clean(self):
        self.fixture.write("README.md", b"candidate documentation\n")
        head = self.fixture.commit("clean candidate")
        (self.root / "uncommitted.txt").write_text("not in candidate\n")
        result = self.fixture.run(head=head)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("candidate checkout is dirty", result.stderr)

    def test_ledger_history_must_be_append_only(self):
        self.fixture.authorize_change()
        # A committed rewrite of the base ledger must not pass as a new decision.
        original = self.fixture.root / "RoR.md"
        current = original.read_bytes()
        original.write_bytes(current.replace(b"# Synthetic", b"# Rewritten"))
        self.fixture.head = self.fixture.commit("rewrite ledger preimage")
        result = self.fixture.run()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("historical bytes", result.stderr)


if __name__ == "__main__":
    unittest.main()
