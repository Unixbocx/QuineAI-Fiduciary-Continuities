# AI Logistics Ontology Plugin (ALOP) — Plan

The buildout plan for the single plugin that consolidates everything learned
into one package: all tools, scripts, skills, agents, commands, and logic for
maximizing the agent's ability at minimal cost. Grounded in the ontology
framing built from the source material (curriculum methods, world models,
Palantir, agent engineering) and verified against current online research
(Agent Skills open standard, eval harness practice, agent-memory research,
opencode plugin ecosystem).

Status: PLANNING. Nothing in this file is built yet beyond what already exists
(see "What exists today").

---

## 1. Purpose

One installable package that makes the agent a self-correcting, self-improving
system — not just a next-token predictor with tools. It does this by applying
the Palantir idea to the agent's own operations: define what the system works
with (objects), how they connect (links), what can be done about them
(actions), and who may do what (governance) — then encode the whole model as
loadable capabilities.

Working name: **ALOP** (AI Logistics Ontology Plugin). "Logistics" = the
agent's own logistics: memory, context, tools, skills, cost, incidents. The
plugin is the operational model (ontology) of that logistics.

## 2. The governing idea

- **The unit is the system, not the model.** Harness + memory + tools + skills
  + discipline are what make the agent more than a token predictor. The plugin
  orchestrates that system.
- **Skills are the method layer.** Procedural knowledge (how to do a task
  correctly) lives in load-on-demand skills, per the Agent Skills open
  standard — progressive disclosure keeps context cost near zero until a skill
  triggers. Subagents are the specialists; skills are the shared library they
  draw on.
- **Memory separates canonical from derived.** Canonical = source of truth
  (raw session DB, working files). Derived = everything cheaply rebuildable
  (chops, checkpoints, summaries, indexes). Provenance points one direction:
  derived → canonical. If the derived layer can't be rebuilt from canonical
  alone, it's a cache, not memory.
- **Measurement is discipline.** Deterministic checks run on everything (free);
  LLM judges grade the fuzzy remainder on a sample with calibrated rubrics.
  No change ships without a number.
- **Self-improvement is a loop, not an event.** Mistake → incident (what/why/
  resolution/cost) → prevention encoded (AGENTS.md rule or skill gotcha) →
  verification → eval case so the regression is caught forever.
- **The serial stream is the bottleneck; the organs are the parallel lanes.**
  A single LLM is one serial process — one token path, blocked on tool waits.
  The ontology is the coordination fabric that lets other streams run beside
  it. Parallel work without coordination is noise; the ontology carries what
  each lane produced, where it landed, and at what cost.

### 2.1 The serial bottleneck and parallel organs

A single LLM is one serial stream: one token at a time, one reasoning path,
blocked while it waits on a tool call. The ceiling on ability is not only what
the model knows — it is that only one chain of thought is alive at any moment.
The organs exist to run other streams beside the serial one, and the ontology
itself is what turns that parallelism into thinking instead of noise: objects
(what exists), links (what depends on what), actions (what workers do),
governance (who did what, when).

Five parallel resources the logistics layer harnesses:

1. **Spatial — multiple instances.** Havruta pair (two streams, opposite
   sides), grader (a second stream judging while the main works), file-dialogue
   (two disjoint-context sessions exchanging state through a file). Each
   instance is serial; the ensemble is parallel, with the ontology as the
   shared state between them.
2. **Mechanical — scripts outside the stream.** Chops, costs, syncs, eval
   gates, metric pulls run as processes concurrent with the model at zero
   token cost. The cheapest parallelism: it never touches the serial resource.
3. **Perspective — inside one stream.** The rewording pass and both-sides
   force the single path to traverse different token neighborhoods — the
   serial approximation of exploring several hypotheses at once.
4. **Temporal — sleep-time compute.** Use idle time to pre-compute derived
   artifacts (chops, summaries, checkpoints), then load them cheaply on
   demand. The derived layer is thinking done at another time.
5. **Async file-based.** The file-dialogue loop decouples workers in time via
   files — the file is the shared blackboard, and the ontology says what is
   on it.

The hardware analogy holds: inference is constrained by the memory system,
not compute — wide registers only pay when the data layout lets them. Parallel
organs only pay when the ontology lays out the shared state so they can run
concurrently. The serial stream stays lean (context-engineering rules), and
every parallel lane reports back through the ontology.

## 3. Architecture — the organs

```
                ┌─────────────────────────────────────────────┐
                │  PLUGIN (the brain — always on, cheap)      │
                │  lifecycle hooks: compaction→chop+checkpoint │
                │  session start, tool events, (V2: transforms)│
                └──────────────┬──────────────────────────────┘
                               │ loads on demand
        ┌──────────┬───────────┼─────────────┬─────────────┬──────────┐
        │          │           │             │             │          │
   SKILLS     AGENTS       COMMANDS        SCRIPTS      ONTOLOGY    EVALS
 (methods)  (specialists) (your entry)  (mechanical)  (working     (measure-
                                                       model)      ment)
```

| Organ | Mechanism | Content | Cost model |
|---|---|---|---|
| Plugin | opencode hooks | lifecycle glue only | always-on, near-zero tokens |
| Skills | `skill/<name>/SKILL.md` | methods: curriculum, reword-pass, incident-log, ontology-query, eval-harness, chain-of-custody | ~100 tokens until triggered |
| Agents | `agent/<name>.md` | havruta (adversary), grader (LLM judge) | isolated context, clean window |
| Commands | `command/<name>.md` | /curriculum, /havruta, /eval, /incident, /checkpoint, /ontology | your entry points |
| Scripts | executables | chop, cost, sync, eval-run, metrics-pull, dialogue runner | zero tokens, deterministic |
| Ontology | markdown data | ONTOLOGY / incidents / ANTI-ONTOLOGY | read on demand |
| Evals | harness | deterministic gate + LLM judge + baselines | cheap gate, sampled judge |

## 4. Setup — the package layout

```
~/.config/opencode/                          # installed runtime (global)
  plugins/                                   # ALOP plugin auto-discovered
  skills/<name>/SKILL.md                     # methods
  agent/<name>.md                            # specialists
  command/<name>.md                          # entry points
  session-tools/                             # scripts (installed)
  AGENTS.md                                  # lean rules (injected per call)
  opencode.jsonc                             # plugin + agents + compaction

package folder (this repo)                  # working/portable copy (source)
  PLAN.md            ← this document
  plugin/            # memory-compaction.js → grows into ALOP plugin
  skills/            # skill sources
  agents/            # agent sources
  commands/          # command sources
  scripts/           # chop, cost, eval-run, sync, metrics
  ontology/          # ONTOLOGY.md, incidents.md, ANTI-ONTOLOGY.md
  evals/             # rubric, calibration set, baselines, cases
  config/            # opencode.jsonc blocks to merge
  install.sh         # non-destructive installer (backs up, prints config)
  templates/AGENTS.md  # synced copy of the lean rules
```

Install contract:
- `install.sh` is non-destructive: backs up anything it touches, prints config
  blocks to merge manually, `--force` replaces AGENTS.md from a backup.
- Everything under `plugins/` is auto-discovered (no config entry needed).
- Skills/agents/commands install by copy into the global dirs; the plugin
  (V2 API, when stable) can alternatively register them via transform hooks.
- Restart opencode after installing; config loads once at startup.

## 5. How it functions — lifecycle

### 5.1 Session start
AGENTS.md (lean) is already in the system prompt: research-first, see-both-
sides, rewording-pass, memory-tools rules. Nothing heavy loads. The agent
consults the ontology (ONTOLOGY.md, incidents, ANTI-ONTOLOGY) only when a
question touches the system's own operation.

### 5.2 During work — the core loop
Per the agent-engineering model: the agent has a tool menu, signals a request,
our code executes it, results return, repeat. ALOP keeps the menu lean (the
"Select" strategy — surface only the tools/skills needed for this step) and
routes deterministic work to scripts so the model spends turns on composition,
not reconstruction.

Context engineering strategies mapped to mechanisms:
| Strategy | Mechanism in ALOP |
|---|---|
| Right (externalize) | notes files, summaries, chops — memory outside the window |
| Select (retrieve) | skills load on demand; ontology queried on demand |
| Compress | compaction hook → chop + STABLE/CURRENT/REFERENCE checkpoint |
| Isolate | subagents (havruta, grader) with clean windows, short summaries back |

### 5.3 Compaction (exists today, kept)
`experimental.session.compacting` hook: chop the pre-compaction middle band to
disk (mechanical, read-only vs the DB) and replace the compaction prompt with
the three-layer STABLE / CURRENT / REFERENCE checkpoint. Applies to parent and
subagent sessions.

### 5.4 Mistakes → incidents → prevention → eval case
1. Something costs more than it should, or fails.
2. Log in `incidents.md`: what, why, resolution, cost, prevention.
3. Encode prevention: AGENTS.md rule (if global) or skill gotcha (if
   task-specific).
4. Verify the prevention works (run it).
5. Add it as an eval case so it's caught forever.

### 5.5 Skills — the method layer
Each skill is `SKILL.md` (name + description as the router, body ≤500 lines)
with `references/` and `scripts/` for detail and deterministic ops. Initial
set:

| Skill | Description (router) | Body source |
|---|---|---|
| curriculum | 5-session mastery method on any document/problem | SINGLE Curriculum video |
| reword-pass | restate stuck/familiar questions in foreign vocabulary | permutation principle (in AGENTS.md too) |
| incident-log | record a mistake: what/why/resolution/cost/prevention | incidents.md discipline |
| ontology-query | how to consult ONTOLOGY/incidents/ANTI-ONTOLOGY | Palantir model |
| eval-harness | how to run/grade an eval: rubric, gate, baselines | online eval practice |
| chain-of-custody | trace a claim to primary source | Hadith isnad method |

Gotchas sections grow from incidents (Anthropic's highest-signal content).

### 5.6 Agents — the specialists
- `havruta` (subagent): given a position, produces the strongest objections,
  then swaps to argue the attacked side. Maps the curriculum's adversarial
  method onto a fresh-context worker.
- `grader` (subagent): LLM-as-judge for evals. Runs on a different model
  family than the agent under test; never told which model produced the output.

### 5.7 Commands — your entry points
`/curriculum <target>`, `/havruta <position>`, `/eval <target>`,
`/incident <what happened>`, `/checkpoint` (write STABLE/CURRENT/REFERENCE
now), `/ontology <query>`.

### 5.8 Scripts — mechanical executors (token-free)
- `chop-session.py` (exists), `session-cost.sh` (exists)
- `sync.sh` — sync AGENTS.md + ontology copies (live ↔ package ↔ templates)
- `eval-run.sh` — run deterministic gate + sampled judge
- `metrics-pull.sh` — the world-model tracking metrics
- `dialogue-run.sh` — file-based AI dialogue between two disjoint-context
  sessions on a schedule (planned; ships when built)

### 5.9 The eval harness — measurement
Hybrid norm:
- **Deterministic gate (100%):** structural checks on every artifact — does the
  checkpoint have STABLE/CURRENT/REFERENCE headers; did the chop land in the
  right dir; does the summary reference its source transcripts. Free, hard.
- **LLM judge (sampled):** 5 anchored dimensions (1–5, concrete anchors per
  level, "0 = cannot tell") — e.g. fidelity, completeness, grounding, clarity,
  cost-efficiency. Judge from a different family; order randomized; model
  metadata stripped; lowest score justified in one sentence.
- **Calibration set:** ~20–30 artifacts labeled by the user on the same rubric;
  judge agreement ≥75% (Krippendorff ~0.8) before the judge is trusted.
- **Baselines + gate:** store scores; flag regression >0.3 on any dimension.
  Run nightly, not per-change.
- **Targets:** checkpoints, chops, summaries, incident quality, skill gotchas.

## 6. Governance rules

- Scripts and plugin never write to `opencode.db` (read-only).
- `CHANGES.md` and `incidents.md`: append-only, one entry per change/incident.
- Derived artifacts must be rebuildable from canonical alone. If they can't,
  they're caches — fix or delete.
- Every change logged in CHANGES.md; every mistake in incidents.md; prevention
  encoded where it binds.
- Reuse before build: any capability already solved by a vetted ecosystem
  plugin is adopted, not rebuilt.
- Push work off the serial stream whenever any parallel resource can do it;
  the serial stream is the bottleneck resource and is treated as precious.
- The human is the governor, the model is the executor, the ledger is the
  memory. The ontology is only as good as the discipline of using it.

## 7. What exists today

- Plugin `memory-compaction.js` (compaction hook only) — the seed of ALOP.
- `chop-session.py`, `session-cost.sh` — installed under
  `~/.config/opencode/session-tools/`.
- Ontology v1: ONTOLOGY.md (objects/links/actions/governance + self-improvement
  loop), incidents.md (INC-001..003 closed), ANTI-ONTOLOGY.md (failure
  taxonomy, incl. the "learned vocabulary" failure).
- Lean AGENTS.md: research-first, see-both-sides, rewording-pass, memory-tools.
- Config: compaction auto, subagent limits (agents block), model pins.

## 8. Build order

| Phase | Deliverable | Verification |
|---|---|---|
| 0 | Ecosystem audit: opencode-skillful, opencode-workspace, opencode-conductor, opencode-scheduler, opencode-supermemory, opencode-dynamic-context-pruning | reuse-vs-build decision recorded per capability |
| 1 | Skills pack (Agent-Skills standard): the six skills | a skill triggers and changes behavior; gotcha from a real incident |
| 2 | Eval harness: deterministic gate + judge + calibration + baselines | calibration ≥75% agreement; a seeded regression is caught |
| 3 | Plugin v2: extend hooks; evaluate V2 transform/hook API for dispatch-time context injection | hooks verified firing; no regression in compaction path |
| 4 | Agents (havruta, grader) + Commands | havruta flips a position; grader scores a known-good and known-bad case correctly |
| 5 | Ontology v2: fold in method layer, core loop, context strategies, eval governance | ontology reflects the running system |
| 6 | Install unification: install.sh covers every organ; portable copy verified on a second install | clean install from scratch works |

Each phase ships with a CHANGES.md entry and, where relevant, an incidents.md
seeding and an eval case.

## 9. Open questions / research required

- V2 plugin API is beta — decide whether to depend on transforms or stay on
  stable V1 hooks + file installs for now.
- Which ecosystem plugins to adopt (phase 0) before building equivalents.
- Whether the judge model for evals should be a remote cross-family model or a
  local one (cost vs. bias control).
- Cron mechanism for the file-dialogue: `opencode-scheduler` vs raw
  systemd/launchd.

## 10. Revert

Full revert = remove installed plugin file, skills, agents, commands,
session-tools, and the merged config keys; restore AGENTS.md from backup.
The portable copy is never modified by install, so it stays the reference.