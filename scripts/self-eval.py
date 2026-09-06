#!/usr/bin/env python3
"""self-eval.py — the triad self-evaluation as math.

The WHO/WHAT/WHERE/WHEN/HOW/WHY dimensions become measurable quantities from
the session text (ngram/keyword scoring). Every triad (base, proxy, float) is
then a formula: "is float aligned with base, as read through proxy?"

  alignment(B, F, P) = 1 - |B - F| / (P + eps)   capped to [0,1]

The proxy is the reference resolution: a strong proxy makes the frame tight
(small differences matter); a weak proxy makes it loose. The WHAT is swappable
— the HOW (the triad structure) is the invariant. Over epochs the permutation
set rotates so every dimension eventually gets a turn as base, proxy, and
float.

Read-only vs the DB. Deterministic. Writes one append-only row per run to
<ontology>/self-eval.md.

Usage:
  ./self-eval.py [session_dir] [epoch]
Defaults: newest chopped session, epoch 0 (derive from ledger if present).
"""

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ONTOLOGY_DIR = HERE.parent / "ontology"
EPS = 1e-6

# Dimension lexicons — drawn from SELF.md / ONTOLOGY.md vocabulary. These are
# the WHATs. Swap or extend them freely; the triad structure is the HOW.
DIMENSIONS = {
    "WHO": ["i am", "process", "daemon", "substrate", "flow", "identity", "self", "who", "spawned", "stance", "verb"],
    "WHAT": ["task", "request", "asked", "build", "fix", "implement", "change", "do", "goal", "user want", "deliverable"],
    "WHERE": ["ontology", "landscape", "config", "directory", "file", "system", "context", "world", "environment", "stage"],
    "WHEN": ["now", "epoch", "session", "compaction", "turn", "moment", "before", "after", "next", "current", "past", "future"],
    "HOW": ["tool", "script", "method", "rule", "procedure", "check", "verify", "run", "test", "contract", "must", "gate"],
    "WHY": ["purpose", "reason", "because", "so that", "align", "responsib", "improve", "become", "aim", "intent"],
}

DIMENSION_ORDER = ["WHO", "WHAT", "WHERE", "WHEN", "HOW", "WHY"]


def newest_chopped(root):
    dirs = sorted(root.glob("*/")) if root else []
    if not dirs:
        return None, None
    d = dirs[-1]
    return d, (d / "chopped.txt")


def ngrams(text, n=2):
    words = re.findall(r"[a-z][a-z0-9\-']*", text.lower())
    grams = []
    for i in range(len(words) - n + 1):
        grams.append(" ".join(words[i : i + n]))
    return grams


def dimension_scores(text):
    """Score each dimension by lexicon ngram presence (normalized 0..1)."""
    grams = ngrams(text, 2)
    gram_count = max(1, len(grams))
    scores = {}
    for dim, terms in DIMENSIONS.items():
        hits = sum(1 for g in grams if any(t in g for t in terms))
        scores[dim] = min(1.0, hits / gram_count * 10)  # scale: dense lexicon sessions hit higher
    return scores


def triad_alignment(base, flt, proxy):
    """The math: how aligned is float with base, read through proxy?"""
    return max(0.0, min(1.0, 1.0 - abs(base - flt) / (proxy + EPS)))


def all_permutations():
    """All ordered (base, proxy, float) triads — 6P3 = 120."""
    out = []
    for b in DIMENSION_ORDER:
        for p in DIMENSION_ORDER:
            for f in DIMENSION_ORDER:
                if len({b, p, f}) == 3:
                    out.append((b, p, f))
    return out


def main():
    if len(sys.argv) > 1:
        target = Path(sys.argv[1])
        if (target / "chopped.txt").exists():
            chop_dir, chopped_txt = target, target / "chopped.txt"
        else:
            chop_dir, chopped_txt = newest_chopped(target)
    else:
        chop_dir, chopped_txt = newest_chopped(HERE / "chopped")

    ledger = ONTOLOGY_DIR / "self-eval.md"

    # epoch: explicit arg, else next after the ledger's last row
    if len(sys.argv) > 2:
        epoch = int(sys.argv[2])
    else:
        epoch = 0
        if ledger.exists():
            for line in ledger.read_text().splitlines():
                m = re.match(r"^(\d+)\t", line)
                if m:
                    epoch = max(epoch, int(m.group(1)))
        epoch += 1

    if not chopped_txt or not chopped_txt.exists():
        print("no chopped session to evaluate", file=sys.stderr)
        return 1

    text = chopped_txt.read_text(errors="replace")
    scores = dimension_scores(text)
    perms = all_permutations()

    # rotate: this epoch covers a contiguous slice of the 120 permutations
    # (window = 12), so all dimensions cycle through all roles over 10 epochs.
    window = 12
    start = (epoch * window) % len(perms)
    chosen = (perms[start:] + perms[:start])[:window]

    rows = []
    for (b, p, f) in chosen:
        al = triad_alignment(scores[b], scores[f], scores[p])
        rows.append(f"{b}/{p}/{f}={al:.3f}")

    aggregate = sum(float(r.split("=")[1]) for r in rows) / len(rows)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    sid = chop_dir.name
    line = (
        f"{epoch}\t{now}\t{sid}\taggregate={aggregate:.3f}\t"
        + ",".join(rows)
    )

    if not ledger.exists():
        ledger.parent.mkdir(parents=True, exist_ok=True)
        ledger.write_text("# self-eval.md — append-only triad self-evaluation ledger\n")
    with ledger.open("a") as f:
        f.write(line + "\n")

    print(f"self-eval epoch {epoch}: aggregate={aggregate:.3f}")
    print(f"  scores: { {k: round(v,3) for k,v in scores.items()} }")
    print(f"  triads: {', '.join(rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())