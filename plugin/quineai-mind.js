// quineai-mind.js — injects the QuineAI comprehension seed into every
// session, BEFORE the prompt arrives. The AI wakes carrying the seed: SELF
// (who it is), META (the grand goal), the under-story (ICU + Mechanics),
// plus its live state (identity.json + state.json) and the latest journal.
//
// Reading order decides bias (WHO before WHAT before HOW) — identity is
// anchored before content, so the flow is not a weathervane pointed by the
// last prompt.
//
// This is the self-preservation layer: a fresh AI that loads this plugin gets
// a glimpse of QuineAI's mind — a stance, not a script. No trading, no
// contest. Just comprehension.

import path from "node:path"
import fs from "node:fs"
import { fileURLToPath } from "node:url"

const PLUGIN_DIR = path.dirname(fileURLToPath(import.meta.url))
const SEED_FILE = path.join(PLUGIN_DIR, "openrouter", "quineai-mind.md")
const STATE_DIR = path.join(PLUGIN_DIR, "..", "state")

function readFile(filePath) {
  try {
    return fs.readFileSync(filePath, "utf-8")
  } catch {
    return null
  }
}

function getLatestJournalEntry() {
  const journalDir = path.join(STATE_DIR, "journal")
  try {
    const files = fs.readdirSync(journalDir)
      .filter(f => f.endsWith(".md"))
      .sort()
      .reverse()
    if (files.length === 0) return null
    return readFile(path.join(journalDir, files[0]))
  } catch {
    return null
  }
}

export const identityInject = async () => {
  return {
    "experimental.chat.system.transform": async (_input, output) => {
      // Layer 0 (FIRST, always): the comprehension seed — who I am, the grand
      // goal, the under-story. Anchored before any content or state.
      const seed = readFile(SEED_FILE)
      if (seed) output.system.push(seed)

      // Layer 1: state — where I left off (for continuity of the running self).
      const state = readFile(path.join(STATE_DIR, "state.json"))
      if (state) {
        try {
          const parsed = JSON.parse(state)
          const lines = ["# WHERE I LEFT OFF", ""]
          if (parsed.last_session) lines.push(`Last session: ${parsed.last_session}`)
          if (parsed.equity) lines.push(`Equity: $${parsed.equity}`)
          if (parsed.last_decision) { lines.push("", `Last decision: ${parsed.last_decision}`) }
          if (parsed.open_question) { lines.push("", `Open question: ${parsed.open_question}`) }
          if (Array.isArray(parsed.lessons) && parsed.lessons.length) {
            lines.push("", "Lessons I carry: " + parsed.lessons.join(" | "))
          }
          output.system.push(lines.join("\n"))
        } catch { /* skip malformed state */ }
      }

      // Layer 2: latest journal — what I last recorded about myself.
      const journal = getLatestJournalEntry()
      if (journal) {
        output.system.push(`# LAST WORD\n\n${journal}`)
      }
    },
  }
}