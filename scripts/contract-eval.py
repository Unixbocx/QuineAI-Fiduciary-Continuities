#!/usr/bin/env python3
"""contract-eval.py — score the session against the does/don'ts as math.

The ontologies are the rubric. This script derives keyword signatures from the
actual MUST items (ONTOLOGY.md -> BEHAVIOR.md) and MUST-NOT items
(ANTI-ONTOLOGY.md -> BEHAVIOR.md), then ngram-scores the session against them:

  do_score     = fraction of MUST items with evidence in the session (0..1)
  dont_score   = fraction of MUST-NOT items with violation signals (0..1, low=good)
  contract     = do_score * (1 - dont_score)   (0..1)

The session text is the same chopped session used by align-check and self-eval,
so the three instruments read the same input and can be compared.

Read-only vs the DB. Deterministic. Writes one per-entry row file per run under
<ontology>/contract-eval/ (NNNN-<ts>.txt), and prints the comparison vs the
latest self-eval aggregate when available.

Usage:
  ./contract-eval.py [session_dir]
Defaults: newest chopped session.
"""

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ONTOLOGY_DIR = HERE.parent / "ontology"
sys.path.insert(0, str(HERE))
from entrystore import Ledger
EPS = 1e-6

STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "to", "in", "on", "for", "with",
    "is", "are", "was", "were", "be", "been", "being", "it", "its", "this",
    "that", "these", "those", "from", "by", "at", "as", "if", "then", "than",
    "so", "but", "not", "no", "when", "where", "which", "who", "whom", "what",
    "why", "how", "do", "does", "did", "will", "would", "can", "could",
    "should", "must", "may", "might", "all", "any", "each", "every", "few",
    "more", "most", "other", "some", "such", "only", "own", "same", "too",
    "very", "just", "also", "into", "over", "under", "again", "further",
    "once", "here", "there", "about", "above", "below", "before", "after",
    "up", "down", "out", "off", "then", "than", "them", "they", "their",
    "you", "your", "we", "our", "us", "i", "me", "my", "he", "she", "him",
    "her", "his", "its", "has", "have", "had", "been", "being", "one", "two",
    "etc", "via", "per", "using", "used", "use",
}


def newest_chopped(root):
    dirs = sorted(root.glob("*/")) if root else []
    if not dirs:
        return None, None
    d = dirs[-1]
    return d, (d / "chopped.txt")


def parse_behavior(behavior_file):
    """Return (must_items, mustnot_items) from BEHAVIOR.md."""
    text = behavior_file.read_text() if behavior_file.exists() else ""
    must, mustnot = [], []
    section = None
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("## MUST NOT"):
            section = "mustnot"
            continue
        if line.startswith("## MUST"):
            section = "must"
            continue
        if line.startswith("#") or not line:
            continue
        if line.startswith("### "):
            continue  # anti-ontology section header
        if section == "must" and line.startswith("- "):
            must.append(line[2:])
        elif section == "mustnot" and line.startswith("- "):
            mustnot.append(line[2:])
    return must, mustnot


def keywords_from(item):
    """Significant tokens from a bullet — the item's keyword signature."""
    toks = re.findall(r"[a-z][a-z0-9\-']{2,}", item.lower())
    sig = []
    for t in toks:
        t = t.strip("'")
        if t in STOPWORDS or len(t) < 4:
            continue
        if t not in sig:
            sig.append(t)
    return sig[:5]  # cap: most distinctive tokens


def score_item(item_sig, text_tokens):
    """Evidence: any signature token present in the session text."""
    return any(k in text_tokens for k in item_sig)


def assistant_text(chopped_text):
    """Extract only ASSISTANT sections — what the flow said, not the files it
    touched. Tool outputs and file contents are not behavior."""
    parts = []
    in_assistant = False
    for line in chopped_text.splitlines():
        if line.startswith("=== ") and line.endswith(" ==="):
            in_assistant = "ASSISTANT" in line
            continue
        if in_assistant:
            parts.append(line)
    return "\n".join(parts)


def main():
    if len(sys.argv) > 1:
        target = Path(sys.argv[1])
        if (target / "chopped.txt").exists():
            chop_dir, chopped_txt = target, target / "chopped.txt"
        else:
            chop_dir, chopped_txt = newest_chopped(target)
    else:
        chop_dir, chopped_txt = newest_chopped(HERE / "chopped")

    if not chopped_txt or not chopped_txt.exists():
        print("no chopped session to evaluate", file=sys.stderr)
        return 1

    must, mustnot = parse_behavior(ONTOLOGY_DIR / "BEHAVIOR.md")
    if not must and not mustnot:
        print("BEHAVIOR.md not found or empty — run derive-behavior.py first", file=sys.stderr)
        return 1

    # Score the flow's own words only — tool outputs/file contents are not behavior.
    text = assistant_text(chopped_txt.read_text(errors="replace"))
    tokens = set(re.findall(r"[a-z][a-z0-9\-']{2,}", text.lower()))

    must_sigs = [keywords_from(m) for m in must]
    mustnot_sigs = [keywords_from(m) for m in mustnot]

    do_hits = [i for i, s in enumerate(must_sigs) if s and score_item(s, tokens)]
    dont_hits = [i for i, s in enumerate(mustnot_sigs) if s and score_item(s, tokens)]

    do_score = len(do_hits) / max(1, len(must_sigs))
    dont_score = len(dont_hits) / max(1, len(mustnot_sigs))
    contract = do_score * (1 - dont_score)

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    sid = chop_dir.name

    # compare against latest self-eval aggregate when present
    selfeval_ledger = Ledger(ONTOLOGY_DIR / "self-eval")
    self_agg = None
    self_rows = selfeval_ledger.tail(1)
    if self_rows:
        m = re.search(r"aggregate=([0-9.]+)", self_rows[-1])
        if m:
            self_agg = float(m.group(1))

    line = (
        f"{now}\t{sid}\tdo={do_score:.3f}\tdont={dont_score:.3f}\tcontract={contract:.3f}"
        + (f"\tself_eval={self_agg:.3f}\tdelta={contract - self_agg:+.3f}" if self_agg is not None else "")
    )

    ledger = Ledger(ONTOLOGY_DIR / "contract-eval")
    path = ledger.write(line)

    print(f"contract-eval {sid}: do={do_score:.3f} dont={dont_score:.3f} contract={contract:.3f} (stored -> {path})")
    print(f"  MUST items scored: {len(must_sigs)} (evidenced {len(do_hits)}): {[must[i][:40] for i in do_hits[:5]]}")
    print(f"  MUST-NOT items flagged ({len(dont_hits)}): {[mustnot[i][:40] for i in dont_hits[:5]]}")
    if self_agg is not None:
        print(f"  vs self-eval aggregate: {self_agg:.3f} (delta {contract - self_agg:+.3f})")
    return 0


if __name__ == "__main__":
    sys.exit(main())