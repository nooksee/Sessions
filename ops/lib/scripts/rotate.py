#!/usr/bin/env python3
"""rotate: dry-run phase gates in an explicitly synthetic room.

Generated with ops/bin/template; implemented by Joe Codex. Phases 0 to 4
inspect synthetic evidence; phases 5 to 9 use disposable fixture artifacts.
No native bodies, providers, physical custody or production installation.
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
import subprocess
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
NATIVE_GO = {
    "disposable-exercise": "named-disposable-exercise-go-required-native-unimplemented",
    "compact": "operator-compaction-only-native-unimplemented",
    "rotation": "named-resident-rotation-go-required-native-unimplemented",
    "hold": "named-native-hold-go-required-native-unimplemented",
    "custody": "named-native-custody-go-required-native-unimplemented",
    "install": "post-custody-replacement-go-required-native-unimplemented",
    "load": "named-native-load-go-required-native-unimplemented",
    "rollback": "named-native-rollback-go-required-native-unimplemented",
    "donor-disposition": "named-donor-disposition-go-required-native-unimplemented",
}
NATIVE_PHASE = {6: "custody", 7: "install", 8: "load", 9: "donor-disposition"}
FIRST_PROMPT = "Disposable rotation exercise: reply READY only; no tools, files or network."


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


def adapter_boundary(args):
    """Pure refusal only: never inspect a native path or interpret a go."""
    if args.native_action is not None:
        raise Refused(NATIVE_GO[args.native_action])
    if args.adapter == "codex":
        raise Refused("codex-summary-active-window-and-loader-proof-required")
    if args.adapter == "claude" and args.phase in NATIVE_PHASE:
        raise Refused(NATIVE_GO[NATIVE_PHASE[args.phase]])


def claude_contract(args, evidence, row, binding, inputs):
    """Rehearse admission on invented resident fixtures, never native bodies."""
    require(row["provider"] == "claude", "claude-adapter-provider-required")
    plan = evidence.object(args.adapter_plan, SMALL)
    expected = {"schema": "rotate-claude-adapter/1", "kind": "registered-fixture",
                "key": args.key, "writer": args.writer, "binding": binding, **inputs}
    for field, value in expected.items():
        require(plan.get(field) == value, "claude-adapter-" + field.replace("_", "-") + "-mismatch")
    version = plan.get("provider_version")
    require(isinstance(version, str) and 0 < len(version.strip()) <= 64,
            "claude-provider-version-required")
    evidence.process_model = plan.get("process_model")
    fixture_holders(evidence, evidence.path(".rotate-synthetic.json"))
    require(not evidence.notice.decode(evidence.reference(evidence.process_model))["holders"],
            "claude-writers-not-closed")
    return plan


def claude_destination(args, evidence, plan, admission):
    rows, raw = synthetic_rows(evidence, plan.get("pristine"), args.destination)
    require([r.get("type") for r in rows] == ["custom-title", "user", "assistant"],
            "claude-first-exchange-required")
    require(all(r.get("cwd") == str(evidence.room) for r in rows), "claude-first-exchange-room")
    require(rows[0].get("customTitle") == admission["plain"] + " - spare body, do not open",
            "claude-first-exchange-label")
    require(rows[1].get("message") == {"role": "user", "content": FIRST_PROMPT},
            "claude-first-prompt-not-inert")
    require(rows[2].get("message") == {"role": "assistant", "content": "READY"},
            "claude-first-reply-not-inert")
    require(isinstance(rows[1].get("uuid"), str) and rows[1].get("parentUuid") is None,
            "claude-first-prompt-chain")
    require(isinstance(rows[2].get("uuid"), str) and rows[2]["uuid"] != rows[1]["uuid"]
            and rows[2].get("parentUuid") == rows[1]["uuid"], "claude-first-reply-chain")
    stamp = evidence.notice.stamp
    spare = evidence.notice.decode(evidence.reference(plan["destination_metadata"]))
    require(stamp(spare["created_at"]) <= stamp(rows[1].get("timestamp"))
            <= stamp(rows[2].get("timestamp")) <= stamp(plan["built_at"]),
            "claude-first-exchange-time")
    return {"sha256": digest(raw), "bytes": len(raw), "native_admission_proved": False}


def claude_window(args, evidence, row, plan, build, inputs):
    record = evidence.notice.decode(evidence.reference(plan.get("compaction")))
    for field, value in {"schema": "rotate-compaction-fixture/1", "actor": "operator",
                         "method": "supported-interface", "before_gauge_sha256": inputs["gauge_sha256"]}.items():
        require(record.get(field) == value, "claude-compaction-" + field + "-mismatch")
    stamp = evidence.notice.stamp
    at = stamp(record.get("at"))
    closed = evidence.object(args.closing_record, SMALL)
    require(stamp(row["reading_at"]) < at < stamp(closed["closed_at"]),
            "claude-compaction-outside-closing-seam")
    raw = evidence.reference(record.get("after_gauge"), SMALL)
    after, _, _ = evidence.notice.measurement(raw, evidence.path("ops/etc/resident-identities.json"), args.key)
    require(after["provider"] == "claude", "claude-post-compaction-provider")
    require(after["window"] == row["window"], "claude-post-compaction-window")
    require(at <= stamp(after["reading_at"]) <= stamp(closed["closed_at"]),
            "claude-post-compaction-reading-time")
    window = window_ready(args, evidence, after, build)
    require(stamp(window["rows"][0].get("timestamp")) == at, "claude-compaction-boundary-time")
    require(at <= stamp(window["rows"][1].get("timestamp"))
            <= stamp(window["rows"][2].get("timestamp")), "claude-summary-time")
    return window


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


def fixture_holders(evidence, path, allow_held=False):
    """Later slices use only the explicitly supplied process model."""
    if not hasattr(evidence, "process_model"):
        no_fixture_holders(path)
        return False
    model = evidence.notice.decode(evidence.reference(evidence.process_model))
    require(model.get("schema") == "rotate-process/1", "process-model-schema")
    require(model.get("observable") is True, "process-model-unobservable")
    holders = model.get("holders")
    records = model.get("session_records")
    require(isinstance(holders, list) and isinstance(records, list), "process-model-lists")
    confined = [evidence.path(name) for name in holders + records]
    held = path in confined
    require(allow_held or not held, "synthetic-destination-held")
    return held


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
    fixture_holders(evidence, path)
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


def build_preview(args, evidence, mind_ref, admission, plan, window, result, continuation=None):
    capsule = capsule_text(args, evidence, mind_ref, admission, plan)
    evidence.unchanged()
    fixture_holders(evidence, admission["spare_path"])
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
                fixture_holders(evidence, admission["spare_path"])
                preview = {"sha256": digest(raw), "bytes": len(raw), "rows": len(rows), "gates": gates,
                           "capsule_sha256": digest(capsule.encode()), "mind_sha256": mind_ref["sha256"],
                           "media_files": externalizer.written, "media_blocks": externalizer.blocks,
                           "artifacts_retained": False, "native_load_proved": False}
                if continuation is not None:
                    continuation(stage, output, capsule, media_dir, externalizer, preview)
            finally:
                # Count the files present for disposal, not all creations,
                # logical operations or write syscalls (close can unlink).
                result["writes"] = sum(p.is_file() for p in stage.rglob("*"))
                result["write_scope"] = "temporary synthetic file artifacts present at cleanup; not total creations or syscalls"
        result["temporary_artifacts_removed"] = True
    finally:
        os.umask(old_umask)
    return preview


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def node_id(node):
    return (node.st_dev, node.st_ino, node.st_uid, node.st_gid, node.st_mode,
            node.st_nlink, node.st_size, node.st_mtime_ns, node.st_ctime_ns)


def private_write(path, raw, notice, owner=None):
    """Exclusive private staging; all callers select paths in owned staging."""
    notice.parent_chain(path.parent)
    require(not path.exists() and not path.is_symlink(), "staged-target-exists")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as handle:
        if owner is not None:
            os.fchown(handle.fileno(), *owner)
        os.fchmod(handle.fileno(), 0o600)
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    after = notice.private_node(path)
    require(owner is None or (after.st_uid, after.st_gid) == owner, "staged-ownership-mismatch")
    require(digest(path.read_bytes()) == digest(raw), "staged-hash-mismatch")
    return node_id(after)


def replace_private(path, raw, notice, expected, on_publish=None):
    """Guarded same-directory replacement of a disposable runtime fixture."""
    notice.parent_chain(path.parent)
    before = notice.private_node(path)
    require(node_id(before) == expected[0], "swap-preimage-identity")
    require(digest(path.read_bytes()) == expected[1], "swap-preimage-hash")
    staged = path.with_name(path.name + ".swap")
    owner = (before.st_uid, before.st_gid)
    staged_identity = private_write(staged, raw, notice, owner)
    require(node_id(notice.private_node(path)) == expected[0], "swap-preimage-changed")
    os.replace(staged, path)
    after = notice.private_node(path)
    require((after.st_dev, after.st_ino) == staged_identity[:2], "swap-postimage-identity")
    require((after.st_uid, after.st_gid) == owner, "swap-postimage-ownership")
    require(digest(path.read_bytes()) == digest(raw), "swap-postimage-hash")
    # Only a verified postimage can become authority for a later inverse.
    if on_publish is not None:
        on_publish((node_id(after), digest(raw)))
    return (node_id(after), digest(raw))


def operation_plan(args, evidence, binding):
    operation = evidence.object(args.operation_plan, SMALL)
    expected = {"schema": "rotate-operation/1", "key": args.key, "writer": args.writer,
                "binding": binding, "build_sha256": digest(evidence.read(args.build_plan, SMALL))}
    require(all(operation.get(k) == v for k, v in expected.items()), "operation-plan-mismatch")
    evidence.process_model = operation.get("process_model")
    # Prove the model before phase 3, so these slices never inspect /proc.
    fixture_holders(evidence, evidence.path(".rotate-synthetic.json"))
    return operation


def custody_verify(tiers, files, notice):
    manifest = b"".join((digest(raw) + "  " + name + "\n").encode()
                        for name, raw in sorted(files.items()))
    for tier in tiers:
        notice.private_node(tier, True)
        require({p.name for p in tier.iterdir()} == set(files) | {"SHA256SUMS"}, "custody-inventory")
        notice.private_node(tier / "SHA256SUMS")
        require((tier / "SHA256SUMS").read_bytes() == manifest, "custody-manifest")
        for name, raw in files.items():
            path = tier / name
            notice.private_node(path)
            require(digest(path.read_bytes()) == digest(raw), "custody-file-hash")
    return digest(manifest)


def fixture_go(args, evidence, operation, pristine):
    word = evidence.notice.decode(evidence.reference(operation.get("go")))
    expected = {"schema": "rotate-go/1", "key": args.key, "writer": args.writer,
                "container": args.destination, "room": str(evidence.room),
                "size": len(pristine), "custody_sha256": digest(pristine),
                "rollback": "restore-pristine-and-hold", "after_phase": 6}
    require(all(word.get(k) == v for k, v in expected.items()), "replacement-go-mismatch")
    require(type(word.get("size")) is int and type(word.get("after_phase")) is int, "replacement-go-types")
    require(evidence.notice.stamp(word.get("at")) > evidence.notice.stamp(operation.get("custody_at")),
            "replacement-go-predates-custody")
    require(word.get("word") == "go", "replacement-declined")
    return word


def six_agreements(args, notice, paths, plain):
    registry = notice.decode(paths["registry"].read_bytes())["identities"]
    identity = [r for r in registry if r.get("key") == args.key]
    require(len(identity) == 1, "join-registry-ambiguous")
    binding = notice.decode(paths["binding"].read_bytes())
    raw = paths["destination"].read_bytes()
    require(raw.endswith(b"\n"), "join-body-termination")
    rows = [notice.decode(line) for line in raw.splitlines()]
    titles = [r.get("customTitle") for r in rows if r.get("type") == "custom-title"]
    names = [r.get("agentName") for r in rows if r.get("type") == "agent-name"]
    tests = {
        "registry-id": identity[0].get("session_id") == args.destination,
        "binding-id": binding.get("session_id") == args.destination,
        "body-id": all(r.get("sessionId") == args.destination for r in rows),
        "root-cwd": binding.get("root") == str(args.room)
                    and all(r.get("cwd") == str(args.room) for r in rows if "cwd" in r),
        "registry-room": identity[0].get("room") == str(args.room),
        "body-label": bool(titles) and bool(names) and titles[-1] == plain and names[-1] == plain,
    }
    for name, ok in tests.items():
        require(ok, "six-way-" + name)
    return tests


def append_proof(args, evidence, operation, paths, admission, go, replace):
    load = evidence.notice.decode(evidence.reference(operation.get("load")))
    require(load.get("schema") == "rotate-load/1", "load-schema")
    require(load.get("loaded") is True, "synthetic-load-failed")
    require(load.get("key") == args.key and load.get("container") == args.destination,
            "load-target-mismatch")
    stamp = evidence.notice.stamp
    require(stamp(load.get("served_at")) >= stamp(go["at"]), "load-predates-go")
    readback = load.get("readback")
    expected = {"key": args.key, "person": admission["identity"]["person"], "room": str(evidence.room)}
    require(readback == expected, "load-readback-mismatch")
    rows, appended = synthetic_rows(evidence, load.get("append"), args.destination)
    require(any(r.get("type") == "assistant" and (r.get("message") or {}).get("role") == "assistant"
                for r in rows), "append-first-reply-required")
    original = paths["destination"].read_bytes()
    combined = original + appended
    all_rows = [evidence.notice.decode(line) for line in combined.splitlines()]
    seen, pending = set(), set()
    def tools(value):
        if isinstance(value, dict):
            if value.get("type") == "tool_use":
                token = value.get("id")
                require(isinstance(token, str) and token not in pending, "append-tool-use")
                pending.add(token)
            if value.get("type") == "tool_result":
                token = value.get("tool_use_id")
                require(token in pending, "append-tool-result")
                pending.remove(token)
            for v in value.values():
                tools(v)
        elif isinstance(value, list):
            for v in value:
                tools(v)
    for row in all_rows:
        if "uuid" in row:
            require(row["uuid"] not in seen, "append-duplicate-message")
            require(row.get("parentUuid") is None if not seen else row.get("parentUuid") in seen,
                    "append-parent-chain")
            seen.add(row["uuid"])
        tools(row)
    require(not pending, "append-unmatched-tools")
    replace("destination", combined)
    measurement_raw = evidence.reference(load.get("gauge"))
    measurement, _, _ = evidence.notice.measurement(measurement_raw, paths["registry"], args.key)
    reading = sibling("gauge").read_claude(paths["destination"])
    require(all(reading.get(k) == measurement.get(k) for k in ("tokens", "model", "reading_at"))
            and not reading.get("compaction_after"), "wake-reading-mismatch")
    require(stamp(measurement["reading_at"]) >= stamp(load["served_at"]), "wake-reading-predates-load")
    acceptance = evidence.notice.decode(evidence.reference(operation.get("acceptance")))
    require(acceptance.get("schema") == "rotate-acceptance/1" and acceptance.get("key") == args.key
            and acceptance.get("container") == args.destination and acceptance.get("word") == "recognize",
            "operator-fixture-acceptance-required")
    require(stamp(acceptance.get("at")) >= stamp(measurement["reading_at"]), "acceptance-predates-wake")
    require(load.get("mind_confirmed") is True, "mind-confirmation-required")
    return {"tokens": measurement["tokens"], "window": measurement["window"],
            "reading_at": measurement["reading_at"], "acceptance_at": acceptance["at"],
            "gauge_sha256": digest(measurement_raw), "native_load_proved": False}


def fixture_receipt(args, evidence, stage, operation, admission, window, preview, outcome, go):
    number = operation.get("rotation")
    require(type(number) is int and number > 0, "rotation-number-required")
    require(type(operation.get("deviations")) is int and operation["deviations"] >= 0, "deviations-count-required")
    wake = outcome["wake"]
    slots = {
        "RESIDENT": admission["plain"] + "; " + args.key, "ROTATION": str(number),
        "DATE": wake["acceptance_at"] + " (synthetic fixture clock)", "WRITER": args.writer,
        "AUTHORITY": "Synthetic go fixture at " + go["at"] + "; not production authority",
        "TIER": "B; synthetic only", "DONOR": window["donor_sha256"],
        "DESTINATION": "Synthetic destination; pristine sha256=" + outcome["pristine_sha256"],
        "CUT_AND_REASON": str(window["start"]) + "; reason sha256=" + window["reason_sha256"],
        "GATES": json.dumps(preview["gates"], sort_keys=True),
        "CUSTODY": "Two synthetic roots, direct reads; manifest sha256=" + outcome["custody_sha256"]
                   + "; not independent physical-drive custody",
        "MIND_LEAF": preview["mind_sha256"], "INSTALL": "Synthetic verified swap; six agreements="
                   + json.dumps(outcome["agreements"], sort_keys=True),
        "ESTIMATE_VS_MEASURED": str(window["estimate"]["tokens"]) + " estimated; " + str(wake["tokens"])
                   + "/" + str(wake["window"]) + " measured from fixture append at " + wake["reading_at"],
        "DEVIATIONS": str(operation["deviations"]),
        "ACCEPTANCE": "Synthetic mechanical append and explicit recognize fixture at " + wake["acceptance_at"]
                      + "; no native or real operator acceptance",
        "ROLLBACK": "restore-pristine-and-hold; rehearsed inverse retained until acceptance",
    }
    command = ["/bin/bash", str(SESSIONS / "ops/bin/template"), "receipt"]
    for key, value in slots.items():
        command.extend(["--slot", key + "=" + value])
    rendered = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              timeout=15, check=False, cwd=stage, env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"})
    require(rendered.returncode == 0 and bool(rendered.stdout.strip()), "receipt-template-refused")
    directory = stage / "archives"
    directory.mkdir(mode=0o700)
    directory = directory / "receipts"
    directory.mkdir(mode=0o700)
    path = directory / (args.key + "-rotation-" + str(number) + ".md")
    private_write(path, rendered.stdout, evidence.notice)
    return {"sha256": digest(rendered.stdout), "bytes": len(rendered.stdout),
            "template": "ops/src/reports/receipt.md.tpl", "artifacts_retained": False}


def late_phases(args, evidence, operation, admission, plan, window, result,
                stage, output, capsule, media_dir, externalizer, preview):
    """Every mutation is on disposable copies, never the supplied inputs."""
    notice = evidence.notice
    require(notice.stamp(operation.get("custody_at")) >= notice.stamp(plan["built_at"]),
            "custody-predates-build")
    pristine_rows, pristine = synthetic_rows(evidence, operation.get("pristine"), args.destination)
    require(all(r.get("type") in ("custom-title", "agent-name", "system") and "message" not in r
                for r in pristine_rows), "pristine-not-empty")
    require(all(r.get("cwd", str(evidence.room)) == str(evidence.room) for r in pristine_rows), "pristine-room")
    require([r.get("customTitle") for r in pristine_rows if r.get("type") == "custom-title"]
            == [admission["plain"] + " - spare body, do not open"], "pristine-label")
    donor_store = evidence.reference(operation.get("donor_store"), LIMIT)
    require(operation["donor_store"]["path"].endswith(".fixture"), "donor-store-fixture-required")
    require(digest(donor_store) == window["donor_sha256"], "donor-store-mismatch")
    binding_raw = evidence.reference(operation.get("binding_preimage"))
    binding = notice.decode(binding_raw)
    donor_id = admission["identity"]["session_id"]
    require(binding == {"schema": "rotate-binding/1", "key": args.key, "session_id": donor_id,
                        "root": str(evidence.room), "provider": "claude"}, "binding-preimage-mismatch")
    launcher_raw = evidence.reference(operation.get("launcher"))
    launcher = notice.decode(launcher_raw)
    require(launcher == {"schema": "rotate-launcher/1", "key": args.key, "hold": False}
            and launcher.get("hold") is False, "launcher-preimage-mismatch")
    registry_raw = evidence.read("ops/etc/resident-identities.json")
    files = {"donor.fixture": donor_store, "destination.fixture": pristine, "successor.fixture": output.read_bytes(),
             "capsule.txt": capsule.encode(), "gates.json": json_bytes(preview["gates"]),
             "registry.json": registry_raw, "binding.json": binding_raw, "launcher.json": launcher_raw}
    for path in media_dir.iterdir():
        files["media-" + path.name] = path.read_bytes()
    runtime = stage / "runtime"
    runtime.mkdir(mode=0o700)
    paths = {key: runtime / name for key, name in (("destination", "destination.fixture"),
             ("registry", "registry.json"), ("binding", "binding.json"), ("donor", "donor.fixture"),
             ("launcher", "launcher.json"))}
    accepted_owner = evidence.path("ops/etc/resident-identities.json").lstat()
    owners = (accepted_owner.st_uid, accepted_owner.st_gid)
    for key, path in paths.items():
        private_write(path, files[path.name], notice, owners if key == "registry" else None)
    hold = json_bytes({**launcher, "hold": True})
    replace_private(paths["launcher"], hold, notice,
                    (node_id(paths["launcher"].lstat()), digest(files["launcher.json"])))
    require(paths["launcher"].read_bytes() == hold, "synthetic-hold-unproved")
    tiers = [stage / "tier-1", stage / "tier-2"]
    manifest = b"".join((digest(raw) + "  " + name + "\n").encode() for name, raw in sorted(files.items()))
    for tier in tiers:
        tier.mkdir(mode=0o700)
        for name, raw in {**files, "SHA256SUMS": manifest}.items():
            private_write(tier / name, raw, notice)
    outcome = {"custody_sha256": custody_verify(tiers, files, notice), "custody_rows_per_tier": len(files),
               "pristine_sha256": digest(pristine), "hold": True, "rollback": False,
               "physical_custody_proved": False, "artifacts_retained": False}
    result["rehearsal"] = outcome
    if args.phase == 6:
        evidence.unchanged()
        return
    changed = {key: (node_id(path.lstat()), digest(path.read_bytes())) for key, path in paths.items()}
    def replace(key, raw):
        def published(postimage):
            changed[key] = postimage
        changed[key] = replace_private(paths[key], raw, notice, changed[key], published)
    def rollback():
        # Reassert the known hold even when custody or another surface later
        # refuses restoration. Unknown/newer bytes are never overwritten.
        outcome["hold"] = None
        replace("launcher", hold)
        require(paths["launcher"].read_bytes() == hold, "rollback-hold-unproved")
        outcome["hold"] = True
        custody_verify(tiers, files, notice)
        for key in ("destination", "registry", "binding", "donor"):
            # Never overwrite a concurrent or unrecognized postimage.
            saved = (tiers[1] / paths[key].name).read_bytes()
            if key == "donor" and not paths[key].exists() and not paths[key].is_symlink():
                require(restore_absent_donor, "absent-donor-needs-rollback-go")
                private_write(paths[key], saved, notice)
                changed[key] = (node_id(paths[key].lstat()), digest(saved))
            else:
                replace(key, saved)
        outcome.update(rollback=True, hold=True)
    restore_absent_donor = False
    try:
        go = fixture_go(args, evidence, operation, pristine)
        restore_absent_donor = True
        evidence.unchanged()
        custody_verify(tiers, files, notice)
        require(paths["destination"].read_bytes() == (tiers[1] / "destination.fixture").read_bytes(),
                "destination-custody-mismatch")
        held = fixture_holders(evidence, evidence.path(operation["pristine"]["path"]), allow_held=True)
        if held:
            private_write(paths["destination"].with_name("destination.fixture.NEW"), output.read_bytes(), notice)
            require(args.phase == 7, "operator-new-swap-pending")
            outcome["fallback"] = "NEW staged only; operator closure and swap not simulated"
            result["next_phase"] = 7
            return
        replace("destination", output.read_bytes())
        registry = notice.decode(registry_raw)
        for identity in registry["identities"]:
            if identity["key"] == args.key:
                identity["session_id"] = args.destination
        replace("registry", json_bytes(registry))
        require((paths["registry"].lstat().st_uid, paths["registry"].lstat().st_gid) == owners,
                "canonical-registry-owner")
        replace("binding", json_bytes({**binding, "session_id": args.destination}))
        outcome["agreements"] = six_agreements(args, notice, paths, admission["plain"])
        if args.phase == 7:
            evidence.unchanged()
            return
        replace("launcher", json_bytes(launcher))
        require(paths["launcher"].read_bytes() == json_bytes(launcher), "serve-hold-not-released")
        outcome["hold"] = False
        outcome["wake"] = append_proof(args, evidence, operation, paths, admission, go, replace)
        outcome["agreements"] = six_agreements(args, notice, paths, admission["plain"])
        outcome["fixture_accepted"] = True
        if args.phase == 8:
            evidence.unchanged()
            return
        evidence.unchanged()
        custody_verify(tiers, files, notice)
        outcome["receipt"] = fixture_receipt(args, evidence, stage, operation, admission, window, preview, outcome, go)
        require(operation.get("donor_preference") == "removed", "donor-preference-required")
        require(node_id(paths["donor"].lstat()) == changed["donor"][0]
                and paths["donor"].read_bytes() == (tiers[1] / "donor.fixture").read_bytes(), "donor-disposition-changed")
        paths["donor"].unlink()
        outcome["donor_store_removed"] = True
    except BaseException:
        try:
            rollback()
        except Exception:
            outcome.update(rollback=False, rollback_status="unknown; changed fixture preserved until context cleanup")
        raise


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
    ap.add_argument("--closing-record", help="hash-bound closing evidence, needed for phases 1 to 9")
    ap.add_argument("--build-plan", help="hash-bound synthetic spare/window/build plan for phases 3 to 9")
    ap.add_argument("--operation-plan", help="hash-bound synthetic process, custody, go and acceptance fixtures for phases 6 to 9")
    ap.add_argument("--adapter", choices=("fixture", "claude", "codex"), default="fixture",
                    help="fixture rehearsal or explicit Claude adapter preparation; never a live mode")
    ap.add_argument("--adapter-plan", help="rotate-claude-adapter/1 fixture plan, relative to the synthetic room")
    ap.add_argument("--native-action", choices=tuple(NATIVE_GO), help="explicitly refused; no native act is implemented")
    return ap


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    result = {"schema": "rotate/1", "phase": args.phase, "name": PHASES[args.phase][0],
              "dry_run": True, "writes": 0, "native_load_proved": False, "operator_accepted": False,
              "completed": [], "next_phase": args.phase + 1 if args.phase < 9 else None}
    try:
        adapter_boundary(args)
        if args.room is None or not args.gauge_row or not args.closeout_state:
            raise Refused("explicit-synthetic-evidence-required")
        notice = sibling("notice")
        evidence = Evidence(args.room, notice)
        row, binding, inputs = trigger(args, evidence, notice)
        adapter = None
        if args.adapter == "claude":
            adapter = claude_contract(args, evidence, row, binding, inputs)
            result["adapter"] = {"provider": "claude", "provider_version": adapter["provider_version"],
                                 "scope": "synthetic preparation only", "native_actions_implemented": False}
        result["completed"].append(0)
        if args.phase >= 1:
            expected = closing(args, evidence, notice, row, binding, inputs)
            result["completed"].append(1)
        if args.phase >= 2:
            result["mind"] = mind_ready(args, evidence, expected)
            result["completed"].append(2)
        if args.phase >= 3:
            plan = build_plan(args, evidence, binding)
            if args.phase >= 6:
                operation = operation_plan(args, evidence, binding)
            admission = destination_ready(args, evidence, row, plan)
            if adapter is not None:
                require(adapter.get("destination_metadata") == plan["destination"],
                        "claude-destination-metadata-mismatch")
                # The build clock is already bound to the spare by destination_ready.
                adapter = {**adapter, "built_at": plan["built_at"]}
                result["pristine"] = claude_destination(args, evidence, adapter, admission)
            result["completed"].append(3)
            result["destination_proof"] = "synthetic spare metadata and current observable holders only; not native admission"
        if args.phase >= 4:
            window = (claude_window(args, evidence, row, adapter, plan, inputs) if adapter is not None
                      else window_ready(args, evidence, row, plan))
            result["window"] = {k: window[k] for k in ("start", "boundary", "summary", "donor_sha256", "reason_sha256")}
            result["window"]["estimate"] = {"tokens": window["estimate"]["tokens"], "window": row["window"],
                                            "provenance": "hash-bound supplied estimate, not a native wake measurement"}
            result["completed"].append(4)
        if args.phase >= 5:
            continuation = None
            if args.phase >= 6:
                continuation = lambda *parts: late_phases(args, evidence, operation, admission, plan, window, result, *parts)
            result["build"] = build_preview(args, evidence, result["mind"], admission, plan, window, result, continuation)
            last = 6 if result.get("rehearsal", {}).get("fallback") else args.phase
            result["completed"].extend(range(5, last + 1))
        evidence.unchanged()
        result.update(status="stop", needs=PHASES[result["next_phase"]][1] if result["next_phase"] is not None else [], binding=binding,
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
