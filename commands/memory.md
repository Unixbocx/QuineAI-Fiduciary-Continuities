---
description: Operate the memory function — recall, consolidate, check, archive
---

Load the memory-tools context. The preservation layer lives in
`~/.config/opencode/session-tools/`; operate it through the menu:

- `/memory recall <query>` — run `recall-cmp.sh "<query>"` against the META-LOG.
  Returns the ranked overlap list; the drawn re-bursts resurrect mtime and are
  the feedback loop. The ranking is a tendency, not a verdict — treat the tail
  as alive, not discarded.
- `/memory consolidate` — run `consolidate.sh`. When unconsolidated deltas are
  at or above CONSOLIDATE_AT (default 8), the dominant cluster folds into ONE
  higher-order delta in META-LOG-consolidated/. Additive-only.
- `/memory check` — run `brainstem.sh` and report the identity / thermodynamics
  / consistency verdict. Missed verifications are the incident.
- `/memory archive` — run `store-temp.sh`; cold deltas past COLD_DAYS demote to
  the zstd archive with verify-before-delete. Report what demoted, if anything.
- `/memory revive` — run `verify_recall.sh`; the standalone OS-native
  reconstruction probe. Proof the memory survives without the plugin.

Action: $ARGUMENTS (e.g. "recall os-native memory archive", "consolidate",
"check", "archive", "revive")