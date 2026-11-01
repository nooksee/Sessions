#!/usr/bin/env python3
"""Report health for Claude Code session JSONL files.

Claude Code transcripts do not carry Codex-style token telemetry, so this
measures the proxies that actually predict a Claude session's failure mode:

- file bytes: the whole transcript is re-read every turn.
- image payload: base64 image blocks are re-processed every turn and are the
  #1 cause of Claude "HAL-9000" degradation (see the Addition case,
  archives/receipts/addition-claude-image-elision-20260716.md). Tracked separately.
- rows and user/assistant turn counts.
- compaction telemetry: count of `compact_boundary` rows, and the carry ratio
  postTokens/preTokens of the most recent compaction. Added 2026-08-05.

Claude Code does carry Codex-style compaction telemetry after all; this script
simply was not reading it. That omission is why it rated the Sessions resident
`healthy` at 21 MB on the day that resident relayed a fabricated finding to
Control after a compaction that carried 1.3% of context forward. Size is a
capacity signal; carry ratio is a damage signal, and they are not the same.

Verdicts (image-aware and compaction-aware, because a 40 MB thread that is half
images is sicker than a 40 MB thread of pure text, and a 20 MB thread that has
shed 96% of its context twice is sicker than either):
  CRITICAL                  : bytes >= CRIT_BYTES or image_mb >= CRIT_IMG_MB
  CRITICAL-compact-treadmill: compacts >= CRIT_COMPACTS, or any compaction
                              carrying < CRIT_CARRY_PCT
  compact-treadmill         : compacts >= WARN_COMPACTS, or any compaction
                              carrying < WARN_CARRY_PCT
  treat-images              : image_mb >= WARN_IMG_MB (elide; keep every turn)
  rotate-soon               : bytes >= WARN_BYTES
  healthy                   : otherwise

Read-only. Never modifies session files.
Lane: session hygiene monitoring (Claude side; mirror of
check_codex_token_health.py).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path

PROJECTS_ROOT = Path("/home/nos4r2/.claude/projects")

WARN_BYTES = 30_000_000
CRIT_BYTES = 60_000_000
WARN_IMG_MB = 10.0
CRIT_IMG_MB = 25.0

# Compaction telemetry. Claude Code writes a `compact_boundary` system row
# carrying `compactMetadata` with preTokens, postTokens, and
# cumulativeDroppedTokens. This checker did not read it until 2026-08-05, which
# is why it rated this resident `healthy` at 21 MB on the same day the resident
# delivered a fabricated finding to Control after a compaction that carried
# 12,705 of 974,001 tokens forward -- a 1.3% carry.
#
# Carry ratio is the damage signal, not file size. A compaction that keeps
# almost nothing preserves conclusions while discarding the evidence that
# produced them, and the resident then relays those conclusions without being
# able to re-derive them.
WARN_COMPACTS = 3
CRIT_COMPACTS = 8
WARN_CARRY_PCT = 25.0
CRIT_CARRY_PCT = 5.0

# Only compactions inside this window count toward a treadmill verdict.
#
# A transplanted resident inherits its donor's compaction rows, because the
# donor's active window is copied in verbatim. Jean-Luc Claude was staffed
# 2026-08-02 and carries eight compactions dated 2026-06-20 to 2026-07-07, all
# of them Addition II's history and none of them his. Counting those rated him
# CRITICAL on his third day alive.
#
# Recency separates the two cleanly and needs no marker string: a compaction
# from four weeks ago says nothing about whether this body is shedding context
# now, whoever it originally belonged to.
RECENT_DAYS = 14

# Nested donor compactions can report postTokens above preTokens, yielding
# carry ratios of 150% or 375%. Those are measurement artifacts of the donor's
# own nesting, not signal. Anything above this is discarded rather than trusted.
MAX_PLAUSIBLE_CARRY_PCT = 100.0

# Map encoded cwd store folder -> friendly resident name.
ROOMS = {
    "-media-nos4r2-user-vol-Sessions": "Sessions (me)",
    "-media-nos4r2-user-vol-Projects-Addition": "Addition",
    "-media-nos4r2-user-vol-Projects-DocumentStudio": "DocumentStudio",
    "-media-nos4r2-user-vol-Projects-OSAI": "OSAI(claude)",
    "-media-nos4r2-user-vol": "Control(claude)",
    "-home-nos4r2": "home",
}


def room_name(store: str) -> str:
    return ROOMS.get(store, store)


def parse_stamp(value) -> dt.datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def scan_images(obj, acc):
    """Count inline media payloads, in BOTH shapes a Claude body uses.

    A Claude body carries media two ways. The message content block,
    `{"type": "image", "source": {"data": ...}}`, and the tool result,
    `toolUseResult.file = {"filePath": ..., "base64": ..., "originalSize": ...}`,
    which has no `type` and no `source` at all.

    Only the first was counted until 2026-09-08. Measured on Home Advisor that
    day: the checker reported 100.6 MB across 209 blocks against an actual
    170.1 MB across 355 -- it was blind to 69.5 MB, 40.8 percent of her real
    media load, and the operator was shown the smaller number.

    The same second shape was found and fixed in
    `externalize_claude_image_payloads.py` on 2026-08-28. The treatment learned
    it; the detector did not, so for eleven days the tool that removes media
    saw more than the tool that looks for it. Fixing one half of a pair and not
    the other is how a measurement quietly stops being a measurement.
    """
    if isinstance(obj, dict):
        if obj.get("type") == "image" and isinstance(obj.get("source"), dict):
            data = obj["source"].get("data") or ""
            if data:
                acc[0] += 1
                acc[1] += len(data)
        b64 = obj.get("base64")
        if isinstance(b64, str) and b64 and not b64.startswith("[media externalized"):
            acc[0] += 1
            acc[1] += len(b64)
        for v in obj.values():
            scan_images(v, acc)
    elif isinstance(obj, list):
        for v in obj:
            scan_images(v, acc)


def measure(path: Path) -> dict:
    size = path.stat().st_size
    rows = users = assistants = bad = 0
    acc = [0, 0]  # image_count, image_bytes
    compacts = recent = 0
    last_meta: dict | None = None
    dropped = 0
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=RECENT_DAYS)
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                bad += 1
                continue
            rows += 1
            t = r.get("type")
            if t == "user":
                users += 1
            elif t == "assistant":
                assistants += 1
            # Count the system boundary row, not the summary row: each
            # compaction emits exactly one boundary. Matching on the string
            # anywhere in the line would also hit ordinary prose that happens
            # to discuss compaction, which inflated an earlier hand count of
            # this resident from 3 to 15.
            if r.get("subtype") == "compact_boundary":
                compacts += 1
                meta = r.get("compactMetadata")
                if isinstance(meta, dict):
                    dropped = max(dropped, meta.get("cumulativeDroppedTokens") or 0)
                    stamp = parse_stamp(r.get("timestamp"))
                    # A boundary at row 0 is the seam this body was cut at, not
                    # a symptom. A resident rotated by an active-window trim
                    # starts with the boundary as its tree root; counting it
                    # would greet the successor with a CRITICAL verdict earned
                    # entirely by its predecessor. Same error class as counting
                    # a donor's inherited compactions, and it survives the
                    # recency window because the cut is by definition recent.
                    origin_seam = rows == 1
                    if stamp is not None and stamp >= cutoff and not origin_seam:
                        recent += 1
                        last_meta = meta
            scan_images(r, acc)

    img_mb = acc[1] / 1e6
    carry_pct: float | None = None
    if last_meta:
        pre = last_meta.get("preTokens") or 0
        post = last_meta.get("postTokens") or 0
        if pre:
            ratio = 100.0 * post / pre
            if ratio <= MAX_PLAUSIBLE_CARRY_PCT:
                carry_pct = ratio

    starved = carry_pct is not None and carry_pct < WARN_CARRY_PCT
    gutted = carry_pct is not None and carry_pct < CRIT_CARRY_PCT

    if size >= CRIT_BYTES or img_mb >= CRIT_IMG_MB:
        verdict = "CRITICAL"
    elif recent >= CRIT_COMPACTS or (recent >= 1 and gutted):
        verdict = "CRITICAL-compact-treadmill"
    elif recent >= WARN_COMPACTS or (recent >= 1 and starved):
        verdict = "compact-treadmill"
    elif img_mb >= WARN_IMG_MB:
        verdict = "treat-images"
    elif size >= WARN_BYTES:
        verdict = "rotate-soon"
    else:
        verdict = "healthy"
    return dict(size=size, rows=rows, users=users, assistants=assistants,
               bad=bad, img_count=acc[0], img_mb=img_mb, verdict=verdict,
               compacts=compacts, recent=recent, carry_pct=carry_pct,
               dropped=dropped)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=PROJECTS_ROOT)
    ap.add_argument("--only-flagged", action="store_true",
                    help="print only rotate-soon/treat-images/CRITICAL")
    args = ap.parse_args()

    files = sorted(args.root.glob("*/*.jsonl"))
    print(f"{'size':>7} {'rows':>6} {'imgMB':>6} {'imgs':>5} {'cmp':>7} {'carry':>6}  "
          f"{'verdict':<26}  room / session")
    print(f"{'':>7} {'':>6} {'':>6} {'':>5} {'rec/tot':>7}")
    worst = "healthy"
    order = {
        "healthy": 0,
        "rotate-soon": 1,
        "treat-images": 2,
        "compact-treadmill": 3,
        "CRITICAL-compact-treadmill": 4,
        "CRITICAL": 5,
    }
    flagged = []
    for f in files:
        m = measure(f)
        if order[m["verdict"]] > order[worst]:
            worst = m["verdict"]
        if m["verdict"] != "healthy":
            flagged.append((room_name(f.parent.name), f.name, m))
        if args.only_flagged and m["verdict"] == "healthy":
            continue
        carry = "-" if m["carry_pct"] is None else f"{m['carry_pct']:.1f}%"
        cmp_col = f"{m['recent']}/{m['compacts']}"
        print(f"{m['size']//1_000_000:>5}MB {m['rows']:>6} {m['img_mb']:>6.1f} "
              f"{m['img_count']:>5} {cmp_col:>7} {carry:>6}  "
              f"{m['verdict']:<26}  "
              f"{room_name(f.parent.name)} / {f.name[:20]}")
    print(f"\nworst verdict: {worst}   flagged: {len(flagged)}")
    for room, name, m in flagged:
        if m["verdict"] == "treat-images":
            action = "elide images (Tier-B, keep every turn)"
        elif m["verdict"].endswith("compact-treadmill"):
            carry = "unknown" if m["carry_pct"] is None else f"{m['carry_pct']:.1f}%"
            action = (f"rotate: {m['recent']} compaction(s) in the last "
                      f"{RECENT_DAYS} days (of {m['compacts']} total), last "
                      f"carried {carry}, {m['dropped']:,} tokens dropped")
        else:
            action = "rotate / trim"
        print(f"  [{m['verdict']}] {room}: {m['size']//1_000_000}MB, "
              f"{m['img_mb']:.1f}MB images -> {action}")
    return 2 if worst.startswith("CRITICAL") else 0


if __name__ == "__main__":
    raise SystemExit(main())
