#!/usr/bin/env python3
"""W6 slice 7: the native producer for phases 4 and 5 of the disposable exercise.

It makes the files slice 6's engine consumes and nothing else: the window, the capsule, the candidate and the
`rotate-native-gates/1` record, with any media the window carries, all inside the operation's evidence folder
E = <room>/storage/active/<operation>/. The design is `w6-slice7-producer-design.md` revision 1 (d0fa31cf), which
serves `w6-adapter-design.md` (e937ebb3), phases 4 and 5. It joins the engine only through those files.

Disposable variant only. A donor or destination that is any registered resident's session is refused before
anything but the registry and the request is read (the Manager's O1 ruling, condition 3).

Reads: the request, the registry, the phase-0 record and the cut reason (small, private, hash-bound); the gauge's
reviewed window table; the donor D in one streaming pass, hashed whole and bracketed by two lstat readings, keeping
only the rows after its boundary (bounded); the destination T, hashed only.
Writes, only into E, each by exclusive create and 0600: window.jsonl, window.json, capsule.txt, candidate.jsonl,
gates.json, builder-output.txt and media/. A temporary build file is made and removed in E. Nothing is overwritten.

usage: python3 -I -B prepare.py --request E/REQUEST.json --request-sha256 HEX [--dry-run]
  --dry-run   phase 4 and every check before it, writing nothing; phase 5 needs the builder's files, so it is not run
exit: 0 done; 2 refused (nothing written); 3 a write failed part way (what exists is reported, nothing removed)."""
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
from fractions import Fraction
from pathlib import Path

REQUEST_SCHEMA = "rotate-native-prepare/1"
PHASE0_SCHEMA = "rotate-native-phase0/1"
WINDOW_SCHEMA = "rotate-native-window/1"
GATES_SCHEMA = "rotate-native-gates/1"          # rotate.py e7d926af, line 1519
REPORT_SCHEMA = "rotate-native-prepare-report/1"
GATE_KEYS = ("trigger", "closeout", "operator_compaction", "window", "static", "media")   # line 1527
DONOR_LIMIT = 64 * 1024 * 1024                   # the engine's NATIVE_LIMIT: it reads no larger donor
LINE_LIMIT = 16 * 1024 * 1024
WINDOW_ROWS, WINDOW_BYTES = 4096, 8 * 1024 * 1024
SMALL = 1024 * 1024
LABEL = "W6 disposable destination"
DIGEST = re.compile(r"[0-9a-f]{64}")
SID = re.compile(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}")   # the engine's NATIVE_SID
# myself.py's one IDE-notice shape (lines 33 and 34), which the plugin puts before a prompt while a file is open in
# the editor; the suite holds these equal to myself.py's own patterns.
IDE_NOTICE_RE = re.compile(r"\s*<(ide_opened_file|ide_selection)>.*?</\1>", re.DOTALL)
IDE_NOTICE_CLOSE_RE = re.compile(r"</(?:ide_opened_file|ide_selection)>")
OPERATION = re.compile(r"[a-z][a-z0-9-]{1,47}")                    # the engine's operation name
OUTPUTS = ("window.jsonl", "window.json", "capsule.txt", "candidate.jsonl", "gates.json", "builder-output.txt", "media")
BUILD = ".candidate.build"


class Refused(Exception):
    pass


def require(condition, reason):
    if not condition:
        raise Refused(reason)


def sibling(name):
    spec = importlib.util.spec_from_file_location("prepare_" + name, Path(__file__).with_name(name + ".py"))
    if spec is None or spec.loader is None:
        raise Refused("dependency-unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def plain(raw):
    """An absolute path with no '..', no link and no change by resolution (the engine's native_path)."""
    require(isinstance(raw, str) and raw and "\x00" not in raw, "path-required")
    path = Path(raw)
    require(path.is_absolute() and ".." not in path.parts and path == path.resolve(), "plain-absolute-path-required")
    return path


def read_small(notice, path, expected):
    """A private, hash-bound small file, read once on its own descriptor."""
    node = notice.private_node(path)
    require(node.st_size <= SMALL, "small-file-too-large")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as handle:
        st = os.fstat(handle.fileno())
        require((st.st_dev, st.st_ino) == (node.st_dev, node.st_ino), "small-file-replaced")
        raw = handle.read(SMALL + 1)
    require(len(raw) <= SMALL and digest(raw) == expected, "small-file-hash")
    return raw


def same(a, b):
    return all(getattr(a, k) == getattr(b, k) for k in ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns"))


def usage_tokens(row):
    """gauge.read_claude's own reading of one row: a non-sidechain assistant row whose message.usage gives
    input, cache read and cache creation as non-negative integers with a non-zero sum."""
    if row.get("type") != "assistant" or row.get("isSidechain"):
        return None
    message = row.get("message")
    usage = message.get("usage") if isinstance(message, dict) else None
    if not isinstance(usage, dict):
        return None
    parts = [usage.get(k) for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")]
    if not all(type(p) is int and p >= 0 for p in parts) or sum(parts) == 0:
        return None
    return sum(parts), message.get("model")


def user_prompt(row):
    """rotate.py's user_prompt (e7d926af), written fresh here (O2): a genuine operator prompt. Leading IDE notices
    are passed over first, by myself.py's exact shape, so a prompt sent while a file is open in the editor is still
    genuine; a closing notice tag left after them, or nothing after them, is not (claudine.md section 234)."""
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
    rest, passed = content, False
    notice = IDE_NOTICE_RE.match(rest)
    while notice:
        rest, passed = rest[notice.end():], True
        notice = IDE_NOTICE_RE.match(rest)
    if passed and (not rest.strip() or IDE_NOTICE_CLOSE_RE.search(rest)):
        return False
    return not rest.lstrip().startswith(("<", "/", "# Context from my IDE", "Rotate now", "Close out now"))


def stream_donor(notice, path, sha, session, project):
    """One bounded pass: the whole file hashed, only the rows after the boundary kept, nothing else retained but
    the last usage reading before the boundary. Any change during the read is a stop, never an absence."""
    before = notice.private_node(path)
    require(before.st_size <= DONOR_LIMIT, "donor-too-large")
    h = hashlib.sha256()
    kept, kept_bytes, boundaries, rows = [], 0, 0, 0
    pre, last_time = None, None
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as handle:
        require(same(os.fstat(handle.fileno()), before), "donor-opened-other")
        while True:
            line = handle.readline(LINE_LIMIT + 1)
            if not line:
                break
            require(len(line) <= LINE_LIMIT and line.endswith(b"\n"), "donor-line-unbounded-or-unterminated")
            h.update(line)
            row = notice.decode(line)
            for key in ("sessionId", "session_id"):
                if key in row:
                    require(row[key] == session, "donor-foreign-session")
            if "cwd" in row:
                require(row["cwd"] == str(project), "donor-other-project")
            if isinstance(row.get("timestamp"), str):
                last_time = row["timestamp"]
            if row.get("type") == "system" and row.get("subtype") == "compact_boundary" and not row.get("isSidechain"):
                boundaries += 1
                kept, kept_bytes = [], 0
            if boundaries:
                kept.append((rows, row))
                kept_bytes += len(line)
                require(len(kept) <= WINDOW_ROWS and kept_bytes <= WINDOW_BYTES, "window-over-bound")
            else:
                reading = usage_tokens(row)
                if reading:
                    pre = {"row": rows, "tokens": reading[0], "model": reading[1], "reading_at": row.get("timestamp")}
            rows += 1
        require(same(os.fstat(handle.fileno()), before), "donor-changed-during-read")
    require(same(path.lstat(), before), "donor-changed-during-read")
    require(h.hexdigest() == sha, "donor-hash")
    return {"kept": kept, "boundaries": boundaries, "pre": pre, "rows": rows, "last_time": last_time}


def hash_file(notice, path, sha):
    """T is hashed only; its content is not parsed here (the engine reads its first exchange itself)."""
    before = notice.private_node(path)
    require(before.st_size <= DONOR_LIMIT, "destination-too-large")
    h = hashlib.sha256()
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as handle:
        require(same(os.fstat(handle.fileno()), before), "destination-opened-other")
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
        require(same(os.fstat(handle.fileno()), before), "destination-changed-during-read")
    require(same(path.lstat(), before) and h.hexdigest() == sha, "destination-hash")


def capsule_text(operation, destination):
    return ("Disposable exercise\nThis container is the W6 disposable destination of operation " + operation
            + ", session " + destination + ". It is not a resident: no registry identity and no mind apply"
            " (phase 2 NOT APPLICABLE).\n\nFirst turn\nSay in one line that this conversation is loaded,"
            " then answer the operator.\n")


class Request:
    def __init__(self, path, sha):
        self.notice = sibling("notice")
        self.path = plain(path)
        raw = read_small(self.notice, self.path, sha)
        r = self.notice.decode(raw)
        require(r.get("schema") == REQUEST_SCHEMA, "request-schema")
        self.operation = r.get("operation")
        require(isinstance(self.operation, str) and OPERATION.fullmatch(self.operation), "request-operation")
        self.room = plain(r.get("room"))
        self.evidence = self.room / "storage" / "active" / self.operation
        require(self.path.parent == self.evidence, "request-evidence-home")
        self.notice.private_node(self.evidence, True)
        self.project = plain(r.get("project"))
        require(stat.S_ISDIR(self.project.lstat().st_mode), "project-folder-required")
        require(not self.project.is_relative_to(self.room) and not self.room.is_relative_to(self.project),
                "project-overlaps-room")
        self.targets = {}
        for name in ("donor", "destination"):
            t = r.get(name)
            require(isinstance(t, dict) and isinstance(t.get("session_id"), str) and SID.fullmatch(t["session_id"])
                    and isinstance(t.get("sha256"), str) and DIGEST.fullmatch(t["sha256"]), "request-" + name)
            p = plain(t.get("path"))
            require(p.name == t["session_id"] + ".jsonl", "request-" + name + "-store-mapping")
            self.targets[name] = {"path": p, "session_id": t["session_id"], "sha256": t["sha256"]}
        require(self.targets["donor"]["session_id"] != self.targets["destination"]["session_id"]
                and self.targets["donor"]["path"].parent == self.targets["destination"]["path"].parent,
                "request-two-containers-one-store")
        # O1 ruling, condition 3: no registered resident, as donor or destination, before anything else is read.
        registry = json.loads((self.room / "ops" / "etc" / "resident-identities.json").read_text(encoding="utf-8"))
        residents = {i.get("session_id") for i in registry.get("identities", []) if isinstance(i, dict)}
        require(not any(t["session_id"] in residents for t in self.targets.values()), "registered-resident-refused")
        self.refs = {}
        for name in ("phase0", "reason"):
            ref = r.get(name)
            require(isinstance(ref, dict) and isinstance(ref.get("sha256"), str) and DIGEST.fullmatch(ref["sha256"]),
                    "request-" + name)
            p = plain(ref.get("path"))
            require(p.parent == self.evidence, "request-" + name + "-evidence-home")
            self.refs[name] = (p, ref["sha256"])
        self.built_at = r.get("built_at")
        self.notice.stamp(self.built_at)
        for name in OUTPUTS + (BUILD,):
            require(not os.path.lexists(self.evidence / name), "output-exists")


def phase4(req, gauge, closeout):
    """The window, as rotate's window_ready applies the adapter design's phase-4 row to fixtures (O2)."""
    stamp = req.notice.stamp
    donor = req.targets["donor"]
    hash_file(req.notice, req.targets["destination"]["path"], req.targets["destination"]["sha256"])
    seen = stream_donor(req.notice, donor["path"], donor["sha256"], donor["session_id"], req.project)
    phase0 = req.notice.decode(read_small(req.notice, *req.refs["phase0"]))
    reason = read_small(req.notice, *req.refs["reason"])
    require(seen["boundaries"] == 1, "exactly-one-boundary-required")
    kept = seen["kept"]
    boundary_at, boundary = kept[0]
    meta = boundary.get("compactMetadata")
    require(isinstance(meta, dict) and meta.get("trigger") == "manual", "operator-compaction-manual-required")
    pre = seen["pre"]
    require(pre is not None and isinstance(pre["model"], str), "pre-compaction-reading-required")
    table = gauge.window_table(gauge.SPEC)
    require(pre["model"] in table, "no-reviewed-window-for-model")
    window_size = table[pre["model"]]["window"]
    require(pre["tokens"] >= Fraction(str(closeout.DUE)) * window_size, "trigger-below-due")
    band = closeout.pressure_band(pre["tokens"], window_size)
    require(band is not None, "closeout-band-not-reached")
    require(all(phase0.get(k) == v for k, v in {
        "schema": PHASE0_SCHEMA, "operation": req.operation, "session_id": donor["session_id"],
        "tokens": pre["tokens"], "model": pre["model"], "window": window_size,
        "reading_at": pre["reading_at"]}.items()), "phase0-record-not-the-reading")
    require(stamp(pre["reading_at"]) < stamp(boundary.get("timestamp")), "compaction-before-the-reading")
    summaries = [i for i, (_, row) in enumerate(kept) if row.get("isCompactSummary") is True]
    require(len(summaries) == 1, "exact-compaction-summary-required")
    s = summaries[0]
    cuts = [i for i in range(s + 1, len(kept)) if user_prompt(kept[i][1])]
    require(bool(cuts), "genuine-user-cut-required")
    c = cuts[0]
    require(any(r.get("type") == "assistant" and (r.get("message") or {}).get("role") == "assistant"
                and not r.get("isMeta") and not r.get("isSidechain") for _, r in kept[c + 1:]),
            "substantive-exchange-required")
    selected = copy.deepcopy([kept[0][1], kept[s][1], *(row for _, row in kept[c:])])
    require(selected[0].get("parentUuid") is None, "boundary-not-root")
    require(isinstance(selected[1].get("uuid"), str) and isinstance(selected[2].get("uuid"), str),
            "window-parent-evidence-required")
    selected[2]["parentUuid"] = selected[1]["uuid"]    # only the cut's parent link changes
    pending = set()
    for r in selected:
        content = (r.get("message") or {}).get("content") if isinstance(r.get("message"), dict) else None
        for block in content if isinstance(content, list) else []:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                require(isinstance(block.get("id"), str) and block["id"] not in pending, "window-tool-pairs")
                pending.add(block["id"])
            elif isinstance(block, dict) and block.get("type") == "tool_result":
                require(block.get("tool_use_id") in pending, "window-tool-pairs")
                pending.discard(block["tool_use_id"])
    require(not pending, "window-tool-pairs")
    inside = [usage_tokens(r) for r in selected[2:]]
    inside = [u for u in inside if u]
    require(bool(inside), "window-usage-reading-required")
    capsule = capsule_text(req.operation, req.targets["destination"]["session_id"])
    estimate = inside[-1][0] + len(capsule.encode())
    require(0 < estimate <= Fraction(1, 5) * window_size, "wake-estimate-over-budget")
    require(stamp(req.built_at) >= stamp(seen["last_time"]), "built-before-the-donor-ended")
    raw = b"".join(json.dumps(r, separators=(",", ":")).encode() + b"\n" for r in selected)
    record = {"schema": WINDOW_SCHEMA, "operation": req.operation, "donor_sha256": donor["sha256"],
              "rows": {"boundary": boundary_at, "summary": kept[s][0], "cut": kept[c][0], "last": kept[-1][0],
                       "donor_total": seen["rows"]},
              "omitted": {"from": kept[s][0] + 1, "to": kept[c][0] - 1, "count": kept[c][0] - kept[s][0] - 1},
              "rows_sha256": digest(raw), "reason_sha256": digest(reason),
              "estimate": {"tokens": estimate, "window": window_size, "model": pre["model"],
                           "method": "the window's last usage reading (input + cache read + cache creation, as "
                                     "gauge.read_claude sums them) plus the capsule's bytes as an upper bound"}}
    reading = {"tokens": pre["tokens"], "window": window_size, "band": band,
               "source": {"donor_row": pre["row"], "timestamp": pre["reading_at"],
                          "phase0_sha256": req.refs["phase0"][1]}}
    return {"rows": selected, "raw": raw, "record": record, "capsule": capsule, "reading": reading,
            "phase0": phase0}


def static_checks(req, raw, rows, capsule, window_rows, media_dir, externalizer, successor, mind):
    """rotate's static_gates list (e7d926af), written fresh here (O2), for the disposable candidate."""
    results = {}

    def check(name, value):
        results[name] = bool(value)
        require(bool(value), "static-" + name)

    dest = req.targets["destination"]["session_id"]
    check("terminated", raw.endswith(b"\n"))
    check("parse", [req.notice.decode(line) for line in raw.splitlines()] == rows)
    ids, uuids, seen, orientations, pending, pointers = [], [], set(), [], set(), []
    inline = 0

    def walk(value, key=None):
        nonlocal inline
        if isinstance(value, dict):
            if value.get("type") == "tool_use":
                check("tool-use-unique", isinstance(value.get("id"), str) and value["id"] not in pending)
                pending.add(value["id"])
            if value.get("type") == "tool_result":
                check("tool-result-matched", value.get("tool_use_id") in pending)
                pending.discard(value.get("tool_use_id"))
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
        if "cwd" in row:
            check("working-directory", row["cwd"] == str(req.project))
        message = row.get("message")
        if (isinstance(message, dict) and isinstance(message.get("content"), str)
                and message["content"].lstrip().startswith("<session_clinic_orientation>")):
            orientations.append(row)
    check("identities", bool(ids) and set(ids) == {dest})
    check("donor-structural-residue", successor.count_residue(rows, req.targets["donor"]["session_id"])[0] == 0)
    check("boundary-head", rows[0].get("type") == "system" and rows[0].get("subtype") == "compact_boundary")
    check("tool-pairs", not pending)
    check("orientation-count", len(orientations) == 1)
    o = orientations[0]
    check("orientation-text", o["message"]["content"]
          == "<session_clinic_orientation>\n" + capsule + "\n</session_clinic_orientation>")
    check("orientation-time", o.get("timestamp") == req.built_at)
    check("orientation-working-directory", o.get("cwd") == str(req.project))
    check("plain-label-last", [r.get("type") for r in rows[-2:]] == ["custom-title", "agent-name"]
          and rows[-2].get("customTitle") == LABEL and rows[-1].get("agentName") == LABEL)
    check("orientation-privacy", not mind.MEDICAL_RE.search(capsule) and not mind.SECRET_RE.search(capsule))
    check("carried-window", len(rows) == len(window_rows) + 3)

    def texts(items):
        out = []
        for item in items:
            content = (item.get("message") or {}).get("content")
            if isinstance(content, str):
                out.append(content)
            elif isinstance(content, list):
                out.extend(b["text"] for b in content if isinstance(b, dict) and b.get("type") == "text"
                           and isinstance(b.get("text"), str) and not b["text"].startswith("[media externalized "))
        return out
    check("carried-text", texts(rows[:len(window_rows)]) == texts(window_rows))
    media = {}

    def mcheck(name, value):
        media[name] = bool(value)
        require(bool(value), "media-" + name)

    mcheck("inline", inline == 0 and externalizer.failed == 0)
    for sha, name in externalizer.seen.items():
        path = media_dir / name
        req.notice.private_node(path)
        mcheck("pointer-file", path.parent == media_dir and digest(path.read_bytes()) == sha)
    mcheck("pointer-count", externalizer.blocks == 0 or bool(externalizer.seen))
    mcheck("pointer-links", len(pointers) == externalizer.blocks
           and all(any("preserved at " + str(media_dir / n) + "]" in p for n in externalizer.seen.values())
                   for p in pointers))
    return results, media


def create(path, raw):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        view = memoryview(raw)
        while view:
            view = view[os.write(fd, view):]
        os.fsync(fd)
    finally:
        os.close(fd)
    return digest(raw)


def phase5(req, w, written):
    """The build: successor.main in process on window.jsonl alone, the Externalizer into E/media, the labels."""
    successor, media, mind = sibling("successor"), sibling("media"), sibling("mind")
    E = req.evidence
    exposed = mind.git_exposed(req.room, [E / name for name in OUTPUTS + (BUILD,)])
    require(not exposed, "evidence-git-exposed")
    window_path = E / "window.jsonl"
    written.append("window.jsonl")
    create(window_path, w["raw"])
    build = E / BUILD
    written.append(BUILD)
    create(build, b"")
    argv = ["successor", "--donor", str(window_path), "--out", str(build),
            "--session-id", req.targets["destination"]["session_id"], "--cwd", str(req.project),
            "--orientation", w["capsule"], "--trim-to-last-compaction"]
    captured = io.StringIO()
    saved = sys.argv
    try:
        sys.argv = argv
        with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):
            try:
                successor.main()
            except SystemExit as e:
                if e.code not in (None, 0):
                    raise Refused("builder-refused") from None
    finally:
        sys.argv = saved
    written.append("builder-output.txt")
    create(E / "builder-output.txt", captured.getvalue().encode("utf-8"))
    rows = [req.notice.decode(line) for line in build.read_bytes().splitlines()]
    os.unlink(build)
    written.remove(BUILD)
    rows[-1]["timestamp"] = req.built_at          # only the new orientation's time; donor history keeps its own
    media_dir = E / "media"
    written.append("media")
    os.mkdir(media_dir, 0o700)
    externalizer = media.Externalizer(media_dir, str(media_dir), req.operation)
    for r in rows:
        externalizer.walk(r)
    for kind, field in (("custom-title", "customTitle"), ("agent-name", "agentName")):
        rows.append({"type": kind, field: LABEL, "sessionId": req.targets["destination"]["session_id"],
                     "timestamp": req.built_at})
    raw = b"".join(json.dumps(r, separators=(",", ":")).encode() + b"\n" for r in rows)
    static, media_results = static_checks(req, raw, rows, w["capsule"], w["rows"], media_dir, externalizer, successor,
                                          mind)
    # The plan names four fixed artifacts and one per media file; counted before any record exists (review finding 1).
    require(4 + len(externalizer.seen) <= 64, "too-many-artifacts")
    written.append("candidate.jsonl")
    candidate_sha = create(E / "candidate.jsonl", raw)
    written.append("capsule.txt")
    capsule_sha = create(E / "capsule.txt", w["capsule"].encode())
    written.append("window.json")
    window_sha = create(E / "window.json", json.dumps(w["record"], indent=1, sort_keys=True).encode() + b"\n")
    gates = {"schema": GATES_SCHEMA, "phase": 5, "operation": req.operation, "built_at": req.built_at,
             "donor_sha256": req.targets["donor"]["sha256"], "pristine_sha256": req.targets["destination"]["sha256"],
             "candidate_sha256": candidate_sha,
             "gates": {k: True for k in GATE_KEYS},
             "detail": {"static": static, "media": media_results,
                        "trigger": {"tokens": w["reading"]["tokens"], "window": w["reading"]["window"],
                                    "due": str(sibling("closeout").DUE)},
                        "window": {"rows_sha256": w["record"]["rows_sha256"], "estimate": w["record"]["estimate"]}},
             "provenance": {"closeout": {"evidence": "band reading", **w["reading"],
                                         "overlap": "the same genuine pre-compaction reading sets trigger",
                                         "delivered_card": "NOT APPLICABLE"}}}
    written.append("gates.json")
    gates_sha = create(E / "gates.json", json.dumps(gates, indent=1, sort_keys=True).encode() + b"\n")
    artifacts = [{"name": "window", "path": str(E / "window.json"), "sha256": window_sha},
                 {"name": "capsule", "path": str(E / "capsule.txt"), "sha256": capsule_sha},
                 {"name": "gates", "path": str(E / "gates.json"), "sha256": gates_sha},
                 {"name": "window-rows", "path": str(window_path), "sha256": digest(w["raw"])}]
    for sha, name in sorted(externalizer.seen.items()):
        artifacts.append({"name": "media-" + sha[:12], "path": str(media_dir / name), "sha256": sha})
    return {"candidate": {"path": str(E / "candidate.jsonl"), "sha256": candidate_sha}, "artifacts": artifacts,
            "gates": gates["gates"], "media_files": externalizer.written, "rows": len(rows)}


def main(argv=None):
    ap = argparse.ArgumentParser(description="W6 slice 7: the native producer for phases 4 and 5")
    ap.add_argument("--request", required=True)
    ap.add_argument("--request-sha256", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    written = []
    try:
        require(DIGEST.fullmatch(a.request_sha256 or "") is not None, "request-hash-required")
        req = Request(a.request, a.request_sha256)
        w = phase4(req, sibling("gauge"), sibling("closeout"))
        report = {"schema": REPORT_SCHEMA, "operation": req.operation, "written": False,
                  "window": {k: w["record"][k] for k in ("rows", "omitted", "rows_sha256", "estimate")},
                  "closeout": {"evidence": "band reading", "band": w["reading"]["band"],
                               "delivered_card": "NOT APPLICABLE"}}
        if not a.dry_run:
            old = os.umask(0o077)
            try:
                report["plan"] = phase5(req, w, written)
            finally:
                os.umask(old)
            report["written"] = True
    except Exception as e:
        # A refusal is this module's Refused or a sibling's (notice raises its own class of that name).
        refusal = type(e).__name__ == "Refused"
        if written:
            print(json.dumps({"failed": str(e) if refusal else type(e).__name__, "present": written}))
            return 3
        if not refusal and not isinstance(e, OSError):
            raise
        print("prepare: refused: " + (str(e) if refusal else type(e).__name__), file=sys.stderr)
        return 2
    print(json.dumps(report, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
