import os
from pathlib import Path

ROOT = Path("f:/TERRA - Copy")
ASK_TERRA = ROOT / "ask_terra.py"
OUT_PATH = ROOT / "logs" / "ask_terra_relation_lines.txt"

def get_relation_lines():
    lines = []
    with open(ASK_TERRA, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f, 1):
            if any(k in line for k in ["OVERRULES", "REPUDIATES", "OVERRULING"]):
                lines.append(f"Line {idx:4d}: {line.rstrip()}")
    return lines

before_lines = get_relation_lines()

output = []
output.append("=" * 80)
output.append("ASK_TERRA.PY RELATION LINES AUDIT (BEFORE EDIT)")
output.append("=" * 80)
output.extend(before_lines)
output.append("\n")

with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.write("\n".join(output))

print(f"Wrote {len(before_lines)} before-edit relation lines to {OUT_PATH}")
