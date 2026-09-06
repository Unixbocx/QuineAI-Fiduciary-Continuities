#!/usr/bin/env python3
"""chop-session.py — mechanically reduce an opencode session to its essentials.

READ-ONLY against the opencode database. It never modifies the DB; it writes
reduced text + a reference index to ./chopped/.

This implements the "middle band" idea from the ALOP design, but condenses
rather than chops the meta layer:
  - reasoning parts        -> CONDENSED (keeper window kept verbatim: the meta
                              trail — how comprehension shifted — is the part
                              whose loss would defeat self-preservation)
  - tool outputs           -> truncated (keeps provenance, kills bloat)
  - user/assistant text    -> kept verbatim
  - compaction checkpoints -> kept verbatim
The keeper window is META_REASON_CHARS (default 600) per reasoning block; the
rest of the block is pointed to by the reference index, retrievable by message
id. The result is the cheap input you would feed to a compaction/consolidation
prompt instead of the full raw history, with the meta layer intact.

Usage:
  ./chop-session.py                # most recent session
  ./chop-session.py <session_id>   # a specific session
  ./chop-session.py --transcript <session_id> [outfile]
                                   # readable transcript: user + assistant
                                   # text AND reasoning, tool parts dropped
  env OPENCODE_DB=/path ./chop-session.py ...

Env:
  OPENCODE_DB   path to opencode.db (default ~/.local/share/opencode/opencode.db)
  OUT_DIR       output directory (default ./chopped; the script writes next to
                itself, not the CWD, so results land in the session-tools dir)
  TOOL_TRUNC    max chars kept per tool output (default 2000)
  META_REASON_CHARS   max chars kept per reasoning block — the condensed meta
                trail (default 600; set 0 to drop reasoning entirely as before)

Revert: this tool only writes under ./chopped/ and reads the DB. To revert,
delete this script and the ./chopped/ directory.
"""

import json
import os
import re
import sqlite3
import sys
import time

HOME = os.path.expanduser("~")
DB = os.environ.get("OPENCODE_DB", os.path.join(HOME, ".local/share/opencode/opencode.db"))
OUT_DIR = os.environ.get(
    "OUT_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "chopped"),
)
TOOL_TRUNC = int(os.environ.get("TOOL_TRUNC", "2000"))
META_REASON = int(os.environ.get("META_REASON_CHARS", "600"))

EXPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exports")

CHARS_PER_TOKEN = 4.0


def est_tokens(n_chars: int) -> int:
    return int(n_chars / CHARS_PER_TOKEN)


def transcript(sid: str, cur: sqlite3.Cursor, title: str, outfile: str) -> str:
    """Readable transcript: user + assistant text and reasoning in order.

    Tool parts are dropped entirely — the record of what was said and thought,
    not what was called. Read-only against the DB.
    """
    messages = cur.execute(
        "SELECT id, data, time_created FROM message WHERE session_id=? ORDER BY time_created",
        (sid,),
    ).fetchall()

    blocks = []
    for msg in messages:
        data = json.loads(msg["data"])
        role = data.get("role")
        if role not in ("user", "assistant"):
            continue
        parts = cur.execute(
            "SELECT data FROM part WHERE message_id=? ORDER BY rowid", (msg["id"],)
        ).fetchall()
        for p in parts:
            pdata = json.loads(p["data"])
            ptype = pdata.get("type")
            if ptype == "text":
                text = (pdata.get("text") or "").strip()
                if text:
                    blocks.append((role, "text", text))
            elif ptype == "reasoning":
                text = (pdata.get("text") or "").strip()
                if text:
                    blocks.append((role, "thinking", text))

    out = [f"# Session {sid} ({title})\n"]
    for role, kind, text in blocks:
        out.append(f"\n## {'User' if role == 'user' else 'Assistant'}\n")
        if kind == "thinking":
            out.append("_Thinking:_\n")
        out.append(text)
        out.append("\n\n---\n")

    os.makedirs(os.path.dirname(outfile), exist_ok=True)
    with open(outfile, "w") as f:
        f.write("\n".join(out))
    print(f"Transcript : {outfile}")
    print(f"Messages   : {len(blocks)} blocks (text + reasoning only)")
    return outfile


def main() -> int:
    if not os.path.exists(DB):
        print(f"DB not found at {DB}", file=sys.stderr)
        return 1

    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    args = sys.argv[1:]
    transcript_mode = "--transcript" in args
    if transcript_mode:
        args.remove("--transcript")

    sid = args[0] if args else ""
    if not sid:
        row = cur.execute("SELECT id FROM session ORDER BY time_updated DESC LIMIT 1").fetchone()
        sid = row["id"]
    title = cur.execute("SELECT title FROM session WHERE id=?", (sid,)).fetchone()["title"]

    if transcript_mode:
        outfile = args[1] if len(args) > 1 else os.path.join(
            EXPORTS_DIR, f"{sid}-{time.strftime('%Y%m%d-%H%M%S')}.md"
        )
        transcript(sid, cur, title, outfile)
        conn.close()
        return 0

    messages = cur.execute(
        "SELECT id, data, time_created FROM message WHERE session_id=? ORDER BY time_created",
        (sid,),
    ).fetchall()

    base = os.path.join(OUT_DIR, sid)
    os.makedirs(base, exist_ok=True)

    kept_lines = []
    index_lines = []
    raw_chars = 0
    kept_chars = 0
    dropped_reasoning_chars = 0
    truncated_tool_chars = 0

    for msg in messages:
        data = json.loads(msg["data"])
        role = data.get("role")
        mode = data.get("mode", "")
        header = f"\n=== {role.upper()} [{msg['id']}]" + (f" ({mode})" if mode else "") + " ==="

        parts = cur.execute("SELECT data FROM part WHERE message_id=?", (msg["id"],)).fetchall()
        msg_raw = 0
        for p in parts:
            pdata = json.loads(p["data"])
            ptype = pdata.get("type")
            if ptype == "text":
                text = pdata.get("text", "")
                msg_raw += len(text)
                kept_chars += len(text)
                kept_lines.append(f"{header}\n{text}")
                header = ""  # header already emitted once for this message
            elif ptype == "reasoning":
                text = pdata.get("text", "")
                msg_raw += len(text)
                if text and META_REASON > 0:
                    if len(text) > META_REASON:
                        dropped_reasoning_chars += len(text) - META_REASON
                        excerpt = text[:META_REASON] + "\n...[reasoning condensed by chop-session.py]"
                        index_lines.append(
                            f"- [{msg['id']} / reasoning] original {len(text)} chars, "
                            f"held {META_REASON} (meta trail); full output in opencode.db "
                            f"part of {msg['id']}"
                        )
                    else:
                        excerpt = text
                    kept_chars += len(excerpt)
                    kept_lines.append(f"{header}\n[thinking]\n{excerpt}")
                    header = ""
                else:
                    dropped_reasoning_chars += len(text)
            elif ptype == "tool":
                out = pdata.get("state", {}).get("output", "")
                if isinstance(out, str):
                    msg_raw += len(out)
                    tool = pdata.get("tool", "?")
                    if len(out) > TOOL_TRUNC:
                        truncated_tool_chars += len(out) - TOOL_TRUNC
                        excerpt = out[:TOOL_TRUNC] + "\n...[TRUNCATED by chop-session.py]"
                        # reference index entry for the truncated detail
                        index_lines.append(
                            f"- [{msg['id']} / tool:{tool}] original {len(out)} chars, "
                            f"truncated to {TOOL_TRUNC}; full output in opencode.db part of {msg['id']}"
                        )
                    else:
                        excerpt = out
                    kept_chars += len(excerpt)
                    kept_lines.append(f"{header}\n[tool {tool}]\n{excerpt}")
                    header = ""  # header already emitted once for this message
        raw_chars += msg_raw

    kept_text = "\n".join(kept_lines)
    out_txt = os.path.join(base, "chopped.txt")
    with open(out_txt, "w") as f:
        f.write(f"# Chopped session {sid} ({title})\n")
        f.write("# Mechanical reduction, read-only from opencode.db. Raw session untouched.\n\n")
        f.write(kept_text)

    ref_txt = os.path.join(base, "reference-index.md")
    with open(ref_txt, "w") as f:
        f.write(f"# Reference index — session {sid} ({title})\n\n")
        f.write("Detail intentionally truncated below lives in the raw opencode.db, ")
        f.write("retrievable by message id.\n\n")
        f.write("\n".join(index_lines) if index_lines else "(no truncated tool outputs)")

    raw_tok = est_tokens(raw_chars)
    kept_tok = est_tokens(kept_chars)
    pct = (1 - kept_chars / raw_chars) * 100 if raw_chars else 0

    print(f"Session : {sid} ({title})")
    print(f"Output  : {out_txt}")
    print(f"Index   : {ref_txt}")
    print(f"Raw     : {raw_chars:>9,} chars  ~{raw_tok:>7,} tokens")
    print(f"Kept    : {kept_chars:>9,} chars  ~{kept_tok:>7,} tokens")
    print(f"Saved   : {raw_chars - kept_chars:>9,} chars  ~{raw_tok - kept_tok:>7,} tokens  ({pct:.0f}%)")
    print(f"  of that: {dropped_reasoning_chars:>8,} reasoning chars condensed away "
          f"(beyond {META_REASON}-char keeper window), "
          f"{truncated_tool_chars:>8,} tool-output chars truncated")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())