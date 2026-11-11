#!/usr/bin/env python3
"""rotate: fixture rehearsal and separately gated disposable operations.

Generated with ops/bin/template; implemented by Joe Codex. Phases 0 to 4
inspect synthetic evidence; phases 5 to 9 use disposable fixture artifacts.
The default fixture path admits no native body. The explicit disposable
path requires hash-bound plan/go/proof inputs and starts no provider.
Spec: docs/ops/specs/scripts/rotate.md. Tests: tools/test/test_rotate.py.
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import datetime as dt
import fcntl
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
import time
from fractions import Fraction
from pathlib import Path

sys.dont_write_bytecode = True
SESSIONS = Path(__file__).resolve().parents[3]
LIMIT = 1_048_576
SMALL = 65_536
DIGEST = re.compile(r"[0-9a-f]{64}")
PHASES = (
    ("trigger", ["a current-body gauge snapshot at the rotation line", "matching recorded closeout state"]),
    ("donor-closeout", ["hash-bound closing handoff", "the mind index it closed with"]),
    ("mind-ready", ["mind check passes", "the checked index matches the closing record"]),
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
MIND_HINT = "Open a leaf with mind.py read <id>; the whole index with mind.py show.\n"
FIRST_PROMPT = "Disposable rotation exercise: reply READY only; no tools, files or network."
# myself.py's one IDE-notice shape: the plugin puts it before a prompt while a file is open in the editor.
IDE_NOTICE_RE = re.compile(r"\s*<(ide_opened_file|ide_selection)>.*?</\1>", re.DOTALL)
IDE_NOTICE_CLOSE_RE = re.compile(r"</(?:ide_opened_file|ide_selection)>")
# What 2.1.322 writes into a fresh plugin chat after one exchange (measured 2026-11-11, by field only).
PRISTINE_TYPES = ("custom-title", "user", "assistant", "file-history-snapshot", "queue-operation", "session-owner",
                  "atis-latch", "last-prompt", "ai-title", "cost-state", "api-request", "api-request-shape",
                  "api-request-blob", "attachment")
PRISTINE_ATTACHMENTS = ("environment", "model", "deferred_tools_delta", "agent_listing_delta", "skill_listing",
                        "session_context", "date", "credential_org", "remote_session_change", "prompt_snapshot")


def past_ide_notices(content):
    """The text after any leading IDE notices, or None when only a notice, or a stray closing tag, remains."""
    rest, passed = content, False
    notice = IDE_NOTICE_RE.match(rest)
    while notice:
        rest, passed = rest[notice.end():], True
        notice = IDE_NOTICE_RE.match(rest)
    if passed and (not rest.strip() or IDE_NOTICE_CLOSE_RE.search(rest)):
        return None
    return rest.lstrip() if passed else rest


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
    # The donor closes with the mind index it holds: its SHA-256, or null when the room has no index.
    mind = record.get("mind")
    if (not isinstance(mind, dict) or set(mind) != {"index_sha256"}
            or not (mind["index_sha256"] is None
                    or (isinstance(mind["index_sha256"], str) and DIGEST.fullmatch(mind["index_sha256"])))):
        raise Refused("mind-index-unproved")
    return {"sha256": mind["index_sha256"]}


def mind_index(evidence):
    """The index bytes and its (id, agent, title) lines, read as evidence; (None, []) when there is none."""
    index = evidence.path("MIND.md")
    if not index.exists() and not index.is_symlink():
        return None, []
    raw = evidence.read("MIND.md", SMALL)
    try:
        lines = sibling("mind").parse_index(raw.decode("utf-8"))
    except Exception:
        raise Refused("mind-check-refused") from None
    return raw, lines


def mind_ready(args, evidence, expected):
    raw, lines = mind_index(evidence)
    if lines:
        evidence.notice.private_node(evidence.path("archives/mind"), True)
        for leaf_id, _, _ in lines:
            evidence.read("archives/mind/" + leaf_id + ".md")
    mind = sibling("mind")
    # This is the mind tool's own verifier, read-only and without Git; never a copy of it.
    try:
        _, failures = mind.verify(evidence.room, mind.read_registry(evidence.path("ops/etc/resident-identities.json")))
    except Exception:
        raise Refused("mind-check-refused") from None
    if failures:
        raise Refused("mind-check-refused")
    sha = digest(raw) if raw is not None else None
    if sha != expected["sha256"]:
        raise Refused("closing-mind-mismatch")
    return {"index_sha256": sha, "own_leaves": sum(1 for _, agent, _ in lines if agent == args.key)}


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
    content = past_ide_notices(content)
    if content is None:
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
    # Pointer first: the capsule carries the resident's own index lines, never a leaf's body.
    _, lines = mind_index(evidence)
    own = [f"- [{i}](archives/mind/{i}.md) {agent} \u2014 {title}\n" for i, agent, title in lines if agent == args.key]
    pointers = "".join(own) or "No leaves of yours yet.\n"
    transition = evidence.reference(plan.get("transition")).decode("utf-8")
    require(not transition.lstrip().startswith(("/", "archives/", "storage/")), "transition-text-required")
    identity = admission["identity"]
    return ("Registry\nYou are `" + admission["plain"] + "`.\nResident: " + args.key
            + "\nRoom: " + str(evidence.room) + "\nDestination container: " + args.destination
            + "\n\nMind\n" + pointers + MIND_HINT + "\nTransition\n" + transition
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
                           "capsule_sha256": digest(capsule.encode()), "mind_sha256": mind_ref["index_sha256"],
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
        "MIND_INDEX": preview["mind_sha256"] or "none: the room held no mind index", "INSTALL": "Synthetic verified swap; six agreements="
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


NATIVE_LIMIT = 64 * 1024 * 1024
NATIVE_SCHEMA = "rotate-disposable/1"
NATIVE_SID = re.compile(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\Z")
NATIVE_ACTIONS = {"disposable-exercise", "custody", "install", "load", "rollback"}


def native_path(raw):
    require(isinstance(raw, str) and raw and "\x00" not in raw, "native-path-required")
    path = Path(raw)
    require(path.is_absolute() and ".." not in path.parts and path == path.resolve(),
            "native-plain-absolute-path-required")
    sibling("notice").parent_chain(path.parent)
    return path


def native_read(path, limit=NATIVE_LIMIT):
    """Private bracketed read; a replacement or a change is never an absence."""
    notice = sibling("notice")
    path = native_path(str(path))
    before = notice.private_node(path)
    require(before.st_size <= limit, "native-file-too-large")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as handle:
        require(node_id(os.fstat(handle.fileno())) == node_id(before), "native-open-identity-changed")
        raw = handle.read(limit + 1)
        require(node_id(os.fstat(handle.fileno())) == node_id(before), "native-read-identity-changed")
    require(len(raw) <= limit and node_id(path.lstat()) == node_id(before), "native-read-preimage-changed")
    return raw, before


def native_snapshot(path):
    path = native_path(str(path))
    st = path.lstat()
    if stat.S_ISREG(st.st_mode):
        raw, st = native_read(path)
        sha = digest(raw)
        kind = "file"
    else:
        sibling("notice").private_node(path, True)
        require(stat.S_ISDIR(st.st_mode), "native-inventory-type")
        sha, kind = None, "directory"
    return {"type": kind, "dev": st.st_dev, "ino": st.st_ino, "size": st.st_size,
            "sha256": sha, "mode": stat.S_IMODE(st.st_mode), "uid": st.st_uid,
            "gid": st.st_gid, "mtime_ns": st.st_mtime_ns, "ctime_ns": st.st_ctime_ns,
            "nlink": st.st_nlink}


def native_inventory(directory):
    """The named folder's immediate listing; never follows a child link."""
    sibling("notice").private_node(directory, True)
    result = {}
    for item in sorted(directory.iterdir()):
        require(not item.is_symlink(), "native-inventory-link")
        result[item.name] = native_snapshot(item)
    return result


def native_same(left, right, identity=True):
    fields = ("type", "size", "sha256", "mode", "uid", "gid", "nlink")
    if identity:
        fields += ("dev", "ino", "mtime_ns", "ctime_ns")
    return all(left.get(k) == right.get(k) for k in fields)


def native_rows(raw, session, project, prefix_ids=()):
    require(bool(raw) and raw.endswith(b"\n"), "native-body-not-terminated")
    notice = sibling("notice")
    rows = [notice.decode(line) for line in raw.splitlines()]
    require(0 < len(rows) <= 65536, "native-row-limit")
    seen, pending = set(prefix_ids), set()
    assistant, identities = 0, 0

    def blocks(row):
        nonlocal identities
        for key in ("sessionId", "session_id"):
            if key in row:
                require(row[key] == session, "native-body-foreign-session")
                identities += 1
        message = row.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        # A row with no uuid is the provider's housekeeping (an api-request-blob repeats the call's blocks).
        if not isinstance(content, list) or "uuid" not in row:
            return
        for value in content:
            require(isinstance(value, dict), "native-message-content-block")
            # Inputs, outputs, text and embedded records are opaque payloads.
            if value.get("type") == "tool_use":
                token = value.get("id")
                require(isinstance(token, str) and bool(token) and token not in pending, "native-tool-use")
                pending.add(token)
            elif value.get("type") == "tool_result":
                token = value.get("tool_use_id")
                require(isinstance(token, str) and bool(token) and token in pending, "native-tool-result")
                pending.remove(token)

    for row in rows:
        blocks(row)
        if "cwd" in row:
            require(row["cwd"] == str(project), "native-body-project")
        if "uuid" in row:
            uid = row["uuid"]
            require(isinstance(uid, str) and uid and uid not in seen, "native-message-id")
            parent = row.get("parentUuid")
            if (seen and parent is None and row.get("type") == "system"
                    and row.get("subtype") == "compact_boundary"):
                # The provider writes a boundary with no parent and names the row it follows.
                require(row.get("logicalParentUuid") in seen, "native-parent-chain")
            else:
                require(parent in seen if seen else parent is None, "native-parent-chain")
            seen.add(uid)
        if row.get("type") == "assistant" and not row.get("isSidechain"):
            assistant += 1
    require(identities > 0 and not pending, "native-identities-or-tool-pairs")
    return rows, seen, assistant


def native_pristine(rows):
    """A fresh destination: one inert exchange inside the measured envelope. Read-only; also the B7 preflight."""
    dialogue = [row for row in rows if row.get("type") in ("user", "assistant")]
    replies = dialogue[1:]
    messages = [row.get("message") for row in replies]
    require(len(dialogue) >= 2 and dialogue[0].get("type") == "user"
            and all(row.get("type") == "assistant" and isinstance(message, dict)
                    for row, message in zip(replies, messages))
            and isinstance(messages[0].get("id"), str) and bool(messages[0]["id"])
            and all(message.get("id") == messages[0]["id"] for message in messages),
            "native-pristine-first-exchange")
    prompt = dialogue[0].get("message")
    asked = prompt.get("content") if isinstance(prompt, dict) and prompt.get("role") == "user" else None
    if isinstance(asked, list) and all(isinstance(b, dict) and b.get("type") == "text" for b in asked):
        asked = "\n".join(b.get("text", "") for b in asked)
    asked = past_ide_notices(asked) if isinstance(asked, str) else None
    blocks = []
    for message in messages:
        content = message.get("content")
        blocks += [{"type": "text", "text": content}] if isinstance(content, str) else list(content or [])
    texts = [b for b in blocks if isinstance(b, dict) and b.get("type") == "text"]
    require(asked == FIRST_PROMPT and all(message.get("role") == "assistant" for message in messages)
            and all(isinstance(b, dict) and b.get("type") in ("text", "thinking", "redacted_thinking") for b in blocks)
            and len(texts) == 1 and texts[0].get("text") == "READY", "native-pristine-inert-exchange")
    require(all(row.get("type") in PRISTINE_TYPES and (row.get("type") != "attachment"
                or (isinstance(row.get("attachment"), dict) and row["attachment"].get("type") in PRISTINE_ATTACHMENTS))
                for row in rows), "native-pristine-unknown-envelope")


class NativeOperation:
    """Explicit disposable operation, never a resident route or provider driver.

    Go/proof files are externally supplied records, not authenticated people.
    Every named go and every actual object must be revalidated at the act.
    """

    def __init__(self, args):
        self.args = args
        self.notice = sibling("notice")
        self.action = args.native_action
        require(getattr(args, "native_apply", False) is True and not args.dry_run,
                "native-explicit-apply-required")
        require(self.action in NATIVE_ACTIONS, "native-action-not-supported")
        require(args.adapter == "claude", "native-claude-adapter-required")
        # No native/body/state read is reachable without both named go inputs.
        require(args.native_go and args.native_go_sha256, "native-named-go-required")
        self.go, self.go_sha = self.record(args.native_go, args.native_go_sha256)
        require(args.native_plan and args.native_plan_sha256, "native-hash-bound-plan-required")
        self.plan, self.plan_sha = self.record(args.native_plan, args.native_plan_sha256)
        p, g = self.plan, self.go
        require(p.get("schema") == NATIVE_SCHEMA and p.get("provider") == "claude", "native-plan-schema-provider")
        self.operation = p.get("operation")
        require(isinstance(self.operation, str) and re.fullmatch(r"[a-z][a-z0-9-]{1,47}", self.operation),
                "native-operation-name")
        self.writer = p.get("writer")
        require(isinstance(self.writer, str) and self.notice.KEY.fullmatch(self.writer), "native-writer-key")
        version = p.get("provider_version")
        require(isinstance(version, str) and 0 < len(version.strip()) <= 64, "native-provider-version")
        expected = {"schema": "rotate-native-go/1", "operation": self.operation,
                    "plan_sha256": self.plan_sha, "writer": self.writer, "action": self.action}
        require(all(g.get(k) == v for k, v in expected.items()), "native-go-binding")
        now = dt.datetime.now(dt.timezone.utc)
        age = (now - self.notice.stamp(g.get("at"))).total_seconds()
        require(0 <= age <= 3600, "native-go-time")
        self.room = native_path(p.get("room"))
        self.evidence_directory = self.room / "storage" / "active" / self.operation
        require(native_path(str(args.native_plan)).parent == self.evidence_directory,
                "native-operation-evidence-home")
        self.notice.private_node(self.evidence_directory, True)
        require(native_path(str(args.native_go)).parent == self.evidence_directory
                and native_path(str(args.native_proof)).parent == self.evidence_directory,
                "native-go-proof-evidence-home")
        self.project = native_path(p.get("project"))
        self.store = native_path(p.get("store"))
        self.records_dir = native_path(p.get("records_dir"))
        self.notice.private_node(self.project, True)
        self.notice.private_node(self.store, True)
        self.notice.private_node(self.records_dir, True)
        require(self.project != self.store and self.project != self.room and self.store != self.room,
                "native-private-disposable-project-required")
        self.registry = p.get("registry")
        require(isinstance(self.registry, dict) and self.registry.get("path") == str(self.room / "ops/etc/resident-identities.json"),
                "native-canonical-registry-required")
        registry, _ = self.reference(self.registry, SMALL * 16)
        rows = self.notice.decode(registry).get("identities")
        require(isinstance(rows, list) and rows, "native-registry-rows")
        keys, bindings, writers = set(), set(), []
        self.auditors = set()
        for row in rows:
            require(isinstance(row, dict), "native-registry-row")
            key, provider, sid = (row.get(k) for k in ("key", "provider", "session_id"))
            require(isinstance(key, str) and self.notice.KEY.fullmatch(key)
                    and provider in ("claude", "codex", "copilot")
                    and isinstance(sid, str) and self.notice.SID.fullmatch(sid), "native-registry-identity")
            require(key not in keys and (provider, sid) not in bindings, "native-ambiguous-registry")
            require(row.get("room") != str(self.project), "native-project-already-resident")
            keys.add(key)
            bindings.add((provider, sid))
            if key == self.writer:
                writers.append(row)
            if row.get("role") == "Auditor":
                self.auditors.add(key)
        require(len(writers) == 1 and writers[0].get("room") == str(self.room), "native-registered-writer-required")
        self.targets = {}
        for name in ("donor", "destination"):
            target = p.get(name)
            require(isinstance(target, dict), "native-target-required")
            sid = target.get("session_id")
            require(isinstance(sid, str) and NATIVE_SID.fullmatch(sid), "native-target-identity")
            require(not any(binding[1] == sid for binding in bindings), "native-target-is-resident")
            path = native_path(target.get("path"))
            require(path.parent == self.store and path.name == sid + ".jsonl", "native-target-store-mapping")
            require(isinstance(target.get("sha256"), str) and DIGEST.fullmatch(target["sha256"]),
                    "native-target-digest")
            self.targets[name] = path
        require(self.targets["donor"] != self.targets["destination"], "native-two-distinct-containers-required")
        wanted = {q.name for q in self.targets.values()}
        if (self.action == "rollback" and self.go.get("restore_absent_donor") is True
                and not os.path.lexists(self.targets["donor"])):
            wanted.remove(self.targets["donor"].name)
        require({q.name for q in self.store.glob("*.jsonl")} == wanted,
                "native-exact-two-containers-required")
        self.candidate, _ = self.reference(p.get("candidate"))
        require(native_path(p["candidate"]["path"]).is_relative_to(self.evidence_directory),
                "native-candidate-evidence-home")
        artifacts = p.get("artifacts")
        require(isinstance(artifacts, list) and 3 <= len(artifacts) <= 64, "native-artifact-list")
        names = set()
        self.artifacts = []
        for item in artifacts:
            require(isinstance(item, dict), "native-artifact-object")
            name = item.get("name")
            require(isinstance(name, str) and re.fullmatch(r"[a-z][a-z0-9-]{0,39}", name)
                    and name not in names and name not in {"donor", "destination", "candidate"}, "native-artifact-name")
            self.reference(item)
            require(native_path(item.get("path")).is_relative_to(self.evidence_directory),
                    "native-artifact-evidence-home")
            names.add(name)
            self.artifacts.append(item)
        require({"capsule", "gates", "window"} <= names, "native-required-staged-objects")
        self.custody = sibling("custody")
        roots = p.get("custody_roots")
        require(isinstance(roots, list) and 2 <= len(roots) <= 4, "native-custody-roots")
        self.roots = self.custody.check_roots(roots, False)
        for root in self.roots:
            native_path(str(root))
            self.notice.private_node(root, True)
            require(not any(root.is_relative_to(path) or path.is_relative_to(root)
                            for path in (self.room, self.project, self.store)), "native-custody-overlap")
        self.batch = self.custody.batch_name(self.writer, p.get("date"))
        self.directory = self.room / "logs" / "rotate" / self.operation
        self.state_path = self.directory / "state.json"
        self.preimages_path = self.directory / "preimages.json"
        self.stage = self.targets["destination"].with_name(self.targets["destination"].name + ".NEW")
        self.proof, self.proof_sha = self.record(args.native_proof, args.native_proof_sha256)
        require(all(self.proof.get(k) == v for k, v in {
            "schema": "rotate-native-proof/1", "operation": self.operation,
            "plan_sha256": self.plan_sha, "action": self.action}.items()), "native-proof-binding")
        for path in (*self.targets.values(), native_path(p["candidate"]["path"]),
                     *(native_path(item["path"]) for item in self.artifacts)):
            self.git_private(path.parent, path)
        self.state = None

    @staticmethod
    def git_private(base, path):
        require(not sibling("mind").git_exposed(base, [path]), "native-git-exposure-or-unknown")

    def write(self, path, raw, owner=None):
        self.git_private(path.parent, path)
        return private_write(path, raw, self.notice, owner)

    def record(self, path, expected):
        require(path and isinstance(expected, str) and DIGEST.fullmatch(expected), "native-record-hash-required")
        raw, _ = native_read(native_path(str(path)), SMALL * 16)
        require(digest(raw) == expected, "native-record-hash-mismatch")
        return self.notice.decode(raw), expected

    def reference(self, ref, limit=NATIVE_LIMIT):
        require(isinstance(ref, dict) and isinstance(ref.get("sha256"), str)
                and DIGEST.fullmatch(ref["sha256"]), "native-reference-required")
        raw, st = native_read(native_path(ref.get("path")), limit)
        require(digest(raw) == ref["sha256"], "native-reference-hash")
        return raw, st

    def current(self, name):
        if (name == "donor" and self.action == "rollback" and self.go.get("restore_absent_donor") is True
                and not os.path.lexists(self.targets[name])):
            return {"type": "absent"}
        return native_snapshot(self.targets[name])

    def instrument_objects(self):
        return {**{name: str(path) for name, path in self.targets.items()},
                "candidate": self.plan["candidate"]["path"],
                **{item["name"]: item["path"] for item in self.artifacts}}

    def instrument_packet(self, name, record_name, holders=None):
        """Exact keys consumed by the independently reviewed I1-I5 readers.

        I1's project is the working cwd, not the store listing used by I2/I5.
        I4 receives a separately named, flattened I3A binding with the UUID set.
        Neither an export nor a supplied record authenticates its author.
        """
        require(isinstance(record_name, str) and re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,119}\.json", record_name),
                "native-instrument-record-name")
        pk = {"evidence": str(self.evidence_directory), "record_name": record_name}
        if "synthetic_root" in self.plan:
            pk["synthetic_root"] = str(native_path(self.plan["synthetic_root"]))
        if name == "I1":
            # An explicitly authorized absent-donor restore has no inode to
            # lstat. Both session IDs still participate in process inspection.
            pk.update(targets={key: str(path) for key, path in self.targets.items() if os.path.lexists(path)}, project=str(self.project),
                      session_ids=[self.plan[key]["session_id"] for key in self.targets],
                      records_dir=str(self.records_dir), interval_s=1)
        elif name == "I2":
            pk.update(objects=self.instrument_objects(), project=str(self.store))
        elif name in ("I3B", "I3A"):
            pk.update(preimage=self.state["i2"]["record"]["path"], destination=str(self.targets["destination"]),
                      staged=str(self.stage), candidate_sha256=digest(self.candidate), destination_token="destination")
            if name == "I3A":
                pk["before"] = self.state["i3b"]["record"]["path"]
        elif name == "I4":
            pk.update(postimage=self.state["i4_postimage"]["path"], destination=str(self.targets["destination"]),
                      destination_sid=self.plan["destination"]["session_id"], donor_sid=self.plan["donor"]["session_id"])
        else:
            require(name == "I5", "native-instrument-name")
            retained = self.state.get("retained_append")
            pk.update(preimages=self.state["i2"]["record"]["path"], items=self.instrument_objects(), donor="donor",
                      custody=[] if retained is None else [
                          {"path": str(root / self.batch / retained["name"]), "sha256": retained["sha256"]}
                          for root in self.roots], project=str(self.store),
                      holders=holders if holders is not None else self.proof["instruments"]["I1"][-1]["record"]["path"])
        return pk

    def instrument(self, name, binding=None):
        if binding is None:
            bindings = self.proof.get("instruments")
            require(isinstance(bindings, dict), "native-instrument-bindings-required")
            binding = bindings.get(name)
        require(isinstance(binding, dict) and set(binding) == {"packet", "record"},
                "native-instrument-reference-required")
        for ref in binding.values():
            require(isinstance(ref, dict) and native_path(ref.get("path")).parent == self.evidence_directory,
                    "native-instrument-evidence-home")
        packet = self.notice.decode(self.reference(binding["packet"], SMALL * 16)[0])
        expected = self.instrument_packet(name, packet.get("record_name"))
        require(packet == expected, "native-instrument-packet-mismatch")
        require(binding["record"]["path"] == str(self.evidence_directory / packet["record_name"]),
                "native-instrument-output-path")
        return self.notice.decode(self.reference(binding["record"], SMALL * 16)[0]), binding

    def publish_instruments(self):
        """Export inert packets only. No observer, provider or child is run."""
        names = ["I2"]
        phase = self.state["phase"] if self.state else "awaiting-instruments"
        if phase == "install-prepared":
            names.append("I3B")
        if phase == "install-renamed":
            names.append("I3A")
        if phase in ("installed", "loaded"):
            names.append("I4")
        if phase in ("rollback-restored", "rolled-back"):
            names.append("I5")
        # Exclusive observer outputs are never reused, including a repeated
        # stop or recovery export at an otherwise unchanged checkpoint.
        suffix = digest(json_bytes(self.state if self.state else self.plan))[:16] + "-" + os.urandom(8).hex()
        exports = {}
        labels = [("I1", "i1a"), ("I1", "i1b")] + [(name, name.lower()) for name in names]
        fresh_holders = str(self.evidence_directory / ("i1b-" + suffix + ".result.json"))
        for name, label in labels:
            packet = self.instrument_packet(name, label + "-" + suffix + ".result.json",
                                            holders=fresh_holders if name == "I5" else None)
            path = self.evidence_directory / (label + "-" + suffix + ".packet.json")
            raw = json_bytes(packet)
            if os.path.lexists(path):
                require(native_read(path)[0] == raw, "native-instrument-export-changed")
            else:
                self.write(path, raw)
            ref = {"path": str(path), "sha256": digest(raw)}
            if name == "I1":
                exports.setdefault(name, []).append(ref)
            else:
                exports[name] = ref
        # Private paths never enter the public CLI result.
        home = self.directory if self.state else self.evidence_directory
        path = home / "instrument-packets.json"
        require(not os.path.lexists(home / ".packets.NEW"), "native-pending-packet-export")
        raw = json_bytes(exports)
        if not os.path.lexists(path):
            self.write(path, raw)
        elif native_read(path)[0] != raw:
            temp = home / ".packets.NEW"
            require(not os.path.lexists(temp), "native-pending-packet-export")
            self.write(temp, raw)
            os.replace(temp, path)
            self.sync(home)

    def quiescence(self):
        observations = self.proof.get("quiescence")
        require(isinstance(observations, list) and len(observations) == 2, "native-two-quiescence-readings")
        times = []
        now = dt.datetime.now(dt.timezone.utc)
        current = {name: self.current(name) for name in self.targets}
        project = self.project.stat()
        bindings = self.proof.get("instruments")
        require(isinstance(bindings, dict) and isinstance(bindings.get("I1"), list)
                and len(bindings["I1"]) == 2, "native-two-i1-records-required")
        identities = set()
        witness_times = []
        for observation, binding in zip(observations, bindings["I1"]):
            require(isinstance(observation, dict), "native-quiescence-object")
            at = self.notice.stamp(observation.get("at"))
            require(0 <= (now - at).total_seconds() <= 60, "native-quiescence-stale")
            times.append(at)
            for name, expected in current.items():
                require(observation.get(name) == expected, "native-quiescence-target-changed")
            require(observation.get("project") == {"dev": project.st_dev, "ino": project.st_ino},
                    "native-quiescence-project")
            require(observation.get("same_user_observable") is True, "native-process-observability")
            for field in ("holders", "session_records", "argument_holders", "locks", "unreadable", "foreign_processes"):
                require(type(observation.get(field)) is int and observation[field] == 0,
                        "native-quiescence-" + field.replace("_", "-"))
            record, _ = self.instrument("I1", binding)
            require(record == {"held": [], "own_unreadable": 0, "foreign_unreadable": 0},
                    "native-i1-not-clear")
            require(type(record["own_unreadable"]) is int and type(record["foreign_unreadable"]) is int,
                    "native-i1-count-type")
            node = native_snapshot(native_path(binding["record"]["path"]))
            identities.add((node["dev"], node["ino"]))
            witness_times.append(node["mtime_ns"])
            require(0 <= now.timestamp() - node["mtime_ns"] / 1e9 <= 60, "native-i1-record-stale")
            if (self.state or {}).get("phase") in ("rollback-restored", "rolled-back"):
                require(node["mtime_ns"] >= self.state["restored_at_ns"], "native-i1-before-restore")
        require(len(identities) == 2, "native-distinct-i1-records-required")
        require(witness_times[1] - witness_times[0] >= 1_000_000_000, "native-i1-record-interval")
        require((times[1] - times[0]).total_seconds() >= 1, "native-quiescence-interval")

    def refresh_at_act(self):
        """Refresh authority bytes and the bounded external witness at the act."""
        self.record(self.args.native_go, self.go_sha)
        self.record(self.args.native_plan, self.plan_sha)
        self.record(self.args.native_proof, self.proof_sha)
        self.reference(self.registry, SMALL * 16)
        self.reference(self.plan["candidate"])
        for item in self.artifacts:
            self.reference(item)
        if self.action == "install" and "i3b" in self.state:
            self.instrument("I3B", self.state["i3b"])
        age = (dt.datetime.now(dt.timezone.utc) - self.notice.stamp(self.go["at"])).total_seconds()
        require(0 <= age <= 3600, "native-go-expired-at-act")
        self.root_identities()
        self.quiescence()

    def unchanged_donor(self):
        current = self.current("donor")
        restored = ((self.state or {}).get("restores", {}).get("donor", {}).get("installed"))
        allowed_absence = (self.action == "rollback" and self.go.get("restore_absent_donor") is True
                           and current == {"type": "absent"})
        require(allowed_absence or native_same(current, self.preimages["donor"])
                or (self.action == "rollback" and restored is not None and native_same(current, restored)),
                "native-donor-preimage-changed")

    def root_identities(self):
        for name, path in (("project_root", self.project), ("store_root", self.store)):
            current = native_snapshot(path)
            expected = self.preimages[name]
            require(all(current[key] == expected[key] for key in ("type", "dev", "ino", "mode", "uid", "gid")),
                    "native-operation-root-changed")

    def listing(self, allow_stage=False, restored=False):
        expected = self.preimages["store"]
        actual = native_inventory(self.store)
        extras = {self.stage.name} if allow_stage else set()
        require(set(actual) == set(expected) | extras, "native-store-listing-changed")
        for name, recorded in expected.items():
            if name == self.targets["destination"].name and not restored:
                continue
            require(native_same(actual[name], recorded, identity=not restored), "native-store-entry-changed")
        require(native_inventory(self.project) == self.preimages["project"], "native-project-listing-changed")

    def save(self):
        raw = json_bytes(self.state)
        temp = self.directory / ".state.NEW"
        require(not os.path.lexists(temp), "native-pending-state-write")
        self.write(temp, raw)
        os.replace(temp, self.state_path)
        self.sync(self.directory)

    @staticmethod
    def sync(directory):
        fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)

    def admission(self):
        if self.state is not None:
            require(self.state["phase"] == "admitted", "native-operation-already-admitted")
            self.quiescence()
            self.unchanged_donor()
            require(native_same(self.current("destination"), self.preimages["destination"]), "native-pristine-changed")
            self.listing()
            return
        require(not os.path.lexists(self.stage), "native-unknown-stage")
        self.quiescence()
        before = {name: self.current(name) for name in self.targets}
        for name, snap in before.items():
            require(snap["sha256"] == self.plan[name]["sha256"], "native-closed-target-hash")
        donor_raw, _ = native_read(self.targets["donor"])
        pristine, _ = native_read(self.targets["destination"])
        native_rows(donor_raw, self.plan["donor"]["session_id"], self.project)
        rows, _, _ = native_rows(pristine, self.plan["destination"]["session_id"], self.project)
        native_pristine(rows)
        candidate_rows, _, _ = native_rows(self.candidate, self.plan["destination"]["session_id"], self.project)
        require(sibling("successor").count_residue(candidate_rows, self.plan["donor"]["session_id"])[0] == 0,
                "native-candidate-donor-residue")
        require(candidate_rows[0].get("type") == "system"
                and candidate_rows[0].get("subtype") == "compact_boundary", "native-candidate-boundary")
        gates_ref = next(item for item in self.artifacts if item["name"] == "gates")
        gates = self.notice.decode(self.reference(gates_ref)[0])
        require(gates.get("schema") == "rotate-native-gates/1" and gates.get("phase") == 5,
                "native-preparation-gates-required")
        for field, value in {"donor_sha256": before["donor"]["sha256"],
                             "pristine_sha256": before["destination"]["sha256"],
                             "candidate_sha256": digest(self.candidate)}.items():
            require(gates.get(field) == value, "native-preparation-binding")
        checks = gates.get("gates")
        require(isinstance(checks, dict) and set(checks) == {
            "trigger", "closeout", "operator_compaction", "window", "static", "media"}
                and all(value is True for value in checks.values()), "native-preparation-incomplete")
        self.preimages = {**before, "store": native_inventory(self.store), "project": native_inventory(self.project),
                          "project_root": native_snapshot(self.project), "store_root": native_snapshot(self.store)}
        i2, binding = self.instrument("I2")
        require(set(i2) == {"objects", "listing", "project"}, "native-i2-shape")
        require(i2["objects"] == {name: native_snapshot(native_path(path))
                                 for name, path in self.instrument_objects().items()}, "native-i2-objects")
        require(i2["project"] == [self.preimages["store_root"][key] for key in ("dev", "ino")]
                and i2["listing"] == {name: ["file" if row["type"] == "file" else "dir", row["mode"], row["size"]]
                                     for name, row in self.preimages["store"].items()}, "native-i2-store-listing")
        self.write(self.preimages_path, json_bytes(self.preimages))
        self.state = {"schema": "rotate-native-state/1", "operation": self.operation,
                      "plan_sha256": self.plan_sha, "preimages_sha256": digest(json_bytes(self.preimages)),
                      "phase": "admitted", "admitted_at": self.go["at"], "go_sha256": self.go_sha, "i2": binding}
        self.save()

    def members(self):
        return [{"name": self.operation + "-" + name, "path": str(self.targets[name]),
                 "sha256": self.preimages[name]["sha256"]} for name in self.targets] + [
            {"name": self.operation + "-candidate", **self.plan["candidate"]},
            {"name": self.operation + "-preimages", "path": str(self.preimages_path),
             "sha256": self.state["preimages_sha256"]}] + [
            {**item, "name": self.operation + "-" + item["name"]} for item in self.artifacts]

    def custody_members(self, members, add=False):
        batches = [root / self.batch for root in self.roots]
        self.custody.agree(batches)
        for item in members:
            for root, batch in zip(self.roots, batches):
                self.git_private(root, batch / item["name"])
            present = [os.path.lexists(batch / item["name"]) for batch in batches]
            require(len(set(present)) == 1, "native-partial-custody-item")
            if not any(present):
                require(add, "native-custody-item-missing")
                self.reference(item)
                call = argparse.Namespace(root=[str(root) for root in self.roots], same_device_ok=False,
                                          direct=[], writer=self.writer, date=self.plan["date"],
                                          files=[item["path"]], as_name=item["name"])
                with contextlib.redirect_stdout(io.StringIO()):
                    require(self.custody.cmd_add(call) == 0, "native-custody-add-refused")
            for batch in batches:
                raw, _ = native_read(batch / item["name"])
                require(digest(raw) == item["sha256"], "native-custody-member-hash")
                manifest = self.custody.manifest_rows(batch)
                require(sum(line.split("  ")[:2] == [item["sha256"], item["name"]]
                            for line in manifest) == 1, "native-custody-member-manifest")
        self.custody.agree(batches)
        return digest(json_bytes([{k: item[k] for k in ("name", "sha256")} for item in members]))

    def preserve(self):
        require(self.state["phase"] in ("admitted", "custody-intent", "custodied"), "native-custody-phase")
        self.quiescence()
        self.unchanged_donor()
        require(native_same(self.current("destination"), self.preimages["destination"]), "native-pristine-changed")
        self.listing()
        members = self.members()
        if self.state["phase"] == "custodied":
            require(self.custody_members(members) == self.state["custody_manifest_sha256"], "native-custody-manifest-changed")
            return
        self.state["phase"] = "custody-intent"
        self.save()
        sha = self.custody_members(members, add=True)
        self.state.update(phase="custodied", custody_manifest_sha256=sha,
                          custody_at=dt.datetime.now(dt.timezone.utc).isoformat())
        self.save()

    def installation(self):
        require(self.state["phase"] in ("custodied", "install-prepared", "install-renamed", "installed"), "native-install-phase")
        require(self.go.get("pristine_sha256") == self.preimages["destination"]["sha256"]
                and self.go.get("candidate_sha256") == digest(self.candidate)
                and self.go.get("custody_manifest_sha256") == self.state.get("custody_manifest_sha256")
                and self.go.get("inverse") == "restore-pristine-and-stop", "native-install-go-targets")
        require(self.notice.stamp(self.go["at"]) > self.notice.stamp(self.state["custody_at"]),
                "native-install-go-before-custody")
        self.quiescence()
        self.unchanged_donor()
        require(self.custody_members(self.members()) == self.state["custody_manifest_sha256"], "native-custody-manifest-changed")
        audit = self.proof.get("custody_audit")
        require(isinstance(audit, dict) and audit.get("manifest_sha256") == self.state["custody_manifest_sha256"]
                and audit.get("auditor") in self.auditors and audit["auditor"] != self.writer
                and audit.get("verdict") == "PASS", "native-independent-custody-audit-required")
        review, _ = self.reference(audit.get("review"), SMALL)
        require(native_path(audit["review"]["path"]).is_relative_to(self.evidence_directory), "native-custody-audit-evidence-home")
        review = self.notice.decode(review)
        require(all(review.get(key) == value for key, value in {
            "schema": "rotate-custody-audit/1", "operation": self.operation, "plan_sha256": self.plan_sha,
            "manifest_sha256": self.state["custody_manifest_sha256"], "auditor": audit["auditor"],
            "verdict": "PASS"}.items()), "native-custody-audit-review-binding")
        if self.state["phase"] == "installed":
            require(native_same(self.current("destination"), self.state["installed"]), "native-installed-postimage-changed")
            self.listing()
            return
        if self.state["phase"] == "custodied":
            self.listing()
            require(native_same(self.current("destination"), self.preimages["destination"]), "native-install-pristine-changed")
            require(not os.path.lexists(self.stage), "native-unknown-stage")
            old = self.preimages["destination"]
            self.write(self.stage, self.candidate, (old["uid"], old["gid"]))
            self.state.update(phase="install-prepared", staged=native_snapshot(self.stage), install_go_sha256=self.go_sha)
            self.save()
            # A real external I3B run must inspect this exact inode before a
            # separate invocation can rename it. Staging is not installation.
            return
        require(self.state["install_go_sha256"] == self.go_sha, "native-install-resume-go-changed")
        if self.state["phase"] == "install-renamed":
            installed = self.current("destination")
            require(native_same(installed, self.state["installed"]), "native-installed-postimage-changed")
            after, binding = self.instrument("I3A")
            require(after == {"postimage": installed}, "native-i3a-postimage")
            _, ids, _ = native_rows(self.candidate, self.plan["destination"]["session_id"], self.project)
            # I3A emits {postimage: ...}; I4 expects a flat record and UUIDs.
            # This explicit derived binding is not called an I3A output.
            raw = json_bytes({**installed, "uuids": sorted(ids)})
            path = self.evidence_directory / ("i4-binding-" + digest(raw)[:16] + ".json")
            if not os.path.lexists(path):
                self.write(path, raw)
            require(native_read(path)[0] == raw, "native-i4-binding-changed")
            self.state.update(phase="installed", i3a=binding,
                              i4_postimage={"path": str(path), "sha256": digest(raw)})
            self.save()
            self.listing()
            return
        if os.path.lexists(self.stage):
            self.listing(allow_stage=True)
            require(native_same(native_snapshot(self.stage), self.state["staged"]), "native-stage-changed")
            require(native_same(self.current("destination"), self.preimages["destination"]), "native-install-preimage-changed")
            before, binding = self.instrument("I3B")
            require(before == {"staged": self.state["staged"]}, "native-i3b-staged-inode")
            self.state["i3b"] = binding
            self.save()
            self.refresh_at_act()
            os.replace(self.stage, self.targets["destination"])
            self.sync(self.store)
        installed = self.current("destination")
        require("i3b" in self.state, "native-install-rename-witness-required")
        self.instrument("I3B", self.state["i3b"])
        require(native_same(installed, self.state["staged"], False)
                and (installed["dev"], installed["ino"]) == (self.state["staged"]["dev"], self.state["staged"]["ino"]),
                "native-install-unknown-postimage")
        require(installed["sha256"] == digest(self.candidate), "native-installed-candidate-hash")
        self.state.update(phase="install-renamed", installed=installed)
        self.save()
        self.listing()

    def load(self):
        require(self.state["phase"] in ("installed", "loaded"), "native-load-phase")
        self.quiescence()
        self.unchanged_donor()
        self.listing()
        current = self.current("destination")
        before = self.state["installed"]
        require((current["dev"], current["ino"]) == (before["dev"], before["ino"]), "native-load-inode-changed")
        raw, _ = native_read(self.targets["destination"])
        require(len(raw) > before["size"] and digest(raw[:before["size"]]) == before["sha256"], "native-load-prefix-changed")
        _, ids, _ = native_rows(self.candidate, self.plan["destination"]["session_id"], self.project)
        _, _, assistant = native_rows(raw[before["size"]:], self.plan["destination"]["session_id"], self.project, ids)
        require(assistant > 0, "native-load-no-assistant-append")
        reading = sibling("gauge").read_claude(self.targets["destination"])
        require(type(reading.get("tokens")) is int and reading["tokens"] > 0
                and not reading.get("compaction_after"), "native-load-first-gauge-unproved")
        # The reading must be a row of the append itself, never one carried in the installed prefix.
        def appended_reading(line):
            row = self.notice.decode(line)
            message = row.get("message")
            usage = message.get("usage") if isinstance(message, dict) else None
            parts = [usage.get(key) for key in ("input_tokens", "cache_read_input_tokens",
                                                "cache_creation_input_tokens")] if isinstance(usage, dict) else []
            return (row.get("type") == "assistant" and not row.get("isSidechain")
                    and message.get("id") == reading.get("call") and row.get("timestamp") == reading.get("reading_at")
                    and len(parts) == 3 and all(type(part) is int and part >= 0 for part in parts)
                    and sum(parts) == reading["tokens"])
        require(any(appended_reading(line) for line in raw[before["size"]:].splitlines()),
                "native-load-gauge-not-appended")
        supplied = self.proof.get("first_gauge")
        require(isinstance(supplied, dict) and all(supplied.get(key) == reading.get(key)
                    for key in ("tokens", "model", "reading_at", "call")), "native-load-gauge-mismatch")
        self.reference(self.state["i4_postimage"], SMALL * 16)
        observed, _ = self.instrument("I4")
        tail_rows = [self.notice.decode(line) for line in raw[before["size"]:].splitlines()]
        kinds = {}
        for row in tail_rows:
            key = str(row.get("type"))
            kinds[key] = kinds.get(key, 0) + 1
        require(observed == {"appended": len(tail_rows), "by_type": kinds}, "native-i4-clean-append-required")
        self.state.update(phase="loaded", appended=current, first_gauge=reading)
        self.save()

    def restore_target(self, name):
        """Resume only a recorded staged inode or its known rename postimage."""
        original = self.preimages[name]
        current = self.current(name)
        restores = self.state.setdefault("restores", {})
        if name not in restores and native_same(current, original, False):
            return
        path = self.targets[name]
        stage = path.with_name(path.name + ".NEW")
        if name not in restores:
            require(current == self.state["rollback_initial"][name], "native-restore-preimage-changed")
            require(not os.path.lexists(stage), "native-restore-unknown-stage")
            raw, _ = native_read(self.roots[0] / self.batch / (self.operation + "-" + name))
            require(digest(raw) == original["sha256"], "native-restore-custody-changed")
            self.write(stage, raw, (original["uid"], original["gid"]))
            restores[name] = {"staged": native_snapshot(stage)}
            self.save()
        record = restores[name]
        if "installed" in record:
            require(native_same(self.current(name), record["installed"]), "native-restored-postimage-changed")
            return
        if os.path.lexists(stage):
            require(native_same(native_snapshot(stage), record["staged"]), "native-restore-stage-changed")
            require(self.current(name) == self.state["rollback_initial"][name], "native-restore-target-changed")
            self.refresh_at_act()
            os.replace(stage, path)
            self.sync(self.store)
        restored = self.current(name)
        require(native_same(restored, record["staged"], False)
                and (restored["dev"], restored["ino"]) == (record["staged"]["dev"], record["staged"]["ino"]),
                "native-restore-unknown-postimage")
        record["installed"] = restored
        self.save()

    def rollback(self):
        require(self.state["phase"] in ("custodied", "install-prepared", "install-renamed", "installed", "loaded",
                                        "rollback-prepared", "rollback-donor-pending", "rollback-restored", "rolled-back"),
                "native-rollback-phase")
        self.quiescence()
        self.unchanged_donor()
        self.custody_members(self.members())
        destination = self.current("destination")
        final_readback = self.state["phase"] in ("rollback-restored", "rolled-back")
        if self.state["phase"] in ("rollback-prepared", "rollback-donor-pending", "rollback-restored", "rolled-back"):
            require(self.state.get("rollback_go_sha256") == self.go_sha, "native-rollback-resume-go-changed")
        else:
            require(self.go.get("destination_sha256") == destination["sha256"], "native-rollback-go-postimage")
            if os.path.lexists(self.stage):
                require(self.state["phase"] == "install-prepared"
                        and native_same(native_snapshot(self.stage), self.state["staged"])
                        and native_same(destination, self.preimages["destination"]), "native-rollback-unknown-stage")
                # Only the recorded, rebuildable candidate stage, after custody.
                self.stage.unlink()
                self.sync(self.store)
            installed = self.state.get("installed")
            if installed is None and self.state["phase"] == "install-prepared":
                staged = self.state.get("staged")
                if (staged and native_same(destination, staged, False)
                        and (destination["dev"], destination["ino"]) == (staged["dev"], staged["ino"])):
                    installed = destination
            if installed is not None and destination["sha256"] != installed["sha256"]:
                raw, _ = native_read(self.targets["destination"])
                require((destination["dev"], destination["ino"]) == (installed["dev"], installed["ino"])
                        and digest(raw[:installed["size"]]) == installed["sha256"], "native-rollback-unknown-destination")
                require(self.proof.get("appended_sha256") == destination["sha256"], "native-rollback-append-evidence-required")
                item = {"name": self.operation + "-appended-" + destination["sha256"][:12],
                        "path": str(self.targets["destination"]), "sha256": destination["sha256"]}
                self.custody_members([item], add=True)
                self.state["retained_append"] = item
            elif installed is not None:
                require(native_same(destination, installed), "native-rollback-installed-identity-changed")
            else:
                require(native_same(destination, self.preimages["destination"]), "native-rollback-pristine-changed")
            self.state.update(phase="rollback-prepared", rollback_go_sha256=self.go_sha,
                              rollback_initial={name: self.current(name) for name in self.targets})
            self.save()
        if not final_readback:
            self.restore_target("destination")
            if self.current("donor") == {"type": "absent"} or "donor" in self.state.get("restores", {}):
                require(self.go.get("restore_absent_donor") is True, "native-donor-restore-go-required")
                if self.state["phase"] != "rollback-donor-pending":
                    # The first rename invalidates the old two-target witness.
                    # Obtain fresh I1 evidence before restoring the other file.
                    self.state["phase"] = "rollback-donor-pending"
                    self.save()
                    return
                self.restore_target("donor")
        self.unchanged_donor()
        require(native_same(self.current("destination"), self.preimages["destination"], False), "native-rollback-inventory-mismatch")
        self.listing(restored=True)
        if "retained_append" in self.state:
            self.custody_members([self.state["retained_append"]])
        if final_readback:
            observed, binding = self.instrument("I5")
            require(isinstance(observed, dict) and set(observed) == {"differences", "notes"}
                    and observed["differences"] == [] and isinstance(observed["notes"], list),
                    "native-i5-inverse-not-clear")
            self.state.update(phase="rolled-back", i5=binding)
        else:
            # The external inverse reader needs the restored files and a fresh
            # post-restore I1. Its second call alone can close the operation.
            self.state.update(phase="rollback-restored", restored_at_ns=time.time_ns())
        self.save()

    def run(self):
        if self.args.native_export_instruments and not os.path.lexists(self.directory):
            require(self.action == "disposable-exercise", "native-initial-export-action")
            self.publish_instruments()
            return {"schema": "rotate-native/1", "status": "stop", "action": self.action, "dry_run": False,
                    "phase": "awaiting-instruments", "resident_mind": "NOT APPLICABLE", "notebook": "NOT APPLICABLE",
                    "launcher_join": "NOT APPLICABLE", "operator_accepted": False,
                    "provider_started": False, "compaction_triggered": False}
        self.notice.parent_chain(self.directory)
        # Only the mapped logs lane is created. No default state elsewhere.
        for directory in (self.room / "logs", self.room / "logs/rotate", self.directory):
            if not os.path.lexists(directory):
                directory.mkdir(mode=0o700)
            self.notice.private_node(directory, True)
        lock_path = self.directory / "operation.lock"
        self.git_private(lock_path.parent, lock_path)
        if os.path.lexists(lock_path):
            self.notice.private_node(lock_path)
        fd = os.open(lock_path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
        try:
            lock_node = self.notice.private_node(lock_path)
            require(node_id(lock_node) == node_id(os.fstat(fd)), "native-operation-lock-replaced")
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise Refused("native-operation-busy") from None
            require(not os.path.lexists(self.directory / ".state.NEW"), "native-pending-state-write")
            require(not os.path.lexists(self.directory / ".packets.NEW"), "native-pending-packet-export")
            if os.path.lexists(self.state_path):
                self.state = self.notice.decode(native_read(self.state_path, SMALL * 16)[0])
                require(all(self.state.get(k) == v for k, v in {
                    "schema": "rotate-native-state/1", "operation": self.operation,
                    "plan_sha256": self.plan_sha}.items()), "native-checkpoint-binding")
                raw, _ = native_read(self.preimages_path, SMALL * 16)
                require(digest(raw) == self.state.get("preimages_sha256"), "native-preimages-changed")
                self.preimages = self.notice.decode(raw)
                self.instrument("I2", self.state["i2"])
                self.root_identities()
            else:
                require(self.action == "disposable-exercise" and not os.path.lexists(self.preimages_path),
                        "native-admission-required")
            actions = {"disposable-exercise": self.admission, "custody": self.preserve,
                       "install": self.installation, "load": self.load, "rollback": self.rollback}
            if self.args.native_export_instruments:
                require(self.state is not None, "native-admission-required")
                if self.state["phase"] == "install-prepared" and os.path.lexists(self.stage):
                    require(native_same(native_snapshot(self.stage), self.state["staged"]), "native-stage-changed")
            else:
                actions[self.action]()
            self.publish_instruments()
            return {"schema": "rotate-native/1", "status": "stop", "action": self.action,
                    "dry_run": False,
                    "phase": self.state["phase"], "state_sha256": digest(json_bytes(self.state)),
                    "custody_manifest_sha256": self.state.get("custody_manifest_sha256"),
                    "resident_mind": "NOT APPLICABLE", "notebook": "NOT APPLICABLE",
                    "launcher_join": "NOT APPLICABLE", "operator_accepted": False,
                    "provider_started": False, "compaction_triggered": False}
        finally:
            os.close(fd)


def native_entry(args):
    try:
        result = NativeOperation(args).run()
        rc = 0
    except (Refused, OSError, ValueError, KeyError, TypeError, RecursionError) as error:
        result = {"schema": "rotate-native/1", "status": "refused", "action": args.native_action,
                  "reason": str(error) if isinstance(error, Refused) else "native-input-or-io-refused",
                  "operator_accepted": False, "provider_started": False, "compaction_triggered": False}
        rc = 2
    except Exception:
        result = {"schema": "rotate-native/1", "status": "refused", "action": args.native_action,
                  "reason": "native-dependency-refused", "operator_accepted": False}
        rc = 2
    print(json.dumps(result, sort_keys=True))
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="rotate", description="Fixture rehearsal or explicitly hash-gated disposable operations")
    ap.add_argument("--phase", type=int, choices=range(10), default=0)
    ap.add_argument("--dry-run", action="store_true", help="fixture rehearsal; forbids a native action even with --native-apply")
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
    ap.add_argument("--native-action", choices=tuple(NATIVE_GO), help="refused by default; disposable actions require all native gates")
    ap.add_argument("--native-apply", action="store_true", help="explicit disposable operation selection; grants no authority or default go")
    ap.add_argument("--native-plan", help="explicit private disposable operation plan; no default")
    ap.add_argument("--native-plan-sha256", help="exact operation-plan digest")
    ap.add_argument("--native-go", help="separate named go record for this one action")
    ap.add_argument("--native-go-sha256", help="exact named-go digest")
    ap.add_argument("--native-proof", help="private, current instrument evidence for this action")
    ap.add_argument("--native-proof-sha256", help="exact instrument-evidence digest")
    ap.add_argument("--native-export-instruments", action="store_true",
                    help="export initial inert I1/I2 packets under the named disposable go, without admission")
    return ap


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.native_plan is not None:
        return native_entry(args)
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
