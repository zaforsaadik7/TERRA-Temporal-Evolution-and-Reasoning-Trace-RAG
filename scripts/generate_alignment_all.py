"""Generate logs/query_gold_alignment_all.txt for all 30 benchmark items.
Fields: query_id, query, gold_holding, target sentence, overruling sentence, scope_class.
All read directly from data/obscure_overruled_benchmark.json. No edits, no commentary.
"""
import json
from pathlib import Path

def main():
    bench_path = Path("data/obscure_overruled_benchmark.json")
    with open(bench_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    out_path = Path("logs/query_gold_alignment_all.txt")
    lines = []
    
    for i, item in enumerate(data):
        qid = item.get("query_id")
        query = item.get("query")
        gold_holding = item.get("gold_holding")
        target_sentence = item.get("grounding_target_holding", {}).get("sentence")
        overruling_sentence = item.get("grounding_overruling_sentence", {}).get("sentence")
        scope_class = item.get("scope_classification")
        
        lines.append(f"query_id: {qid}")
        lines.append(f"query: {query}")
        lines.append(f"gold_holding: {gold_holding}")
        lines.append(f"target sentence: {target_sentence}")
        lines.append(f"overruling sentence: {overruling_sentence}")
        lines.append(f"scope_class: {scope_class}")
        if i < len(data) - 1:
            lines.append("")

    content = "\n".join(lines) + "\n"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Wrote {len(data)} items to {out_path}")

if __name__ == "__main__":
    main()
