#!/usr/bin/env python3
"""Synthetic integration proof: redact artifacts and the unchanged constitution gate.

No real ledger, private words, body, settings or repository refs are used.
Passing this suite is not authorization for real rendering or policy adoption.
"""
import hashlib
import importlib.util
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REDACT = ROOT / "ops/lib/scripts/redact.py"
spec = importlib.util.spec_from_file_location("ror_join_constitution_fixture",
                                            Path(__file__).with_name("test_constitution.py"))
fixture_module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = fixture_module
spec.loader.exec_module(fixture_module)


class RorJoinTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ror-join-", dir=ROOT / "var/tmp")
        self.directory = Path(self.temp.name)
        repo = self.directory / "repo"
        repo.mkdir()
        self.fixture = fixture_module.Fixture(repo)
        self.raw = b'# Synthetic ledger\nOperator: "invented baseline permission"\n'
        self.fixture.write("RoR.md", self.raw)
        self.base = self.fixture.commit("synthetic raw-ledger baseline")
        self.private = self.directory / "private-source.md"
        self.private.write_bytes(self.raw)
        self.private.chmod(0o600)

    def tearDown(self):
        self.temp.cleanup()

    def render(self, source, out_name="derived.md", words_name=None):
        out = self.directory / out_name
        args = [sys.executable, "-I", "-B", str(REDACT), "render", str(source), "--out", str(out)]
        if words_name:
            args += ["--words-out", str(self.directory / words_name)]
        result = subprocess.run(args, capture_output=True, text=True, timeout=30)
        return out, result

    def first_render(self):
        derived, result = self.render(self.private, words_name="private-words.md")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        data = derived.read_bytes()
        self.fixture.write("RoR.md", data)
        return data, self.fixture.commit("synthetic first privacy render")

    def private_authority_entry(self, public_base):
        self.fixture.authorize_change()
        combined = (self.fixture.root / "RoR.md").read_bytes()
        self.assertTrue(combined.startswith(public_base))
        public_entry = combined[len(public_base):]
        words = b"synthetic private operator words"
        digest = hashlib.sha256(words).hexdigest().encode()
        private_entry = public_entry.replace(b"[words sha256=" + digest + b"]", words)
        self.assertNotEqual(private_entry, public_entry)
        entry_source = self.directory / "entry-source.md"
        entry_source.write_bytes(private_entry)
        entry_source.chmod(0o600)
        return entry_source, private_entry

    def test_first_privacy_render_passes_with_policy_unchanged(self):
        original_hash = hashlib.sha256(self.private.read_bytes()).hexdigest()
        data, rendered_base = self.first_render()
        result = self.fixture.run(base=self.base, head=rendered_base)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PoT unchanged", result.stdout)
        self.assertNotIn(b"invented baseline permission", data)
        self.assertEqual(hashlib.sha256(self.private.read_bytes()).hexdigest(), original_hash)
        self.assertEqual(stat.S_IMODE((self.directory / "private-words.md").stat().st_mode), 0o600)

    def test_combining_first_render_and_policy_change_is_rejected(self):
        self.first_render()
        self.fixture.authorize_change()
        result = self.fixture.run(base=self.base)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must be appended", result.stderr)

    def test_digest_append_alone_does_not_update_the_original_header_binding(self):
        public_base, rendered_base = self.first_render()
        _, private_entry = self.private_authority_entry(public_base)
        result = self.fixture.run(base=rendered_base)
        self.assertEqual(result.returncode, 0, result.stderr)
        combined = (self.fixture.root / "RoR.md").read_bytes()
        self.assertEqual(combined.splitlines()[0], public_base.splitlines()[0])
        self.assertIn(hashlib.sha256(self.raw).hexdigest().encode(), combined.splitlines()[0])
        # The structural gate does not certify a whole-current-source hash.
        current_private_hash = hashlib.sha256(self.raw + private_entry).hexdigest().encode()
        self.assertNotIn(current_private_hash, combined.splitlines()[0])
        self.assertEqual(combined.count(b"<!-- redact:"), 1)

    def test_rendered_entry_segment_preserves_both_bindings_and_passes_adoption(self):
        public_base, rendered_base = self.first_render()
        entry_source, private_entry = self.private_authority_entry(public_base)
        segment, rendered = self.render(entry_source, out_name="entry-derived.md")
        self.assertEqual(rendered.returncode, 0, rendered.stdout + rendered.stderr)
        entry_data = segment.read_bytes()
        combined = public_base + entry_data
        self.fixture.write("RoR.md", combined)
        head = self.fixture.commit("synthetic append-only derived entry segment")
        result = self.fixture.run(base=rendered_base, head=head)
        self.assertEqual(result.returncode, 0, result.stderr)
        headers = [line for line in combined.splitlines() if line.startswith(b"<!-- redact:")]
        self.assertEqual(len(headers), 2)
        self.assertIn(hashlib.sha256(self.raw).hexdigest().encode(), headers[0])
        self.assertIn(hashlib.sha256(private_entry).hexdigest().encode(), headers[1])
        self.assertNotIn(b"synthetic private operator words", combined)
        self.assertEqual(entry_source.read_bytes(), private_entry)

    def test_full_rerender_at_adoption_breaks_append_only_guard(self):
        public_base, rendered_base = self.first_render()
        _, private_entry = self.private_authority_entry(public_base)
        full_source = self.directory / "full-private-source.md"
        full_source.write_bytes(self.raw + private_entry)
        derived, rendered = self.render(full_source, out_name="full-derived.md")
        self.assertEqual(rendered.returncode, 0, rendered.stdout + rendered.stderr)
        self.fixture.write("RoR.md", derived.read_bytes())
        head = self.fixture.commit("synthetic full rerender at adoption")
        result = self.fixture.run(base=rendered_base, head=head)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must be appended", result.stderr)

    def test_render_does_not_supply_missing_authority_evidence(self):
        _, rendered_base = self.first_render()
        self.fixture.authorize_change(include_decision=False)
        result = self.fixture.run(base=rendered_base)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must be appended", result.stderr)

    def test_output_collision_preserves_input_and_existing_output(self):
        target = self.directory / "existing.md"
        target.write_bytes(b"existing synthetic artifact\n")
        before = self.private.read_bytes()
        _, result = self.render(self.private, out_name=target.name)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(target.read_bytes(), b"existing synthetic artifact\n")
        self.assertEqual(self.private.read_bytes(), before)
        self.assertEqual(list(self.directory.glob(".*.redact-*")), [])

    def test_malformed_words_leave_no_public_or_private_derivative(self):
        self.private.write_bytes(b'- **Words:** "the "role" remains private\n')
        before = self.private.read_bytes()
        _, result = self.render(self.private, words_name="words.md")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertFalse((self.directory / "derived.md").exists())
        self.assertFalse((self.directory / "words.md").exists())
        self.assertEqual(self.private.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
