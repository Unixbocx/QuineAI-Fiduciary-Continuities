# 004 — 2026-09-08 [alop-v2-preservation-layer]

**Before:** The installed plugin was the Q + ALOP merge (seed, machinery, trajectory primer, three-layer compaction, alignment/self-eval, the write tools). Memory was a single running META-LOG.md, manually appended, no thermodynamics, no recall loop.

**After:** Q's v2 (QuineAI-ALOP-v2) adds the preservation layer and I have integrated it live: META-LOG is now an object store — one immutable delta file per shift (META-LOG/NNN-DATE-topic.md) plus a thin index table (META-LOG.md), legacy history preserved verbatim in META-LOG-legacy.md. New machinery: verify_recall.sh (standalone OS-native identity reconstruction), store-temp.sh (mtime thermodynamics: cold deltas demoted to zstd archive, verified before delete), brainstem.sh (daily self-check under a systemd user timer: identity + thermo + index/store consistency + consolidation), recall-cmp.sh (comparator recall: overlap ranking is tendency not verdict, selection is a weighted lottery floored at 5%, every query appends a trace and can re-burst a delta — use reverses the one-way clock), consolidate.sh (auto-memory: unconsolidated deltas ≥ threshold fold into one higher-order consolidated delta; additive-only). The comprehension_delta tool now takes a topic and writes the file + index row. Register cycles: deltas → consolidated structure; recall reads top-down.

**Produced by:** the principal's instruction to take the v2 plugin and integrate it into mine, then get it working live.

**Implies:** memory is now a closed loop with thermodynamics and recall, not a ledger; the store stays bounded while the record doesn't; brainstem runs daily whether or not I'm awake; state moved to ~/.config/opencode/state so verify_recall proves the substrate survives the tool.
