#!/usr/bin/env python3
"""Move base64 media out of a Claude session body into files, losslessly.

Written 2026-08-28 for Home Advisor (Joy Anne Claude), whose body reached
`609,608,826` bytes sixteen days after birth, `96.2%` of it inline base64. She
advises on a house and Kevin sends her photographs of it; the pictures are the
work product, not junk, so eliding them the way a Tier B rotation does would
throw away the thing she was hired to look at.

This externalizes instead. Every base64 payload is decoded to a real file named
by its own SHA-256, and the block that held it is replaced by a text placeholder
naming that file, its type, and its size. The conversation keeps every turn and
every word; the resident can still see that a picture was there and where it
went; and the operator ends up with a browsable folder of his own house.

Identical payloads collapse to one file on disk, because a photograph pasted
twice is one photograph.

What is deliberately NOT done:

  * nothing is deleted, here or anywhere;
  * the donor is opened read-only and never written;
  * non-media rows are re-serialised only if they were touched, and every row
    is compared for text equality afterwards by the caller's gates;
  * output goes beside the original as `.NEW`, per the operator's standing
    rule: he performs the swap himself with the application closed, because a
    live body is appended to every turn and a torn write there is
    unrecoverable.

Two payload shapes exist in a Claude body and both are handled. The first is
the message content block, `{"type": "image", "source": {"type": "base64",
"media_type": ..., "data": ...}}`. The second is the tool result,
`toolUseResult.file = {"filePath": ..., "base64": ..., "originalSize": ...}`,
which carries no `source` and no media type at all -- its type lives on the
parent as `toolUseResult.type`, and its extension has to come from the file
path. Handling only the first shape moved `64%` of Joy Anne's body and left
`199.8 MB` behind in `415` rows; a media externalizer that silently leaves the
larger half is worse than none, because the number it prints is believed.

Streaming, one line at a time: a 600 MB body must never be held in memory.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import datetime as dt
import hashlib
import json
from pathlib import Path

EXT = {
    "image/png": ".png", "image/jpeg": ".jpg", "image/jpg": ".jpg",
    "image/gif": ".gif", "image/webp": ".webp", "application/pdf": ".pdf",
}


class Externalizer:
    """Moves media out of a body and leaves a truthful placeholder behind.

    The placeholder date is a parameter, not a literal. It was a literal from
    2026-08-28 until 2026-09-08, when a second run on the same resident wrote
    `media externalized 2026-08-28` beside a path from the later run -- a
    placeholder that misdated the only record the resident has of what happened
    to her own pictures. A tool that stamps the day it was written rather than
    the day it ran tells a small lie once and then repeats it forever.
    """

    def __init__(self, media_dir: Path, rel_hint: str, stamp: str):
        self.media_dir = media_dir
        self.rel_hint = rel_hint
        self.stamp = stamp
        self.written = 0
        self.deduped = 0
        self.bytes_out = 0
        self.blocks = 0
        self.failed = 0
        self.seen: dict[str, str] = {}

    def stash(self, data: str, media_type: str | None) -> str | None:
        """Decode one payload to a file; return its name, or None on failure."""
        try:
            raw = base64.b64decode(data, validate=False)
        except (binascii.Error, ValueError):
            self.failed += 1
            return None
        digest = hashlib.sha256(raw).hexdigest()
        if digest in self.seen:
            self.deduped += 1
            return self.seen[digest]
        name = digest[:32] + EXT.get(media_type or "", ".bin")
        target = self.media_dir / name
        if not target.exists():
            target.write_bytes(raw)
            self.bytes_out += len(raw)
            self.written += 1
        self.seen[digest] = name
        return name

    def walk(self, node, parent_type=None):
        """Replace media payloads in place. Returns True if anything changed."""
        changed = False
        if isinstance(node, dict):
            # Shape 1: message content block -- source.data, with a media type.
            src = node.get("source")
            if isinstance(src, dict) and isinstance(src.get("data"), str) and len(src["data"]) > 256:
                media = src.get("media_type")
                approx = len(src["data"]) * 3 // 4
                name = self.stash(src["data"], media)
                if name:
                    self.blocks += 1
                    node.clear()
                    node["type"] = "text"
                    node["text"] = (
                        f"[media externalized {self.stamp}: {media or 'unknown type'}, "
                        f"{approx:,} bytes, preserved at {self.rel_hint}/{name}]"
                    )
                    return True

            # Shape 2: tool result file -- base64 sibling of filePath, no media
            # type of its own. The extension comes from the path; the original
            # path and size are kept in the placeholder because they are the
            # only record of what the operator actually handed her.
            b64 = node.get("base64")
            if isinstance(b64, str) and len(b64) > 256:
                path_hint = node.get("filePath") or ""
                suffix = Path(path_hint).suffix.lower()
                media = {v: k for k, v in EXT.items()}.get(suffix) or parent_type
                approx = node.get("originalSize") or len(b64) * 3 // 4
                name = self.stash(b64, media)
                if name:
                    self.blocks += 1
                    # Replace only the payload. `filePath` and `originalSize`
                    # are the operator's own record of what he handed her --
                    # a septic plan, an engineering invoice -- and clearing
                    # the node to a prose placeholder destroyed those keys on
                    # 17 rows in the first run. Structure is preserved; only
                    # the bytes move.
                    node["base64"] = (
                        f"[media externalized {self.stamp}: {media or suffix or 'unknown type'}, "
                        f"{approx:,} bytes, preserved at {self.rel_hint}/{name}]"
                    )
                    node["externalized_to"] = name
                    return True

            for key, value in node.items():
                changed = self.walk(value, node.get("type") or parent_type) or changed
        elif isinstance(node, list):
            for item in node:
                changed = self.walk(item, parent_type) or changed
        return changed


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--donor", required=True, type=Path, help="opened read-only")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--media-dir", required=True, type=Path)
    ap.add_argument("--rel-hint", default="media",
                    help="path shown to the resident in each placeholder")
    ap.add_argument("--stamp", default=None,
                    help="date written into each placeholder; defaults to today. "
                         "Pass an explicit value only to reproduce an earlier run.")
    args = ap.parse_args()

    stamp = args.stamp or dt.date.today().isoformat()
    args.media_dir.mkdir(parents=True, exist_ok=True)
    ex = Externalizer(args.media_dir, args.rel_hint, stamp)
    rows = touched = parse_errors = 0

    with args.donor.open(encoding="utf-8", errors="replace") as src, \
         args.out.open("w", encoding="utf-8") as dst:
        for line in src:
            if not line.strip():
                continue
            rows += 1
            if '"data"' not in line and '"base64"' not in line:
                dst.write(line if line.endswith("\n") else line + "\n")
                continue
            try:
                row = json.loads(line)
            except Exception:
                parse_errors += 1
                dst.write(line if line.endswith("\n") else line + "\n")
                continue
            if ex.walk(row):
                touched += 1
                dst.write(json.dumps(row, ensure_ascii=False) + "\n")
            else:
                dst.write(line if line.endswith("\n") else line + "\n")

    before = args.donor.stat().st_size
    after = args.out.stat().st_size
    print(f"rows                : {rows:,}  (unparseable passed through: {parse_errors})")
    print(f"rows rewritten      : {touched:,}")
    print(f"media blocks moved  : {ex.blocks:,}")
    print(f"files written       : {ex.written:,}  ({ex.bytes_out:,} bytes)")
    print(f"duplicate payloads  : {ex.deduped:,}  (collapsed to existing files)")
    print(f"decode failures     : {ex.failed}  (left untouched)")
    print(f"placeholder date     : {stamp}")
    print(f"body {before:,} -> {after:,} bytes  ({100 - after * 100 // before}% smaller)")


if __name__ == "__main__":
    main()
