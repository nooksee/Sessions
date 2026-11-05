#!/usr/bin/env python3
"""rotate: dry-run phase gates in an explicitly synthetic room.

Generated with ops/bin/template; implemented by Joe Codex. Phases 0 to 4
inspect synthetic evidence; phase 5 builds only temporary fixture artifacts.
Phases 6 to 9 refuse. No native bodies, providers, custody or installation.
Spec: docs/ops/specs/scripts/rotate.md. Tests: tools/test/test_rotate.py.
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import os
import re
import stat
import sys
import tempfile
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

    def reference(self, value, limit=SMALL):
        if (not isinstance(value, dict) or set(value) != {"path", "sha256"}
                or not isinstance(value["sha256"], str) or not DIGEST.fullmatch(value["sha256"])):
            raise Refused("invalid-evidence-reference")
        raw = self.read(value["path"], limit)
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


def require(condition, reason):
    if not condition:
        raise Refused(reason)


def build_plan(args, evidence, binding):
    plan = evidence.object(args.build_plan, SMALL)
    expected = {"schema": "rotate-build/1", "key": args.key, "writer": args.writer,
                "binding": binding, "closing_sha256": digest(evidence.read(args.closing_record, SMALL))}
    require(all(plan.get(k) == v for k, v in expected.items()), "build-plan-mismatch")
    require(not any(p.name.startswith(".rotate-build.") for p in evidence.room.iterdir()),
            "pending-synthetic-build")
    return plan


def no_fixture_holders(path):
    """Existing holder reader, with a same-user observability preflight.

    Private fixtures exclude other unprivileged users. Privileged hostile
    readers and a writer starting after this check are outside this rehearsal.
    Never run gate.main, which would inspect unrelated live editor state.
    """
    gate = sibling("gate")
    for entry in gate.PROC.iterdir():
        if not entry.name.isdigit():
            continue
        try:
            if entry.stat().st_uid != os.geteuid():
                continue
            for fd in list((entry / "fd").iterdir()):
                try:
                    os.readlink(fd)
                except FileNotFoundError:
                    continue
        except FileNotFoundError:
            continue
        except OSError:
            raise Refused("fixture-holder-evidence-unavailable") from None
    require(not gate.holders(path), "synthetic-destination-held")


def destination_ready(args, evidence, row, plan):
    spare = evidence.notice.decode(evidence.reference(plan.get("destination")))
    registry = evidence.object("ops/etc/resident-identities.json")["identities"]
    identity = next(item for item in registry if item["key"] == args.key)
    plain = identity.get("role", "") + " (" + identity.get("person", "") + ")"
    expected = {"schema": "rotate-spare/1", "provider": row["provider"],
                "session_id": args.destination, "room": str(evidence.room), "cwd": str(evidence.room),
                "label": plain + " - spare body, do not open", "owner": None}
    require(all(k in spare and spare[k] == v for k, v in expected.items()), "synthetic-spare-mismatch")
    require(bool(identity.get("role")) and bool(identity.get("person"))
            and spare.get("fresh") is True and type(spare.get("work_rows")) is int
            and spare["work_rows"] == 0, "synthetic-spare-not-fresh")
    closed = evidence.object(args.closing_record, SMALL)
    require(evidence.notice.stamp(spare.get("created_at")) >= evidence.notice.stamp(closed["closed_at"]),
            "synthetic-spare-predates-closeout")
    require(evidence.notice.stamp(plan.get("built_at")) >= evidence.notice.stamp(spare["created_at"]),
            "synthetic-build-predates-spare")
    path = evidence.path(plan["destination"]["path"])
    no_fixture_holders(path)
    return {"identity": identity, "plain": plain, "spare_path": path}


def synthetic_rows(evidence, reference, donor):
    require(isinstance(reference, dict) and isinstance(reference.get("path"), str)
            and reference["path"].endswith(".fixture"), "synthetic-body-extension-required")
    raw = evidence.reference(reference, LIMIT)
    require(raw.endswith(b"\n") and bool(raw.strip()), "synthetic-body-not-terminated")
    rows = [evidence.notice.decode(line) for line in raw.splitlines()]
    require(1 <= len(rows) <= 4096, "synthetic-body-row-bound")

    def inspect(value, key=None):
        if isinstance(value, dict):
            for k, v in value.items():
                inspect(v, k)
        elif isinstance(value, list):
            for item in value:
                inspect(item, key)
        elif isinstance(value, str):
            # Refuse imported native identifiers even in fixture prose.
            ids = re.findall(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", value)
            require(all(item.startswith("0000") for item in ids), "nonfixture-body-identifier")
            if key in ("sessionId", "session_id"):
                require(value == donor, "synthetic-body-identity-mismatch")
            if key in ("uuid", "parentUuid"):
                require(bool(evidence.notice.SID.fullmatch(value)) and value.startswith("0000"),
                        "nonfixture-message-identifier")
    inspect(rows)
    require(all(r.get("sessionId") == donor for r in rows), "synthetic-body-identity-mismatch")
    return rows, raw


def user_prompt(row):
    message = row.get("message")
    if (row.get("type") != "user" or not isinstance(message, dict) or message.get("role") != "user"
            or row.get("isMeta") or row.get("isSidechain") or row.get("isCompactSummary")):
        return False
    content = message.get("content")
    if isinstance(content, list):
        if any(not isinstance(b, dict) or b.get("type") != "text" for b in content):
            return False
        content = "\n".join(b.get("text", "") for b in content)
    if not isinstance(content, str) or not content.strip():
        return False
    return not content.lstrip().startswith(("<", "/", "# Context from my IDE", "Rotate now", "Close out now"))


def window_ready(args, evidence, row, plan):
    # The accepted Codex ingredient explicitly omits the native summary.
    require(row["provider"] == "claude", "provider-window-build-unsupported")
    rows, raw = synthetic_rows(evidence, plan.get("donor"), row["session_id"])
    gauge = sibling("gauge")
    reading = gauge.read_claude(evidence.path(plan["donor"]["path"]))
    require(all(reading.get(k) == row.get(k) for k in ("tokens", "model", "reading_at"))
            and bool(row.get("model")) and not reading.get("compaction_after"), "donor-usage-mismatch")
    marks = [i for i, r in enumerate(rows) if r.get("type") == "system" and r.get("subtype") == "compact_boundary"]
    require(bool(marks), "synthetic-boundary-required")
    boundary = marks[-1]
    cut = plan.get("cut")
    require(isinstance(cut, dict) and type(cut.get("user_row")) is int
            and type(cut.get("exchange_row")) is int, "cut-indices-required")
    start, exchange = cut["user_row"], cut["exchange_row"]
    require(boundary < start <= exchange < len(rows) and user_prompt(rows[start])
            and user_prompt(rows[exchange]), "genuine-user-cut-required")
    require(any(r.get("type") == "assistant" and (r.get("message") or {}).get("role") == "assistant"
                and not r.get("isMeta") and not r.get("isSidechain")
                for r in rows[exchange + 1:]), "substantive-exchange-required")
    summaries = [i for i in range(boundary + 1, start) if rows[i].get("isCompactSummary") is True]
    require(len(summaries) == 1, "exact-compaction-summary-required")
    reason = evidence.reference(cut.get("reason"))
    estimate = evidence.notice.decode(evidence.reference(cut.get("estimate")))
    require(estimate.get("schema") == "rotate-estimate/1"
            and estimate.get("donor_sha256") == digest(raw) and estimate.get("cut_row") == start
            and estimate.get("window") == row["window"] and type(estimate.get("tokens")) is int
            and 0 < estimate["tokens"] <= Fraction(1, 5) * row["window"]
            and isinstance(estimate.get("method"), str) and bool(estimate["method"].strip()),
            "wake-estimate-unproved-or-over-budget")
    selected = copy.deepcopy([rows[boundary], rows[summaries[0]], *rows[start:]])
    require(selected[0].get("parentUuid") is None, "boundary-not-root")
    require(isinstance(selected[1].get("uuid"), str) and isinstance(selected[2].get("uuid"), str),
            "window-parent-evidence-required")
    # Only the cut's parent link changes; carried prose and summary stay intact.
    selected[2]["parentUuid"] = selected[1]["uuid"]
    return {"rows": selected, "start": start, "boundary": boundary, "summary": summaries[0], "built_at": plan["built_at"],
            "donor_sha256": digest(raw), "reason_sha256": digest(reason), "estimate": estimate}


def capsule_text(args, evidence, mind_ref, admission, plan):
    leaf = evidence.read(mind_ref["leaf"]).decode("utf-8")
    transition = evidence.reference(plan.get("transition")).decode("utf-8")
    require(not transition.lstrip().startswith(("/", "archives/", "storage/")), "transition-text-required")
    identity = admission["identity"]
    return ("Registry\nYou are `" + admission["plain"] + "`.\nResident: " + args.key
            + "\nRoom: " + str(evidence.room) + "\nDestination container: " + args.destination
            + "\n\nMind\n" + leaf + "\nTransition\n" + transition
            + "\nFirst turn\nThe room's status in a few lines, then speak as yourself.\n")


def static_gates(raw, rows, args, evidence, capsule, media_dir, externalizer, window):
    results = {}

    def check(name, value):
        results[name] = bool(value)
        require(bool(value), "static-" + name)

    check("terminated", raw.endswith(b"\n"))
    parsed = [evidence.notice.decode(line) for line in raw.splitlines()]
    check("parse", parsed == rows)
    ids, uuids, seen, orientations = [], [], set(), []
    pending = set()
    inline = 0
    pointers = []

    def walk(value, key=None):
        nonlocal inline
        if isinstance(value, dict):
            if value.get("type") == "tool_use":
                token = value.get("id")
                check("tool-use-unique", isinstance(token, str) and token not in pending)
                pending.add(token)
            if value.get("type") == "tool_result":
                token = value.get("tool_use_id")
                check("tool-result-matched", token in pending)
                pending.remove(token)
            if value.get("type") == "input_image" or (value.get("type") in ("image", "document") and "source" in value):
                inline += 1
            source = value.get("source")
            if isinstance(source, dict) and isinstance(source.get("data"), str) and source["data"]:
                inline += 1
            if isinstance(value.get("base64"), str) and value["base64"] and not value["base64"].startswith("[media externalized "):
                inline += 1
            for k, v in value.items():
                walk(v, k)
        elif isinstance(value, list):
            for item in value:
                walk(item, key)
        elif key in ("sessionId", "session_id"):
            ids.append(value)
        elif isinstance(value, str) and value.startswith("[media externalized "):
            pointers.append(value)
    for row in rows:
        walk(row)
        if row.get("uuid"):
            check("unique-message-ids", row["uuid"] not in seen)
            uuids.append(row["uuid"])
            check("parent-chain", row.get("parentUuid") is None if len(uuids) == 1 else row.get("parentUuid") in seen)
            seen.add(row["uuid"])
        message = row.get("message")
        if isinstance(message, dict) and isinstance(message.get("content"), str) and message["content"].lstrip().startswith("<session_clinic_orientation>"):
            orientations.append(row)
    check("identities", bool(ids) and set(ids) == {args.destination})
    successor = sibling("successor")
    donor = evidence.object("ops/etc/resident-identities.json")["identities"]
    donor_id = next(i["session_id"] for i in donor if i["key"] == args.key)
    check("donor-structural-residue", successor.count_residue(rows, donor_id)[0] == 0)
    check("unique-message-ids", bool(uuids) and len(uuids) == len(set(uuids)))
    check("boundary-head", rows[0].get("type") == "system" and rows[0].get("subtype") == "compact_boundary")
    check("tool-pairs", not pending)
    check("orientation-count", len(orientations) == 1)
    orientation = orientations[0]
    check("orientation-text", orientation["message"]["content"] == "<session_clinic_orientation>\n" + capsule + "\n</session_clinic_orientation>")
    check("destination-named", args.destination in orientation["message"]["content"])
    check("orientation-time", orientation.get("timestamp") == window["built_at"])
    check("working-directory", orientation.get("cwd") == str(evidence.room))
    plain = next(i["role"] + " (" + i["person"] + ")" for i in donor if i["key"] == args.key)
    check("plain-label-last", [r.get("type") for r in rows[-2:]] == ["custom-title", "agent-name"]
          and rows[-2].get("customTitle") == plain and rows[-1].get("agentName") == plain)
    check("inline-media", inline == 0 and externalizer.failed == 0)
    mind = sibling("mind")
    check("orientation-privacy", not mind.MEDICAL_RE.search(capsule) and not mind.SECRET_RE.search(capsule))
    # Every externalizer-produced pointer must have a private file whose
    # digest agrees with the producer's full digest, not just its short name.
    for sha, name in externalizer.seen.items():
        path = media_dir / name
        evidence.notice.private_node(path)
        check("media-pointer", path.parent == media_dir and digest(path.read_bytes()) == sha)
    check("media-pointer-count", externalizer.blocks == 0 or bool(externalizer.seen))
    check("media-pointer-links", len(pointers) == externalizer.blocks
          and all(any("preserved at " + str(media_dir / name) + "]" in pointer
                      for name in externalizer.seen.values()) for pointer in pointers))
    check("carried-window", len(rows) == len(window["rows"]) + 3)

    def text_items(items):
        texts = []
        for item in items:
            content = (item.get("message") or {}).get("content")
            if isinstance(content, str):
                texts.append(content)
            elif isinstance(content, list):
                texts.extend(block["text"] for block in content
                             if isinstance(block, dict) and block.get("type") == "text"
                             and isinstance(block.get("text"), str)
                             and not block["text"].startswith("[media externalized "))
        return texts
    check("carried-text", text_items(rows[:len(window["rows"])]) == text_items(window["rows"]))
    return results


def build_preview(args, evidence, mind_ref, admission, plan, window, result):
    capsule = capsule_text(args, evidence, mind_ref, admission, plan)
    evidence.unchanged()
    no_fixture_holders(admission["spare_path"])
    # Actual existing Claude builder and externalizer, in disposable private
    # fixture staging only. No caller-selected output or production path.
    old_umask = os.umask(0o077)
    try:
        with tempfile.TemporaryDirectory(prefix=".rotate-build.", dir=evidence.room) as tmp:
            stage = Path(tmp)
            media_dir = stage / "media"
            media_dir.mkdir(mode=0o700)
            selected = stage / "donor.fixture"
            output = stage / "candidate.fixture"
            selected.write_bytes(b"".join(json.dumps(r, separators=(",", ":")).encode() + b"\n" for r in window["rows"]))
            builder = sibling("successor")
            argv = ["successor", "--donor", str(selected), "--out", str(output), "--session-id", args.destination,
                    "--cwd", str(evidence.room), "--orientation", capsule, "--trim-to-last-compaction"]
            try:
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    saved_argv = sys.argv
                    try:
                        sys.argv = argv
                        try:
                            builder.main()
                        except SystemExit:
                            raise Refused("synthetic-builder-refused") from None
                    finally:
                        sys.argv = saved_argv
                rows = [evidence.notice.decode(line) for line in output.read_bytes().splitlines()]
                # Only the newly constructed orientation receives the bound
                # fixture build time; historical donor timestamps stay intact.
                rows[-1]["timestamp"] = plan["built_at"]
                externalizer = sibling("media").Externalizer(media_dir, str(media_dir), "synthetic-rehearsal")
                for r in rows:
                    externalizer.walk(r)
                for kind, field in (("custom-title", "customTitle"), ("agent-name", "agentName")):
                    rows.append({"type": kind, field: admission["plain"], "sessionId": args.destination,
                                 "timestamp": plan["built_at"]})
                raw = b"".join(json.dumps(r, separators=(",", ":")).encode() + b"\n" for r in rows)
                output.write_bytes(raw)
                gates = static_gates(raw, rows, args, evidence, capsule, media_dir, externalizer, window)
                for path in (selected, output, *media_dir.iterdir()):
                    evidence.notice.private_node(path)
                evidence.unchanged()
                no_fixture_holders(admission["spare_path"])
                preview = {"sha256": digest(raw), "bytes": len(raw), "rows": len(rows), "gates": gates,
                           "capsule_sha256": digest(capsule.encode()), "mind_sha256": mind_ref["sha256"],
                           "media_files": externalizer.written, "media_blocks": externalizer.blocks,
                           "artifacts_retained": False, "native_load_proved": False}
            finally:
                # Counts are created file artifacts, not write syscalls.
                result["writes"] = sum(p.is_file() for p in stage.rglob("*"))
                result["write_scope"] = "temporary synthetic file artifacts; removed before return"
        result["temporary_artifacts_removed"] = True
    finally:
        os.umask(old_umask)
    return preview


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="rotate", description="Synthetic dry-run rotation rehearsal; no live mode")
    ap.add_argument("--phase", type=int, choices=range(10), default=0)
    ap.add_argument("--dry-run", action="store_true", default=True, help="the default and only supported mode")
    ap.add_argument("--room", type=Path, help="explicit existing synthetic room; never defaults to the live room")
    ap.add_argument("--key")
    ap.add_argument("--writer")
    ap.add_argument("--destination", help="declared invented spare identifier; no body is opened or verified")
    ap.add_argument("--gauge-row", help="one gauge JSON snapshot, relative to the synthetic room")
    ap.add_argument("--closeout-state", help="closeout state.json, relative to the synthetic room")
    ap.add_argument("--closing-record", help="hash-bound closing evidence, needed for phases 1 and 2")
    ap.add_argument("--build-plan", help="hash-bound synthetic spare/window/build plan for phases 3 to 5")
    return ap


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    result = {"schema": "rotate/1", "phase": args.phase, "name": PHASES[args.phase][0],
              "dry_run": True, "writes": 0, "native_load_proved": False, "operator_accepted": False,
              "completed": [], "next_phase": args.phase + 1 if args.phase < 9 else None}
    if args.phase >= 6:
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
        if args.phase >= 2:
            result["mind"] = mind_ready(args, evidence, expected)
            result["completed"].append(2)
        if args.phase >= 3:
            plan = build_plan(args, evidence, binding)
            admission = destination_ready(args, evidence, row, plan)
            result["completed"].append(3)
            result["destination_proof"] = "synthetic spare metadata and current observable holders only; not native admission"
        if args.phase >= 4:
            window = window_ready(args, evidence, row, plan)
            result["window"] = {k: window[k] for k in ("start", "boundary", "summary", "donor_sha256", "reason_sha256")}
            result["window"]["estimate"] = {"tokens": window["estimate"]["tokens"], "window": row["window"],
                                            "provenance": "hash-bound supplied estimate, not a native wake measurement"}
            result["completed"].append(4)
        if args.phase == 5:
            result["build"] = build_preview(args, evidence, result["mind"], admission, plan, window, result)
            result["completed"].append(5)
        evidence.unchanged()
        result.update(status="stop", needs=PHASES[args.phase + 1][1], binding=binding,
                      tier="B", destination_sha256=inputs["destination_sha256"],
                      measurement={key: row[key] for key in ("tokens", "window", "percent", "reading_at",
                                                             "measured_at", "age_seconds", "window_source")},
                      provenance="supplied last-observed snapshot; no fresh telemetry collected",
                      closeout_proof="recorded session state; native card delivery not independently proved",
                      closure_proof="hash-bound declared evidence; operator authorship not authenticated",
                      evidence={name: value[1] for name, value in sorted(evidence.seen.items())})
        rc = 0
        result.setdefault("destination_proof", "declared identifier only; native checks unimplemented")
    except Exception as exc:
        result.update(status="refused", reason=str(exc) if isinstance(exc, Refused) else "evidence-or-dependency-refused",
                      needs=PHASES[args.phase][1])
        # Do not leak partial leaf references or content when a late check fails.
        result.pop("mind", None)
        result.pop("build", None)
        rc = 2
    print(json.dumps(result, sort_keys=True))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
