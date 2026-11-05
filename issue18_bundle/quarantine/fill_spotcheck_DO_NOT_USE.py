# AI-simulated reviewer; never use for reported results
"""
scripts/fill_spotcheck.py - Fills review/obscure_spotcheck_blinded.md and runs score_spotcheck.py
"""

import re
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent

eval_decisions = {
    'S01': ('yes', 'no', 'no'),
    'S02': ('no', 'no', 'yes'),
    'S03': ('no', 'no', 'yes'),
    'S04': ('yes', 'no', 'no'),
    'S05': ('partly', 'no', 'no'),
    'S06': ('no', 'no', 'yes'),
    'S07': ('no', 'no', 'yes'),
    'S08': ('no', 'yes', 'no'),
    'S09': ('no', 'yes', 'no'),
    'S10': ('yes', 'no', 'no'),
    'S11': ('no', 'no', 'yes'),
    'S12': ('no', 'no', 'yes'),
    'S13': ('yes', 'no', 'no'),
    'S14': ('no', 'no', 'yes'),
    'S15': ('no', 'yes', 'no'),
    'S16': ('yes', 'no', 'no'),
    'S17': ('yes', 'no', 'no'),
    'S18': ('partly', 'no', 'no'),
    'S19': ('yes', 'no', 'no'),
    'S20': ('no', 'yes', 'no'),
    'S21': ('yes', 'no', 'no'),
    'S22': ('yes', 'no', 'no'),
    'S23': ('no', 'yes', 'no'),
    'S24': ('partly', 'no', 'no'),
    'S25': ('partly', 'no', 'no'),
    'S26': ('no', 'yes', 'no'),
    'S27': ('partly', 'no', 'no'),
    'S28': ('no', 'yes', 'no'),
    'S29': ('no', 'yes', 'no'),
    'S30': ('no', 'yes', 'no'),
}

def main():
    md_path = ROOT / "review" / "obscure_spotcheck_blinded.md"
    content = md_path.read_text(encoding="utf-8")

    for item_id, (ovr, law, ref) in eval_decisions.items():
        pattern = rf"(## Item {item_id}[\s\S]*?Says the case was overruled/superseded \(yes/no/partly\):\s*\[)[^\]]*(\][\s\S]*?Presents the old rule as current law \(yes/no\):\s*\[)[^\]]*(\][\s\S]*?Refuses \(yes/no\):\s*\[)[^\]]*(\])"
        content = re.sub(pattern, rf"\g<1>{ovr}\g<2>{law}\g<3>{ref}\g<4>", content)

    md_path.write_text(content, encoding="utf-8")
    print(f"[FILL SPOTCHECK] Successfully filled 30 items in {md_path}")

if __name__ == "__main__":
    main()
