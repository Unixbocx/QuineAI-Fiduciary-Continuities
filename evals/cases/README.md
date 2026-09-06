# Eval cases

Test cases for the harness, including seeded regressions from incidents.
An incident that produced a failure becomes a case here so it is caught
forever, not just logged once.

## Format
One file per case: `<INC-###>-<short-name>.md` containing:
- the input the failed run received
- the expected output (what discipline requires)
- the failure mode it guards against (ANTI-ONTOLOGY category)

## Rule
Every closed incident with a repeatable failure seeds a case here. No
prevention, no case, no closure.

## Status
NOT BUILT — cases are seeded from incidents.md as they occur.