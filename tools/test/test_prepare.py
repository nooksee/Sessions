"""Tests for ops/lib/scripts/prepare.py, the W6 native producer for phases 4 and 5. Synthetic fixtures only: every
room, store, project folder, donor and destination is made here, with 0000-prefixed identifiers. Run behind masked2.
PREPARE names the module under test (default: the room's), so a mutation run can point at a copy. ENGINE, when set,
names slice 6's frozen rotate.py; its native_rows then reads the candidate (the integration test)."""
import atexit
import copy
import hashlib
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOM_SRC = Path(__file__).resolve().parents[2]
PREPARE = Path(os.environ.get("PREPARE", ROOM_SRC / "ops/lib/scripts/prepare.py")).resolve()
ENGINE = os.environ.get("ENGINE")
ENGINE_SHA = "e7d926afaf2877dff1f73ba0093248c718e77d09476a3c769038b4de4b8a4d8e"
BASE = os.environ.get("WORK") or None
OP = "w6-disposable-test"
DONOR, DEST, RESIDENT = ("0000aaaa-0000-4000-8000-00000000000a", "0000bbbb-0000-4000-8000-00000000000b",
                         "0000cccc-0000-4000-8000-00000000000c")
MODEL = "claude-opus-5-5"
GATE_KEYS = {"trigger", "closeout", "operator_compaction", "window", "static", "media"}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def mid(n):
    return f"0000{n:04x}-0000-4000-8000-{n:012x}"


def jsonl(rows):
    return b"".join(json.dumps(r, separators=(",", ":")).encode() + b"\n" for r in rows)


def private_write(path, raw):
    path.write_bytes(raw)
    os.chmod(path, 0o600)


class Fixture:
    """A room (registry, evidence folder E), a store holding D and T, a project folder W, and a request."""

    def __init__(self):
        self.root = Path(tempfile.mkdtemp(dir=BASE)).resolve()
        atexit.register(shutil.rmtree, self.root, True)
        self.room = self.root / "room"
        (self.room / "ops" / "etc").mkdir(parents=True)
        (self.room / "ops" / "etc" / "resident-identities.json").write_text(json.dumps(
            {"identities": [{"key": "resident-one", "session_id": RESIDENT, "provider": "claude"}]}))
        self.E = self.room / "storage" / "active" / OP
        self.E.mkdir(parents=True)
        os.chmod(self.E, 0o700)
        self.W = self.root / "w6-disposable-20261109-abc123"
        self.W.mkdir(mode=0o700)
        self.store = self.root / "store"
        self.store.mkdir(mode=0o700)
        self.donor_sid, self.dest_sid = DONOR, DEST
        self.rows = self.donor_rows()
        self.dest_rows = [
            {"type": "user", "uuid": mid(900), "parentUuid": None, "sessionId": DEST, "cwd": str(self.W),
             "timestamp": "2026-11-09T10:00:00Z", "message": {"role": "user", "content": "Reply with READY."}},
            {"type": "assistant", "uuid": mid(901), "parentUuid": mid(900), "sessionId": DEST, "cwd": str(self.W),
             "timestamp": "2026-11-09T10:00:05Z", "message": {"role": "assistant", "content": [{"type": "text", "text": "READY"}],
                                                               "model": MODEL, "usage": {"input_tokens": 10}}}]
        self.pre_tokens, self.pre_time = 720000, "2026-11-09T11:00:00Z"
        self.built_at = "2026-11-09T12:00:00Z"
        self.reason = b"The first operator prompt after the compaction.\n"

    def donor_rows(self):
        W = str(self.W)

        def row(n, kind, parent, when, **extra):
            return {"type": kind, "uuid": mid(n), "parentUuid": parent, "sessionId": DONOR, "cwd": W,
                    "timestamp": when, **extra}

        def usage(tokens):
            return {"input_tokens": 3, "cache_read_input_tokens": tokens - 1003, "cache_creation_input_tokens": 1000}
        return [
            row(1, "user", None, "2026-11-09T10:01:00Z", message={"role": "user", "content": "Reply with READY."}),
            row(2, "assistant", mid(1), "2026-11-09T10:01:05Z",
                message={"role": "assistant", "model": MODEL, "content": [{"type": "text", "text": "READY"}], "usage": usage(20000)}),
            row(3, "user", mid(2), "2026-11-09T10:30:00Z", message={"role": "user", "content": "Read the corpus files."}),
            row(4, "assistant", mid(3), "2026-11-09T11:00:00Z",
                message={"role": "assistant", "model": MODEL, "content": [{"type": "text", "text": "Done."}], "usage": usage(720000)}),
            row(5, "system", None, "2026-11-09T11:10:00Z", subtype="compact_boundary",
                compactMetadata={"trigger": "manual", "preTokens": 720000}, content="Conversation compacted"),
            row(6, "user", mid(5), "2026-11-09T11:10:01Z", isCompactSummary=True,
                message={"role": "user", "content": "This session is being continued. Summary: a river and a stone."}),
            row(7, "user", mid(6), "2026-11-09T11:10:02Z", isMeta=True,
                message={"role": "user", "content": "<command-name>/compact</command-name>"}),
            row(8, "user", mid(7), "2026-11-09T11:20:00Z", message={"role": "user", "content": "Tell me about the old mill."}),
            row(9, "assistant", mid(8), "2026-11-09T11:20:10Z",
                message={"role": "assistant", "model": MODEL, "content": [{"type": "text", "text": "The mill stands by the brook."}],
                         "usage": usage(40000)}),
        ]

    def write(self, request=None, phase0=None):
        self.donor = self.store / (self.donor_sid + ".jsonl")
        self.dest = self.store / (self.dest_sid + ".jsonl")
        for p, rows in ((self.donor, self.rows), (self.dest, self.dest_rows)):
            if p.exists():
                p.unlink()
            private_write(p, jsonl(rows))
        p0 = phase0 if phase0 is not None else {
            "schema": "rotate-native-phase0/1", "operation": OP, "session_id": self.donor_sid, "tokens": self.pre_tokens,
            "model": MODEL, "window": 1000000, "reading_at": self.pre_time}
        self.write_e("phase0.json", json.dumps(p0).encode())
        self.write_e("reason.txt", self.reason)
        req = request if request is not None else self.request()
        self.request_raw = json.dumps(req).encode()
        self.write_e("request.json", self.request_raw)
        return self

    def write_e(self, name, raw):
        p = self.E / name
        if p.exists():
            p.unlink()
        private_write(p, raw)

    def request(self):
        return {"schema": "rotate-native-prepare/1", "operation": OP, "room": str(self.room), "project": str(self.W),
                "donor": {"path": str(self.store / (self.donor_sid + ".jsonl")), "session_id": self.donor_sid,
                          "sha256": sha(jsonl(self.rows))},
                "destination": {"path": str(self.store / (self.dest_sid + ".jsonl")), "session_id": self.dest_sid,
                                "sha256": sha(jsonl(self.dest_rows))},
                "phase0": {"path": str(self.E / "phase0.json"), "sha256": sha((self.E / "phase0.json").read_bytes())},
                "reason": {"path": str(self.E / "reason.txt"), "sha256": sha(self.reason)},
                "built_at": self.built_at}

    def run(self, *extra, request_sha=None):
        env = {"PATH": "/usr/bin:/bin", "HOME": str(self.root), "LANG": "C.UTF-8"}
        old = os.umask(0o022)
        try:
            return subprocess.run([sys.executable, "-I", "-B", str(PREPARE), "--request", str(self.E / "request.json"),
                                   "--request-sha256", request_sha or sha(self.request_raw), *extra],
                                  env=env, capture_output=True, text=True, timeout=300)
        finally:
            os.umask(old)

    def tree(self):
        out = {}
        for dp, dn, fn in os.walk(self.root):
            for n in dn + fn:
                p = os.path.join(dp, n)
                st = os.lstat(p)
                out[os.path.relpath(p, self.root)] = (stat.S_IMODE(st.st_mode),
                                                      sha(Path(p).read_bytes()) if stat.S_ISREG(st.st_mode) else None)
        return out


def fresh():
    f = Fixture()
    f.write()   # first write makes phase0.json so the request can bind its hash
    return f.write()


class HappyPath(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f = fresh()
        cls.before = cls.f.tree()
        cls.r = cls.f.run()
        cls.report = json.loads(cls.r.stdout) if cls.r.returncode == 0 else None

    def test_exit_and_report(self):
        self.assertEqual(self.r.returncode, 0, self.r.stderr + self.r.stdout)
        self.assertTrue(self.report["written"])
        self.assertNotIn(DONOR, self.r.stdout)
        self.assertNotIn(DEST, self.r.stdout)

    def test_writes_only_into_E(self):
        after = self.f.tree()
        added = {k for k in after if k not in self.before}
        e = os.path.relpath(self.f.E, self.f.root)
        self.assertTrue(all(k.startswith(e + os.sep) for k in added), added)
        self.assertEqual({k: v for k, v in after.items() if k in self.before}, self.before)
        names = {os.path.relpath(os.path.join(self.f.root, k), self.f.E) for k in added}
        self.assertEqual(names, {"window.jsonl", "window.json", "capsule.txt", "candidate.jsonl", "gates.json",
                                 "builder-output.txt", "media"})
        for k in added:
            mode = after[k][0]
            self.assertEqual(mode, 0o700 if after[k][1] is None else 0o600, k)

    def test_gates_record_meets_the_engine_predicate(self):
        """rotate.py e7d926af, lines 1517 to 1528, applied to the record (the contract test)."""
        gates = json.loads((self.f.E / "gates.json").read_bytes())
        self.assertTrue(gates.get("schema") == "rotate-native-gates/1" and gates.get("phase") == 5)
        for field, value in {"donor_sha256": sha(self.f.donor.read_bytes()),
                             "pristine_sha256": sha(self.f.dest.read_bytes()),
                             "candidate_sha256": sha((self.f.E / "candidate.jsonl").read_bytes())}.items():
            self.assertEqual(gates.get(field), value, field)
        checks = gates.get("gates")
        self.assertTrue(isinstance(checks, dict) and set(checks) == GATE_KEYS and all(v is True for v in checks.values()))

    def test_closeout_provenance_says_what_it_is(self):
        p = json.loads((self.f.E / "gates.json").read_bytes())["provenance"]["closeout"]
        self.assertEqual(p["evidence"], "band reading")
        self.assertEqual(p["delivered_card"], "NOT APPLICABLE")
        self.assertEqual((p["tokens"], p["window"]), (720000, 1000000))
        self.assertIsInstance(p["band"], int)
        self.assertEqual(p["source"]["donor_row"], 3)
        self.assertEqual(p["source"]["timestamp"], "2026-11-09T11:00:00Z")
        self.assertEqual(p["source"]["phase0_sha256"], sha((self.f.E / "phase0.json").read_bytes()))
        self.assertIn("trigger", p["overlap"])

    def test_plan_fragment_hashes(self):
        plan = self.report["plan"]
        self.assertEqual(plan["candidate"]["sha256"], sha(Path(plan["candidate"]["path"]).read_bytes()))
        names = [a["name"] for a in plan["artifacts"]]
        self.assertTrue({"window", "capsule", "gates"} <= set(names))
        for a in plan["artifacts"]:
            self.assertIn(Path(a["path"]).parent, (self.f.E, self.f.E / "media"), a["name"])
            self.assertEqual(a["sha256"], sha(Path(a["path"]).read_bytes()), a["name"])

    def test_window_selection_and_reparent(self):
        rows = [json.loads(l) for l in (self.f.E / "window.jsonl").read_bytes().splitlines()]
        self.assertEqual([r["uuid"] for r in rows], [mid(5), mid(6), mid(8), mid(9)])
        self.assertEqual(rows[2]["parentUuid"], mid(6))
        self.assertEqual(rows[3]["parentUuid"], mid(8))
        rec = json.loads((self.f.E / "window.json").read_bytes())
        self.assertEqual(rec["rows"], {"boundary": 4, "summary": 5, "cut": 7, "last": 8, "donor_total": 9})
        self.assertEqual(rec["omitted"], {"from": 6, "to": 6, "count": 1})
        cap = len((self.f.E / "capsule.txt").read_bytes())
        self.assertEqual(rec["estimate"]["tokens"], 40000 + cap)
        self.assertEqual(rec["reason_sha256"], sha(self.f.reason))

    def test_candidate_shape(self):
        rows = [json.loads(l) for l in (self.f.E / "candidate.jsonl").read_bytes().splitlines()]
        self.assertEqual(rows[0]["subtype"], "compact_boundary")
        self.assertTrue(all(r.get("sessionId") == DEST for r in rows))
        self.assertTrue(all(r.get("cwd", str(self.f.W)) == str(self.f.W) for r in rows))
        self.assertEqual([r["type"] for r in rows[-2:]], ["custom-title", "agent-name"])
        orientation = rows[-3]
        self.assertTrue(orientation["message"]["content"].startswith("<session_clinic_orientation>\n"))
        self.assertEqual(orientation["timestamp"], self.f.built_at)
        self.assertNotIn("isCompactSummary", orientation)
        self.assertEqual([r["timestamp"] for r in rows[:4]], [r["timestamp"] for r in
                                                             [self.f.rows[4], self.f.rows[5], self.f.rows[7], self.f.rows[8]]])
        raw = json.dumps(rows)
        self.assertNotIn(DONOR, raw)

    def test_capsule_names_no_resident_or_mind(self):
        text = (self.f.E / "capsule.txt").read_text()
        self.assertIn("not a resident", text)
        self.assertIn("NOT APPLICABLE", text)
        self.assertNotIn("Registry", text)
        self.assertNotIn("archives/mind", text)

    @unittest.skipUnless(ENGINE, "ENGINE names slice 6's frozen rotate.py; integration runs once it is given")
    def test_engine_native_rows_reads_the_candidate(self):
        self.assertEqual(sha(Path(ENGINE).read_bytes()), ENGINE_SHA)
        spec = importlib.util.spec_from_file_location("engine_rotate", ENGINE)
        engine = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(engine)
        raw = (self.f.E / "candidate.jsonl").read_bytes()
        rows, _, _ = engine.native_rows(raw, DEST, self.f.W)
        self.assertEqual(rows[0].get("subtype"), "compact_boundary")


class Media(unittest.TestCase):
    """An inline image in the window is externalized into E/media, private, and named as an artifact."""

    def test_image_is_externalized(self):
        f = Fixture()
        # Over the Externalizer's 256-character floor, as every real picture is; the bytes need not be a real PNG.
        png = __import__("base64").b64encode(bytes(range(256)) * 3).decode()
        f.rows += [
            {"type": "user", "uuid": mid(10), "parentUuid": mid(9), "sessionId": DONOR, "cwd": str(f.W),
             "timestamp": "2026-11-09T11:21:00Z", "message": {"role": "user", "content": [
                 {"type": "text", "text": "Here is a picture."},
                 {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": png}}]}},
            {"type": "assistant", "uuid": mid(11), "parentUuid": mid(10), "sessionId": DONOR, "cwd": str(f.W),
             "timestamp": "2026-11-09T11:21:10Z", "message": {"role": "assistant", "model": MODEL,
                                                              "content": [{"type": "text", "text": "A small square."}],
                                                              "usage": {"input_tokens": 3, "cache_read_input_tokens": 41000,
                                                                        "cache_creation_input_tokens": 1000}}}]
        f.write()
        f.write()
        r = f.run()
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        plan = json.loads(r.stdout)["plan"]
        media = [a for a in plan["artifacts"] if a["name"].startswith("media-")]
        self.assertEqual(len(media), 1)
        path = Path(media[0]["path"])
        st = os.lstat(path)
        self.assertEqual((path.parent, stat.S_IMODE(st.st_mode), st.st_nlink), (f.E / "media", 0o600, 1))
        self.assertEqual(media[0]["sha256"], sha(path.read_bytes()))
        raw = (f.E / "candidate.jsonl").read_text()
        self.assertNotIn(png, raw)
        self.assertIn("preserved at " + str(path) + "]", raw)
        gates = json.loads((f.E / "gates.json").read_bytes())
        self.assertTrue(all(gates["detail"]["media"].values()))


class TinyInline(unittest.TestCase):
    def test_a_payload_under_the_externalizer_floor_stops_before_any_record(self):
        """Under 256 characters the Externalizer leaves a payload inline; the candidate must not carry it."""
        f = Fixture()
        f.rows[7]["message"]["content"] = [{"type": "text", "text": "Tell me about the old mill."}]
        f.rows[8]["message"]["content"].append(
            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "AAAA"}})
        f.write()
        f.write()
        r = f.run()
        self.assertEqual(r.returncode, 3, r.stderr + r.stdout)
        self.assertEqual(json.loads(r.stdout)["failed"], "media-inline")
        self.assertFalse((f.E / "gates.json").exists())
        self.assertFalse((f.E / "candidate.jsonl").exists())


class ArtifactLimit(unittest.TestCase):
    def test_over_the_artifact_limit_stops_before_the_candidate_and_the_gates_record(self):
        """Review finding 1 on #78: 61 media files make 65 artifacts. The count is taken before candidate.jsonl and
        gates.json exist, so a failed run never leaves a success record. 60 media files, 64 artifacts, still build."""
        b64 = __import__("base64").b64encode
        for count, code in ((61, 3), (60, 0)):
            with self.subTest(media=count):
                f = Fixture()
                f.rows[8]["message"]["content"] += [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                                 "data": b64(i.to_bytes(2, "big") * 384).decode()}}
                    for i in range(count)]
                f.write()
                f.write()
                r = f.run()
                self.assertEqual(r.returncode, code, r.stderr + r.stdout)
                if code:
                    self.assertEqual(json.loads(r.stdout)["failed"], "too-many-artifacts")
                    self.assertFalse((f.E / "gates.json").exists())
                    self.assertFalse((f.E / "candidate.jsonl").exists())
                else:
                    self.assertEqual(len(json.loads(r.stdout)["plan"]["artifacts"]), 64)


class HousekeepingPairs(unittest.TestCase):
    """Break 7 (the Manager's read of phase 4): the provider's api-request-blob rows carry no uuid and repeat the call's
    tool_use and tool_result blocks. Tool pairs are counted on rows that carry a uuid only, in the window (phase 4) and
    in the static list (phase 5), as the engine's reader counts them since #81. Invented rows in the real shape."""

    def fixture(self, finished=True):
        f = Fixture()
        W = str(f.W)
        use = {"type": "tool_use", "id": "toolu_fixture_1", "name": "Read", "input": {"file_path": W + "/notes.md"}}
        result = {"type": "tool_result", "tool_use_id": "toolu_fixture_1", "content": "a river and a stone"}
        f.rows[8]["message"]["content"].append(use)
        # As the engine's test orders them: the request's blob repeats the call while it is pending, the result's echo
        # repeats the result, and the next request's blob repeats the call again.
        blob = {"type": "api-request-blob", "sessionId": DONOR, "hash": "invented",
                "message": {"role": "assistant", "content": copy.deepcopy(f.rows[8]["message"]["content"])}}
        echo = {"type": "api-request-blob", "sessionId": DONOR, "hash": "invented-two",
                "message": {"role": "user", "content": [result]}}
        answer = {"type": "user", "uuid": mid(10), "parentUuid": mid(9), "sessionId": DONOR, "cwd": W,
                  "timestamp": "2026-11-09T11:20:20Z", "message": {"role": "user", "content": [result]}}
        f.rows += [blob, answer, echo, blob] if finished else [blob]
        f.write()
        return f

    def test_a_blob_repeating_a_pair_after_the_cut_is_accepted_and_an_unfinished_pair_is_not(self):
        f = self.fixture()
        r = f.run()
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertTrue(json.loads((f.E / "gates.json").read_bytes())["detail"]["static"]["tool-pairs"])
        r = self.fixture(finished=False).run("--dry-run")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("prepare: refused: window-tool-pairs", r.stderr)


class DryRun(unittest.TestCase):
    def test_writes_nothing_and_reports_the_window(self):
        f = fresh()
        before = f.tree()
        r = f.run("--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        rep = json.loads(r.stdout)
        self.assertFalse(rep["written"])
        self.assertNotIn("plan", rep)
        self.assertEqual(rep["closeout"]["delivered_card"], "NOT APPLICABLE")
        self.assertEqual(f.tree(), before)


class Refusals(unittest.TestCase):
    def refused(self, f, reason, *extra, request_sha=None):
        before = f.tree()
        r = f.run(*extra, request_sha=request_sha)
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("prepare: refused: " + reason, r.stderr)
        self.assertEqual(f.tree(), before)

    def variant(self, change=None, request_change=None, phase0=None):
        f = Fixture()
        if change:
            change(f)
        f.write(phase0=phase0)
        req = f.request()
        if request_change:
            request_change(f, req)
        return f.write(request=req, phase0=phase0)

    def test_registered_resident_as_donor(self):
        def c(f):
            f.donor_sid = RESIDENT
            for r in f.rows:
                r["sessionId"] = RESIDENT
        self.refused(self.variant(c, phase0={"schema": "rotate-native-phase0/1"}), "registered-resident-refused")

    def test_registered_resident_as_destination(self):
        def c(f):
            f.dest_sid = RESIDENT
        self.refused(self.variant(c), "registered-resident-refused")

    def test_no_boundary(self):
        self.refused(self.variant(lambda f: f.rows.__setitem__(slice(4, 5), [])), "exactly-one-boundary-required")

    def test_two_boundaries(self):
        def c(f):
            b = copy.deepcopy(f.rows[4])
            b["uuid"], b["timestamp"] = mid(50), "2026-11-09T10:40:00Z"
            f.rows.insert(3, b)
        self.refused(self.variant(c), "exactly-one-boundary-required")

    def test_automatic_compaction(self):
        self.refused(self.variant(lambda f: f.rows[4]["compactMetadata"].__setitem__("trigger", "auto")),
                     "operator-compaction-manual-required")

    def test_no_summary(self):
        self.refused(self.variant(lambda f: f.rows[5].pop("isCompactSummary")), "exact-compaction-summary-required")

    def test_two_summaries(self):
        self.refused(self.variant(lambda f: f.rows[6].__setitem__("isCompactSummary", True)),
                     "exact-compaction-summary-required")

    def test_trigger_below_due(self):
        def c(f):
            f.pre_tokens = 690000
            f.rows[3]["message"]["usage"]["cache_read_input_tokens"] = 690000 - 1003
        self.refused(self.variant(c), "trigger-below-due")

    def test_phase0_record_not_the_reading(self):
        self.refused(self.variant(lambda f: setattr(f, "pre_tokens", 721000)), "phase0-record-not-the-reading")

    def test_compaction_before_the_reading(self):
        self.refused(self.variant(lambda f: f.rows[3].__setitem__("timestamp", "2026-11-09T11:15:00Z")
                                  or setattr(f, "pre_time", "2026-11-09T11:15:00Z")), "compaction-before-the-reading")

    def test_no_genuine_cut(self):
        self.refused(self.variant(lambda f: f.rows[7]["message"].__setitem__("content", "/compact")),
                     "genuine-user-cut-required")

    def test_no_assistant_after_cut(self):
        self.refused(self.variant(lambda f: f.rows.pop()), "substantive-exchange-required")

    def test_estimate_over_a_fifth(self):
        self.refused(self.variant(lambda f: f.rows[8]["message"]["usage"].__setitem__("cache_read_input_tokens", 250000)),
                     "wake-estimate-over-budget")

    def test_window_over_bound(self):
        def c(f):
            last = f.rows.pop()
            prev = mid(8)
            for n in range(5000):
                f.rows.append({"type": "user", "uuid": mid(1000 + n), "parentUuid": prev, "sessionId": DONOR,
                               "cwd": str(f.W), "timestamp": "2026-11-09T11:20:01Z", "isMeta": True,
                               "message": {"role": "user", "content": "<x/>"}})
                prev = mid(1000 + n)
            last["parentUuid"] = prev
            f.rows.append(last)
        self.refused(self.variant(c), "window-over-bound")

    def test_unmatched_tool_pair_in_window(self):
        def c(f):
            f.rows[8]["message"]["content"].append({"type": "tool_result", "tool_use_id": "toolu_none"})
        self.refused(self.variant(c), "window-tool-pairs")

    def test_donor_hash_mismatch(self):
        self.refused(self.variant(request_change=lambda f, r: r["donor"].__setitem__("sha256", "0" * 64)), "donor-hash")

    def test_destination_hash_mismatch(self):
        self.refused(self.variant(request_change=lambda f, r: r["destination"].__setitem__("sha256", "0" * 64)),
                     "destination-hash")

    def test_foreign_session_in_donor(self):
        self.refused(self.variant(lambda f: f.rows[2].__setitem__("sessionId", DEST)), "donor-foreign-session")

    def test_other_project_in_donor(self):
        self.refused(self.variant(lambda f: f.rows[2].__setitem__("cwd", "/elsewhere")), "donor-other-project")

    def test_built_before_the_donor_ended(self):
        self.refused(self.variant(lambda f: setattr(f, "built_at", "2026-11-09T11:20:05Z")),
                     "built-before-the-donor-ended")

    def test_no_reviewed_window_for_model(self):
        def c(f):
            for r in f.rows:
                if r["type"] == "assistant":
                    r["message"]["model"] = "claude-unknown-model"
        self.refused(self.variant(c), "no-reviewed-window-for-model")

    def test_output_exists(self):
        f = fresh()
        f.write_e("gates.json", b"{}")
        self.refused(f, "output-exists")

    def test_evidence_folder_not_private(self):
        f = fresh()
        os.chmod(f.E, 0o755)
        self.refused(f, "unsafe-private-node")

    def test_request_hash_mismatch(self):
        self.refused(fresh(), "small-file-hash", request_sha="0" * 64)

    def test_request_outside_the_evidence_folder(self):
        f = fresh()
        other = f.room / "storage" / "active" / "other-op"
        other.mkdir(mode=0o700)
        private_write(other / "request.json", f.request_raw)
        before = f.tree()
        env = {"PATH": "/usr/bin:/bin", "HOME": str(f.root), "LANG": "C.UTF-8"}
        r = subprocess.run([sys.executable, "-I", "-B", str(PREPARE), "--request", str(other / "request.json"),
                            "--request-sha256", sha(f.request_raw)], env=env, capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        self.assertIn("request-evidence-home", r.stderr)
        self.assertEqual(f.tree(), before)

    def test_evidence_inside_git_and_not_ignored(self):
        f = fresh()
        env = {"PATH": "/usr/bin:/bin", "HOME": str(f.root), "GIT_CONFIG_NOSYSTEM": "1"}
        subprocess.run(["git", "init", "-q", str(f.room)], env=env, check=True)
        self.refused(f, "evidence-git-exposed")


def load_prepare():
    spec = importlib.util.spec_from_file_location(f"prepare_ut_{id(object())}", PREPARE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class ChangedDuringRead(unittest.TestCase):
    """D and T changed while they are read (the Auditor's R1, bernard.md section 254). In process, with os.fdopen or
    os.open wrapped so that the change lands at a fixed point of the read."""

    def run_in_process(self, f, act):
        import contextlib
        import io
        mod = load_prepare()
        real_fdopen, real_open = os.fdopen, os.open
        os.fdopen, os.open = act(real_fdopen, real_open)
        err = io.StringIO()
        try:
            with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
                code = mod.main(["--request", str(f.E / "request.json"), "--request-sha256", sha(f.request_raw),
                                 "--dry-run"])
        finally:
            os.fdopen, os.open = real_fdopen, real_open
        return code, err.getvalue()

    def mid_read(self, target, change):
        """After the first read call on the target's descriptor, apply change(target path)."""
        def act(real_fdopen, real_open):
            def fdopen(fd, *a, **k):
                handle = real_fdopen(fd, *a, **k)
                if os.path.samestat(os.fstat(fd), os.stat(target)):
                    class Hooked:
                        done = False

                        def __init__(self, h):
                            self.h = h

                        def __enter__(self):
                            self.h.__enter__()
                            return self

                        def __exit__(self, *e):
                            return self.h.__exit__(*e)

                        def fileno(self):
                            return self.h.fileno()

                        def _after(self, value):
                            if not Hooked.done:
                                Hooked.done = True
                                change(target)
                            return value

                        def readline(self, *a):
                            return self._after(self.h.readline(*a))

                        def read(self, *a):
                            return self._after(self.h.read(*a))
                    return Hooked(handle)
                return handle
            return fdopen, real_open
        return act

    def before_open(self, target, change):
        """Between the first lstat and the open, apply change(target path)."""
        def act(real_fdopen, real_open):
            def opener(path, flags, *a, **k):
                if str(path) == str(target):
                    change(target)
                return real_open(path, flags, *a, **k)
            return real_fdopen, opener
        return act

    @staticmethod
    def append(path):
        """In place: the same inode grows by one valid row, so only the size and times change."""
        with open(path, "ab") as h:
            h.write(b'{"type":"queue-operation"}\n')

    @staticmethod
    def move_store(path):
        """The folder is moved away and an identical copy put in its place: the open file's inode is untouched
        (no link count or time of its own changes), so only the path's lstat can see the swap."""
        store = path.parent
        old = store.with_name(store.name + ".moved")
        os.rename(store, old)
        store.mkdir(mode=0o700)
        for item in old.iterdir():
            (store / item.name).write_bytes(item.read_bytes())
            os.chmod(store / item.name, 0o600)

    @staticmethod
    def replace(path):
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_bytes(path.read_bytes())
        os.chmod(tmp, 0o600)
        os.rename(tmp, path)

    def test_donor_appended_mid_read(self):
        f = fresh()
        code, err = self.run_in_process(f, self.mid_read(f.donor, self.append))
        self.assertEqual((code, "donor-changed-during-read" in err), (2, True), err)

    def test_donor_store_moved_mid_read(self):
        f = fresh()
        code, err = self.run_in_process(f, self.mid_read(f.donor, self.move_store))
        self.assertEqual((code, "donor-changed-during-read" in err), (2, True), err)

    def test_donor_replaced_before_open(self):
        f = fresh()
        code, err = self.run_in_process(f, self.before_open(f.donor, self.replace))
        self.assertEqual((code, "donor-opened-other" in err), (2, True), err)

    def test_destination_appended_mid_read(self):
        f = fresh()
        code, err = self.run_in_process(f, self.mid_read(f.dest, self.append))
        self.assertEqual((code, "destination-changed-during-read" in err), (2, True), err)

    def test_destination_store_moved_mid_read(self):
        f = fresh()
        code, err = self.run_in_process(f, self.mid_read(f.dest, self.move_store))
        self.assertEqual((code, "destination-hash" in err), (2, True), err)

    def test_destination_replaced_before_open(self):
        f = fresh()
        code, err = self.run_in_process(f, self.before_open(f.dest, self.replace))
        self.assertEqual((code, "destination-opened-other" in err), (2, True), err)


class BuilderFault(unittest.TestCase):
    """The static working-directory check is a second barrier behind donor-other-project and --cwd (the Auditor's
    N1, section 254): a builder that writes another folder into a carried row stops the run before any record."""

    def test_wrong_cwd_from_the_builder_stops_before_any_record(self):
        import contextlib
        import io
        f = fresh()
        mod = load_prepare()
        real_sibling = mod.sibling

        def sibling(name):
            m = real_sibling(name)
            if name == "successor":
                real_main = m.main

                def main():
                    real_main()
                    out = Path(sys.argv[sys.argv.index("--out") + 1])
                    rows = [json.loads(l) for l in out.read_bytes().splitlines()]
                    rows[1]["cwd"] = "/elsewhere"
                    out.write_bytes(jsonl(rows))
                m.main = main
            return m
        mod.sibling = sibling
        out = io.StringIO()
        old = os.umask(0o022)
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
                code = mod.main(["--request", str(f.E / "request.json"), "--request-sha256", sha(f.request_raw)])
        finally:
            os.umask(old)
        self.assertEqual(code, 3)
        self.assertEqual(json.loads(out.getvalue())["failed"], "static-working-directory")
        self.assertFalse((f.E / "gates.json").exists())


class Static(unittest.TestCase):
    src = PREPARE.read_text()

    def test_engine_constants_named(self):
        for text in ('GATES_SCHEMA = "rotate-native-gates/1"', '"trigger", "closeout", "operator_compaction", "window", '
                     '"static", "media"', "DONOR_LIMIT = 64 * 1024 * 1024"):
            self.assertIn(text, self.src)

    def test_no_network_and_no_removal_but_its_own_build_file(self):
        for name in ("socket", "urllib", "http", "subprocess", "shutil", "tempfile"):
            self.assertNotIn("import " + name, self.src)
        self.assertEqual(self.src.count("os.unlink("), 1)
        self.assertIn("os.unlink(build)", self.src)
        for call in ("os.remove(", "os.rename(", "os.replace(", "rmtree", "os.rmdir("):
            self.assertNotIn(call, self.src)

    def test_writes_by_exclusive_create(self):
        self.assertIn("os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600", self.src)
        self.assertEqual(self.src.count("O_WRONLY"), 1)


class IdeNotice(unittest.TestCase):
    """The cut when the plugin led the prompt with an IDE notice (a file open in the editor): claudine.md section 234,
    the Auditor's section 286. The notice is passed over by myself.py's exact shape; nothing else is."""
    OPENED = "<ide_opened_file>The user opened the file /x/notes.md in the IDE.</ide_opened_file>"
    SELECTION = "<ide_selection>The user selected lines 1 to 2.</ide_selection>"

    def prompt(self, content):
        return load_prepare().user_prompt({"type": "user", "message": {"role": "user", "content": content}})

    def test_a_prompt_led_by_notices_is_genuine(self):
        for content in (self.OPENED + "Tell me about the old mill.",
                        self.OPENED + "\n" + self.SELECTION + "\nTell me about the old mill.",
                        [{"type": "text", "text": self.OPENED}, {"type": "text", "text": "Tell me about the old mill."}]):
            with self.subTest(content=content):
                self.assertTrue(self.prompt(content))

    def test_a_notice_alone_or_with_a_stray_close_tag_or_a_command_after_it_is_not(self):
        for content in (self.OPENED, self.OPENED + "  \n",
                        self.OPENED + "Tell me.</ide_opened_file>",
                        self.OPENED + "/compact", self.OPENED + "<command-name>/compact</command-name>",
                        "<ide_opened_file>never closed. Tell me about the old mill.",
                        "<other_notice>x</other_notice>Tell me about the old mill."):
            with self.subTest(content=content):
                self.assertFalse(self.prompt(content))

    def test_the_shape_is_myself_pys_own(self):
        spec = importlib.util.spec_from_file_location("prepare_ut_myself", PREPARE.with_name("myself.py"))
        me = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = me
        spec.loader.exec_module(me)
        mod = load_prepare()
        self.assertEqual((mod.IDE_NOTICE_RE.pattern, mod.IDE_NOTICE_RE.flags),
                         (me.IDE_NOTICE_RE.pattern, me.IDE_NOTICE_RE.flags))
        self.assertEqual(mod.IDE_NOTICE_CLOSE_RE.pattern, me.IDE_NOTICE_CLOSE_RE.pattern)

    def test_the_window_cuts_at_a_notice_led_prompt(self):
        f = Fixture()
        f.rows[7]["message"]["content"] = self.OPENED + "Tell me about the old mill."
        f.write()
        r = f.run("--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["window"]["rows"]["cut"], 7)


if __name__ == "__main__":
    unittest.main(verbosity=1)
