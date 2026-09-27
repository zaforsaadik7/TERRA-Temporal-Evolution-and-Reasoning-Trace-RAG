"""
scripts/extract_w2_candidates.py - Generate logs/candidates_W2.txt
================================================================
Task W2 requirements (list only, NO edits):
 a) 437_0001-01 (Burks): every sentence containing "Forman" or "Bryan"; plus the 3 sentences before offset 26395.
 b) 383_0663-01 (Harper): the 4 sentences before offset 6302.
 c) 419_0522-01 (Taylor): every sentence containing "Hoyt"; plus the 3 sentences before offset 18028.
Uses the verifier's sentence splitter with exact offsets. Asserts text[s:e] == sentence.
"""

import json
import re
from pathlib import Path

ROOT = Path(".")
OUT_LOG = ROOT / "logs" / "candidates_W2.txt"

ABBREVIATIONS = {
    'u. s', 'u.s', 'v', 'vs', 'co', 'inc', 'ltd', 'no', 'nos', 'mr', 'mrs', 'ms',
    'justice', 'justices', 'al', 'supra', 'infra', 'id', 'ibid', 'st', 'cir', 'f',
    'fed', 'app', 'd', 'c', 'conn', 'supp', 'pa', 'art', 'sec', 'cl', 'stat', 'ct',
    'wheat', 'how', 'wall', 'pet', 'resp', 'cert', 'jan', 'feb', 'mar', 'apr', 'jun',
    'jul', 'aug', 'sept', 'oct', 'nov', 'dec', 'mass', 'wash', 'mich', 'cal', 'tex',
    'ill', 'ohio', 'seq', 'viz', 'e.g', 'i.e', 'etc'
}

def is_abbreviation(text_before_punct: str) -> bool:
    words = text_before_punct.strip().split()
    if not words:
        return False
    last_word = words[-1].lower().rstrip('.!?')
    if last_word in ABBREVIATIONS:
        return True
    if len(last_word) == 1 and last_word.isalpha():
        return True
    if len(words) >= 2:
        last_two = f"{words[-2]} {words[-1]}".lower().rstrip('.!?')
        if last_two in ABBREVIATIONS:
            return True
    return False

def split_into_sentences_with_offsets(text: str):
    boundary_regex = re.compile(
        r'([.!?])(["\'\u201c\u201d\u2018\u2019)\]]*)(?:\s+(?=[A-Z\u201c"\'\(\[\d])|[\n\r]+|\Z)'
    )
    
    sentences = []
    curr_start = 0
    
    for match in boundary_regex.finditer(text):
        punct = match.group(1)
        punct_pos = match.start(1)
        closing_quotes = match.group(2)
        end_pos = match.end(2) if closing_quotes else match.end(1)
        
        slice_before = text[curr_start:punct_pos]
        if punct == '.' and is_abbreviation(slice_before):
            continue
            
        raw_slice = text[curr_start:end_pos]
        stripped = raw_slice.strip()
        if stripped:
            s_offset = text.find(stripped, curr_start)
            e_offset = s_offset + len(stripped)
            assert text[s_offset:e_offset] == stripped
            sentences.append((s_offset, e_offset, stripped))
        curr_start = end_pos
        
    if curr_start < len(text):
        stripped = text[curr_start:].strip()
        if stripped:
            s_offset = text.find(stripped, curr_start)
            e_offset = s_offset + len(stripped)
            assert text[s_offset:e_offset] == stripped
            sentences.append((s_offset, e_offset, stripped))
            
    return sentences

def load_case_text(case_id: str) -> str:
    path = ROOT / "dataset_20k_cap" / "raw_cases" / f"{case_id}.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["casebody"]["opinions"][0]["text"]

def main():
    log_lines = []
    log_lines.append("=" * 110)
    log_lines.append("W2 CANDIDATE SENTENCES AUDIT: RAW CAP CORPUS SENTENCE EXTRACTIONS")
    log_lines.append("Splitter: Verifier rule-based sentence tokenizer with abbreviation safeguard and offset assertions")
    log_lines.append("=" * 110)

    # -------------------------------------------------------------------------
    # PART A: 437_0001-01 (Burks v. United States)
    # -------------------------------------------------------------------------
    text_burks = load_case_text("437_0001-01")
    sents_burks = split_into_sentences_with_offsets(text_burks)
    log_lines.append("\n" + "=" * 110)
    log_lines.append("PART A: 437_0001-01 (Burks v. United States)")
    log_lines.append("Query Requirements: Every sentence containing 'Forman' or 'Bryan', plus 3 sentences before offset 26395")
    log_lines.append(f"Total sentences in opinion: {len(sents_burks)}")
    log_lines.append("=" * 110)

    # Find target sentence at 26395
    target_burks_idx = None
    for idx, (s, e, sent) in enumerate(sents_burks):
        if s <= 26395 < e or s == 26395:
            target_burks_idx = idx
            break
    assert target_burks_idx is not None, "Target offset 26395 not found in Burks sentences"

    # Sentences containing "Forman" or "Bryan"
    name_indices_burks = []
    for idx, (s, e, sent) in enumerate(sents_burks):
        if "Forman" in sent or "Bryan" in sent:
            name_indices_burks.append(idx)

    # 3 sentences before 26395: target_burks_idx - 3, -2, -1
    preceding_burks_indices = [target_burks_idx - 3, target_burks_idx - 2, target_burks_idx - 1]

    # Combine and sort
    all_burks_indices = sorted(list(set(name_indices_burks + preceding_burks_indices + [target_burks_idx])))

    for idx in all_burks_indices:
        s, e, sent = sents_burks[idx]
        assert text_burks[s:e] == sent
        tags = []
        if "Forman" in sent:
            tags.append("Contains 'Forman'")
        if "Bryan" in sent:
            tags.append("Contains 'Bryan'")
        if idx in preceding_burks_indices:
            tags.append(f"Preceding offset 26395 #{idx - target_burks_idx}")
        if idx == target_burks_idx:
            tags.append("TARGET OVERRULING SENTENCE (offset 26395)")
            
        log_lines.append(f"\n[Sentence #{idx}] Offsets: {s}:{e} (Length: {len(sent)}) | {', '.join(tags)}")
        log_lines.append(f"Text: {repr(sent)}")

    # -------------------------------------------------------------------------
    # PART B: 383_0663-01 (Harper v. Virginia Board of Elections)
    # -------------------------------------------------------------------------
    text_harper = load_case_text("383_0663-01")
    sents_harper = split_into_sentences_with_offsets(text_harper)
    log_lines.append("\n\n" + "=" * 110)
    log_lines.append("PART B: 383_0663-01 (Harper v. Virginia Board of Elections)")
    log_lines.append("Query Requirements: The 4 sentences before offset 6302")
    log_lines.append(f"Total sentences in opinion: {len(sents_harper)}")
    log_lines.append("=" * 110)

    target_harper_idx = None
    for idx, (s, e, sent) in enumerate(sents_harper):
        if s <= 6302 < e or s == 6302:
            target_harper_idx = idx
            break
    assert target_harper_idx is not None, "Target offset 6302 not found in Harper sentences"

    # 4 sentences before offset 6302: target_harper_idx - 4, -3, -2, -1
    harper_indices = [target_harper_idx - 4, target_harper_idx - 3, target_harper_idx - 2, target_harper_idx - 1, target_harper_idx]

    for idx in harper_indices:
        s, e, sent = sents_harper[idx]
        assert text_harper[s:e] == sent
        tag = f"Preceding offset 6302 #{idx - target_harper_idx}" if idx < target_harper_idx else "TARGET OVERRULING SENTENCE (offset 6302)"
        log_lines.append(f"\n[Sentence #{idx}] Offsets: {s}:{e} (Length: {len(sent)}) | {tag}")
        log_lines.append(f"Text: {repr(sent)}")

    # -------------------------------------------------------------------------
    # PART C: 419_0522-01 (Taylor v. Louisiana)
    # -------------------------------------------------------------------------
    text_taylor = load_case_text("419_0522-01")
    sents_taylor = split_into_sentences_with_offsets(text_taylor)
    log_lines.append("\n\n" + "=" * 110)
    log_lines.append("PART C: 419_0522-01 (Taylor v. Louisiana)")
    log_lines.append("Query Requirements: Every sentence containing 'Hoyt', plus 3 sentences before offset 18028")
    log_lines.append(f"Total sentences in opinion: {len(sents_taylor)}")
    log_lines.append("=" * 110)

    target_taylor_idx = None
    for idx, (s, e, sent) in enumerate(sents_taylor):
        if s <= 18028 < e or s == 18028:
            target_taylor_idx = idx
            break
    assert target_taylor_idx is not None, "Target offset 18028 not found in Taylor sentences"

    # Sentences containing "Hoyt"
    hoyt_indices = []
    for idx, (s, e, sent) in enumerate(sents_taylor):
        if "Hoyt" in sent:
            hoyt_indices.append(idx)

    # 3 sentences before offset 18028: target_taylor_idx - 3, -2, -1
    preceding_taylor_indices = [target_taylor_idx - 3, target_taylor_idx - 2, target_taylor_idx - 1]

    all_taylor_indices = sorted(list(set(hoyt_indices + preceding_taylor_indices + [target_taylor_idx])))

    for idx in all_taylor_indices:
        s, e, sent = sents_taylor[idx]
        assert text_taylor[s:e] == sent
        tags = []
        if "Hoyt" in sent:
            tags.append("Contains 'Hoyt'")
        if idx in preceding_taylor_indices:
            tags.append(f"Preceding offset 18028 #{idx - target_taylor_idx}")
        if idx == target_taylor_idx:
            tags.append("TARGET OVERRULING SENTENCE (offset 18028)")
            
        log_lines.append(f"\n[Sentence #{idx}] Offsets: {s}:{e} (Length: {len(sent)}) | {', '.join(tags)}")
        log_lines.append(f"Text: {repr(sent)}")

    # Write output log
    OUT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n")
    print(f"Wrote W2 candidates to {OUT_LOG}")

if __name__ == "__main__":
    main()
