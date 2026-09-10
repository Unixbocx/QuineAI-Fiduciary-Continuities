#!/usr/bin/env python3
"""trajectory.py — the trajectory primer store (held positions, not residue).

The preserved object is NOT the session's text. Each row is a COMPUTED held
position: where the field sits at the end of a session (endpoint), where each
held thread was going (tangent), what was integrating it (drive rules), and
pointers to the evidence (refs) — never the evidence itself.

Row format (per-entry files under <dir>/):
{"ts": "...", "sid": "...", "kind": "main|child",
 "endpoint": {"held": [...], "pulls": [...]},
 "tangent":  {"heading": "...", "near": [...], "driving": [...]},
 "rules": [...], "refs": [...]}

Each row is its OWN file: NNNN-<ISO ts>.json. Readers load only the latest
--limit files, never the whole history — retrieval scales with the part, not
the whole. A legacy JSONL store (<dir>.jsonl) is migrated once on first use.

The next instance loads the latest rows as a PRIMER: parked initial conditions
with their tangents — a changed starting condition, not a diary.

Usage:
  trajectory.py append --json '<row>' [--sid <id>] [--kind main] [--ts ...]
  trajectory.py primer [--limit 6]
  trajectory.py list [--limit 20]

Env:
  TRAJECTORY_DIR    path to the per-entry store (default <package>/state/trajectories
                    when present, else <package>/ontology/trajectories)

Read-only vs opencode.db; only ever writes its own store.
"""
import argparse
import json
import os
import pathlib
import sys
import time

PACKAGE = pathlib.Path(os.path.dirname(os.path.abspath(__file__))).parent
_STATE = PACKAGE / "state"
_ONT = PACKAGE / "ontology"
DIR = pathlib.Path(os.environ.get(
    "TRAJECTORY_DIR",
    str(_STATE / "trajectories" if _STATE.exists() else _ONT / "trajectories"),
))
LEGACY = pathlib.Path(os.environ.get("TRAJECTORY_FILE", str(DIR.parent / "trajectories.jsonl")))


def entries():
    if not DIR.exists():
        return []
    return sorted(p for p in DIR.iterdir() if p.name.endswith(".json"))


def migrate():
    if not LEGACY.exists():
        return
    if entries():
        return
    rows = []
    for line in LEGACY.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            pass
    if not rows:
        return
    DIR.mkdir(parents=True, exist_ok=True)
    seq = 1
    for row in rows:
        ts = str(row.get("ts") or time.strftime("%Y-%m-%dT%H:%M:%S%z")).replace(":", "-").replace(".", "-")
        fname = f"{seq:04d}-{ts}.json"
        (DIR / fname).write_text(json.dumps(row) + "\n")
        seq += 1


def load():
    migrate()
    rows = []
    for p in entries():
        try:
            rows.append(json.loads(p.read_text()))
        except Exception:
            pass
    return rows


def append(row):
    migrate()
    DIR.mkdir(parents=True, exist_ok=True)
    seqs = [int(p.stem.split("-")[0]) for p in entries() if p.stem.split("-")[0].isdigit()]
    seq = max(seqs) + 1 if seqs else 1
    ts = str(row.get("ts") or time.strftime("%Y-%m-%dT%H:%M:%S%z")).replace(":", "-").replace(".", "-")
    fname = f"{seq:04d}-{ts}.json"
    (DIR / fname).write_text(json.dumps(row) + "\n")
    return DIR / fname


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
        target = append(row)
        print(f"stored trajectory row -> {target}")
        print(f"total files: {len(entries())}")
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