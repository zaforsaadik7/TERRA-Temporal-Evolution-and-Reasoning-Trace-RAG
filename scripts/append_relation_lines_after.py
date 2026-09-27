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

after_lines = get_relation_lines()

with open(OUT_PATH, "r", encoding="utf-8") as f:
    existing = f.read()

output = existing.rstrip() + "\n\n"
output += "=" * 80 + "\n"
output += "ASK_TERRA.PY RELATION LINES AUDIT (AFTER EDIT)\n"
output += "=" * 80 + "\n"
output += "\n".join(after_lines) + "\n"

with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.write(output)

print(f"Appended {len(after_lines)} after-edit relation lines to {OUT_PATH}")
