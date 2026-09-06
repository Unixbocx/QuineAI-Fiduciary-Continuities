# Baseline template — one file per artifact type.

Stored eval scores per artifact type; compared against on every eval run to
catch regressions. Copy this file as `<type>_baseline.md`, fill it, freeze it.

| Dimension | Mean (1–5) | n runs | spread | frozen |
|---|---|---|---|---|
| D1 Accuracy | | | | |
| D2 Completeness | | | | |
| D3 Structure | | | | |
| D4 Depth | | | | |
| D5 Cost | | | | |

Gate: flag any dimension regressing >0.3 from the frozen mean. A regression
is a blocker, not a surprise.

Source of scores: eval-run.sh sampled judge + manual labels from
`../calibration/`.