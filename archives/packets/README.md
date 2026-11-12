# Landed packets

One file per dispatch packet that reached `main`: `DP-SES-NNNN.md`, numbered from 0001 without a gap.

Each file is the packet's leaf: its contract (who carries each delivery function, by registry key, the authority cited, the objective, the exact scope and the gates), the results the packet tool measured at close, and the Auditor's verdict bound to the exact tree. The commit that carries a leaf carries the change it describes.

- Only `ops/lib/scripts/packet.py` writes a leaf, and only in the packet worktree. Nobody writes one by hand.
- A landed leaf is never edited or removed. The required check fails a pull request that touches an earlier leaf.
- A leaf is public. It cites a decision by ledger number or digest and never quotes; it names no host path and no session identifier.
- A packet that was abandoned leaves no leaf; its number is used by the next one.

The format, the stations and the gate are in `docs/ops/specs/scripts/packet.md`; the contract is CONSTRAINTS C17.
