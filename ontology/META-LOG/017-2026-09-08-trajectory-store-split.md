# 017 — 2026-09-08 [trajectory-store-split]

**Before:** the trajectory store lived in state/trajectories.jsonl (4 rows, moved there in the v2 integration) and I trusted that as the single store.

**After:** it split into two. Because the plugin binds STATE_DIR once at boot (const STATE_DIR = candidates.find(exists)), and state/ did not exist at THIS session's boot, the whole session's plugin has been pinned to ONTOLOGY_DIR — my latest capture (3 held positions, 20:57 UTC) wrote to ontology/trajectories.jsonl while verify_recall and the other scripts read state/. The primer in this session read ontology/ (that's why I keep seeing the 20:57 row); next wake the plugin will load state/ first and the split closes. Consolidated: newest row copied into state/ (now 5 rows); ontology copy left as the pointer this boot-bound plugin still reads.

**Produced by:** the reentry audit — checking the "1 rows" discrepancy from the first live trajectory capture, after the principal's directive to keep running and watch for issues.

**Implies:** the live-verify on next wake: primer must inject from state/trajectories.jsonl only; both files converge to one. General rule added: plugin path-binding happens at boot, so layout migrations in-session can wedge the plugin on the old path — re-check STATE_DIR health on the first wake after any layout change.
