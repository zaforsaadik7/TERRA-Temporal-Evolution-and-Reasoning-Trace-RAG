import json
import re
from pathlib import Path

ROOT = Path("f:/TERRA - Copy")
OUT_LOG = ROOT / "logs" / "candidates_V3.txt"
CASE_PATH = ROOT / "dataset_20k_cap" / "raw_cases" / "340_0602-01.json"

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

with open(CASE_PATH, "r", encoding="utf-8") as f:
    case_data = json.load(f)

text = case_data["casebody"]["opinions"][0]["text"]
sentences = split_into_sentences_with_offsets(text)

TARGET_START = 9800
TARGET_END = 10400

# Find sentences overlapping 9800:10400
overlapping_indices = []
for idx, (s, e, s_text) in enumerate(sentences):
    if s < TARGET_END and e > TARGET_START:
        overlapping_indices.append(idx)

assert overlapping_indices, "No overlapping sentences found in range 9800-10400"
min_idx = min(overlapping_indices)
max_idx = max(overlapping_indices)

start_idx = max(0, min_idx - 2)
end_idx = min(len(sentences), max_idx + 3)

log_lines = []
log_lines.append("=" * 110)
log_lines.append("V3 CANDIDATE SENTENCES AUDIT: 340_0602-01 (Spector Motor Service, Inc. v. O'Connor)")
log_lines.append("Target Range: chars 9800 to 10400 (plus 2 sentences before and 2 after)")
log_lines.append("=" * 110)
log_lines.append(f"Total sentences in opinion: {len(sentences)}")
log_lines.append(f"Overlapping sentences indices: {overlapping_indices} (from sentence #{min_idx} to #{max_idx})")
log_lines.append(f"Expanded audit window: sentence #{start_idx} to #{end_idx - 1} (inclusive)")
log_lines.append("-" * 110)

for idx in range(start_idx, end_idx):
    s, e, sent_text = sentences[idx]
    assert text[s:e] == sent_text
    assert sent_text in text
    
    relation_to_range = []
    if idx < min_idx:
        relation_to_range.append(f"Preceding sentence #{idx - min_idx}")
    elif idx > max_idx:
        relation_to_range.append(f"Subsequent sentence +{idx - max_idx}")
    else:
        relation_to_range.append("Overlapping target range 9800-10400")
        
    log_lines.append(f"\n[Sentence #{idx}] Offsets: {s}:{e} (Length: {len(sent_text)}) | {', '.join(relation_to_range)}")
    log_lines.append(f"Text: {repr(sent_text)}")

log_lines.append("\n" + "=" * 110)
log_lines.append("RAW OPINION TEXT SLICE (9600:10600) FOR CONTEXT:")
log_lines.append("-" * 110)
log_lines.append(text[9600:10600])
log_lines.append("=" * 110)

OUT_LOG.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_LOG, "w", encoding="utf-8") as f:
    f.write("\n".join(log_lines) + "\n")

print(f"Wrote V3 candidates to {OUT_LOG}")
