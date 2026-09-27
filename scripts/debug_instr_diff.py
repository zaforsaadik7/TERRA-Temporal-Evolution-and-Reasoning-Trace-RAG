import re
import sys
import difflib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

with open(ROOT / "ask_terra.py", "r", encoding="utf-8") as f:
    ask_src = f.read()

m_i2 = re.search(r'if arm4_unlabeled:\s*instruction_2 = "([^"]+)"', ask_src)
raw_i2 = m_i2.group(1)

m_instr = re.search(r'(\[INSTRUCTIONS\].*?)(?=\n\s*Question:)', ask_src, re.DOTALL)
raw_block_template = m_instr.group(1)

clean_lines = []
for line in raw_block_template.splitlines():
    line_s = line.strip()
    if line_s == "{instruction_2}":
        clean_lines.append(raw_i2)
    elif line_s:
        clean_lines.append(line_s)
engine_block = "\n".join(clean_lines)

from scripts.run_obscure_overruled_inference import TERRA_INSTRUCTION_BLOCK
runner_block = "\n".join([l.strip() for l in TERRA_INSTRUCTION_BLOCK.splitlines() if l.strip()])

print(f"engine_block:\n{engine_block}\n")
print(f"runner_block:\n{runner_block}\n")

diff = list(difflib.unified_diff(engine_block.splitlines(), runner_block.splitlines(), lineterm=""))
for d in diff:
    print(d)
