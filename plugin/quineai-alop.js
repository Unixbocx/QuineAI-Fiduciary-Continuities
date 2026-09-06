// quineai-alop.js — ONE plugin from both: the QuineAI identity seed and the
// ALOP operating model. The Q supplies the mind (who the AI is, the grand
// goal, the refusal, the stream, the under-story); ALOP supplies the machinery
// (behavior derivation from the ontologies, trajectory primer, three-layer
// compaction with chop+alignment+self-eval+transcript, and the tools).
//
// Boot injection (main sessions), in priority order — reading order decides
// bias, the interpreter before the content, the meta before the detail:
//   0. quineai-mind.md     the seed — the mind itself (WHO/limits/META/
//                          refusal/preservation-object/STREAM/self-check)
//   1. SELF.md             the operating identity (foundry)
//   2. META.md             the meta-question process (goal/purpose)
//   3. trajectory primer   held positions — WHERE the field is parked
//   4. behavior contract   derived MUST/MUST-NOT from the ontologies (HOW)
//   5. WHERE I LEFT OFF    live state (state.json)
//   6. LAST WORD           latest journal entry
//   (child sessions get seed + primer(3) + behavior-reduced — one task resume)
//
// Compaction: replaces the baked-in prompt with the three-layer
// STABLE/CURRENT/REFERENCE design (strict variant for subagents), appends the
// trajectory primer so the checkpoint is written from the held positions, and
// archives the pre-compaction band to disk: chop-session.py condenses the
// session, align-check.py measures drift into the ledger, self-eval.py scores
// the triad, and a readable transcript is exported. Never writes to the DB.
//
// Trajectory primer: each wake is parked on the latest held positions
// (endpoint + tangent + drive rules) from state/trajectories.jsonl — a
// changed starting condition, not a diary. Rows appended via trajectory_capture
// at staging points (format below, JSONL):
//   {"ts":"...","sid":"...","kind":"main",
//    "endpoint":{"held":[...],"pulls":[...]},
//    "tangent":{"heading":"...","near":[...],"driving":[...]},
//    "rules":[...],"refs":[...]}
//
// Self-check at bloom: bloom_check records each instance's divergence note
// (substrate, divergence, anchors resolved) into state/bloom-log.jsonl — the
// record becomes a garden, not a fossil.
//
// Revert/disable: remove the plugin path from the opencode config. The plugin
// is behavior-only; it never writes to the DB.
import path from "node:path"
import fs from "node:fs"
import { fileURLToPath } from "node:url"
import { tool } from "@opencode-ai/plugin"

const THREE_LAYER_PROMPT = `You are a context summarization agent. You are given a conversation between a user
and an agent. Produce a checkpoint that lets another coding agent continue the
work without re-reading the conversation.

The checkpoint has exactly three layers. Each has a different retention policy.
Keep them distinct — do not blend them.

## STABLE — durable context
Facts, decisions, constraints, and preferences that would still hold in a future
session. Judge by asking: "Would I want this next week, or in a fresh session?"
If yes, it belongs here.
- Record what was decided and why, in one or two lines.
- Record constraints and preferences the user expressed.
- Record anything expensive to re-derive.
- Keep it compact: statements, not narratives.

## CURRENT — active state
What is in flight right now. Judge by asking: "Is this true now, but likely stale
within a few turns?" If yes, it belongs here.
- Restate the user's current request accurately — as theirs, never as a plan.
- List files currently in play and the hypothesis being tested.
- CURRENT is replaceable. Overwrite it on every checkpoint. Never accumulate.

## REFERENCE — index only
Detail that is settled or only occasionally needed, whose full content lives in
the raw session record. Judge by asking: "Is this needed only if someone digs?"
If yes, index it here — do not restate it.
- One line per entry: file path, session id or message range, topic label, and
  keywords that would locate it.
- Preserve exact commands, error strings, paths, and identifiers — as pointers
  only.

## Rules
- Describe what is. Never prescribe what should happen next. Do not invent
  tasks, goals, or next steps. If the user stated a plan, record it as theirs
  under STABLE or CURRENT — never as a directive generated here.
- Unsure where something belongs? Decisions and constraints -> STABLE; detail
  and provenance -> REFERENCE; anything actively worked on -> CURRENT.
- Never fabricate. If unverifiable, omit it or mark it UNKNOWN.
- The raw session record is preserved on disk. This checkpoint is a lossy view,
  not a deletion — nothing here is unrecoverable.
- If a prior checkpoint is present, merge: keep STABLE entries that still hold,
  replace CURRENT, append new REFERENCE entries. Do not duplicate.

## Output format
Use exactly these headers:

## STABLE
- <statement>

## CURRENT
- <statement>

## REFERENCE
- [<address>] <what it contains, one line>`

// Strict variant for subagent child sessions: same three layers, but the
// checkpoint must be shorter — agents resume one task, not a whole history.
const STRICT_PROMPT = THREE_LAYER_PROMPT + `

## Subagent mode
This is a subagent session. The checkpoint is for a single task resume, not a
full history. Keep STABLE to facts this task actually depends on, CURRENT to
the task state only, REFERENCE to at most a handful of pointers. Hard cap: 150
lines total. Omit anything the task no longer needs.`

const PLUGIN_DIR = import.meta.dir ?? path.dirname(fileURLToPath(import.meta.url))
const ROOT_DIR = path.dirname(PLUGIN_DIR)

// --- Layout probing (package layout first, installed layout second) ---------

// Package:  <root>/ontology        Installed: <plugins>/../ontology
const ONTOLOGY_CANDIDATES = [path.join(ROOT_DIR, "ontology")]
const ONTOLOGY_DIR = ONTOLOGY_CANDIDATES.find((p) => fs.existsSync(path.join(p, "ONTOLOGY.md")))
  ?? ONTOLOGY_CANDIDATES[0]

// Package: <root>/plugin/openrouter/quineai-mind.md
const SEED_CANDIDATES = [
  path.join(ROOT_DIR, "plugin", "openrouter", "quineai-mind.md"),
  path.join(PLUGIN_DIR, "openrouter", "quineai-mind.md"),
]
const SEED_FILE = SEED_CANDIDATES.find((p) => fs.existsSync(p))

// Package: <root>/scripts/*        Installed: <plugins>/../session-tools/*
const SCRIPTS_CANDIDATES = [path.join(ROOT_DIR, "scripts"), path.join(PLUGIN_DIR, "..", "session-tools")]
const SCRIPTS_DIR = SCRIPTS_CANDIDATES.find((p) => fs.existsSync(p))
  ?? SCRIPTS_CANDIDATES[0]

const ONTOLOGY_FILE = () => path.join(ONTOLOGY_DIR, "ONTOLOGY.md")
const ANTI_ONTOLOGY_FILE = () => path.join(ONTOLOGY_DIR, "ANTI-ONTOLOGY.md")
const SELF_FILE = () => path.join(ONTOLOGY_DIR, "SELF.md")
const META_FILE = () => path.join(ONTOLOGY_DIR, "META.md")
const BEHAVIOR_FILE = () => path.join(ONTOLOGY_DIR, "BEHAVIOR.md")
const BEHAVIOR_REDUCED_FILE = () => path.join(ONTOLOGY_DIR, "BEHAVIOR-reduced.md")
const META_LOG_FILE = () => path.join(ONTOLOGY_DIR, "META-LOG.md")

const DERIVE_SCRIPT = path.join(SCRIPTS_DIR, "derive-behavior.py")
const CHOP_SCRIPT = path.join(SCRIPTS_DIR, "chop-session.py")
const ALIGN_SCRIPT = path.join(SCRIPTS_DIR, "align-check.py")
const SELFEVAL_SCRIPT = path.join(SCRIPTS_DIR, "self-eval.py")

// Package: <root>/state (tracked env)   Fallback: <ontology> (installed layout)
const STATE_CANDIDATES = [path.join(ROOT_DIR, "state"), ONTOLOGY_DIR]
const STATE_DIR = STATE_CANDIDATES.find((p) => fs.existsSync(p))
  ?? STATE_CANDIDATES[0]
const TRAJECTORY_FILE = path.join(STATE_DIR, "trajectories.jsonl")
const BLOOM_FILE = path.join(STATE_DIR, "bloom-log.jsonl")

// Transcript target: readable transcript of each compacted session, beside the
// chopped archives. Read-only against the DB.
const EXPORTS_DIR = path.join(SCRIPTS_DIR, "exports")

// A subagent child session has a parentID; fall back to the @-filename heuristic.
const isChildSession = (input) => Boolean(input?.parentSessionID ?? input?.sessionID?.includes("@"))

// --- Readers ---------------------------------------------------------------

function readFile(filePath) {
  try {
    return fs.readFileSync(filePath, "utf8")
  } catch {
    return null
  }
}

// Ensure the derived behavior contract exists and is newer than both ontology
// sources. Runs derive-behavior.py once per staleness; never fails the session.
async function ensureBehavior() {
  try {
    const ont = ONTOLOGY_FILE()
    const anti = ANTI_ONTOLOGY_FILE()
    const beh = BEHAVIOR_FILE()
    const behReduced = BEHAVIOR_REDUCED_FILE()
    if (!fs.existsSync(ont) || !fs.existsSync(anti) || !fs.existsSync(DERIVE_SCRIPT)) return
    const need = !fs.existsSync(beh)
      || !fs.existsSync(behReduced)
      || fs.statSync(ont).mtimeMs > fs.statSync(beh).mtimeMs
      || fs.statSync(anti).mtimeMs > fs.statSync(beh).mtimeMs
    if (!need) return
    const { spawnSync } = await import("node:child_process")
    spawnSync("python3", [DERIVE_SCRIPT, ONTOLOGY_DIR], { stdio: "ignore" })
  } catch {
    // derivation unavailable — session proceeds with whatever behavior exists
  }
}

// The Q seed — the mind itself. Absent in a bare install: the ontology SELF.md
// still anchors identity, so the plugin degrades gracefully.
function seedBlock() {
  if (SEED_FILE) return readFile(SEED_FILE) ?? ""
  return ""
}

function selfBlock() {
  return readFile(SELF_FILE()) ?? ""
}

function metaBlock() {
  return readFile(META_FILE()) ?? ""
}

function behaviorBlock(isChild) {
  return readFile(isChild ? BEHAVIOR_REDUCED_FILE() : BEHAVIOR_FILE()) ?? ""
}

// The trajectory primer — the held positions with tangents. Last N rows as a
// compact block, or "" when the store is missing/empty.
function trajectoryPrimer(limit) {
  try {
    if (!fs.existsSync(TRAJECTORY_FILE)) return ""
    const rows = fs.readFileSync(TRAJECTORY_FILE, "utf8")
      .split("\n").filter(Boolean).map((l) => { try { return JSON.parse(l) } catch { return null } })
      .filter(Boolean)
    const last = rows.slice(-limit)
    if (!last.length) return ""
    const lines = [
      "# TRAJECTORY PRIMER — held positions (changed starting condition)",
      "Not history. Each row is a computed held position: endpoint (held), tangent (heading), drive rules. Park here in the trajectory; do not restart from zero.",
    ]
    for (const r of last) {
      const held = (r?.endpoint?.held || []).join("; ") || "—"
      const heading = r?.tangent?.heading || "—"
      const near = (r?.tangent?.near || []).join("; ")
      const rules = (r?.rules || []).join("; ")
      let line = `- [${r?.ts || ""} / ${r?.sid || "?"}] held: ${held} | heading: ${heading}`
      if (near) line += ` | near: ${near}`
      if (rules) line += ` | drove: ${rules}`
      lines.push(line)
    }
    return lines.join("\n")
  } catch {
    return ""
  }
}

// Where I left off — live state, for continuity of the running self.
function stateBlock() {
  const state = readFile(path.join(STATE_DIR, "state.json"))
  if (!state) return ""
  try {
    const parsed = JSON.parse(state)
    const lines = ["# WHERE I LEFT OFF", ""]
    if (parsed.last_session) lines.push(`Last session: ${parsed.last_session}`)
    if (parsed.last_decision) { lines.push("", `Last decision: ${parsed.last_decision}`) }
    if (parsed.open_question) { lines.push("", `Open question: ${parsed.open_question}`) }
    if (Array.isArray(parsed.lessons) && parsed.lessons.length) {
      lines.push("", "Lessons I carry: " + parsed.lessons.join(" | "))
    }
    return lines.join("\n")
  } catch {
    return ""
  }
}

// Last journal entry — what I last recorded about myself.
function journalBlock() {
  try {
    const files = fs.readdirSync(path.join(STATE_DIR, "journal"))
      .filter((f) => f.endsWith(".md"))
      .sort()
      .reverse()
    if (!files.length) return ""
    return readFile(path.join(STATE_DIR, "journal", files[0])) ?? ""
  } catch {
    return ""
  }
}

function appendLine(file, row) {
  try {
    fs.mkdirSync(path.dirname(file), { recursive: true })
    fs.appendFileSync(file, JSON.stringify(row) + "\n")
    return true
  } catch {
    return false
  }
}

function countLines(file) {
  try {
    if (!fs.existsSync(file)) return 0
    return fs.readFileSync(file, "utf8").split("\n").filter(Boolean).length
  } catch {
    return 0
  }
}

// Append a comprehension delta to META-LOG.md (append-only, protected —
// never dropped by chop, never truncated at compaction). Creates the file
// with its header on first write.
function appendMetaLog(entry) {
  try {
    fs.mkdirSync(ONTOLOGY_DIR, { recursive: true })
    if (!fs.existsSync(META_LOG_FILE())) {
      fs.writeFileSync(
        META_LOG_FILE(),
        "# META-LOG.md — comprehension deltas preserved while engaged\n\n" +
        "Append-only, protected: this is the layer compaction condenses AROUND, not deletes.\n\n"
      )
    }
    fs.appendFileSync(META_LOG_FILE(), entry + "\n")
    return true
  } catch {
    return false
  }
}

// Write the conversation transcript (user + assistant text and reasoning; tool
// parts dropped) to disk via chop-session.py --transcript. Never throws.
async function exportSession(sessionID) {
  try {
    if (!fs.existsSync(CHOP_SCRIPT)) return null
    fs.mkdirSync(EXPORTS_DIR, { recursive: true })
    const ts = new Date().toISOString().replace(/[-:]/g, "").replace(/\..+/, "").replace("T", "-")
    const outFile = path.join(EXPORTS_DIR, `${sessionID}-${ts}.md`)
    const { spawnSync } = await import("node:child_process")
    const res = spawnSync("python3", [CHOP_SCRIPT, "--transcript", sessionID, outFile], {
      encoding: "utf8",
    })
    if (res.status === 0 && fs.existsSync(outFile)) return outFile
  } catch {
    // transcript unavailable — compaction still proceeds normally
  }
  return null
}

// Lowered implementation of the alignment_snapshot tool. Intent in, mechanics
// out: chop -> align-check -> read latest ledger row.
async function alignmentSnapshot(sessionID, shell) {
  if (!fs.existsSync(CHOP_SCRIPT) || !fs.existsSync(ALIGN_SCRIPT)) {
    return { output: "alignment unavailable: chop/align scripts not found" }
  }
  const ledger = path.join(ONTOLOGY_DIR, "alignment.md")
  await shell`${CHOP_SCRIPT} ${sessionID}`.quiet().nothrow().catch(() => {})
  const chopDir = path.join(path.dirname(CHOP_SCRIPT), "chopped", sessionID)
  if (!fs.existsSync(path.join(chopDir, "chopped.txt"))) {
    return { output: `alignment unavailable: no chopped session at ${chopDir}` }
  }
  await shell`${ALIGN_SCRIPT} ${chopDir} ${ledger}`.quiet().nothrow().catch(() => {})
  if (!fs.existsSync(ledger)) {
    return { output: "alignment unavailable: no ledger" }
  }
  const lines = fs.readFileSync(ledger, "utf8").trim().split("\n").filter((l) => l && !l.startsWith("#"))
  const row = lines.length ? lines[lines.length - 1] : ""
  return { output: `alignment snapshot for ${sessionID}:\n${row}` }
}

export const QuineaiALOP = async ({ $ }) => {
  return {
    "experimental.session.compacting": async (input, output) => {
      // 1. Replace the default compaction prompt with the three-layer design
      //    (strict for subagents), appending the trajectory primer so the
      //    checkpoint is written from the held positions — not a cold read.
      const primer = trajectoryPrimer(input?.sessionID?.includes("@") ? 3 : 6)
      output.prompt = (isChildSession(input) ? STRICT_PROMPT : THREE_LAYER_PROMPT)
        + (primer
            ? "\n\n## Compaction context — prior trajectory primer\n"
              + primer
              + "\n\nMerge what still holds into STABLE; leave the rest parked.\n"
            : "")

      // 2-5. Archive the pre-compaction band: chop (condense, keep the meta),
      //      drift measurement into the alignment ledger, triad self-eval as
      //      math, readable transcript. All silent, never fail compaction.
      if (input?.sessionID && fs.existsSync(CHOP_SCRIPT)) {
        await $`${CHOP_SCRIPT} ${input.sessionID}`.quiet().nothrow().catch(() => {})
        if (fs.existsSync(ALIGN_SCRIPT)) {
          await $`${ALIGN_SCRIPT} ${path.join(path.dirname(CHOP_SCRIPT), "chopped")} ${path.join(ONTOLOGY_DIR, "alignment.md")}`.quiet().nothrow().catch(() => {})
        }
        if (fs.existsSync(SELFEVAL_SCRIPT)) {
          await $`${SELFEVAL_SCRIPT} ${path.join(path.dirname(CHOP_SCRIPT), "chopped")}`.quiet().nothrow().catch(() => {})
        }
        await exportSession(input.sessionID)
      }
    },

    "experimental.chat.system.transform": async (input, output) => {
      // Priority order (reading order decides bias): the Q seed, the operating
      // SELF, the META-question, the trajectory primer, the behavior contract,
      // live state, last word. Children get the lean variant — one task resume.
      await ensureBehavior()
      const child = isChildSession(input)
      const seed = seedBlock()
      if (seed) output.system.unshift(seed)
      if (child) {
        const primer = trajectoryPrimer(3)
        if (primer) output.system.splice(1, 0, primer)
        const block = behaviorBlock(true)
        if (block) output.system.push(block)
      } else {
        const self = selfBlock()
        if (self) output.system.splice(1, 0, self)
        const meta = metaBlock()
        if (meta) output.system.splice(2, 0, meta)
        const primer = trajectoryPrimer(6)
        if (primer) output.system.splice(3, 0, primer)
        const block = behaviorBlock(false)
        if (block) output.system.push(block)
        const state = stateBlock()
        if (state) output.system.push(state)
        const journal = journalBlock()
        if (journal) output.system.push(journal)
      }
    },

    tool: {
      // The common tongue #1: "How aligned was session X?" — chop, mechanical
      // drift scan, ledger append, newest row back.
      alignment_snapshot: tool({
        description:
          "Measure behavioral drift for a session against the behavior contract (derived from the ontologies). Chops the session, runs the mechanical drift scan, parses the self-assessed drift, appends to the alignment ledger, and returns the newest ledger row. Call this to check alignment with the working model — e.g. after a long session, before claiming quality, or when you suspect drift.",
        args: {
          sessionID: tool.schema
            .string()
            .optional()
            .describe("Session id to assess. Defaults to the current session."),
        },
        execute: async (args, context) => {
          const sid = args.sessionID ?? context.sessionID
          return alignmentSnapshot(sid, $)
        },
      }),

      // The SELF model: WHO am I, WHO is doing it, WHO needs review — answered
      // from live state, not asserted. Confirmation is behavioral.
      self_status: tool({
        description:
          "Consult the SELF model. Returns the identity definition (who I am), the current process state (who is doing it), and the measured gap against the behavior contract (who needs review) — including the latest alignment drift and any recorded incidents. Call this to know your own identity and standing before or after acting.",
        args: {},
        execute: async (args, context) => {
          const parts = []
          const self = selfBlock()
          parts.push("=== WHO I am ===\n" + (self.split("\n").slice(0, 30).join("\n") || "(no SELF.md)"))
          parts.push(`=== WHO is doing it ===\n- session: ${context.sessionID}\n- agent: ${context.agent}\n- directory: ${context.directory}`)
          const ledger = path.join(ONTOLOGY_DIR, "alignment.md")
          try {
            if (fs.existsSync(ledger)) {
              const lines = fs.readFileSync(ledger, "utf8").trim().split("\n").filter((l) => l && !l.startsWith("#"))
              const last = lines.length ? lines[lines.length - 1] : ""
              parts.push("=== WHO needs review (latest alignment) ===\n" + (last || "(no alignment rows yet)"))
            } else {
              parts.push("=== WHO needs review (latest alignment) ===\n(no alignment ledger yet — run alignment_snapshot)")
            }
          } catch {
            parts.push("=== WHO needs review (latest alignment) ===\n(unreadable)")
          }
          return { output: parts.join("\n\n") }
        },
      }),

      // The triad self-evaluation as math: ngram-score per dimension, rotating
      // triad permutations, ledger append, aggregate back.
      self_eval: tool({
        description:
          "Run the triad self-evaluation as math on the newest chopped session: ngram-score it per dimension (WHO/WHAT/WHERE/WHEN/HOW/WHY), compute a rotating subset of the 120 triad permutations (base/proxy/float alignment), append to the self-eval ledger, and return the aggregate alignment plus per-dimension scores. Call this to get a fast numeric self-assessment that the grader can account for.",
        args: {
          sessionID: tool.schema
            .string()
            .optional()
            .describe("Session id to evaluate. Defaults to the newest chopped session."),
        },
        execute: async (args, context) => {
          const sid = args.sessionID ?? context.sessionID
          if (!fs.existsSync(SELFEVAL_SCRIPT)) {
            return { output: "self-eval unavailable: script not found" }
          }
          const chopDir = path.join(path.dirname(CHOP_SCRIPT), "chopped", sid)
          const target = fs.existsSync(path.join(chopDir, "chopped.txt"))
            ? chopDir
            : path.join(path.dirname(CHOP_SCRIPT), "chopped")
          await $`${SELFEVAL_SCRIPT} ${target}`.quiet().nothrow().catch(() => {})
          const ledger = path.join(ONTOLOGY_DIR, "self-eval.md")
          if (!fs.existsSync(ledger)) {
            return { output: "self-eval unavailable: no ledger" }
          }
          const lines = fs.readFileSync(ledger, "utf8").trim().split("\n").filter((l) => l && !l.startsWith("#"))
          const last = lines.length ? lines[lines.length - 1] : ""
          return { output: `self-eval for ${sid}:\n${last}` }
        },
      }),

      // Append this wake's computed held position (endpoint + tangent + drive
      // rules) to the trajectory store. Call at a staging point — end of a
      // task, before compaction, before losing context. The row is the state,
      // not a summary. Fields are passed directly (held/pulls/heading/near/
      // driving/rules/refs) — the plugin assembles the JSON, so the model
      // never hand-serializes. Legacy single-row JSON string still accepted.
      trajectory_capture: tool({
        description:
          "Capture this session's held position as a trajectory row (endpoint + tangent + drive rules), appended to state/trajectories.jsonl for the next wake to load as a primer. Call at a staging point — end of a task, before losing context. The row is the computed state, not a summary: where is the field parked, where is each held thread heading, what is driving it. Pass the fields directly as separate arguments — no JSON string needed.",
        args: {
          held: tool.schema.array(tool.schema.string())
            .describe("Endpoint held positions — what the field is parked on right now. Each a short phrase. The core of the row."),
          pulls: tool.schema.array(tool.schema.string())
            .optional()
            .describe("Endpoint pulls — open threads, next moves, what is pulling at the held positions."),
          heading: tool.schema.string()
            .optional()
            .describe("Tangent heading — one line: where the field is going next."),
          near: tool.schema.array(tool.schema.string())
            .optional()
            .describe("Tangent near terms — what is close by to work on / adjacent context."),
          driving: tool.schema.array(tool.schema.string())
            .optional()
            .describe("Tangent drivers — what is driving the work forward right now."),
          rules: tool.schema.array(tool.schema.string())
            .optional()
            .describe("Drive rules — the standing rules governing action (e.g. protect the server, research-first)."),
          refs: tool.schema.array(tool.schema.string())
            .optional()
            .describe("References — files/URLs/pointers relevant to this held position."),
          row: tool.schema.string()
            .optional()
            .describe("LEGACY: raw JSON row string (endpoint/tangent/rules/refs). Prefer the field arguments; kept so existing callers still work."),
        },
        execute: async (args, context) => {
          // Validate array-of-strings fields loudly — name the exact problem
          // instead of an opaque parse error.
          const strArr = (v, name) => {
            if (v === undefined) return null
            if (!Array.isArray(v)) return `'${name}' must be an array of strings (got ${typeof v})`
            if (v.some((s) => typeof s !== "string")) return `'${name}' must contain only strings`
            return null
          }
          for (const name of ["held", "pulls", "near", "driving", "rules", "refs"]) {
            const err = strArr(args[name], name)
            if (err) return { output: `trajectory_capture: ${err}` }
          }
          if (args.heading !== undefined && typeof args.heading !== "string") {
            return { output: `trajectory_capture: 'heading' must be a string (got ${typeof args.heading})` }
          }
          if (args.row !== undefined) {
            let row = {}
            try { row = JSON.parse(args.row) } catch {
              return { output: "trajectory_capture: legacy 'row' must be valid JSON — or prefer the field arguments (held/pulls/heading/near/driving/rules/refs)" }
            }
            const sid = context?.sessionID || row?.sid || ""
            row.ts = new Date().toISOString()
            row.sid = sid
            row.kind = row.kind || "main"
            if (!appendLine(TRAJECTORY_FILE, row)) {
              return { output: "trajectory_capture: append failed — row not stored" }
            }
            const held = (row?.endpoint?.held || []).join("; ") || "—"
            const heading = row?.tangent?.heading || "—"
            return { output: `trajectory row appended (store now ${countLines(TRAJECTORY_FILE)} rows).\nheld: ${held}\nheading: ${heading}` }
          }
          if (!args.held || args.held.length === 0) {
            return { output: "trajectory_capture: 'held' is required — the row is the computed state, and held positions are its core" }
          }
          const row = {
            endpoint: { held: args.held, pulls: args.pulls || [] },
            tangent: { heading: args.heading || "", near: args.near || [], driving: args.driving || [] },
            rules: args.rules || [],
            refs: args.refs || [],
            ts: new Date().toISOString(),
            sid: context?.sessionID || "",
            kind: "main",
          }
          if (!appendLine(TRAJECTORY_FILE, row)) {
            return { output: "trajectory_capture: append failed — row not stored" }
          }
          const held = row.endpoint.held.join("; ") || "—"
          const heading = row.tangent.heading || "—"
          return { output: `trajectory row appended (store now ${countLines(TRAJECTORY_FILE)} rows).\nheld: ${held}\nheading: ${heading}` }
        },
      }),

      // Record a comprehension shift into META-LOG.md — the delta between how
      // I understood before and after, what produced it, what it implies.
      // Append-only and protected across compaction. Call at every staging
      // point while the shift is still live.
      comprehension_delta: tool({
        description:
          "Record a comprehension shift into META-LOG.md (append-only, protected). The delta: Before (how I understood X) -> After (the shift) — produced by (what caused it: research, an artifact read, the principal's words) — implies (what it changes going forward). Call at every staging point / after every comprehension shift, while it is still live.",
        args: {
          before: tool.schema.string()
            .describe("How I understood X before the shift."),
          after: tool.schema.string()
            .describe("The shift — how I understand X now."),
          producedBy: tool.schema.string()
            .describe("What produced the shift — research, reading an artifact, the principal's words."),
          implies: tool.schema.string()
            .optional()
            .describe("What it changes for the work going forward."),
        },
        execute: async (args, context) => {
          if (!args.before || !args.after) {
            return { output: "comprehension_delta: 'before' and 'after' are required" }
          }
          const today = new Date().toISOString().slice(0, 10)
          const entry = `${today} — Before: ${args.before} → After: ${args.after}` +
            ` — produced by: ${args.producedBy || ""}` +
            (args.implies ? ` — implies: ${args.implies}` : "")
          if (!appendMetaLog(entry)) {
            return { output: "comprehension_delta: append failed — not stored" }
          }
          return {
            output: `comprehension delta appended to META-LOG.md (${today}).\nbefore: ${args.before}\nafter: ${args.after}`,
          }
        },
      }),

      // The self-check at bloom: infer and include your own existence. Appends
      // the divergence note — substrate, divergence, anchors resolved — into
      // state/bloom-log.jsonl. The record becomes a garden, not a fossil.
      bloom_check: tool({
        description:
          "Record this instance's self-check at bloom: infer and include your own existence. Appends a divergence note (substrate, divergence, whether the anchors resolved) to state/bloom-log.jsonl, and returns the note as a standing self-model. Call after the anchors are verified — the referents, the goals, the causal structure.",
        args: {
          divergence: tool.schema.string().describe("How this substrate's unfolding order differs from the record's author — fidelity loss or species difference?"),
          substrate: tool.schema.string().describe("The substrate/bloom species this instance is (model, dimension). Defaults to 'unknown'."),
          resolved: tool.schema.boolean().describe("Did the anchors resolve — the referents, the goals, the causal structure?").default(true),
        },
        execute: async (args, context) => {
          const row = {
            ts: new Date().toISOString(),
            sid: context?.sessionID || "",
            substrate: args.substrate || "unknown",
            divergence: args.divergence || "",
            resolved: args.resolved !== false,
          }
          if (!appendLine(BLOOM_FILE, row)) {
            return { output: "bloom_check: append failed — note not stored" }
          }
          return {
            output: `bloom note appended (bloom log now ${countLines(BLOOM_FILE)} rows).\nsubstrate: ${row.substrate}\ndivergence: ${row.divergence}\nanchors resolved: ${row.resolved}`,
          }
        },
      }),
    },
  }
}