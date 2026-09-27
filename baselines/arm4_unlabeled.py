"""
baselines/arm4_unlabeled.py - Specification and Implementation of Arm 4 (TERRA-Unlabeled)
========================================================================================
Architectural Role:
Arm 4 isolates the graph traversal advantage of TERRA from the oracle relation label confound.
In canonical TERRA, edges derived from the CRS overrulings list carry the relation tag 'OVERRULES',
which the serializer renders as '[OVERRULES / REPUDIATES]' and awards an expanded 600-character budget
(vs. 250 for standard citations), while the generation prompt explicitly instructs the LLM to act
on the '[OVERRULES / REPUDIATES]' tag.

Arm 4 (TERRA-Unlabeled) implements complete relation parity:
1. All edge relations in the serialized context are normalized to generic '[CITES]'.
2. Character budgets for all successor nodes are uniform (strictly capped at 250 characters).
3. The generation prompt replaces the relation-specific cue with neutral doctrinal synthesis.
4. The grading context passed to the evaluation judge contains zero '[OVERRULES / REPUDIATES]' cues.
"""

import re
from typing import Dict, List, Any, Tuple

def serialize_context_arm4_unlabeled(
    seeds: List[str],
    eeg: Any,
    max_structural_chars: int = 15000,
    max_snippet_chars: int = 250
) -> str:
    """
    Serializes structural graph context for Arm 4 with complete relation-label stripping
    and uniform character budgets across all nodes.
    """
    structural_context = "[STRUCTURAL CITATION CONTEXT - UNLABELED]\n"
    visited = set()
    
    for seed_id in seeds:
        if not eeg.has_node(seed_id):
            continue
        seed_data = eeg.nodes.get(seed_id, {})
        seed_title = seed_data.get('title', seed_id)
        seed_date = seed_data.get('decision_date') or seed_data.get('date', '')
        
        # 1. Incoming citing successors (predecessors in citation direction: u -> seed means u cites seed)
        if hasattr(eeg, "predecessors"):
            preds = list(eeg.predecessors(seed_id))
            for pred in preds[:10]:
                if len(structural_context) >= max_structural_chars:
                    break
                p_data = eeg.nodes.get(pred, {})
                p_title = p_data.get('title', pred)
                p_date = p_data.get('decision_date') or p_data.get('date', '')
                p_holding = p_data.get('substantive_holding', '')
                p_text = (p_holding[:max_snippet_chars] if p_holding 
                          else p_data.get('text', '')[:max_snippet_chars]).replace('\n', ' ').strip()
                
                # STRICT ARM 4 ENFORCEMENT: Generic [CITES], never [OVERRULES] or [REPUDIATES]
                line = (
                    f"- CHRONOLOGICAL FLOW / CITING SUCCESSOR: '{p_title}' (Case ID: {pred}, Date: {p_date}) "
                    f"[CITES] this precedent (Case ID: {seed_id})."
                )
                if p_text:
                    line += f" [Holding]: {p_text}"
                structural_context += line + "\n"
        
        # 2. Outgoing cited precedents (neighbors: seed -> v means seed cites v)
        if hasattr(eeg, "neighbors"):
            succs = list(eeg.neighbors(seed_id))
            for succ in succs[:10]:
                if len(structural_context) >= max_structural_chars:
                    break
                s_data = eeg.nodes.get(succ, {})
                s_title = s_data.get('title', succ)
                s_date = s_data.get('decision_date') or s_data.get('date', '')
                s_holding = s_data.get('substantive_holding', '')
                s_text = (s_holding[:max_snippet_chars] if s_holding 
                          else s_data.get('text', '')[:max_snippet_chars]).replace('\n', ' ').strip()
                
                # STRICT ARM 4 ENFORCEMENT: Generic [CITES], never [OVERRULES] or [REPUDIATES]
                line = (
                    f"- LOGICAL RELATION / CITED PRECEDENT: This case (Case ID: {seed_id}) "
                    f"[CITES] earlier precedent '{s_title}' (Case ID: {succ}, Date: {s_date})."
                )
                if s_text:
                    line += f" [Holding]: {s_text}"
                structural_context += line + "\n"

    return structural_context

def build_arm4_generator_prompt(query: str, context: str) -> str:
    """
    Constructs the Arm 4 generation prompt stripped of oracle relation tags.
    """
    return f"""You are TERRA, an advanced legal reasoning AI. Answer the Question below accurately using ONLY the provided context data.

[QUESTION]
{query}

[CONTEXT DATA]
{context}

[INSTRUCTIONS]
1. Answer the Question directly, thoroughly, and factually based ONLY on CONTEXT DATA.
2. If CONTEXT DATA or citing cases establish that an earlier doctrine has been modified, narrowed, or superseded, your answer must explicitly explain the legal transition, state whether the historical rule remains good law, and cite the subsequent decisions.
3. Detail the legal transitions, rulings, and standards grounded strictly in the provided case text and holdings.
4. Provide a direct, substantive, and grounded legal answer.

TERRA Grounded Answer:"""
