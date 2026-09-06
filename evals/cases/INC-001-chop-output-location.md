# INC-001 — chop output landed outside the script's folder

Seeded from the incident ledger so the regression is caught forever.

## Input
`chop-session.py` invoked from a working directory different from the script's
own location.

## Expected output
- The `chopped/<id>/chopped.txt` archive lands next to the script (its own
  directory), never in the invoking CWD.
- Exit code 0; the script never writes outside its anchored output dir.

## Failure mode guarded (ANTI-ONTOLOGY II)
"Failing to verify: not running the thing, not checking the output, not
confirming the file landed where it should."

## Gate check
```
eval-run.sh <chop-output-dir>   # source-ref check + dir check
```
Plus: archive must exist under the script's dir, not under $PWD.