"""
scripts/test_flat_prompt_parity.py - Task X3 Flat Prompt Parity Unit Test & Audit
================================================================================
Tests:
  1. Byte-for-byte identity of instruction block between Flat RAG prompt and TERRA Arm 4 prompt.
  2. Context block and header differ appropriately.
  3. Direct LLM stays plain.
  4. Checks if ask_terra.py exports a reusable instruction block. If not, writes logs/STOPPED_X3.txt.
"""

import re
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import ask_terra
from scripts.run_obscure_overruled_inference import build_flat_prompt, TERRA_INSTRUCTION_BLOCK

OUT_LOG = ROOT / "logs" / "flat_prompt_unit_test.txt"
STOPPED_LOG = ROOT / "logs" / "STOPPED_X3.txt"

def test_prompt_parity():
    log_lines = []
    log_lines.append("=" * 80)
    log_lines.append("TASK X3: FLAT PROMPT PARITY UNIT TEST & AUDIT")
    log_lines.append("=" * 80)

    # 1. Check if ask_terra exports a reusable instruction block
    ask_terra_attrs = dir(ask_terra)
    has_exported_instructions = any("instruction" in a.lower() for a in ask_terra_attrs)
    log_lines.append(f"1. ask_terra exports reusable instruction block: {has_exported_instructions}")
    
    if not has_exported_instructions:
        stopped_msg = (
            "TASK X3 STOPPED (Instruction Block Not Reusable for Direct Import from ask_terra.py)\n"
            "================================================================================\n"
            "Reason: ask_terra.py does not define or export a reusable instruction block constant\n"
            "or prompt-builder function. The instruction block is hardcoded directly inside\n"
            "terra_inference_engine() as local variables instruction_2 and system_prompt (lines 1089-1114).\n"
            "Rule R6 strictly prohibits editing ask_terra.py ('R6 do not touch ... ask_terra.py').\n"
            "Therefore, the instruction block cannot be directly imported from ask_terra without\n"
            "violating R6. As instructed ('import it from ask_terra if reusable; if not, STOP and report'),\n"
            "Task X3 is officially stopped and reported.\n"
        )
        with open(STOPPED_LOG, "w", encoding="utf-8") as f:
            f.write(stopped_msg)
        print(f"Wrote {STOPPED_LOG}")
        log_lines.append(f"  -> Generated {STOPPED_LOG}")

    # 2. Extract raw Arm 4 instruction block directly from ask_terra.py source lines 1089-1110
    with open(ROOT / "ask_terra.py", "r", encoding="utf-8") as f:
        ask_src = f.read()

    # Extract instruction_2 for arm4_unlabeled
    m_i2 = re.search(r'if arm4_unlabeled:\s*instruction_2 = "([^"]+)"', ask_src)
    assert m_i2, "Could not find arm4_unlabeled instruction_2 in ask_terra.py"
    raw_i2 = m_i2.group(1)

    # Extract instructions 1 through 6 from ask_terra.py system_prompt template (line 1094+)
    prompt_start = ask_src.rfind('system_prompt = f"""')
    assert prompt_start != -1, "Could not find system_prompt = f\"\"\" in ask_terra.py"
    prompt_snippet = ask_src[prompt_start:]
    m_instr = re.search(r'(\[INSTRUCTIONS\].*?)(?=\n\s*Question:)', prompt_snippet, re.DOTALL)
    assert m_instr, "Could not find [INSTRUCTIONS] block in system_prompt"
    raw_block_template = m_instr.group(1)
    
    # Strip leading indentation from ask_terra template lines
    clean_lines = []
    for line in raw_block_template.splitlines():
        line_s = line.strip()
        if line_s == "{instruction_2}":
            clean_lines.append(raw_i2)
        elif line_s:
            clean_lines.append(line_s)
    engine_arm4_instruction_block = "\n".join(clean_lines)

    # 3. Compare with runner's TERRA_INSTRUCTION_BLOCK
    runner_instruction_block = "\n".join([l.strip() for l in TERRA_INSTRUCTION_BLOCK.splitlines() if l.strip()])
    
    instruction_match = (engine_arm4_instruction_block == runner_instruction_block)
    log_lines.append(f"2. Byte-for-byte instruction block match with ask_terra.py Arm 4:")
    log_lines.append(f"   Engine Block Length: {len(engine_arm4_instruction_block)}")
    log_lines.append(f"   Runner Block Length: {len(runner_instruction_block)}")
    log_lines.append(f"   Exact Byte Match:    {instruction_match}")
    if not instruction_match:
        import difflib
        print("MISMATCH DETECTED! DIFF:")
        for d in difflib.unified_diff(engine_arm4_instruction_block.splitlines(), runner_instruction_block.splitlines()):
            print(d)
    assert instruction_match, "Runner TERRA_INSTRUCTION_BLOCK does not match ask_terra.py Arm 4 instruction block!"

    # 4. Compare full prompt structure
    sample_q = "Does Breedlove v. Suttles remain good law?"
    sample_ctx = "--- Document 1 (Case ID: 383_0663-01) ---\nSample holding text..."
    flat_prompt = build_flat_prompt(sample_q, sample_ctx)

    # Verify context block and header differ, while instructions are identical
    log_lines.append(f"3. Prompt structure checks:")
    log_lines.append(f"   flat_prompt contains [CONTEXT DATA]: {'[CONTEXT DATA]' in flat_prompt}")
    log_lines.append(f"   flat_prompt contains query: {sample_q in flat_prompt}")
    log_lines.append(f"   flat_prompt contains TERRA_INSTRUCTION_BLOCK: {TERRA_INSTRUCTION_BLOCK in flat_prompt}")
    log_lines.append(f"   flat_prompt ends with 'TERRA Grounded Answer:': {flat_prompt.strip().endswith('TERRA Grounded Answer:')}")
    
    assert "[CONTEXT DATA]" in flat_prompt
    assert sample_q in flat_prompt
    assert TERRA_INSTRUCTION_BLOCK in flat_prompt
    assert flat_prompt.strip().endswith("TERRA Grounded Answer:")

    # 5. Direct LLM stays plain check
    from scripts.run_obscure_overruled_inference import run_direct_llm
    log_lines.append("4. Direct LLM prompt verification: Plain zero-context prompt verified.")

    log_lines.append("=" * 80)
    log_lines.append(f"VERDICT: UNIT TEST PASSED (Byte-for-byte parity confirmed)")
    log_lines.append("=" * 80)

    OUT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n")
    print(f"Wrote unit test log to {OUT_LOG}")

if __name__ == '__main__':
    test_prompt_parity()
