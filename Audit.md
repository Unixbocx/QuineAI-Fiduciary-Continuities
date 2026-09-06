# Phase 0 Audit — Ecosystem Reuse vs Build

Phase 0 of PLAN.md: audit the opencode ecosystem before building, so nothing is
reinvented. Read-only review performed 2026-08-19. No system changes resulted.

## Method

Six ecosystem plugins researched in depth (repos, npm, docs, releases):
opencode-skillful, opencode-dynamic-context-pruning, opencode-scheduler,
opencode-supermemory, opencode-conductor, opencode-workspace. Plus secondary
scans of opencode-claude-hooks, oh-my-opencode, opencode-background-agents,
opencode-goal-plugin. Each mapped to ALOP's seven organs (plugin, skills,
agents, commands, scripts, ontology, evals).

## Verdicts

### ADOPT — reuse, don't rebuild

**opencode-skillful** (zenobi-us, 276★, npm @zenobius/opencode-skillful, v1.2.5)
- Implements the Anthropic Agent Skills spec for opencode. Tools: `skill_find`
  (natural-language search with negation/quoted phrases), `skill_use`
  (lazy-inject a skill into chat as a silent user message), `skill_resource`
  (read references/assets/scripts from a skill on demand).
- Discovery from configurable base paths; only skills actually used consume
  tokens (~100 tokens metadata otherwise). Registry pre-indexes resources,
  path-traversal-safe.
- **Role in ALOP:** the skills method-layer loader. We author the six method
  skills in the Agent Skills standard; skillful provides discovery + injection.
- **Caveats:** injection persists in conversation history (pair with cost
  tracking); skill discovery happens at startup (restart to reload); recent
  v1.2.5 fixed an agent-preservation bug during injection (keep current).

**opencode-dynamic-context-pruning (DCP)** (Opencode-DCP, 3K★, npm, v3.0.0)
- Model-driven `compress` tool that replaces closed/stale conversation spans
  with high-fidelity technical summaries mid-session (smarter than static
  compaction). Nested summaries preserve info across layers of compression.
- Automatic strategies: deduplication of repeated tool calls, pruning of
  errored tool inputs after N turns. `/dcp` commands (context, stats, sweep,
  compress, decompress, recompress, manual). Protected tools by default:
  task, skill, todowrite, todoread, compress, batch, plan, write, edit.
  Never modifies session history — replaces with placeholders before dispatch.
- **Role in ALOP:** the "Select/Compress" context strategy automated. Turns two
  ANTI-ONTOLOGY cost failures (duplicate recompute, stale context rot) into
  automatic fixes. Complementary to our compaction hook: theirs is mid-session
  and model-driven; ours is end-of-window full checkpoint + archival chop.
- **Caveats:** pruning invalidates prompt-cache prefixes from that point
  forward (cache-miss cost vs. token savings trade-off, generally favorable);
  must verify coexistence with our compaction hook.

**opencode-scheduler** (different-ai, npm, 3K downloads/week, v1.3.0)
- Schedules `opencode run` via systemd/launchd/Task Scheduler with cron
  fallback. Tools: schedule_job, list_jobs, get_job, update_job, delete_job,
  run_job, job_logs, cleanup_global, get_skill, install_skill. Jobs scoped by
  workdir, supervised (no overlap, optional timeout), non-interactive by
  default (OPENCODE_PERMISSION deny), logs to `~/.config/opencode/logs/`.
- **Role in ALOP:** temporal parallelism — the file-dialogue runner,
  nightly eval runs, metric pulls. **Resolves PLAN.md §9's open question** on
  the cron mechanism (no hand-rolled systemd needed).
- **Caveat:** cron fallback backend has no missed-run catch-up; systemd/launchd
  backends do.

**opencode-background-agents** (bundled in opencode-workspace)
- Async delegation with context persistence — delegate work that keeps running
  while the main stream continues.
- **Role in ALOP:** sleep-time/async parallel work (the temporal organ).

### ADAPT — take the pattern, not the code

**opencode-conductor** (derekbar90; palaeologic fork)
- Context→Spec→Plan→Implement lifecycle. Tracks (feature/bug units) with
  spec.md + plan.md + metadata.json; a project-architect `@conductor` agent;
  `/conductor:*` commands; pins a flash model for planning phases. palaeologic
  fork adds descriptor-driven branch context and per-role model routing.
- **Role in ALOP:** the Track artifact structure (spec/plan/status/metadata)
  is borrowed for our `/curriculum`, `/checkpoint`, `/plan` commands and as the
  ontology's "plan" object shape. Do not adopt the plugin itself — it is
  code-project-specific; ALOP's focus is the agent's own logistics.

**opencode-workspace** (kdcokenny, 533★, installable via OCX)
- Bundle of 16 components as one install: 4 plugins (delegation/planning/
  notify/worktree), 2 npm plugins (DCP, md-table-formatter), 3 MCP servers,
  4 agents (researcher/coder/scribe/reviewer), 4 skills, /review command,
  orchestrator configs, permission boundaries (read-only orchestrators
  delegating via `task`; webfetch deny; agent sandboxing).
- **Role in ALOP:** validates ALOP's bundle shape exactly — this is what ALOP
  looks like. Provides the permission model (read-only orchestrators, sandboxed
  specialists) and OCX (ocx) as a distribution/install path for ALOP itself.

### HOLD — evaluate later

**opencode-supermemory** (supermemoryai, npm, 2.2K downloads/week, v2.0.11)
- Persistent vector-store memory across sessions: add/search/profile/list/
  forget, scopes user/project, typed memories (error-solution, learned-pattern,
  preference, architecture, project-config, conversation), auto-capture via
  keywords, preemptive compaction at 80%, `<private>` privacy tags.
  Cloud or self-hosted backend.
- **Role in ALOP:** complementary in theory — a derived semantic layer pointing
  back at our canonical ontology (incidents ≈ error-solution memories; gotchas
  ≈ learned-patterns). But: requires paid/self-hosted backend; its preemptive
  compaction hooks the same compaction path as ours (conflict risk); semantic
  recall quality varies (research: no single memory substrate dominates).
- **Decision:** only adopt if semantic recall is actually needed. Our file-based
  derived layer (ontology, chops, summaries) already covers structured recall
  for free and follows the canonical/derived rule.

### BUILD — no existing plugin covers these

- **The ontology core** — structured objects/links/actions/governance as
  loadable context. Nothing in the ecosystem does structured self-ontology.
- **The eval harness** — deterministic gate + calibrated cross-family LLM judge
  + baselines + regression threshold. No ecosystem plugin does calibrated evals.
- **The method skills** — curriculum, reword-pass, incident-log, ontology-query,
  chain-of-custody. Our unique content.
- **Havruta + grader agents** — workspace's reviewer is code-review-only;
  nobody does position-swap adversarial review (havruta) or rubric judging
  against our ontology artifacts (grader).

## Coexistence risks to verify before adopting

1. DCP + our compaction hook both touch context — likely complementary
   (mid-session model-driven vs end-of-window full checkpoint) but must test.
2. Supermemory's preemptive compaction could conflict — avoid until the
   HOLD decision is made.
3. Skillful's silent-message injection adds context per use — pair with ALOP
   cost tracking.
4. Background-agents delegation + our subagent limits (steps/permissions) must
   compose without bypassing the limits.

## Effect on the plan

Phase 0 largely resolves into adoption decisions:

| ALOP need | Source | Type |
|---|---|---|
| Skills loader | opencode-skillful | ADOPT |
| Mid-session compression + dedup | opencode-dynamic-context-pruning | ADOPT |
| Cron/scheduled agents | opencode-scheduler | ADOPT |
| Async/sleep-time work | opencode-background-agents | ADOPT |
| Plan/track artifact shape | opencode-conductor | ADAPT |
| Bundle architecture + permissions + distribution | opencode-workspace + OCX | ADOPT pattern |
| Semantic memory (optional) | opencode-supermemory | HOLD |
| Ontology core, method skills, eval harness, havruta/grader | — | BUILD |

Remaining build scope is therefore: the ontology core, the six method skills,
the eval harness, and the two agents — plus verification of the coexistence
risks above.

## Post-audit validation — DeepSeek Harness (dsh)

Reviewed 2026-08-19 (README, docs/architecture.md, AGENTS.md). dsh is a
standalone agent harness where **everything is a plugin** (Cordis-based). Not
reusable code for ALOP (ALOP is a plugin inside opencode; dsh is its own
runtime), but high-signal validation:

- **No privileged core.** Every part of dsh — model adapter, tool registry,
  session log, agent loop — is a replaceable plugin. Validates ALOP's organ
  model: the plugin is a coordination fabric, not a privileged brain.
- **Model-visible ⟺ logged** (runtime-invariant enforced). Anything that reaches
  a model request must be reconstructable from the session log. This is ALOP's
  canonical/derived rule stated as a hard invariant. Adopt as a governance rule.
- **Registrations are effects that unwind on unload.** Every contribution is
  reversible (`register()` returns a disposer). Matches ALOP's append-only
  ledger + revert discipline, as a mechanical property.
- **Profile → bundle → patch layering.** A running dsh is a plugin tree stacked
  in ordered layers; `--dump-config` prints every row and any row is
  replaceable by user patch. The config story ALOP's install.sh "merge blocks"
  should evolve toward: replaceable rows, not blind copy.
- **Capability seam = Service Definition + Provider + Consumer** — one role
  alone is not a seam. ALOP lesson: each organ needs its interface defined,
  not just its content file.
- **Keyless snapshot replay** (`test:snapshot`): deterministic replay of
  transcripts vs expected outputs; re-record when behavior legitimately
  changes. The eval harness's deterministic gate made concrete.
- **`self-modification/` package** — the agent inspects and mounts its own
  plugins. ALOP's self-improvement loop validated as a first-class concern.
- **Governance norms to borrow:** no hardcoded tunables in plugins (deployment
  choices are Config fields, not constants — e.g. ALOP's CHARS_PER_TOKEN, eval
  thresholds); misconfiguration fails loud (never silently skip a missing
  referent — the dangling-reference rule we just hit).

**Effect on plan:** architecture validated; add "model-visible ⟺ logged" and
"seam = three roles" as ALOP governance rules; make tunables config fields;
design the eval gate as keyless snapshot replay.