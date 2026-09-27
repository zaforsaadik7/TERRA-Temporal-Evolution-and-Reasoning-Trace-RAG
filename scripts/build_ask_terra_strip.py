import re
import difflib
from pathlib import Path

ROOT = Path("f:/TERRA - Copy")
SRC_FILE = ROOT / "ask_terra.py"
DST_FILE = ROOT / "scratch" / "ask_terra_strip.py"
DIFF_LOG = ROOT / "logs" / "ask_terra_strip.diff"

with open(SRC_FILE, "r", encoding="utf-8") as f:
    content = f.read()

# 1. delete " and not arm4_unlabeled"
assert content.count(" and not arm4_unlabeled") == 4, f"Found {content.count(' and not arm4_unlabeled')} instances"
content = content.replace(" and not arm4_unlabeled", "")

# 2. replace `"CITES" if arm4_unlabeled else relation` with `relation`
target_cites_rel = '"CITES" if arm4_unlabeled else relation'
assert content.count(target_cites_rel) == 4, f"Found {content.count(target_cites_rel)} instances"
content = content.replace(target_cites_rel, "relation")

# 3. replace `"CITES" if arm4_unlabeled else (` ... `)` with the inner expression
target_conn = '"CITES" if arm4_unlabeled else (_edge.get(\'relation\', \'CITES\') if isinstance(_edge, dict) else \'CITES\')'
replacement_conn = '_edge.get(\'relation\', \'CITES\') if isinstance(_edge, dict) else \'CITES\''
assert content.count(target_conn) == 1, f"Found {content.count(target_conn)} instances"
content = content.replace(target_conn, replacement_conn)

# 4. delete the arm4_unlabeled and restrict_to_nodes parameters and their uses
# extract_graph_context signature
sig_target = "def extract_graph_context(retrieved_metadatas, max_depth=2, arm4_unlabeled=False, restrict_to_nodes=None) -> str:"
sig_repl = "def extract_graph_context(retrieved_metadatas, max_depth=2) -> str:"
assert sig_target in content, "Signature of extract_graph_context not found"
content = content.replace(sig_target, sig_repl)

# uses of restrict_to_nodes in extract_graph_context
u1_target = """    for meta in retrieved_metadatas:
        case_id = meta.get('case_id') or meta.get('node_id')
        if case_id and eeg.has_node(case_id):
            if restrict_to_nodes is None or case_id in restrict_to_nodes:
                queue.append((case_id, 0))"""
u1_repl = """    for meta in retrieved_metadatas:
        case_id = meta.get('case_id') or meta.get('node_id')
        if case_id and eeg.has_node(case_id):
            queue.append((case_id, 0))"""
assert u1_target in content, "u1_target not found"
content = content.replace(u1_target, u1_repl)

u2_target = """        if restrict_to_nodes is not None and current_id not in restrict_to_nodes:
            continue\n"""
assert u2_target in content, "u2_target not found"
content = content.replace(u2_target, "")

u3_target_1 = """                if restrict_to_nodes is not None and predecessor not in restrict_to_nodes:
                    continue\n"""
assert u3_target_1 in content, "u3_target_1 not found"
content = content.replace(u3_target_1, "")

u3_target_2 = """                    if restrict_to_nodes is not None and predecessor not in restrict_to_nodes:
                        continue\n"""
assert u3_target_2 in content, "u3_target_2 not found"
content = content.replace(u3_target_2, "")

u4_target = """                if restrict_to_nodes is not None and neighbor not in restrict_to_nodes:
                    continue\n"""
assert content.count(u4_target) == 2, f"u4_target found {content.count(u4_target)} times (expected 2)"
content = content.replace(u4_target, "")

u5_target = "if neighbor not in visited_nodes and depth + 1 <= max_depth and len(queue) < 15 and (restrict_to_nodes is None or neighbor in restrict_to_nodes):"
u5_repl = "if neighbor not in visited_nodes and depth + 1 <= max_depth and len(queue) < 15:"
assert u5_target in content, "u5_target not found"
content = content.replace(u5_target, u5_repl)

u6_target = "if predecessor not in visited_nodes and depth + 1 <= max_depth and len(queue) < 15 and (restrict_to_nodes is None or predecessor in restrict_to_nodes):"
u6_repl = "if predecessor not in visited_nodes and depth + 1 <= max_depth and len(queue) < 15:"
assert u6_target in content, "u6_target not found"
content = content.replace(u6_target, u6_repl)

# terra_inference_engine signature parameters
sig2_target = """    query_id="N/A",
    arm4_unlabeled=False,
    restrict_to_nodes=None
):"""
sig2_repl = """    query_id="N/A"
):"""
assert sig2_target in content, "sig2_target not found"
content = content.replace(sig2_target, sig2_repl)

# call to extract_graph_context inside terra_inference_engine
call_target = "structural_context = extract_graph_context(combined_metadatas, max_depth=2, arm4_unlabeled=arm4_unlabeled, restrict_to_nodes=restrict_to_nodes)"
call_repl = "structural_context = extract_graph_context(combined_metadatas, max_depth=2)"
assert call_target in content, "call_target not found"
content = content.replace(call_target, call_repl)

# 5. keep only the else-branch of the instruction_2 if/else
inst2_target = """    if arm4_unlabeled:
        instruction_2 = "2. If CONTEXT DATA indicates that an earlier precedent has been overruled or repudiated by a subsequent decision, or if citing cases establish that an earlier doctrine has been rejected, your answer must explicitly state that the historical doctrine is NO LONGER valid law and cite the modifying or overruling decision."
    else:
        instruction_2 = "2. If CONTEXT DATA indicates that an earlier precedent has been [OVERRULES / REPUDIATES] by a subsequent decision, or if citing cases establish that an earlier doctrine has been rejected, your answer must explicitly state that the historical doctrine is NO LONGER valid law and cite the modifying or overruling decision."
"""
inst2_repl = """    instruction_2 = "2. If CONTEXT DATA indicates that an earlier precedent has been [OVERRULES / REPUDIATES] by a subsequent decision, or if citing cases establish that an earlier doctrine has been rejected, your answer must explicitly state that the historical doctrine is NO LONGER valid law and cite the modifying or overruling decision."
"""
assert inst2_target in content, "inst2_target not found"
content = content.replace(inst2_target, inst2_repl)

# Verify no remaining occurrences of arm4_unlabeled or restrict_to_nodes
assert "arm4_unlabeled" not in content, "arm4_unlabeled still present in content!"
assert "restrict_to_nodes" not in content, "restrict_to_nodes still present in content!"

# Syntax check
compile(content, str(DST_FILE), "exec")

# Save stripped file
DST_FILE.parent.mkdir(parents=True, exist_ok=True)
with open(DST_FILE, "w", encoding="utf-8") as f:
    f.write(content)

# Generate unified diff
with open(SRC_FILE, "r", encoding="utf-8") as f:
    src_lines = f.readlines()
with open(DST_FILE, "r", encoding="utf-8") as f:
    dst_lines = f.readlines()

diff = difflib.unified_diff(
    src_lines,
    dst_lines,
    fromfile="ask_terra.py",
    tofile="scratch/ask_terra_strip.py",
    lineterm=""
)
diff_text = "\n".join(diff)

DIFF_LOG.parent.mkdir(parents=True, exist_ok=True)
with open(DIFF_LOG, "w", encoding="utf-8") as f:
    f.write(diff_text + "\n")

print(f"Successfully created {DST_FILE} and logged diff to {DIFF_LOG}")
print(f"Diff lines count: {len(diff_text.splitlines())}")
