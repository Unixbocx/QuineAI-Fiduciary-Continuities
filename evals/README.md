# The hybrid eval harness

Measurement is discipline. No change to the system ships without a number.

**The hybrid norm:**
1. **Deterministic gate (100%).** Structural checks, free to run: required
   headers present? output landed in the right directory? summary references
   its source? A failed check fails the artifact — no judge needed.
2. **LLM judge (sampled).** For the fuzzy remainder, the grader agent scores
   against `rubrics.md`: 5 anchored dimensions, 1–5, "0 = cannot tell". The
   judge must be a different model family than the producer; order randomized,
   model metadata stripped, lowest score justified in one sentence.
3. **Calibration.** Hand-label ~20–30 artifacts on the same rubric, run the
   judge on them, require ≥75% agreement (Krippendorff ~0.8). Re-run when the
   judge model or rubric changes.
4. **Baselines + gate.** Store scores per artifact type in `baselines/`. Flag
   any dimension regressing >0.3. Run nightly, not per-change.

**Targets:** checkpoints, chops, summaries, incident quality, skill gotchas.

## Layout
- `rubrics.md` — the 5-dimension rubric with anchors.
- `calibration/` — hand-labeled reference set + agreement report.
- `baselines/` — stored scores per artifact type.
- `cases/` — eval cases; incidents seed regressions here so they never recur.

## Usage
`scripts/eval-run.sh` runs the gate and dispatches the sampled judge run. See
`../skills/eval-harness/SKILL.md` for the full method.