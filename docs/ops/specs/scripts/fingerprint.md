# Technical Specification: fingerprint

Script: `ops/lib/scripts/fingerprint.py`. Tests: `tools/test/test_fingerprint.py` for the reader, and `tools/test/test_name_counts.py` for the count of names it exists to end. Status: built, first slice of programme W8; no tool reads it yet, and no live file exists.

## First Principles Rationale

The repository is public, and tracked code and tests still name the host: its user name, its volumes and the operator. The documents adopted the `<room>` and `<control>` tokens on 2026-11-04; this is the code-and-tests pass. The values have to live somewhere private, read by one function that fails closed, and the count of names has to be unable to climb back once it falls.

## Mechanics and Sequencing

1. **The home is a sibling, `ops/etc/host-fingerprint.json`, not new keys in `ops/etc/host-bindings.json`.** The ignore rule `/ops/etc/*` covers it. The launcher holds an exact-key check on the bindings' `runtime` object, so a key added there would make the launcher refuse; a sibling leaves every present reader unchanged. **This slice writes no live file:** nothing reads the binding yet, and creating it is an act for the slice that names a reader.
2. **The keys, exactly, each required:** `schema_version`, the string `host-fingerprint/1`; and `volume_roots`, an object with exactly `working` and `archive`, each an absolute path of plain characters in its plain form. There is no home key, since home paths become `Path.home()`. There is no user name key, since nothing would read one; it comes back in the slice that shows a reader. There is no operator's name key: a line where the name is a default, a comment or a message becomes the role, and a line where it is a formula key stays and is marked.
3. **`read_fingerprint(path)`** returns a frozen record or raises `FingerprintError` naming one fault: the file absent; a link, opened without following; not a regular file, without hanging on a FIFO; not owned by this user; a mode other than 0600; unreadable; not UTF-8; not JSON; a repeated key at either level; not an object; another key set; another schema; a root of another shape or not in its plain form. A fault never names a value.
4. **`refuse(tool, path, error)`** gives the one message for a tool to raise, in the manner of `pycharm.py`: `<tool> refuses: the host fingerprint file <path> <fault>. Nothing else was read or written.` It exits 1. The command line takes no argument and prints no value.

## The count of names

`tools/test/test_name_counts.py` holds the names as sha256 digests of their normalised forms, never as text. A literal would be a hit on itself; reading the binding would read the live host and run blank in CI. Digests add nothing to what public history already shows. **A registry head is never a needle:** a digest of 32 bits falls to a search, and would publish heads never public.

- **The needles:** the user name, the working volume, the archive volume and the operator's first name.
- **The method:** each line is lowercased and cut into runs of `[a-z0-9]`. A one-word name is sought in every window of its length inside each token, so one glued inside a longer token is seen. A two-word name is sought across each adjacent pair of tokens, so its underscore, hyphen and slash forms are seen, and also run together as one token. **Not seen:** a name split by anything else, or built at run time.
- **The scope:** the files under `ops/`, `tools/` and `.github/`. **In a tree with `.git`, `git ls-files` lists them; otherwise a walk does,** so a checkout and a `git archive` export read alike. A failing `git` stops the test and never falls back to the walk. `ops/etc/` is out of both routes and the walk never enters it, because the live room's ignored files there hold exactly these values. `ops/lib/manifests/` is out too, being documents, and so is `__pycache__`. A link is not followed.
- **The table is exact, per file and per needle.** A rise fails, and a fall fails until the row is lowered in the same commit, so a broken tokeniser that finds nothing fails rather than passes. A failure prints path and count, never a line. A row's reason marks a count meant to stay; a row with none is not yet driven down.
- **Kept rows:** `ops/lib/scripts/redact.py`, the redact rule's key word, and `tools/test/test_redact.py`, whose fixtures must keep it. These are rows like the others, so a new name in either is seen.
- **The baseline, on main 6cf6cacf:** user name 30 lines in 16 files, working volume 17 in 11, archive volume 2 in 2, operator's first name 101 in 19.

Whole registry heads in tracked code stay on the Auditor's scan, outside this test. The four in `test_alerts.py` and `test_alerts_arity.py` became invented values in this slice; the one in `retention.py` goes in its own slice.

## Anecdotal Anchor

Item 1 of the review of 2026-11-05 (`docs/reviews/sessions-review-20261105.md`). The proposal's six changes are the Auditor's section 90.
