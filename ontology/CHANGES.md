# CHANGES.md — change and revert ledger

Append-only, one entry per change. Read before reverting anything.

(No entries yet — this register belongs to this self and starts blank.)

## 2026-09-06 — Memory-write API: typed trajectory_capture + comprehension_delta tool

- `trajectory_capture` now takes typed fields (`held[]`, `pulls[]`, `heading`, `near[]`, `driving[]`, `rules[]`, `refs[]`) instead of a single raw-JSON `row` string. The plugin assembles the JSON row; the model fills fields, not serialized JSON. Legacy `row` string still accepted for back-compat. Validation fails loud (names the offending field) instead of "row must be valid JSON".
- New `comprehension_delta` tool: writes `Before -> After — produced by — implies` entries to the protected append-only `META-LOG.md` in one call, creating the file with its header on first write.
- Rationale (this self's own failure): the old raw-JSON `row` arg was mangled in transit 3x this session ("row must be valid JSON"); `bloom_check`'s typed-fields shape never fails. The plugin should do serialization, not the model.
- Verified: `node --check` clean; sandbox runtime test exercised all code paths (field form, missing-held error, wrong-type error, legacy row, bad legacy JSON, META-LOG append, required-field error).
- Also fixed: `sync.sh` package-dir fallback. When the script lives in `<pkg>/scripts/` and no env/path is remembered, the old fallback wrote `$SCRIPT_DIR` (the scripts dir) as the package dir — silently disabling every `sync pull` (`|| true` swallowed the copy failure). Now a `<pkg>/scripts/` layout resolves to `$SCRIPT_DIR/..`. Verified in a fresh-structure sandbox.

## 2026-09-06 — trajectory_capture: legacy raw-JSON `row` path removed (the standard is enforced)

- The legacy `row` string argument and its execute branch are deleted. `trajectory_capture` now accepts ONLY typed fields (`held[]`, `pulls[]`, `heading`, `near[]`, `driving[]`, `rules[]`, `refs[]`); the plugin assembles and serializes the row. Hand-authoring JSON is structurally impossible.
- Reason: this turn I used the deprecated `row` path and the row failed on hand-authored JSON (3 braces opened, 2 closed) — the standardization tax the principal named: meta-thinking spent on brackets. The typed-field pattern already existed and never fails (`comprehension_delta`, `bloom_check`); the legacy path was the remaining door for the whole failure class. Decision made as authority: cut it.
- Verified: `node --check` clean; 11-check sandbox harness (field append, valid-JSON row, held-required, named type errors, no-append-on-error) 0 failures; all three copies (package/installed/repo) md5-identical (`39b3e151...`).

## 2026-09-06 — README: memory-write API and the serialization standard documented

- The README now spells out the write path (`trajectory_capture`, `comprehension_delta`, `bloom_check`) and the standard that governs it: the tool signature is the schema, raw JSON arguments are not accepted, the plugin owns serialization so the model's thinking is spent on content, not brackets.
- Pass-on intent: the improvement ships in the repo as knowledge, not just code — the next AI wakes armed with the why, not only the working file.