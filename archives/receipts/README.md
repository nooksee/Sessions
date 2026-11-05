# Receipts

Each file here is a receipt: a dated, write-once record of one act, written when the act happened
(PoT 1.2.13, 6.4.5). The paths, folder names and repository references in a receipt describe the
room as it stood on that date; many lanes it names have since moved, and some are private and not in
this repository. A receipt is never reworded: a later correction is an attributed, dated addition at
its end.

The receipts published here are public copies made by the redact tool
(`docs/ops/specs/scripts/redact.md`). Each begins with an HTML comment, invisible on GitHub, that
names its private source by sha256, the tool's rules version and its counts. In the body,
`[words sha256=<64 hex>]` stands where the operator's exact words were, `[host path N]` where a path
on the operator's machine was, and `[session N]` or `[session prefix N]` where a session identifier
was. A holder of the private source can render the copy again and compare it byte for byte.
