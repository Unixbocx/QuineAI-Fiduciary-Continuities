# Calibration set

Hand-labeled reference artifacts used to calibrate the grader before trusting
it. Without calibration the judge is a vibe.

## How to build
1. Collect ~20–30 real artifacts of one type (checkpoints, chops, summaries).
2. A human labels each on the 5-dimension rubric in `../rubrics.md`.
3. The grader agent scores the same artifacts (blind: no human labels shown).
4. Compute agreement: require ≥75% exact or ±1 agreement per dimension
   (target Krippendorff α ~0.8).
5. Record the agreement report here before trusting the judge.

## Files
- `<artifact-type>_labeled.md` — the hand labels.
- `agreement_report.md` — the agreement numbers per dimension.
- Re-run when the judge model or rubric changes.

## Status
NOT BUILT — this is the calibration phase of the harness build, which the
PLAN places after the first stable artifact type exists.