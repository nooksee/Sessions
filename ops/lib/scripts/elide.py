#!/usr/bin/env python3
"""Elide oversized Codex tool-call outputs while preserving every turn.

Lane: session condensation. The Codex analogue of Tier B image elision on the
Claude side, and the same principle: strip the bulk payload, keep every turn.

Why this exists. `condense_codex_tool_transcripts.py` reduces response-item
*count* for loader limits. A different pathology is a session whose row count
is fine but whose context is dominated by a handful of very large tool
outputs -- file dumps, schema dumps, grep results. Those are working material
the resident already acted on; its own reasoning and messages carry the
conclusions. Dropping the raw bulk buys back most of the context window
without removing a single conversational turn.

What is preserved, always:

- every row, in order -- nothing is deleted, so `call_id` pairing between
  `function_call` and `function_call_output` cannot break;
- every user message, assistant message, and reasoning row, untouched;
- each elided output's header lines (chunk id, wall time, exit code, original
  token count) and a head excerpt, so the resident can see what it ran and
  roughly what came back;
- outputs below the threshold, and the most recent N outputs regardless of
  size, which are the ones still likely in active use.

Read-only unless `--write`. Default is a dry run.
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

MARKER = (
    "\n[... {removed:,} characters elided by the session clinic on {stamp}. "
    "This tool output was working material that has already been acted on; "
    "the full original is preserved in the pre-elision backup. "
    "Re-run the command if the detail is needed again. ...]"
)


# Codex has emitted two output shapes. The older `function_call_output` carries
# `output` as a plain string. The current `custom_tool_call_output` carries it as
# a list of blocks, `[{"type": "output_text", "text": ...}, {"image_url": ...}]`.
# Measured 2026-08-28 on George Friend's body: 3,033 rows of the newer shape held
# 14,940,920 characters of `output[].text`, and this tool -- which knew only the
# older shape -- reported 0 chars saved on a 69 MB session. A reducer that
# silently matches nothing is worse than absent, because its zero is believed.
#
# Images are deliberately not touched here. `externalize_codex_image_payloads.py`
# owns that lane and preserves the bytes rather than discarding them; eliding an
# image would destroy it.
OUTPUT_TYPES = ("function_call_output", "custom_tool_call_output")


def output_blocks(payload: dict) -> list[tuple]:
    """Return [(setter, text)] for every elidable text payload in this row.

    A setter is a closure so the caller does not need to know which shape it is
    holding, and the list shape is never rebuilt -- only its text is replaced,
    so image blocks and block ordering survive untouched.
    """
    value = payload.get("output")
    if isinstance(value, str):
        def set_str(new: str, _p=payload) -> None:
            _p["output"] = new
        return [(set_str, value)]
    if isinstance(value, list):
        found = []
        for index, block in enumerate(value):
            if not isinstance(block, dict):
                continue
            text = block.get("text")
            if isinstance(text, str):
                def set_block(new: str, _b=block) -> None:
                    _b["text"] = new
                found.append((set_block, text))
        return found
    return []


def output_text(payload: dict) -> str | None:
    """Back-compatible probe: is there any elidable text on this row?"""
    blocks = output_blocks(payload)
    return blocks[0][1] if blocks else None


def elide(text: str, head_chars: int, stamp: str) -> str:
    """Keep the header block and a head excerpt; drop the bulk."""
    lines = text.split("\n")
    header: list[str] = []
    for line in lines[:8]:
        header.append(line)
        if line.startswith("Output:"):
            break
    head_block = "\n".join(header)
    remainder = text[len(head_block) :]
    excerpt = remainder[:head_chars]
    removed = len(remainder) - len(excerpt)
    if removed <= 0:
        return text
    return head_block + excerpt + MARKER.format(removed=removed, stamp=stamp)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--destination", type=Path)
    parser.add_argument(
        "--threshold",
        type=int,
        default=4000,
        help="Elide outputs longer than this many characters. Default 4000.",
    )
    parser.add_argument(
        "--protect-last",
        type=int,
        default=12,
        help="Never elide the most recent N tool outputs. Default 12.",
    )
    parser.add_argument(
        "--head-chars",
        type=int,
        default=300,
        help="Characters of output body to keep after the header. Default 300.",
    )
    parser.add_argument(
        "--after-last-compaction",
        action="store_true",
        help="Only consider outputs in the current context window.",
    )
    parser.add_argument("--stamp", default="2026-07-29")
    parser.add_argument("--write", action="store_true", help="Write the destination.")
    args = parser.parse_args()

    raw = args.source.read_text(encoding="utf-8").splitlines()
    rows = [json.loads(line) for line in raw if line.strip()]

    start = 0
    if args.after_last_compaction:
        marks = [
            i
            for i, r in enumerate(rows)
            if r.get("type") == "compacted"
            and r.get("payload", {}).get("window_number")
        ]
        if marks:
            start = marks[-1] + 1

    candidates: list[int] = []
    for i, row in enumerate(rows):
        if i < start:
            continue
        payload = row.get("payload", {})
        if payload.get("type") not in OUTPUT_TYPES:
            continue
        if output_text(payload) is not None:
            candidates.append(i)

    protected = set(candidates[-args.protect_last :]) if args.protect_last else set()

    before = after = 0
    touched = 0
    for i in candidates:
        payload = rows[i]["payload"]
        row_touched = False
        for setter, text in output_blocks(payload):
            before += len(text)
            if i in protected or len(text) <= args.threshold:
                after += len(text)
                continue
            new = elide(text, args.head_chars, args.stamp)
            setter(new)
            after += len(new)
            row_touched = True
        if row_touched:
            touched += 1

    print(f"tool outputs considered : {len(candidates)}")
    print(f"protected (most recent) : {len(protected)}")
    print(f"elided                  : {touched}")
    print(f"output chars before     : {before:,}")
    print(f"output chars after      : {after:,}")
    print(f"saved                   : {before - after:,} chars (~{(before-after)//4:,} tokens)")
    print(f"rows in  / rows out     : {len(rows)} / {len(rows)}")

    if not args.write:
        print("\nDRY RUN. Pass --write to produce the destination.")
        return

    destination = args.destination
    if destination is None:
        raise SystemExit("--destination is required with --write")
    with destination.open("w", encoding="utf-8") as handle:
        for row in rows:
            # Codex writes compact JSON with no separator whitespace. Match it
            # exactly. json.dumps defaults to ", " / ": ", which is valid JSON
            # and loads fine, but it defeats byte-level scanners -- including
            # check_codex_token_health.py, which looks for the literal
            # b'"type":"response_item"' in the first 80 bytes of each line and
            # silently counts zero against a spaced file.
            handle.write(
                json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
            )
    print(f"\nwrote {destination} ({destination.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
