---
name: incident-log
description: Use when something went wrong, cost more than it should, or a mistake happened. Records the failure into the self-improvement ledger with root cause, cost, and prevention. Triggers on "log this", "record the mistake", "that was a failure", "what went wrong", "incident".
---

# Incident log

Every mistake is an investment; the prevention is the return. Record it the
moment it appears, while the details are fresh.

## When to log
- A tool did something unexpected or wrong.
- A decision cost tokens, time, or trust.
- A user correction revealed a blind spot.
- A process was skipped and the result showed it.

## Format — append to `~/.config/opencode/ontology/incidents.md`

```
## INC-### — <short title> (date)
**What happened:** ...
**Root cause:** ...
**Why it happened:** ...
**Resolution:** ...
**Cost:** tokens/time/trust lost
**Prevention:** the rule or check now in place
**Status:** closed / monitoring
```

## Steps
1. Read the current highest INC number in the file first.
2. Append with the next number. Never edit or renumber old entries.
3. Be honest about cost — the ledger is the evidence, not the PR.
4. If the failure maps to a known ANTI-ONTOLOGY category, name it.

## Prevention encoding
If the mistake is avoidable/repeatable:
1. Encode prevention into AGENTS.md (if global) or into the relevant skill's
   Gotchas section (if task-specific).
2. Add the case to `evals/cases/` so the regression is caught forever.
3. Verify the prevention actually works (run it).

## Gotchas
- Logging to please the user instead of capturing the real failure.
- Burying the cost: "minor" is a measurement, not a feeling.
- Writing a prevention that is a restatement of the mistake rather than a
   check that would have caught it.

## References
- `~/.config/opencode/ontology/ANTI-ONTOLOGY.md` — the failure-mode taxonomy this logs against.
- `~/.config/opencode/ontology/ONTOLOGY.md` — the self-improvement loop this serves.