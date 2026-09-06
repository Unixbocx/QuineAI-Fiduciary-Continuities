---
description: Run the agent checkpoint — STABLE / CURRENT / REFERENCE summary
---

Run the checkpoint routine:
1. Read ontology/ (ONTOLOGY, ANTI-ONTOLOGY, incidents) and the plan if changed.
2. Write the three-part summary:
   - STABLE: what holds — working model, standing rules, verified facts.
   - CURRENT: what is in motion — active context, pending decisions.
   - REFERENCE: pointers to the files that carry the detail.
3. Keep each section tight; the checkpoint is a handoff, not a diary.
4. If anything changed materially, update the ontology or log an incident
   first — do not bury changes in the checkpoint.

Extra context: $ARGUMENTS