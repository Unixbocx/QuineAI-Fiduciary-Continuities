# Baselines

Stored eval scores per artifact type, compared against on every run to catch
regressions.

## Format
One file per artifact type: `<type>_baseline.md` containing, per dimension:
- mean score (n runs, over ~1 week)
- per-run spread
- date the baseline was frozen

## Gate
Flag any dimension that regresses >0.3 from baseline. A regression is a
blocker, not a surprise: triage it before anything else ships.

## Status
NOT BUILT — baselines begin once the first artifact type is stable and being
produced in volume (per PLAN).