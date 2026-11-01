#!/usr/bin/env python3
"""Rotate a Codex resident into a fresh provider-created container.

Active-window method, structural-only re-ID. The established house method:

- the TARGET supplies identity and scaffolding. Its `session_meta`, developer
  instructions, `world_state`, and `turn_context` are provider-native and are
  kept byte-for-byte, so Codex resumes a container it created itself;
- the DONOR supplies history, but only its *active window* -- dialogue rows
  physically appended after its last native compaction. The compaction
  `replacement_history` is never replayed: it is already compacted state and
  can contain hundreds of retained user messages without their assistant
  replies;
- a lineage capsule is inserted both as a `compacted` marker for house tooling
  and as a developer message the model can actually read;
- only structural identifiers are rewritten. Prose is never touched.

The donor is opened read-only and never modified.
"""
from __future__ import annotations

import argparse
import collections
import copy
import json
from pathlib import Path

# Rows the target contributes before any donor history. Everything up to and
# including the first turn_context is provider scaffolding.
SCAFFOLD_TYPES = ("session_meta", "event_msg", "response_item", "world_state", "turn_context")

INJECTED_PREFIXES = (
    "<environment_context>",
    "<skills_instructions>",
    "<recommended_plugins>",
    "<permissions instructions>",
    "# Context from my IDE setup",
)

IMAGE_MARKER = "[Image omitted during rotation; original remains in donor custody.]"


def load(path: Path) -> tuple[list[dict], int]:
    """Parse a rollout, tolerating rows damaged by a torn write.

    A session body can take a partial write when the provider is killed
    mid-append. STELA George carries one such row at line 10741, found
    2026-08-01 and still present. Aborting the whole rotation over it would
    strand exactly the residents most in need of one, since the biggest, most
    heavily compacted bodies are the likeliest to have been interrupted.

    Damaged rows are skipped and counted. The count is reported rather than
    swallowed: a donor losing rows is a fact the operator must see, not an
    implementation detail.
    """
    rows: list[dict] = []
    damaged = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            damaged += 1
    return rows, damaged


def dump(rows: list[dict], path: Path) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            # Codex writes compact JSON. Match it exactly; a spaced file is
            # valid but invisible to byte-level scanners.
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def split_target(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """Scaffolding (through the first turn_context) and the trailing turn."""
    cut = 0
    for i, r in enumerate(rows):
        if r.get("type") == "turn_context":
            cut = i + 1
            break
    return rows[:cut], rows[cut:]


def message_text(payload: dict) -> str:
    return " ".join(
        item.get("text", "")
        for item in payload.get("content", [])
        if isinstance(item, dict)
    )


def is_injected(payload: dict) -> bool:
    text = message_text(payload).lstrip()
    return any(text.startswith(prefix) for prefix in INJECTED_PREFIXES)


def donor_active_window(rows: list[dict]) -> tuple[list[dict], dict[str, int]]:
    """Return portable dialogue physically after the last native compaction.

    `replacement_history` is deliberately ignored. Codex uses it as compacted
    model state, not as a faithful conversation transcript. Rewrapping it as
    ordinary response items duplicates retained context and can make an exact
    thread hang during resume.
    """
    marks = [
        i
        for i, r in enumerate(rows)
        if r.get("type") == "compacted" and r.get("payload", {}).get("window_number")
    ]
    start = marks[-1] + 1 if marks else 0
    counts = {
        "kept": 0,
        "injected_context": 0,
        "images_elided": 0,
        "non_dialogue": 0,
        "replayed_block": 0,
    }

    # Donors built before this bug was found carry the damage inside them, so
    # ignoring `replacement_history` on this pass is not enough: the previous
    # builder already flattened it into ordinary rows.
    #
    # It left a fingerprint. Carried rows were all stamped with the single
    # timestamp of the compaction they came from, while real turns arrive
    # seconds or minutes apart. Measured 2026-08-08 on the pre-rotation donors:
    # George Prime `280` of `300` messages at one second, Jerry Codex `424` of
    # `438`, Jacob Codex `334` of `343`. Dropping that one timestamp leaves a
    # balanced conversation underneath -- 5 user to 15 assistant, 4 to 10, and
    # 4 to 5 respectively.
    #
    # Twenty messages sharing one second is not a conversation, so any such
    # cluster is treated as a replayed block and dropped.
    stamps = collections.Counter(
        r.get("timestamp") for r in rows[start:]
        if isinstance(r.get("payload"), dict)
        and r["payload"].get("type") == "message"
        and r["payload"].get("role") in ("user", "assistant")
    )
    replayed = {ts for ts, n in stamps.items() if ts and n >= 20}

    kept: list[dict] = []
    for row in rows[start:]:
        payload = row.get("payload", {})
        if (
            isinstance(payload, dict)
            and payload.get("type") == "message"
            and row.get("timestamp") in replayed
        ):
            counts["replayed_block"] += 1
            continue
        if (
            row.get("type") != "response_item"
            or not isinstance(payload, dict)
            or payload.get("type") != "message"
            or payload.get("role") not in ("user", "assistant")
        ):
            counts["non_dialogue"] += 1
            continue
        if is_injected(payload):
            counts["injected_context"] += 1
            continue

        portable = copy.deepcopy(payload)
        portable.pop("internal_chat_message_metadata_passthrough", None)
        content = []
        for item in portable.get("content", []):
            if isinstance(item, dict) and item.get("type") == "input_image":
                content.append({"type": "input_text", "text": IMAGE_MARKER})
                counts["images_elided"] += 1
            else:
                content.append(item)
        portable["content"] = content
        kept.append(
            {
                "timestamp": row.get("timestamp"),
                "type": "response_item",
                "payload": portable,
            }
        )
        counts["kept"] += 1
    return kept, counts


def reid(rows: list[dict], donor_id: str, target_id: str) -> tuple[list[dict], int]:
    """Replace exact session ids under structural keys; never rewrite prose."""
    structural_keys = {"id", "session_id", "thread_id"}
    short_d, short_t = donor_id.split("-")[0], target_id.split("-")[0]
    replaced = 0

    def visit(value: object, parent_key: str | None = None) -> object:
        nonlocal replaced
        if isinstance(value, dict):
            return {key: visit(item, key) for key, item in value.items()}
        if isinstance(value, list):
            return [visit(item, parent_key) for item in value]
        if parent_key in structural_keys and value == donor_id:
            replaced += 1
            return target_id
        if parent_key in structural_keys and value == short_d:
            replaced += 1
            return short_t
        return value

    return visit(rows), replaced  # type: ignore[return-value]


def build_rotation(
    donor_rows: list[dict], target_rows: list[dict], capsule_text: str
) -> tuple[list[dict], dict[str, int], int]:
    """Build one destination-native rotation and return rows and accounting."""
    donor_id = donor_rows[0]["payload"].get("id") or donor_rows[0]["payload"]["session_id"]
    target_id = target_rows[0]["payload"].get("id") or target_rows[0]["payload"]["session_id"]
    scaffold, trailing = split_target(target_rows)
    if not scaffold or scaffold[0].get("type") != "session_meta":
        raise ValueError("target does not begin with native session_meta scaffolding")

    window, window_counts = donor_active_window(donor_rows)
    window, replaced = reid(window, donor_id, target_id)
    capsule = {
        "timestamp": scaffold[0]["timestamp"],
        "type": "compacted",
        "payload": {"message": capsule_text, "replacement_history": []},
    }
    capsule_message = {
        "timestamp": scaffold[0]["timestamp"],
        "type": "response_item",
        "payload": {
            "type": "message",
            "role": "developer",
            "content": [{"type": "input_text", "text": capsule_text}],
        },
    }
    window_counts["user_messages"] = sum(
        1 for r in window if r.get("payload", {}).get("role") == "user")
    window_counts["assistant_messages"] = sum(
        1 for r in window if r.get("payload", {}).get("role") == "assistant")
    return scaffold + [capsule, capsule_message] + window + trailing, window_counts, replaced


def imbalance_refusal(counts: dict[str, int]) -> str | None:
    """Refuse a window that is operator turns with almost no replies.

    This is the check that was missing on 2026-08-08. All fourteen builds that
    night passed every structural gate -- row zero, identifier equality, capsule
    count, zero donor leakage, every row parsing -- while carrying hundreds of
    Kevin's turns against a handful of replies. Structure was never the problem.
    Shape was, and nothing measured shape.

    A conversation alternates. A window that does not is either a builder fault
    or a donor that deserves a human look before anything is installed.
    """
    users = counts.get("user_messages", 0)
    assistants = counts.get("assistant_messages", 0)
    if users >= 20 and assistants * 10 < users:
        return (f"window carries {users} user messages against {assistants} "
                f"assistant messages. A conversation does not look like this. "
                f"Refusing; pass --allow-imbalance if the donor genuinely is "
                f"one-sided.")
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--donor", required=True, type=Path)
    ap.add_argument("--target", required=True, type=Path)
    ap.add_argument("--capsule", required=True, help="LINEAGE MEMORY text")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--allow-imbalance", action="store_true",
                    help="permit a window that is nearly all operator turns")
    args = ap.parse_args()

    donor_rows, donor_damaged = load(args.donor)
    target_rows, target_damaged = load(args.target)
    if target_damaged:
        raise SystemExit(
            f"target has {target_damaged} damaged row(s). A fresh container "
            f"must be intact; refusing to build on it."
        )

    # Use `id`, not `session_id`. For a fresh container the two are equal, but
    # a provider-spawned worker thread carries its OWN container in `id` and its
    # PARENT's thread in `session_id`. Reading `session_id` on a worker target
    # silently re-IDs the build to the parent -- found 2026-08-01 while staging
    # a rebuild over a worker, and caught only because the build was staged
    # rather than applied.
    donor_id = donor_rows[0]["payload"].get("id") or donor_rows[0]["payload"]["session_id"]
    target_id = target_rows[0]["payload"].get("id") or target_rows[0]["payload"]["session_id"]

    out, window_counts, replaced = build_rotation(donor_rows, target_rows, args.capsule)
    scaffold, trailing = split_target(target_rows)
    window_length = window_counts["kept"]

    refusal = imbalance_refusal(window_counts)
    if refusal and not args.allow_imbalance:
        raise SystemExit(f"REFUSED: {refusal}")

    dump(out, args.out)
    if refusal:
        print(f"WARNING, overridden: {refusal}")
    print(f"balance  user={window_counts['user_messages']}  "
          f"assistant={window_counts['assistant_messages']}")

    if donor_damaged:
        print(f"donor  WARNING: skipped {donor_damaged} row(s) damaged by a "
              f"torn write; they carry no recoverable message")
    print(f"donor  {donor_id}  active-window messages: {window_length}")
    print(
        "excluded  "
        f"non-dialogue={window_counts['non_dialogue']}  "
        f"injected={window_counts['injected_context']}  "
        f"images-elided={window_counts['images_elided']}"
    )
    print(f"target {target_id}  scaffold rows: {len(scaffold)}  trailing: {len(trailing)}")
    print(f"structural ids replaced: {replaced}")
    print(f"wrote {args.out}  rows={len(out)}  bytes={args.out.stat().st_size:,}")


if __name__ == "__main__":
    main()
