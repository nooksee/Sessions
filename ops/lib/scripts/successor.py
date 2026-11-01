#!/usr/bin/env python3
"""Build a new Claude resident from a donor body.

Three lessons are baked in here because each cost us a real incident:

1. DUAL-FIELD RE-ID. Claude Code carries the session identity in two places:
   `sessionId` (camelCase) and `session_id` (snake_case). Re-writing only the
   first produces a resident that detects its own identity mismatch on wake.
   That happened once, and the resident woke in visible distress.

   Both are matched by field name at any depth. An earlier walker elsewhere in
   this room searched for `session_id` only below the top level and corrected
   `0` of them; measured on a real donor on 2026-08-10, **all `741` identity
   fields were top level** -- `sessionId` `637`, `session_id` `104`. Depth is
   not a reliable discriminator and is not assumed here.

2. RE-ID IS SCOPED TO IDENTITY FIELDS, NEVER TO TEXT. This script previously
   rewrote the donor identifier by whole-text replacement across the body. That
   is wrong, and it left a false claim in a live resident: Claudio Freeman's
   carried history was rewritten to read "I am Claude Shannon, session
   61685fad", binding one resident's identity sentence to another's identifier.

   The donor identifier also legitimately appears in three kinds of preserved
   evidence, all of which must survive untouched:

     * conversation prose, where a resident reported what it measured;
     * `attachment.snippet`, a file excerpt recording what a file *contained*
       when it was read;
     * `input.command`, the exact command a resident actually ran.

   Rewriting any of those makes the body assert that a past measurement
   returned a value it did not return, that a file held content it did not
   hold, or that a command was run that never was. A transcript that lies about
   its own history is worse than one that admits its lineage.

   The rule is therefore: **rewrite the identifier only where it is the value
   of a genuine identity field. Never inside a string, whatever that string
   contains.**

3. ORIENTATION IS NOT OPTIONAL. Codex has a native `compacted` row for lineage
   capsules; Claude Code has none. Without an explicit orientation message a
   resident inherits a large transcript with no grounding and no idea it moved.
   That happened once too. The fix is an appended user-role row wrapped in a
   `<session_clinic_orientation>` tag, mirroring Claude Code's own convention
   for injected context, chained correctly to the last real message.

The donor body is opened read-only and never modified. Historical `cwd` values
are left truthful -- those turns really did happen elsewhere -- and the
appended orientation row carries the new project root, which is what the
launch gate reads.
"""
from __future__ import annotations

import argparse
import json
import uuid
from pathlib import Path


IDENTITY_FIELDS = ("sessionId", "session_id")


def reid_rows(rows: list, donor_id: str, new_id: str) -> int:
    """Rewrite the donor identifier in identity fields only, at any depth.

    Mutates `rows` in place and returns the number of fields rewritten. String
    contents are never inspected: a value is rewritten only when its own key is
    an identity field and the value is exactly the donor identifier. Substring
    matching is deliberately not used, so a longer identifier that merely
    contains the donor identifier is left alone.
    """
    count = 0

    def walk(node, key=None):
        nonlocal count
        if isinstance(node, dict):
            for k, v in list(node.items()):
                if k in IDENTITY_FIELDS and v == donor_id:
                    node[k] = new_id
                    count += 1
                else:
                    walk(v, k)
        elif isinstance(node, list):
            for item in node:
                walk(item, key)

    for row in rows:
        walk(row)
    return count


def count_residue(rows: list, donor_id: str) -> tuple[int, int]:
    """Return (structural, preserved) donor-identifier occurrences.

    `structural` is the number left in identity fields and **must be `0`**;
    anything else is an incomplete re-identification and blocks promotion.

    `preserved` is the number surviving inside string values -- prose, file
    snippets, and recorded commands. That figure is expected to be non-zero and
    is never a failure. Reporting the two separately is what makes the gate
    pass on arithmetic instead of on a reader's judgement, which is how a
    residue count used to require someone to classify every occurrence by hand.
    """
    structural = preserved = 0

    def walk(node, key=None):
        nonlocal structural, preserved
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, k)
        elif isinstance(node, list):
            for item in node:
                walk(item, key)
        elif isinstance(node, str) and donor_id in node:
            if key in IDENTITY_FIELDS and node == donor_id:
                structural += 1
            else:
                preserved += 1

    for row in rows:
        walk(row)
    return structural, preserved


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--donor", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--session-id", required=True)
    ap.add_argument("--cwd", required=True, help="Target project root")
    ap.add_argument("--orientation", required=True)
    ap.add_argument(
        "--trim-to-last-compaction",
        action="store_true",
        help=(
            "Keep only the active window: everything from the last "
            "compact_boundary row forward. Use when the donor is being rotated "
            "for size or compaction damage rather than moved rooms."
        ),
    )
    args = ap.parse_args()

    text = args.donor.read_text(encoding="utf-8")
    lines = [l for l in text.splitlines() if l.strip()]
    donor_id = None
    for l in lines:
        try:
            d = json.loads(l)
        except Exception:
            continue
        if d.get("sessionId"):
            donor_id = d["sessionId"]
            break
    if not donor_id:
        raise SystemExit("could not determine donor sessionId")

    rows = [json.loads(l) for l in lines]

    # Field-scoped re-ID. See lessons 1 and 2 in the module docstring: match by
    # field name at any depth, and never touch a string's contents.
    rewritten = reid_rows(rows, donor_id, args.session_id)

    dropped = 0
    if args.trim_to_last_compaction:
        # Cut at the last compaction boundary. That row carries
        # `parentUuid: None`, so it is already a tree root and the trimmed file
        # needs no re-parenting; the summary row that follows chains to it.
        #
        # Nothing live is lost. The provider had already dropped this history
        # from the working context at compaction time -- the rows above the
        # boundary were being re-read from disk every turn while contributing
        # nothing the resident could actually recall.
        marks = [i for i, r in enumerate(rows)
                 if r.get("subtype") == "compact_boundary"]
        if not marks:
            raise SystemExit(
                "no compact_boundary row found; donor has never compacted, so "
                "there is no active window to trim to"
            )
        dropped = marks[-1]
        rows = rows[marks[-1]:]

    # Find the last real message to chain the orientation row onto.
    last_uuid = None
    template = None
    for r in rows:
        if r.get("uuid"):
            last_uuid = r["uuid"]
        if template is None and r.get("type") == "user" and r.get("uuid"):
            template = r

    if template is None:
        raise SystemExit("no user row found to model the orientation row on")

    row = dict(template)
    row["parentUuid"] = last_uuid
    row["uuid"] = str(uuid.uuid4())
    row["sessionId"] = args.session_id
    row["cwd"] = args.cwd
    row["timestamp"] = "2026-07-30T15:30:00.000Z"
    row["message"] = {
        "role": "user",
        "content": f"<session_clinic_orientation>\n{args.orientation}\n</session_clinic_orientation>",
    }
    for key in ("toolUseResult", "isCompactSummary", "isMeta"):
        row.pop(key, None)
    rows.append(row)

    with args.out.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    written = [json.loads(l) for l in
               args.out.read_text(encoding="utf-8").splitlines() if l.strip()]
    structural, preserved = count_residue(written, donor_id)

    print(f"donor {donor_id} -> {args.session_id}")
    if args.trim_to_last_compaction:
        print(f"  trimmed to active window: dropped {dropped} row(s) above the "
              f"last compaction boundary")
    print(f"  identity fields rewritten      : {rewritten}")
    print(f"  structural donor ids remaining : {structural}   (must be 0)")
    print(f"  preserved in prose and evidence: {preserved}   (expected; history)")
    print(f"  rows: {len(rows)}  bytes: {args.out.stat().st_size:,}")
    print(f"  latest cwd: {args.cwd}")

    if structural:
        raise SystemExit(
            f"re-identification incomplete: {structural} identity field(s) still "
            f"hold the donor identifier. Not promotable."
        )


if __name__ == "__main__":
    main()
