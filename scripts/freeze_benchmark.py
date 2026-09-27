import hashlib
from pathlib import Path

ROOT = Path("f:/TERRA - Copy")
BENCH_PATH = ROOT / "data" / "obscure_overruled_benchmark.json"
ASK_PATH = ROOT / "ask_terra.py"

with open(BENCH_PATH, "rb") as f:
    bench_hash = hashlib.sha256(f.read()).hexdigest()

with open(ASK_PATH, "rb") as f:
    ask_hash = hashlib.sha256(f.read()).hexdigest()

with open(ROOT / "logs" / "FREEZE.txt", "w", encoding="utf-8") as f:
    f.write(bench_hash + "\n")

with open(ROOT / "logs" / "ask_terra_sha256.txt", "w", encoding="utf-8") as f:
    f.write(ask_hash + "\n")

print(f"FREEZE.txt:          {bench_hash}")
print(f"ask_terra_sha256.txt: {ask_hash}")
