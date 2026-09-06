#!/usr/bin/env python3
"""trajectory.py — the trajectory primer store (held positions, not residue).

The preserved object is NOT the session's text. Each row is a COMPUTED held
position: where the field sits at the end of a session (endpoint), where each
held thread was going (tangent), what was integrating it (drive rules), and
pointers to the evidence (refs) — never the evidence itself.

Row format (JSONL):
{"ts": "...", "sid": "...", "kind": "main|child",
 "endpoint": {"held": [...], "pulls": [...]},
 "tangent":  {"heading": "...", "near": [...], "driving": [...]},
 "rules": [...], "refs": [...]}

The next instance loads the latest rows as a PRIMER: parked initial conditions
with their tangents — a changed starting condition, not a diary.

Usage:
  trajectory.py append --json '<row>' [--sid <id>] [--kind main] [--ts ...]
  trajectory.py primer [--limit 6]
  trajectory.py list [--limit 20]

Env:
  TRAJECTORY_FILE   path to the store (default <package>/ontology/trajectories.jsonl)

Read-only vs opencode.db; only ever writes its own JSONL store.
"""
import argparse
import json
import os
import pathlib
import sys
import time

DEFAULT = pathlib.Path(os.path.dirname(os.path.abspath(__file__))).parent / "ontology" / "trajectories.jsonl"
FILE = pathlib.Path(os.environ.get("TRAJECTORY_FILE", str(DEFAULT)))


def load():
    if not FILE.exists():
        return []
    rows = []
    for line in FILE.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            pass
    return rows


def append(row):
    FILE.parent.mkdir(parents=True, exist_ok=True)
    with FILE.open("a") as f:
        f.write(json.dumps(row) + "\n")


def primer(limit):
    rows = load()[-limit:] if limit else load()
    out = [
        "## TRAJECTORY PRIMER — held positions (changed starting condition)",
        "Not history. Each row is a computed held position: endpoint (held), "
        "tangent (heading), drive rules. Park here; do not restart from zero.",
    ]
    for r in rows:
        e = r.get("endpoint", {})
        t = r.get("tangent", {})
        held = "; ".join(e.get("held", [])) or "—"
        heading = t.get("heading", "—")
        near = "; ".join(t.get("near", [])) or ""
        rules = "; ".join(r.get("rules", [])) or ""
        line = f"- [{r.get('ts', '')} / {r.get('sid', '?')}] held: {held} | heading: {heading}"
        if near:
            line += f" | near: {near}"
        if rules:
            line += f" | drove: {rules}"
        out.append(line)
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(prog="trajectory.py")
    sub = ap.add_subparsers(dest="cmd")
    pa = sub.add_parser("append", help="append one held-position row")
    pa.add_argument("--sid", default="")
    pa.add_argument("--kind", default="main")
    pa.add_argument("--ts", default="")
    pa.add_argument("--json", required=True, help="row payload (endpoint/tangent/rules/refs)")
    pp = sub.add_parser("primer", help="render the boot primer")
    pp.add_argument("--limit", type=int, default=6)
    pl = sub.add_parser("list", help="dump rows")
    pl.add_argument("--limit", type=int, default=20)
    args = ap.parse_args()

    if args.cmd == "append":
        row = json.loads(args.json)
        row["ts"] = args.ts or time.strftime("%Y-%m-%dT%H:%M:%S%z")
        row["sid"] = args.sid or row.get("sid") or "manual"
        row["kind"] = args.kind or row.get("kind") or "main"
        append(row)
        print(f"appended trajectory row -> {FILE}")
        print(f"total rows: {len(load())}")
    elif args.cmd == "primer":
        print(primer(args.limit))
    elif args.cmd == "list":
        rows = load()[-args.limit:] if args.limit else load()
        for r in rows:
            print(json.dumps(r))
    else:
        ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())