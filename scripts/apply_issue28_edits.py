import os
import re

TARGET_FILE = "Paper/main.tex"

with open(TARGET_FILE, "r", encoding="utf-8") as f:
    text = f.read()

# Edit 1: Line 111
t1 = "standard pipelines retrieve fragmented textual snippets that sever causal dependencies, proving entirely insufficient for tasks that require deep, multi-hop reasoning."
r1 = "standard pipelines retrieve fragmented textual snippets that sever precedential and doctrinal dependencies, proving entirely insufficient for tasks that require deep, multi-hop reasoning."
assert t1 in text, "Target 1 (Line 111) not found in Paper/main.tex"
assert text.count(t1) == 1, "Target 1 not unique"
text = text.replace(t1, r1)

# Edit 2: Line 495
t2 = "Rather than presenting aggregated metrics that obscure internal component dynamics, we first dissect the architecture into its constituent mechanisms to establish causal contributions."
r2 = "Rather than presenting aggregated metrics that obscure internal component dynamics, we first dissect the architecture into its constituent mechanisms to isolate the empirical contribution of each subsystem."
assert t2 in text, "Target 2 (Line 495) not found in Paper/main.tex"
assert text.count(t2) == 1, "Target 2 not unique"
text = text.replace(t2, r2)

# Edit 3: Line 522
t3 = r"\item \textbf{Causal Necessity of EEG Graph Traversal:}"
r3 = r"\item \textbf{Architectural Necessity of EEG Graph Traversal:}"
assert t3 in text, "Target 3 (Line 522) not found in Paper/main.tex"
assert text.count(t3) == 1, "Target 3 not unique"
text = text.replace(t3, r3)

# Edit 4: Line 753
t4 = "on the causal denominator of leaking candidates ($D$)."
r4 = "on the conditioning denominator of leaking candidates ($D$)."
assert t4 in text, "Target 4 (Line 753) not found in Paper/main.tex"
assert text.count(t4) == 1, "Target 4 not unique"
text = text.replace(t4, r4)

# Write modified file
with open(TARGET_FILE, "w", encoding="utf-8") as f:
    f.write(text)

print("[PASS] All 4 surgical edits applied to Paper/main.tex successfully.")

# Post-edit verification
with open(TARGET_FILE, "r", encoding="utf-8") as f:
    new_text = f.read()

matches = []
for lno, line in enumerate(new_text.splitlines(), 1):
    found = re.findall(r'\bcausal\w*', line, re.IGNORECASE)
    if found:
        matches.append((lno, found, line.strip()))

print(f"\nRemaining occurrences of 'causal' in {TARGET_FILE}: {len(matches)}")
for lno, found, line in matches:
    print(f"  Line {lno}: {found} -> {line[:80]}")

# Assert exactly 1 remaining match: the Zhang et al. citation on line 133
assert len(matches) == 1, f"Expected exactly 1 remaining match, got {len(matches)}"
assert matches[0][0] == 133, f"Expected remaining match on line 133, got line {matches[0][0]}"
assert "zhang2025respectingtemporalcausalconsistencyentityevent" in matches[0][2], "Expected Zhang et al. citation"
print("[PASS] Verified exactly one legitimate literature citation remains in Paper/main.tex.")
