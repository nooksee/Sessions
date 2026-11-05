#!/usr/bin/env python3
"""rotate: read-only phase gates in an explicitly synthetic room.

Generated with ops/bin/template; implemented by Joe Codex. Phases 0 to 2
inspect supplied evidence; phases 3 to 9 refuse. No bodies, writes, provider
calls, custody, installation or implicit advancement. Standard library only.
Spec: docs/ops/specs/scripts/rotate.md. Tests: tools/test/test_rotate.py.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import re
import stat
import sys
from fractions import Fraction
from pathlib import Path

sys.dont_write_bytecode = True
SESSIONS = Path(__file__).resolve().parents[3]
LIMIT = 1_048_576
SMALL = 65_536
DIGEST = re.compile(r"[0-9a-f]{64}")
PHASES = (
    ("trigger", ["a current-body gauge snapshot at the rotation line", "matching recorded closeout state"]),
    ("donor-closeout", ["hash-bound closing handoff", "explicit mind-entry disposition"]),
    ("mind-ready", ["mind show --ref passes", "the checked leaf matches the closing record"]),
    ("destination", ["operator-created native container", "exact room, identity, spare label and closed writers"]),
    ("window", ["provider-specific summary and active-window design", "justified operator-prompt cut and wake estimate"]),
    ("build-and-static-gates", ["reviewed builder and media adapters", "capsule assembly and every static gate"]),
    ("custody-and-hold", ["reviewed launcher hold", "two independent directly verified custody copies"]),
    ("install", ["post-custody named operator go", "closed writers, guarded swap and registry/binding join", "C09-bounded rollback"]),
    ("acceptance", ["native load and clean append", "first gauge reading and operator recognition"]),
    ("close", ["evidence-backed receipt", "separately authorized unchanged-donor disposition"]),
)


class Refused(Exception):
    """A bounded reason code; input contents never enter diagnostics."""


def sibling(name):
    spec = importlib.util.spec_from_file_location("rotate_" + name, Path(__file__).with_name(name + ".py"))
    if spec is None or spec.loader is None:
        raise Refused("dependency-unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


class Evidence:
    """Bounded reads, with a final unchanged-preimage check; never writes."""

    def __init__(self, room, notice):
        self.notice = notice
        self.room = Path(os.path.abspath(room))
        if self.room != self.room.resolve() or self.room == SESSIONS:
            raise Refused("synthetic-room-required")
        notice.parent_chain(self.room)
        notice.private_node(self.room, True)
        self.seen = {}
        self.state_inputs = set()
        marker = self.object(".rotate-synthetic.json", SMALL)
        if marker != {"schema": "rotate-synthetic/1", "synthetic": True} or marker.get("synthetic") is not True:
            raise Refused("synthetic-room-required")

    def path(self, relative):
        if not isinstance(relative, str) or not relative or "\x00" in relative:
            raise Refused("invalid-evidence-path")
        rel = Path(relative)
        if rel.is_absolute() or ".." in rel.parts or rel.suffix == ".jsonl":
            raise Refused("escaped-or-body-path")
        path = self.room / rel
        parent = self.room
        for part in rel.parts[:-1]:
            parent = parent / part
            if not stat.S_ISDIR(parent.lstat().st_mode):
                raise Refused("unsafe-evidence-parent")
        if path.resolve() != path:
            raise Refused("linked-evidence-path")
        return path

    def read(self, relative, limit=LIMIT):
        path = self.path(relative)
        before = self.notice.private_node(path)
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, "rb") as handle:
            opened = os.fstat(handle.fileno())
            if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino):
                raise Refused("evidence-replaced")
            raw = handle.read(limit + 1)
            after = os.fstat(handle.fileno())
        if len(raw) > limit:
            raise Refused("oversized-evidence")
        fields = lambda node: (node.st_dev, node.st_ino, node.st_size, node.st_mtime_ns, node.st_ctime_ns)
        fingerprint = (fields(after), digest(raw))
        if fields(before) != fields(after) or (relative in self.seen and self.seen[relative] != fingerprint):
            raise Refused("evidence-changed")
        self.seen[relative] = fingerprint
        return raw

    def object(self, relative, limit=LIMIT):
        return self.notice.decode(self.read(relative, limit))

    def reference(self, value):
        if (not isinstance(value, dict) or set(value) != {"path", "sha256"}
                or not isinstance(value["sha256"], str) or not DIGEST.fullmatch(value["sha256"])):
            raise Refused("invalid-evidence-reference")
        raw = self.read(value["path"], SMALL)
        if not raw.strip() or digest(raw) != value["sha256"]:
            raise Refused("evidence-hash-mismatch")
        return raw

    def unchanged(self):
        self.notice.private_node(self.room, True)
        for relative in list(self.seen):
            self.read(relative)
        for relative in self.state_inputs:
            self.no_pending_state(relative)

    def no_pending_state(self, relative):
        path = self.path(relative)
        if any(item.name.startswith(".state.") for item in path.parent.iterdir()):
            raise Refused("pending-closeout-state")
        self.state_inputs.add(relative)


def trigger(args, evidence, notice):
    if not notice.KEY.fullmatch(args.key or "") or not notice.KEY.fullmatch(args.writer or ""):
        raise Refused("exact-resident-and-writer-required")
    if args.key == args.writer:
        raise Refused("self-rotation-refused")
    registry = evidence.object("ops/etc/resident-identities.json")
    identities = registry.get("identities")
    if not isinstance(identities, list):
        raise Refused("invalid-registry")
    # This slice admits invented fixtures only, never an actual native binding.
    if any(not isinstance(item, dict) or not isinstance(item.get("session_id"), str)
           or not item["session_id"].startswith("0000") for item in identities):
        raise Refused("synthetic-identities-required")
    raw = evidence.read(args.gauge_row, SMALL)
    row, band, binding = notice.measurement(raw, evidence.path("ops/etc/resident-identities.json"), args.key)
    resident = [item for item in identities if item.get("key") == args.key]
    writer = [item for item in identities if item.get("key") == args.writer]
    if len(resident) != 1 or len(writer) != 1 or resident[0].get("room") != str(evidence.room):
        raise Refused("resident-room-or-writer-mismatch")
    if row["provider"] not in ("claude", "codex"):
        raise Refused("provider-preflight-unsupported")
    if (not isinstance(args.destination, str) or not notice.SID.fullmatch(args.destination)
            or not args.destination.startswith("0000")
            or any(item["session_id"] == args.destination for item in identities)):
        raise Refused("synthetic-unregistered-destination-required")
    closeout = notice.sibling("closeout")
    if row["tokens"] < Fraction(str(closeout.DUE)) * row["window"]:
        raise Refused("rotation-line-not-reached")
    evidence.no_pending_state(args.closeout_state)
    state_raw = evidence.read(args.closeout_state)
    entry = notice.decode(state_raw).get(row["session_id"])
    if (not isinstance(entry, dict) or entry.get("key") != args.key
            or type(entry.get("band")) is not int or band is None
            or not 0 <= entry["band"] <= band or type(entry.get("unknown")) is not int
            or entry["unknown"] != 0):
        raise Refused("closeout-state-unproved")
    return row, binding, {"gauge_sha256": digest(raw), "closeout_sha256": digest(state_raw),
                          "destination_sha256": digest(args.destination.encode("ascii"))}


def closing(args, evidence, notice, row, binding, inputs):
    record = evidence.object(args.closing_record, SMALL)
    expected = {"schema": "rotate-closing/1", "key": args.key, "writer": args.writer,
                "binding": binding, "tier": "B", **inputs}
    if any(record.get(key) != value for key, value in expected.items()):
        raise Refused("closing-record-mismatch")
    if notice.stamp(record.get("closed_at")) < notice.stamp(row["reading_at"]):
        raise Refused("closing-record-predates-reading")
    evidence.reference(record.get("handoff"))
    mind = record.get("mind")
    if (not isinstance(mind, dict) or type(mind.get("proposed")) is not int
            or not 0 <= mind["proposed"] <= 3 or not isinstance(mind.get("leaf_sha256"), str)
            or not DIGEST.fullmatch(mind["leaf_sha256"])):
        raise Refused("mind-disposition-unproved")
    if mind["proposed"] == 0:
        if mind.get("decision") != "none-proposed" or mind.get("approval") is not None:
            raise Refused("mind-disposition-unproved")
    else:
        if mind.get("decision") != "approved-and-written":
            raise Refused("mind-disposition-unproved")
        evidence.reference(mind.get("approval"))
    return {"sha256": mind["leaf_sha256"], "proposed": mind["proposed"],
            "not_before": row["reading_at"], "not_after": record["closed_at"]}


def mind_ready(args, evidence, expected):
    evidence.read("MIND.md", SMALL)
    archives = evidence.path("archives")
    evidence.notice.private_node(archives, True)
    for leaf in archives.iterdir():
        if leaf.name.startswith("MIND-"):
            evidence.read("archives/" + leaf.name)
    mind = sibling("mind")
    output, errors = io.StringIO(), io.StringIO()
    # This is the existing read-only show --ref path, not a copied verifier.
    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
        rc = mind.main(["--room", str(evidence.room), "--registry",
                        str(evidence.path("ops/etc/resident-identities.json")), "show", args.key, "--ref"])
    if rc != 0:
        raise Refused("mind-show-ref-refused")
    match = re.fullmatch(r"leaf=(archives/MIND-[a-z0-9-]+\.md)\|sha256=([0-9a-f]{64})\n", output.getvalue())
    if match is None:
        raise Refused("invalid-mind-reference")
    leaf, sha = match.groups()
    raw = evidence.read(leaf)
    if sha != expected["sha256"] or digest(raw) != sha:
        raise Refused("closing-mind-mismatch")
    if expected["proposed"]:
        head, entries = mind.parse_leaf(raw.decode("utf-8"))
        stamp = evidence.notice.stamp
        if not stamp(expected["not_before"]) <= stamp(head["written"]) <= stamp(expected["not_after"]):
            raise Refused("new-mind-write-unproved")
        previous = []
        if head["predecessor"] != "none":
            predecessor = mind.PRED_RE.fullmatch(head["predecessor"])
            if predecessor is None:
                raise Refused("new-mind-write-unproved")
            _, previous = mind.parse_leaf(evidence.read(predecessor.group(1)).decode("utf-8"))
        added, amended, _ = mind.difference(previous, entries)
        if len(added) + len(amended) != expected["proposed"]:
            raise Refused("new-mind-entry-count-mismatch")
    return {"leaf": leaf, "sha256": sha}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="rotate", description="Synthetic read-only rotation preflight; no live mode")
    ap.add_argument("--phase", type=int, choices=range(10), default=0)
    ap.add_argument("--dry-run", action="store_true", default=True, help="the default and only supported mode")
    ap.add_argument("--room", type=Path, help="explicit existing synthetic room; never defaults to the live room")
    ap.add_argument("--key")
    ap.add_argument("--writer")
    ap.add_argument("--destination", help="declared invented spare identifier; no body is opened or verified")
    ap.add_argument("--gauge-row", help="one gauge JSON snapshot, relative to the synthetic room")
    ap.add_argument("--closeout-state", help="closeout state.json, relative to the synthetic room")
    ap.add_argument("--closing-record", help="hash-bound closing evidence, needed for phases 1 and 2")
    return ap


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    result = {"schema": "rotate/1", "phase": args.phase, "name": PHASES[args.phase][0],
              "dry_run": True, "writes": 0, "native_load_proved": False, "operator_accepted": False,
              "completed": [], "next_phase": args.phase + 1 if args.phase < 9 else None}
    if args.phase >= 3:
        result.update(status="unsupported", reason="phase-not-implemented", needs=PHASES[args.phase][1])
        print(json.dumps(result, sort_keys=True))
        return 2
    try:
        if args.room is None or not args.gauge_row or not args.closeout_state:
            raise Refused("explicit-synthetic-evidence-required")
        notice = sibling("notice")
        evidence = Evidence(args.room, notice)
        row, binding, inputs = trigger(args, evidence, notice)
        result["completed"].append(0)
        if args.phase >= 1:
            expected = closing(args, evidence, notice, row, binding, inputs)
            result["completed"].append(1)
        if args.phase == 2:
            result["mind"] = mind_ready(args, evidence, expected)
            result["completed"].append(2)
        evidence.unchanged()
        result.update(status="stop", needs=PHASES[args.phase + 1][1], binding=binding,
                      tier="B", destination_sha256=inputs["destination_sha256"],
                      destination_proof="declared identifier only; native checks unimplemented",
                      measurement={key: row[key] for key in ("tokens", "window", "percent", "reading_at",
                                                             "measured_at", "age_seconds", "window_source")},
                      provenance="supplied last-observed snapshot; no fresh telemetry collected",
                      closeout_proof="recorded session state; native card delivery not independently proved",
                      closure_proof="hash-bound declared evidence; operator authorship not authenticated",
                      evidence={name: value[1] for name, value in sorted(evidence.seen.items())})
        rc = 0
    except Exception as exc:
        result.update(status="refused", reason=str(exc) if isinstance(exc, Refused) else "evidence-or-dependency-refused",
                      needs=PHASES[args.phase][1])
        # Do not leak partial leaf references or content when a late check fails.
        result.pop("mind", None)
        rc = 2
    print(json.dumps(result, sort_keys=True))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
