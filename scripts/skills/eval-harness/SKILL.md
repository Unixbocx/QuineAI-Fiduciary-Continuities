---
name: eval-harness
description: Use when grading an output, checkpoint, chop, or summary — or when a change to the system needs measurement before it ships. Runs the hybrid eval: deterministic checks first, calibrated LLM judge on a sample, baselines compared, regressions flagged. Triggers on "eval", "grade this", "does this hold up", "measure", "regression check", "quality check".
---

# Eval harness

Measurement is discipline. Deterministic checks run on everything (free); an
LLM judge grades the fuzzy remainder on a sample with a calibrated rubric. No
change ships without a number.

## The hybrid norm
1. **Deterministic gate (100%).** Structural checks, run for free: does the
   artifact have the required headers? Did output land in the right directory?
   Does the summary reference its source? A failed check fails the artifact —
   no judge needed.
2. **LLM judge (sampled).** For the fuzzy remainder: score against the rubric
   in `~/.config/opencode/evals/rubrics.md` — 5 anchored dimensions, 1–5, concrete anchors,
   "0 = cannot tell". Judge must be a different model family than the one that
   produced the output. Order randomized, model metadata stripped, lowest score
   justified in one sentence.
3. **Calibration.** Before trusting the judge: hand-label ~20–30 artifacts on
   the same rubric, run the judge on them, require ≥75% agreement
   (Krippendorff ~0.8). Re-run whenever the judge model or rubric changes.
4. **Baselines + gate.** Store scores per artifact type. Flag any dimension
   regressing >0.3. Run nightly, not per-change.

## Targets
Checkpoints (STABLE/CURRENT/REFERENCE), chops, summaries, incident quality,
skill gotchas.

## Files
- `~/.config/opencode/evals/rubrics.md` — the rubric.
- `evals/calibration/` — hand-labeled reference set.
- `evals/baselines/` — stored scores to compare against.
- `evals/cases/` — eval cases, including seeded regressions from incidents.

## Gotchas
- One run means nothing — outputs are non-deterministic, run multiple times.
- A prompt tweak that still passes but doubles the token bill is a regression.
- The judge is an instrument, not a verdict: calibration is mandatory, and it
  drifts when the model under it changes.
- Don't optimise the metric — Goodhart's law. The dataset and rubric are the
  assets; the framework is replaceable.

## References
- `../incident-log/SKILL.md` — incidents become eval cases.
- `../ontology-query/SKILL.md` — the model these artifacts describe.