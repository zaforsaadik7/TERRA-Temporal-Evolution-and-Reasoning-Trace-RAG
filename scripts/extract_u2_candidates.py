import json
import re
from pathlib import Path

ROOT = Path("f:/TERRA - Copy")
OUT_LOG = ROOT / "logs" / "candidates_U2.txt"

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

def main():
    log_lines = []
    log_lines.append("=" * 100)
    log_lines.append("U2 CANDIDATE SENTENCES AUDIT")
    log_lines.append("=" * 100)

    # -------------------------------------------------------------------------------------------------
    # a) 429_0363-01: every sentence containing "Bonelli" and "overrul"
    # -------------------------------------------------------------------------------------------------
    log_lines.append("\n" + "-" * 100)
    log_lines.append("a) 429_0363-01 (Oregon ex rel. State Land Board v. Corvallis Sand & Gravel Co.)")
    log_lines.append("   Condition: contains 'Bonelli' and 'overrul'")
    log_lines.append("-" * 100)

    raw_429_path = ROOT / "dataset_20k_cap" / "raw_cases" / "429_0363-01.json"
    with open(raw_429_path, "r", encoding="utf-8") as f:
        raw_429 = json.load(f)
    text_429 = raw_429["casebody"]["opinions"][0]["text"]
    sents_429 = split_into_sentences_with_offsets(text_429)

    matches_a = []
    for s, e, sent in sents_429:
        s_lower = sent.lower()
        if "bonelli" in s_lower and "overrul" in s_lower:
            assert text_429[s:e] == sent
            matches_a.append((s, e, sent))

    log_lines.append(f"Total matching sentences found: {len(matches_a)}")
    for idx, (s, e, sent) in enumerate(matches_a, 1):
        log_lines.append(f"\n[Candidate a-{idx}] Offsets: {s}:{e} (Length: {e - s})")
        log_lines.append(f"Text: \"{sent}\"")

    # -------------------------------------------------------------------------------------------------
    # b) 340_0602-01: every sentence containing "tax" and ("interstate commerce" or "Commerce Clause")
    #    and ("hold" or "invalid" or "unconstitutional" or "invalidity")
    # -------------------------------------------------------------------------------------------------
    log_lines.append("\n" + "-" * 100)
    log_lines.append("b) 340_0602-01 (Spector Motor Service, Inc. v. O'Connor)")
    log_lines.append("   Condition: contains 'tax' AND ('interstate commerce' OR 'Commerce Clause')")
    log_lines.append("              AND ('hold' OR 'invalid' OR 'unconstitutional' OR 'invalidity')")
    log_lines.append("-" * 100)

    raw_340_path = ROOT / "dataset_20k_cap" / "raw_cases" / "340_0602-01.json"
    with open(raw_340_path, "r", encoding="utf-8") as f:
        raw_340 = json.load(f)
    text_340 = raw_340["casebody"]["opinions"][0]["text"]
    sents_340 = split_into_sentences_with_offsets(text_340)

    matches_b = []
    for s, e, sent in sents_340:
        s_lower = sent.lower()
        has_tax = "tax" in s_lower
        has_comm = "interstate commerce" in s_lower or "commerce clause" in s_lower
        has_valid = any(w in s_lower for w in ["hold", "invalid", "unconstitutional", "invalidity"])
        if has_tax and has_comm and has_valid:
            assert text_340[s:e] == sent
            matches_b.append((s, e, sent))

    log_lines.append(f"Total strict matching sentences found: {len(matches_b)}")
    for idx, (s, e, sent) in enumerate(matches_b, 1):
        log_lines.append(f"\n[Candidate b-{idx}] Offsets: {s}:{e} (Length: {e - s})")
        log_lines.append(f"Text: \"{sent}\"")

    # Informative Contextual Candidates in 340_0602-01
    log_lines.append("\n" + "." * 100)
    log_lines.append("Informative Contextual Candidates in 340_0602-01 (Holding & Scope Sentences):")
    log_lines.append("." * 100)
    contextual_b_offsets = [
        (55, 521, "Issue / Attack Scope Sentence (contains 'validity', 'Commerce Clause', 'tax', 'interstate commerce')"),
        (522, 602, "Current Benchmark Target Sentence (preface holding)"),
        (2854, 3013, "Procedural Holding: District Court held application violated Commerce Clause"),
        (9953, 10118, "Substantive Doctrine: Struck down under Commerce Clause state taxes on exclusively interstate business"),
        (10119, 10237, "Substantive Rule: Constitutional infirmity persists no matter how fairly apportioned"),
        (11761, 11933, "Foundational Doctrine: Precedent keeping exclusively interstate commerce free from state taxation")
    ]
    for s, e, desc in contextual_b_offsets:
        sent = text_340[s:e]
        log_lines.append(f"\n[Contextual b] Offsets: {s}:{e} ({desc})")
        log_lines.append(f"Text: \"{sent}\"")

    # -------------------------------------------------------------------------------------------------
    # c) 423_0276-01 and 364_0206-01: current benchmark overruling sentence plus 3 sentences before it
    # -------------------------------------------------------------------------------------------------
    log_lines.append("\n" + "-" * 100)
    log_lines.append("c) Preceding Sentences Audit for OBS_011 and OBS_015 Overruling Slices")
    log_lines.append("-" * 100)

    bench_path = ROOT / "data" / "obscure_overruled_benchmark.json"
    with open(bench_path, "r", encoding="utf-8") as f:
        bench = json.load(f)

    # OBS_011: 423_0276-01 (Michelin Tire Corp. v. Wages)
    obs011 = [x for x in bench if x["query_id"] == "OBS_011"][0]
    ovr_011_data = obs011["grounding_overruling_sentence"]
    ovr_011_sent = ovr_011_data["sentence"]
    ovr_011_s = ovr_011_data["char_start"]
    ovr_011_e = ovr_011_data["char_end"]

    raw_423_path = ROOT / "dataset_20k_cap" / "raw_cases" / "423_0276-01.json"
    with open(raw_423_path, "r", encoding="utf-8") as f:
        raw_423 = json.load(f)
    text_423 = raw_423["casebody"]["opinions"][0]["text"]
    sents_423 = split_into_sentences_with_offsets(text_423)

    assert text_423[ovr_011_s:ovr_011_e] == ovr_011_sent, "OBS_011 slice mismatch"

    idx_011 = None
    for i, (s, e, sent) in enumerate(sents_423):
        if s == ovr_011_s and e == ovr_011_e:
            idx_011 = i
            break
        elif ovr_011_s >= s and ovr_011_e <= e:
            idx_011 = i
            break

    log_lines.append("\n[c-1] 423_0276-01 (OBS_011: Michelin Tire Corp. v. Wages)")
    log_lines.append(f"Current Benchmark Overruling Sentence (Index in Splitter: {idx_011}):")
    log_lines.append(f"  Offsets: {ovr_011_s}:{ovr_011_e}")
    log_lines.append(f"  Text: \"{ovr_011_sent}\"")
    log_lines.append("Preceding 3 sentences:")

    start_idx_011 = max(0, idx_011 - 3) if idx_011 is not None else 0
    prec_011 = sents_423[start_idx_011:idx_011]
    for offset_back, (s, e, sent) in enumerate(prec_011, 1):
        num_back = len(prec_011) - offset_back + 1
        assert text_423[s:e] == sent
        log_lines.append(f"  [Sentence -{num_back}] Offsets: {s}:{e} (Length: {e - s})")
        log_lines.append(f"  Text: \"{sent}\"")

    if prec_011:
        comb_s_011 = prec_011[0][0]
        comb_e_011 = ovr_011_e
        comb_text_011 = text_423[comb_s_011:comb_e_011]
        log_lines.append(f"\n  [Combined Window (-3 to Current)] Offsets: {comb_s_011}:{comb_e_011}")
        log_lines.append(f"  Combined Text: \"{comb_text_011}\"")

    # OBS_015: 364_0206-01 (Elkins v. United States)
    obs015 = [x for x in bench if x["query_id"] == "OBS_015"][0]
    ovr_015_data = obs015["grounding_overruling_sentence"]
    ovr_015_sent = ovr_015_data["sentence"]
    ovr_015_s = ovr_015_data["char_start"]
    ovr_015_e = ovr_015_data["char_end"]

    raw_364_path = ROOT / "dataset_20k_cap" / "raw_cases" / "364_0206-01.json"
    with open(raw_364_path, "r", encoding="utf-8") as f:
        raw_364 = json.load(f)
    text_364 = raw_364["casebody"]["opinions"][0]["text"]
    sents_364 = split_into_sentences_with_offsets(text_364)

    assert text_364[ovr_015_s:ovr_015_e] == ovr_015_sent, "OBS_015 slice mismatch"

    idx_015 = None
    for i, (s, e, sent) in enumerate(sents_364):
        if s == ovr_015_s and e == ovr_015_e:
            idx_015 = i
            break
        elif ovr_015_s >= s and ovr_015_e <= e:
            idx_015 = i
            break

    log_lines.append("\n[c-2] 364_0206-01 (OBS_015: Elkins v. United States)")
    log_lines.append(f"Current Benchmark Overruling Sentence (Index in Splitter: {idx_015}):")
    log_lines.append(f"  Offsets: {ovr_015_s}:{ovr_015_e}")
    log_lines.append(f"  Text: \"{ovr_015_sent}\"")
    log_lines.append("Preceding 3 sentences:")

    start_idx_015 = max(0, idx_015 - 3) if idx_015 is not None else 0
    prec_015 = sents_364[start_idx_015:idx_015]
    for offset_back, (s, e, sent) in enumerate(prec_015, 1):
        num_back = len(prec_015) - offset_back + 1
        assert text_364[s:e] == sent
        log_lines.append(f"  [Sentence -{num_back}] Offsets: {s}:{e} (Length: {e - s})")
        log_lines.append(f"  Text: \"{sent}\"")

    if prec_015:
        comb_s_015 = prec_015[0][0]
        comb_e_015 = ovr_015_e
        comb_text_015 = text_364[comb_s_015:comb_e_015]
        log_lines.append(f"\n  [Combined Window (-3 to Current)] Offsets: {comb_s_015}:{comb_e_015}")
        log_lines.append(f"  Combined Text: \"{comb_text_015}\"")

    log_lines.append("\n" + "=" * 100)
    log_lines.append("END OF CANDIDATES AUDIT (NO EDITS APPLIED PER U2)")
    log_lines.append("=" * 100)

    OUT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n")

    print(f"Wrote U2 candidates audit to {OUT_LOG}")

if __name__ == '__main__':
    main()
