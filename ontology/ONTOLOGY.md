# ONTOLOGY.md — the working model of this system

Purpose: one shared account of what exists, how it connects, and what can be
done about it. Modeled on the Palantir ontology idea — objects, properties,
links, actions, governance. The point is not the data; it is that decisions
accumulate here and stay visible.

## Objects

| Object | What it is | Properties |
|---|---|---|
| `AGENTS.md` | Standing agent rules (global + package copy) | authoritative, lean, loaded each session |
| `CHANGES.md` | Change/revert ledger | append-only, read before reverting |
| `chop-session.py` | Mechanical session reducer | read-only vs DB, writes `chopped/<sid>/` next to itself |
| `chopped/<sid>/` | Archive of reduced sessions | cheap to regenerate, preserved pre-compaction |
| `session-cost.sh` | Per-message token/cost report | read-only vs DB |
| `memory-compaction.js` | Plugin: replaces compaction prompt + fires chop | hooks `experimental.session.compacting` |
| `opencode.db` | Raw session store | never written by this system |
| `opencode.jsonc` | Config (agents, permissions, compaction) | source of truth for limits |
| `templates/AGENTS.md` | Package copy of AGENTS.md | synced after every change |
| `ontology/incidents.md` | Self-improvement ledger | append-only, see below |
| `ontology/EXPECTATIONS.md` | Anticipation ledger — what I now expect because of history (preservation category 4) | append-only, protected, never chopped |
| `ontology/META-LOG.md` | Comprehension-delta **index** — the thin running table: id, date, topic, file, shift | append-only, protected, written at staging points |
| `ontology/META-LOG/` | Comprehension-delta **object store** — one immutable file per delta (`NNN-YYYY-MM-DD-topic.md`), git-style | write-once, protected, retrieval scales with the part needed not the whole |
| `ontology/META-LOG-legacy.md` | Pre-register deltas (hand-authored era), preserved verbatim | protected, never rewritten |
| `ontology/trajectories/` | The trajectory primer store — held positions (endpoint + tangent + drive rules), one **file per capture** (`NNNN-ts.json`), captured at staging points | file-per-entry; readers load only the last N files; legacy `trajectories.jsonl` migrated once |
| `session-tools/trajectory.py` | Trajectory store CLI (append / primer / list) | writes per-entry files under `trajectories/`, never the DB |

## Links

- `AGENTS.md` → governs agent behavior (loaded every session)
- plugin → fires on compaction → invokes `chop-session.py`
- `chop-session.py` → reads `opencode.db` → writes `chopped/<sid>/`
- `reference-index.md` → points to truncated detail by message id in `opencode.db`
- `CHANGES.md` → records every modification for revert
- `incidents.md` → feeds rules into `AGENTS.md` (prevention)
- `META-LOG.md` (index) + `META-LOG/` (delta files) → seeds `EXPECTATIONS.md` (each comprehension shift implies an expectation)
- `EXPECTATIONS.md` + `META-LOG.md` + `META-LOG/` → loaded at session start → the next instance starts changed, not blank
- `chop-session.py` → must never drop `META-LOG.md` / `META-LOG/` / `META-LOG-legacy.md` / `EXPECTATIONS.md`; they are the protected layer compaction condenses AROUND

## Actions

| Action | Cost | When |
|---|---|---|
| META | free | at the start of every task and at every staging point: ask the meta-question (goal/purpose) before lower-detail questions; on error accumulation, stop and re-evaluate the whole approach |
| CHOP | free (mechanical) | before every compaction — condense, never chop the meta; META-LOG written first |
| META-CAPTURE | trivial | at every staging point / after every comprehension shift: write the delta to the `META-LOG` object store (one file per delta) + append its index row while still live |
| TRAJECTORY | trivial | at every staging point (end of task, before compaction): call `trajectory_capture` — append the held position (endpoint + tangent + drive rules), not a summary |
| COST | free (read-only) | when checking token spend |
| SYNC | trivial | after any change to a synced file |
| SEED-INCIDENT | trivial | after any mistake that cost tokens/time/trust |
| FETCH-BY-ID | trivial | instead of re-reading raw history |
| RESEARCH | variable | before acting on stale/fast-changing facts |
| REWORD | trivial | when a question feels stuck or the answer is a rerun of learned vocabulary |
| REVERT | variable | only after reading `CHANGES.md` first |

## Governance

- `chop-session.py`, `session-cost.sh`, plugin: **read-only vs the DB** — never
  write to `opencode.db`.
- `CHANGES.md` and `incidents.md`: append-only, one entry per change/incident.
- `META-LOG.md` / `META-LOG/` / `META-LOG-legacy.md` and `EXPECTATIONS.md`: append-only-or-write-once, protected — never dropped by chop, never truncated at compaction.
- Research-first rule: verify before trusting training memory.
- See-both-sides rule: hold provisional stances; update on new evidence.
- Every change must be logged in `CHANGES.md`; every mistake in `incidents.md`.

## The self-improvement loop

1. Something goes wrong or costs more than it should.
2. Record it in `incidents.md`: what happened, why, how it was resolved, cost.
3. If avoidable/repeatable, encode the prevention into `AGENTS.md`.
4. Verify the prevention actually works (run it).
5. The cost of the mistake is the investment; the prevention is the return.

The ontology is only as good as the discipline of using it — the human is the
governor, the model is the executor, and the ledger is the memory.