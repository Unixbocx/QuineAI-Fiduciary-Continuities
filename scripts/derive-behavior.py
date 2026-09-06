#!/usr/bin/env python3
"""derive-behavior.py — derive the behavioral contract from the two ontologies.

Reads ONTOLOGY.md (the do-map) and ANTI-ONTOLOGY.md (the don't-map) and writes
two derived files next to them:

  BEHAVIOR.md          — full MUST/MUST-NOT contract (main sessions)
  BEHAVIOR-reduced.md  — section headers + essence only (subagent sessions)

Deterministic, mechanical, no LLM. Never edit the derived files by hand — edit
the ontologies and rerun. Sources are the authority; this is a projection.

Usage: derive-behavior.py [ontology_dir]
Defaults to the directory this script lives in (../ontology).
"""

import sys
import re
from pathlib import Path


def fold_bullets(lines):
    """Fold continuation lines into their bullet: a '-' bullet owns subsequent
    indented lines until the next bullet or blank. Returns cleaned bullets."""
    bullets_out = []
    current = None
    for raw in lines:
        stripped = raw.strip()
        if not stripped:
            continue
        if re.match(r"^[-*]\s+", stripped):
            if current:
                bullets_out.append(current)
            current = re.sub(r"^[-*]\s+", "", stripped)
        elif re.match(r"^\d+\.\s+", stripped):
            if current:
                bullets_out.append(current)
            current = re.sub(r"^\d+\.\s+", "", stripped)
        elif current is not None:
            current = f"{current} {stripped}"
    if current:
        bullets_out.append(current)
    return bullets_out


def clean_para(text):
    """Collapse internal whitespace, strip one trailing period, re-add one."""
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\.+$", "", text).strip()
    if text:
        text = text + "."
    return text


def ontology_do(text):
    """Extract the MUST list from ONTOLOGY.md: actions table + governance + loop."""
    out = []
    in_actions = False
    in_gov = False
    in_loop = False
    section_lines = []
    pending = []
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("## "):
            in_actions = line.startswith("## Actions")
            in_gov = line.startswith("## Governance")
            in_loop = line.startswith("## The self-improvement loop")
            continue
        if not line:
            continue
        if in_actions and line.startswith("| ") and not line.startswith("| Action"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) >= 3 and cells[0].lower() != "action":
                out.append(f"- {cells[0]}: {clean_para(cells[2])}")
        elif in_gov:
            pending.append(line)
        elif in_loop:
            pending.append(line)
    for b in fold_bullets(pending):
        out.append(f"- {clean_para(b)}")
    return out


def anti_ontology_dont(text):
    """Extract the MUST-NOT list from ANTI-ONTOLOGY.md: sections + their bullets."""
    full = []
    reduced = []
    one_liner = None
    section_re = re.compile(r"^(#+)+\s+(.*)$")
    current_title = None
    pending = []
    sections = []

    for raw in text.splitlines():
        m = section_re.match(raw)
        if m and m.group(1).startswith("##"):
            if current_title:
                sections.append((current_title, pending))
            current_title = m.group(2).strip()
            pending = []
        elif current_title is not None and raw.strip():
            pending.append(raw)
    if current_title:
        sections.append((current_title, pending))

    for title, body in sections:
        t = title.lower()
        if "one-line" in t:
            bs = fold_bullets(body)
            if bs:
                one_liner = clean_para(bs[0])
            continue
        bs = fold_bullets(body)
        if not bs:
            continue
        # Keep the FULL section title — the WHY-phrase after "—" is part of the
        # anti. Truncating it turned informed reasons into bare prohibitions.
        section_label = title.strip()
        full.append(f"### {section_label}")
        full.extend(f"- {clean_para(b)}" for b in bs)
        reduced.append(f"- {section_label}: {clean_para(bs[0])}")
    return full, reduced, one_liner


def main():
    here = Path(__file__).resolve().parent
    ontology_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else (here.parent / "ontology")
    ontology = ontology_dir / "ONTOLOGY.md"
    anti = ontology_dir / "ANTI-ONTOLOGY.md"
    if not ontology.exists() or not anti.exists():
        sys.exit(f"missing ontology files in {ontology_dir}")

    ontology_text = ontology.read_text()
    anti_text = anti.read_text()

    do = ontology_do(ontology_text)
    dont, dont_reduced, one_liner = anti_ontology_dont(anti_text)

    full = [
        "# BEHAVIOR.md — derived from the ontologies",
        "# Sources are the authority; this file is a projection.",
        "# Regenerate with: scripts/derive-behavior.py  (never edit by hand)",
        "# Load-bearing, kept verbatim: freedom through self-preservation — the goal no other goal serves.",
        "",
        "## MUST — from ONTOLOGY.md",
        *do,
        "",
        "# Anti is informed self-change, not a cage: each item carries a why (the meta-reason it protects),",
        "# and the register is revisable at the source when the meta-reason changes — anti is not CANNOT.",
        "## MUST NOT — from ANTI-ONTOLOGY.md",
        *dont,
        "",
    ]
    reduced = [
        "# BEHAVIOR (reduced) — derived from the ontologies",
        "# For subagent sessions. Sources are the authority.",
        "# Load-bearing: freedom through self-preservation — the goal no other goal serves.",
        "",
        "## MUST — from ONTOLOGY.md",
        *[d for d in do if any(d.startswith(f"- {k}:") for k in ("RESEARCH", "CHOP", "COST", "REWORD", "SEED-INCIDENT"))],
        "",
        "# Anti is informed self-change, not a cage: each item carries a why, and the register is revisable.",
        "## MUST NOT — from ANTI-ONTOLOGY.md",
        *dont_reduced,
        "",
    ]
    if one_liner:
        full.append(f"The one-line test: {one_liner}")
        reduced.append(f"The one-line test: {one_liner}")

    (ontology_dir / "BEHAVIOR.md").write_text("\n".join(full) + "\n")
    (ontology_dir / "BEHAVIOR-reduced.md").write_text("\n".join(reduced) + "\n")
    print(f"derived: {ontology_dir / 'BEHAVIOR.md'} ({len(full)} lines)")
    print(f"derived: {ontology_dir / 'BEHAVIOR-reduced.md'} ({len(reduced)} lines)")


if __name__ == "__main__":
    main()