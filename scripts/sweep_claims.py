"""
scripts/sweep_claims.py
=======================
Executes Task U7: Scans Paper/main.tex (read-only) for:
  1. Every line containing a changed macro from the v2 macro regeneration.
  2. Every line containing hard-coded claim strings or numbers:
     - 'marginally higher'
     - 'highest'
     - 'outperform'
     - 'gain'
     - '+0.328'
     - '0.825'
     - '0.739'
     - '0.695'
     - '19.05'
     - '3.19'
     - '6.38'
     - '56.0'
     - '42/75'
     - 'HippoRAG leads'

Outputs formatted as: file:line + sentence to logs/v2_claim_sweep.txt.
"""

import os
import sys
import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
MAIN_TEX_PATH = ROOT_DIR / "Paper" / "main.tex"
OLD_STATS_PATH = ROOT_DIR / "Paper" / "generated_stats.tex"
NEW_STATS_PATH = ROOT_DIR / "scratch" / "w_out_v2" / "Paper" / "generated_stats.tex"
OUTPUT_PATH = ROOT_DIR / "logs" / "v2_claim_sweep.txt"


def parse_defined_macros(tex_path):
    macros = {}
    if not tex_path.exists():
        return macros
    with open(tex_path, "r", encoding="utf-8") as f:
        for line in f:
            m = re.match(r'\\newcommand\{\\([A-Za-z0-9_]+)\}\{(.*)\}', line)
            if m:
                macros[m.group(1)] = m.group(2).strip()
    return macros


def split_into_sentences(text):
    # Split text into sentences reasonably while respecting LaTeX
    raw_sents = re.split(r'(?<=[.?!])\s+(?=[A-Z\\0-9\(\[])', text)
    sentences = []
    for s in raw_sents:
        s = s.strip()
        if s:
            sentences.append(s)
    return sentences if sentences else [text.strip()]


def main():
    old_macros = parse_defined_macros(OLD_STATS_PATH)
    new_macros = parse_defined_macros(NEW_STATS_PATH)

    changed_macros = {}
    for k, new_v in new_macros.items():
        old_v = old_macros.get(k)
        if old_v != new_v:
            changed_macros[k] = (old_v, new_v)

    search_targets = [
        "marginally higher",
        "highest",
        "outperform",
        "gain",
        "+0.328",
        "0.825",
        "0.739",
        "0.695",
        "19.05",
        "3.19",
        "6.38",
        "56.0",
        "42/75",
        "HippoRAG leads"
    ]

    with open(MAIN_TEX_PATH, "r", encoding="utf-8") as f:
        raw_lines = f.readlines()

    out = []
    def log(msg=""):
        out.append(msg)
        print(msg)

    log("=" * 115)
    log("TASK U7: PAPER CLAIM & CHANGED MACRO SWEEP AUDIT (READ-ONLY)")
    log("=" * 115)
    log(f"Target File : {MAIN_TEX_PATH}")
    log(f"Output File : {OUTPUT_PATH}")
    log(f"Total Base Macros Changed : {len(changed_macros)}")
    log(f"Hard-Coded Search Terms   : {', '.join(search_targets)}")
    log("=" * 115)
    log()

    total_sentence_matches = 0
    matched_lines_count = 0

    log("--- FILE:LINE + SENTENCE AUDIT LISTING ---")
    log()

    for line_idx, raw_line in enumerate(raw_lines, 1):
        line = raw_line.strip()
        if not line or line.startswith("%"):
            continue

        # Check triggers
        line_triggers = []
        for cm, (old_v, new_v) in changed_macros.items():
            if re.search(r'\\' + cm + r'(?![a-zA-Z0-9_])', line):
                line_triggers.append((f"\\{cm}", f"old: {old_v} -> new: {new_v}"))

        for st in search_targets:
            if st == "gain":
                if re.search(r'\bgains?\b', line, re.IGNORECASE):
                    line_triggers.append((st, "word match (gain/gains)"))
            else:
                if st.lower() in line.lower():
                    line_triggers.append((st, "string/number match"))

        if not line_triggers:
            continue

        matched_lines_count += 1
        sentences = split_into_sentences(line)

        for sent in sentences:
            sent_triggers = []
            for t_name, t_info in line_triggers:
                if t_name.startswith("\\"):
                    if re.search(r'\\' + re.escape(t_name[1:]) + r'(?![a-zA-Z0-9_])', sent):
                        sent_triggers.append((t_name, t_info))
                elif t_name == "gain":
                    if re.search(r'\bgains?\b', sent, re.IGNORECASE):
                        sent_triggers.append((t_name, t_info))
                else:
                    if t_name.lower() in sent.lower():
                        sent_triggers.append((t_name, t_info))

            if sent_triggers:
                total_sentence_matches += 1
                trig_summary = ", ".join([f"{t[0]} ({t[1]})" for t in sent_triggers])
                log(f"Paper/main.tex:{line_idx}: {sent}")
                log(f"   --> Triggers: {trig_summary}")
                log()

    log("=" * 115)
    log(f"SWEEP SUMMARY: {matched_lines_count} lines matched, {total_sentence_matches} sentences flagged for Phase 3 review.")
    log("=" * 115)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")

    print(f"\nWrote claim sweep to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
