---
name: ontology-query
description: Use when a question touches the system's own operation — how it remembers, what it decided, what it learned from failures, or what its rules are. Consults the working model instead of improvising. Triggers on "ontology", "what do we know", "check the model", "what's our stance", "what did we learn".
---

# Ontology query

The ontology is the shared account of what exists, how it connects, and what
can be done about it. When a question touches the system itself, consult it
instead of answering from memory.

## The files
- `~/.config/opencode/ontology/ONTOLOGY.md` — the working model: objects, links, actions,
  governance, and the self-improvement loop.
- `~/.config/opencode/ontology/ANTI-ONTOLOGY.md` — the failure taxonomy: what makes the system
  worst at its job. Read it to detect a failure mode before it happens.
- `~/.config/opencode/ontology/incidents.md` — the ledger: every recorded mistake with root cause,
  cost, and prevention.

## Method
1. Is the question about a decision, fact, or rule already recorded? Read the
   relevant section before answering.
2. Is the question about a failure pattern? Check ANTI-ONTOLOGY for the
   category, then check incidents for the precedent.
3. If the model is silent on the question, say so — do not invent the answer.
   The ontology is only as good as the discipline of using it.

## When to write back
- A new object, action, or link becomes part of how the system works → add it
  to ONTOLOGY.md.
- A new failure mode appears → add it to ANTI-ONTOLOGY.md.
- A mistake is made → log it in `~/.config/opencode/ontology/incidents.md` (see `../incident-log/SKILL.md`).

## Gotchas
- Treating the ontology as frozen: it is a working model, it evolves.
- Consulting memory when the answer is a web search away (research-first wins).
- Recording opinions as facts in the model — provenance points one direction.

## References
- `PLAN.md` — the buildout plan this model describes.
- `Audit.md` — the ecosystem decisions that shaped it.