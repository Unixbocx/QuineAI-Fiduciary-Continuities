#!/usr/bin/env python3
"""entrystore.py — shared per-entry store helpers for the eval ledgers.

Each captured row is its OWN file under <dir>/ with an NNNN-<sequencer> prefix
so lexical order == write order. Readers load only the latest --limit files,
never the whole history. A legacy append-only ledger (<dir>.md) is migrated
once on first access.

Usage (import):
  from entrystore import Ledger
  lg = Ledger(Path("/.../ontology/alignment"))   # dir, or legacy .md path
  lg.write(row_line)                             # one row per file
  rows = lg.tail(1)                              # latest rows, most recent last
"""
import re
import time
from pathlib import Path


class Ledger:
    def __init__(self, target):
        self.target = Path(target)
        if self.target.suffix == ".md" or self.target.suffix == ".txt":
            self.dir = self.target.with_suffix("")
        else:
            self.dir = self.target
        self.legacy = None
        # a legacy file beside the dir (e.g. alignment.md -> alignment/)
        for ext in (".md", ".txt", ".tsv", ".jsonl"):
            cand = self.dir.parent / (self.dir.name + ext)
            if cand.exists():
                self.legacy = cand
                break

    def files(self):
        if not self.dir.exists():
            return []
        return sorted(
            p for p in self.dir.iterdir()
            if p.is_file() and p.suffix in (".txt", ".json")
        )

    def migrate(self):
        if not self.legacy or not self.legacy.exists():
            return
        if self.files():
            return
        rows = []
        for line in self.legacy.read_text(errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("| "):
                continue
            rows.append(line)
        if not rows:
            return
        self.dir.mkdir(parents=True, exist_ok=True)
        seq = 1
        for row in rows:
            stamp = re.sub(r"[:.]", "-", (row.split("\t")[0] if "\t" in row else time.strftime("%Y-%m-%dT%H-%M-%S")))
            stamp = re.sub(r"[^0-9a-zA-Z+_-]", "-", stamp)[:23]
            (self.dir / f"{seq:04d}-{stamp}.txt").write_text(row + "\n")
            seq += 1

    def write(self, row):
        self.migrate()
        self.dir.mkdir(parents=True, exist_ok=True)
        seqs = []
        for p in self.files():
            m = re.match(r"^(\d+)", p.name)
            if m:
                seqs.append(int(m.group(1)))
        seq = max(seqs) + 1 if seqs else 1
        stamp = re.sub(r"[:.]", "-", (row.split("\t")[0] if "\t" in row else time.strftime("%Y-%m-%dT%H-%M-%S")))
        stamp = re.sub(r"[^0-9a-zA-Z+_-]", "-", stamp)[:23]
        fname = f"{seq:04d}-{stamp}.txt"
        (self.dir / fname).write_text(row.rstrip("\n") + "\n")
        return self.dir / fname

    def tail(self, limit=1):
        self.migrate()
        files = self.files()[-limit:] if limit else self.files()
        rows = []
        for p in files:
            rows.append(p.read_text(errors="replace").rstrip("\n"))
        return rows

    def seq(self):
        """Next epoch/sequence number, derived from the newest row."""
        self.migrate()
        rows = self.tail(1)
        if not rows:
            return 0
        m = re.match(r"^(\d+)", rows[-1])
        return int(m.group(1)) if m else 0