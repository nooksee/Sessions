#!/usr/bin/env python3
"""Build a current-version, CLI-native Codex successor from a copied session body.

This is a variant of the house rotation method, not a replacement for it. Use
`build_codex_rotation.py` when donor and target sit on the same machine, on the
same provider surface, at the same CLI version, and the operator has created the
target container by hand. Use this script when none of that is true.

The Remote Device tablet body of 2026-07-22 is the case that motivated it:

- the donor ran VS Code on Windows (`codex_vscode`, `cwd c:\\Users\\Highs`) at
  CLI `0.145.0-alpha.27`; the successor must run the Codex CLI at the current
  version, so scaffolding cannot simply be carried across;
- no container can be created by hand on the destination, because the
  destination is a tablet the operator holds and this agent must not touch. The
  scaffold therefore comes from a genuine container minted by the current CLI on
  this machine, and only its `session_meta` is adopted;
- that scaffold was minted on Linux. Its injected environment rows -- host skill
  list, recommended plugins, multi-agent developer blocks, `world_state`, and
  `turn_context` -- describe THIS machine. Carrying them onto a Windows tablet
  would hand the resident a false picture of where it is standing. They are
  dropped, because Codex regenerates all of them on resume; the donor itself is
  the proof, having regenerated its own set when it reopened on 2026-08-02.

Four classes are excluded from the donor, each for a stated reason rather than
by taste:

failed transport
    Turns whose `task_complete` carries an error and a null
    `last_agent_message`. In the donor these are the 2026-08-02 stream
    disconnection that left the operator's greeting unanswered, and the remote
    compaction that failed immediately after.

compaction artifacts
    The last compaction's `replacement_history`. It looks like recoverable
    history and is not: it preserves the user and developer items only, while
    the assistant half is sealed inside a single `compaction` item as
    `encrypted_content`. Replaying it would give the successor hundreds of
    operator turns with no replies between them. The substance belongs in the
    lineage capsule as prose, where it can be read.

encrypted or incompatible reasoning
    `reasoning` items carrying `encrypted_content`. That payload is bound to the
    session and account that produced it and cannot be decrypted or replayed
    anywhere else.

obsolete tool-call structures
    `function_call` / `custom_tool_call` pairs naming tools the current version
    no longer exposes. The donor calls `shell_command` and `apply_patch`; the
    current CLI calls `exec`. Calls and their outputs are always dropped
    together, so no output is ever orphaned from its call.

What survives is the dialogue: the user and assistant messages carried since the
last successful compaction, in order, with injected environment scaffolding
removed. The evidence body is opened read-only and is never modified.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import time
from pathlib import Path

# Injected context that Codex regenerates every turn. Matching is on the opening
# marker of the text, never on a substring that could appear in ordinary prose.
INJECTED_PREFIXES = (
    "<environment_context>",
    "<skills_instructions>",
    "<recommended_plugins>",
    "<permissions instructions>",
    "# Context from my IDE setup",
)


def load(path: Path) -> tuple[list[dict], int]:
    """Parse a rollout, tolerating rows damaged by a torn write."""
    rows: list[dict] = []
    damaged = 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            damaged += 1
    return rows, damaged


def dump(rows: list[dict], path: Path) -> None:
    """Write compact JSON lines, then fsync. Codex writes compact; match it."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def uuid7(when_ms: int) -> str:
    """Mint a UUIDv7 the way Codex does: 48-bit millisecond prefix, then random.

    The prefix matters. Codex session identifiers sort by time, and the session
    picker relies on that ordering, so a random v4 would file the successor in
    the wrong place in the operator's own list.
    """
    b = bytearray(secrets.token_bytes(16))
    b[0:6] = when_ms.to_bytes(6, "big")
    b[6] = 0x70 | (b[6] & 0x0F)          # version 7
    b[8] = 0x80 | (b[8] & 0x3F)          # RFC 4122 variant
    h = b.hex()
    return f"{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


def message_text(payload: dict) -> str:
    return " ".join(
        c.get("text", "")
        for c in payload.get("content", [])
        if isinstance(c, dict)
    )


def is_injected(payload: dict) -> bool:
    text = message_text(payload).lstrip()
    return any(text.startswith(p) for p in INJECTED_PREFIXES)


def last_compaction_index(rows: list[dict]) -> int:
    """Index of the last real compaction, or -1.

    A lineage capsule is also stored as a `compacted` row, so the marker is
    `window_number`, which only a provider compaction carries. Matching on the
    row type alone would cut the body at a capsule and discard everything the
    resident actually said.
    """
    marks = [
        i
        for i, r in enumerate(rows)
        if r.get("type") == "compacted" and r.get("payload", {}).get("window_number")
    ]
    return marks[-1] if marks else -1


def failed_turn_ids(rows: list[dict]) -> set[str]:
    """Turns whose completion carries an error and produced no agent message."""
    failed = set()
    for r in rows:
        p = r.get("payload", {})
        if p.get("type") != "task_complete":
            continue
        if p.get("error") and not p.get("last_agent_message"):
            tid = p.get("turn_id")
            if tid:
                failed.add(tid)
    return failed


def harvest(rows: list[dict], start: int, failed: set[str]) -> tuple[list[dict], dict]:
    """Keep the dialogue after `start`; count every exclusion by reason."""
    counts = {
        "kept": 0,
        "encrypted_reasoning": 0,
        "obsolete_tool_call": 0,
        "injected_context": 0,
        "failed_transport": 0,
        "non_dialogue": 0,
    }
    kept: list[dict] = []
    for r in rows[start + 1:]:
        rtype = r.get("type")
        p = r.get("payload", {})
        ptype = p.get("type") if isinstance(p, dict) else None

        if ptype == "reasoning":
            counts["encrypted_reasoning"] += 1
            continue
        if ptype in ("function_call", "function_call_output",
                     "custom_tool_call", "custom_tool_call_output"):
            counts["obsolete_tool_call"] += 1
            continue
        if ptype == "task_complete" and p.get("turn_id") in failed:
            counts["failed_transport"] += 1
            continue
        if rtype != "response_item" or ptype != "message":
            counts["non_dialogue"] += 1
            continue
        if p.get("role") not in ("user", "assistant"):
            counts["non_dialogue"] += 1
            continue
        if is_injected(p):
            counts["injected_context"] += 1
            continue

        payload = dict(p)
        # `internal_chat_message_metadata_passthrough` pins a message to a
        # turn identifier in the old session. It is optional metadata, and a
        # stale pointer is worse than an absent one.
        payload.pop("internal_chat_message_metadata_passthrough", None)
        kept.append({"timestamp": r.get("timestamp"), "type": "response_item",
                     "payload": payload})
        counts["kept"] += 1
    return kept, counts


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--evidence", required=True, type=Path,
                    help="copied donor body; opened read-only")
    ap.add_argument("--scaffold", required=True, type=Path,
                    help="container minted by the current CLI; supplies session_meta")
    ap.add_argument("--capsule", required=True, type=Path, help="lineage capsule text")
    ap.add_argument("--cwd", required=True, help="destination working directory")
    ap.add_argument("--originator", default="codex_cli")
    ap.add_argument("--source", default="cli")
    ap.add_argument("--out-dir", required=True, type=Path)
    args = ap.parse_args()

    evidence, ev_damaged = load(args.evidence)
    scaffold, sc_damaged = load(args.scaffold)
    if sc_damaged:
        raise SystemExit(f"scaffold has {sc_damaged} damaged row(s); refusing to build")
    if scaffold[0].get("type") != "session_meta":
        raise SystemExit("scaffold row 0 is not session_meta")

    donor_id = evidence[0]["payload"].get("id") or evidence[0]["payload"]["session_id"]
    now_ms = int(time.time() * 1000)
    new_id = uuid7(now_ms)
    window_id = uuid7(now_ms)
    stamp = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(now_ms / 1000)) + \
        f".{now_ms % 1000:03d}Z"

    meta = dict(scaffold[0]["payload"])
    meta.update({
        "session_id": new_id,
        "id": new_id,
        "timestamp": stamp,
        "cwd": args.cwd,
        "originator": args.originator,
        "source": args.source,
        "thread_source": "user",
        "context_window": {"window_id": window_id},
    })
    # The scaffold was minted in a throwaway directory on this machine. Any
    # field describing that repository would be a lie on the destination.
    for stale in ("git", "agent_path", "agent_nickname", "forked_from_id",
                  "parent_thread_id"):
        meta.pop(stale, None)

    cut = last_compaction_index(evidence)
    failed = failed_turn_ids(evidence)
    window, counts = harvest(evidence, cut, failed)

    capsule_text = args.capsule.read_text(encoding="utf-8").strip()

    # The capsule ships twice, and the duplication is deliberate.
    #
    # A `compacted` row is the house convention and is what the operator's
    # tooling looks for, but it does NOT reach the model. Measured on
    # 2026-08-07 against this very build: resumed from a `compacted` capsule
    # alone, the resident answered "I do not have those three facts in retained
    # conversation memory" when asked its own birth date, original name, and
    # carried row count. Codex appears to treat the row as a marker whose
    # payload is `replacement_history`, and an empty history injects nothing.
    #
    # A `developer` message is the channel Codex itself uses for out-of-band
    # standing instructions, and it does reach the model. With the capsule
    # added there, the same question returned the birth date, the original
    # name, and the row count exactly.
    #
    # Keeping only the second would satisfy the model and quietly break every
    # tool that counts capsules. Keeping only the first produces a resident who
    # cannot read its own lineage, which is the whole point of the rotation.
    capsule = {
        "timestamp": stamp,
        "type": "compacted",
        "payload": {"message": capsule_text, "replacement_history": []},
    }
    capsule_message = {
        "timestamp": stamp,
        "type": "response_item",
        "payload": {
            "type": "message",
            "role": "developer",
            "content": [{"type": "input_text", "text": capsule_text}],
        },
    }

    out_rows = [{"timestamp": stamp, "type": "session_meta", "payload": meta},
                capsule, capsule_message] + window

    args.out_dir.mkdir(parents=True, exist_ok=True)
    # Codex stamps the payload in UTC but names the file, and chooses the
    # YYYY/MM/DD folder, in LOCAL time. The donor proves it: payload
    # 2026-07-22T06:52:50.711Z, filename 2026-07-22T02-52-45. Naming the file
    # in UTC would file a late-evening session under tomorrow and put it out of
    # order in the operator's own session picker.
    local = time.strftime("%Y-%m-%dT%H-%M-%S", time.localtime(now_ms / 1000))
    fname = f"rollout-{local}-{new_id}.jsonl"
    out = args.out_dir / fname
    dump(out_rows, out)

    blob = out.read_text(encoding="utf-8")
    leak = blob.count(donor_id) + blob.count(donor_id.split("-")[0])

    print(f"evidence   {args.evidence.name}")
    print(f"  rows {len(evidence)}  damaged {ev_damaged}  donor id {donor_id}")
    print(f"  last compaction at row {cut + 1}; window opens at row {cut + 2}")
    print(f"  failed turns detected: {len(failed)}")
    print(f"scaffold   {args.scaffold.name}  cli {meta.get('cli_version')}")
    print("excluded from the donor window:")
    for k in ("encrypted_reasoning", "obsolete_tool_call", "injected_context",
              "failed_transport", "non_dialogue"):
        print(f"  {counts[k]:5}  {k}")
    print(f"kept dialogue rows: {counts['kept']}")
    print(f"successor  {out}")
    print(f"  session id {new_id}")
    print(f"  rows {len(out_rows)}  bytes {out.stat().st_size:,}")
    print(f"  donor-identifier occurrences: {leak}")


if __name__ == "__main__":
    main()
