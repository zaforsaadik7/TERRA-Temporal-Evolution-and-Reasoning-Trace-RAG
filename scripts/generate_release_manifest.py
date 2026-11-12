#!/usr/bin/env python3
"""
Generate Release Manifest v1.0 and Data Licensing Documentation for TERRA.
Computes cryptographic SHA-256 checksums and exact byte sizes for all released artifacts.
"""

import os
import json
import hashlib
from datetime import datetime

ROOT_DIR = r"f:\TERRA"

ARTIFACT_DEFINITIONS = [
    # 1. Source Data
    {
        "id": "scotus_20k_raw_opinions",
        "category": "Source Data (External Corpus)",
        "path": r"scratch\scotus_20k_opinions.zip",
        "archive_target_path": "corpus_20k_scotus/scotus_20k_opinions.zip",
        "description": "Full-text substantive SCOTUS judicial opinions (1850-1980, Volumes 50-448), filtered char_count >= 4,000, 0 cert denials.",
        "source": "CourtListener (Free Law Project) and Harvard Caselaw Access Project (CAP)",
        "license": "Public Domain (17 U.S.C. § 105)",
        "attribution_terms": "Federal judicial decisions are public domain under 17 U.S.C. § 105. Attribution to Free Law Project (CourtListener API) and Harvard Library Innovation Lab.",
        "rights_status": "Resolved (Public Domain / Free Access)"
    },
    # 2. Benchmark
    {
        "id": "terra_350_benchmark",
        "category": "Benchmark (Team-Created Derivative)",
        "path": r"terra_350_benchmark.json",
        "archive_target_path": "benchmark/terra_350_benchmark.json",
        "description": "Canonical 350-query legal evaluation benchmark across 7 domains: 100 Category A (factual), 100 Category B (multi-hop 3-5 hops), 75 Category C (refusal/OOD), 75 Category D (adversarial precedent traps).",
        "source": "TERRA Research Team (Hand-crafted & certified)",
        "license": "Creative Commons Attribution 4.0 International (CC-BY 4.0)",
        "attribution_terms": "Cite TERRA Research Manuscript (2026). Free for research, educational, and commercial use with attribution.",
        "rights_status": "Resolved (Original Work)"
    },
    # 3. Graphs
    {
        "id": "terra_eeg_index_20k",
        "category": "Precedent Graph Index (Team-Created Derivative)",
        "path": r"dataset_20k_cap\terra_eeg_index_20k.json",
        "archive_target_path": "graph/terra_eeg_index_20k.json",
        "description": "Expanded Event Evolution Graph (EEG) covering 20,000 pure substantive opinions and 145,363 directed citation edges with temporal validities.",
        "source": "Constructed by TERRA pipeline from SCOTUS corpus",
        "license": "Creative Commons Attribution 4.0 International (CC-BY 4.0)",
        "attribution_terms": "Cite TERRA Research Manuscript (2026). Free for research, educational, and commercial use with attribution.",
        "rights_status": "Resolved (Original Work)"
    },
    {
        "id": "terra_eeg_index_10k",
        "category": "Precedent Graph Index (Team-Created Derivative)",
        "path": r"dataset_10k_cap\terra_eeg_index_10k.json",
        "archive_target_path": "graph/terra_eeg_index_10k.json",
        "description": "Baseline Event Evolution Graph (EEG) covering 10,009 cases and 37,918 citation edges (pilot scale).",
        "source": "Constructed by TERRA pipeline from SCOTUS corpus",
        "license": "Creative Commons Attribution 4.0 International (CC-BY 4.0)",
        "attribution_terms": "Cite TERRA Research Manuscript (2026).",
        "rights_status": "Resolved (Original Work)"
    },
    # 4. Manifests
    {
        "id": "selection_manifest_20k",
        "category": "Curation Manifest (Team-Created Derivative)",
        "path": r"dataset_20k_cap\manifests\selection_manifest_20k.json",
        "archive_target_path": "manifests/selection_manifest_20k.json",
        "description": "Selection and validation manifest for 20,000 substantive cases, including character counts, date validation, and domain taxonomy tags.",
        "source": "TERRA Curation Pipeline",
        "license": "Creative Commons Attribution 4.0 International (CC-BY 4.0)",
        "attribution_terms": "Cite TERRA Research Manuscript (2026).",
        "rights_status": "Resolved (Original Work)"
    },
    {
        "id": "selection_manifest_10k",
        "category": "Curation Manifest (Team-Created Derivative)",
        "path": r"dataset_10k_cap\manifests\selection_manifest.json",
        "archive_target_path": "manifests/selection_manifest_10k.json",
        "description": "Pilot selection manifest for 10,009 cases.",
        "source": "TERRA Curation Pipeline",
        "license": "Creative Commons Attribution 4.0 International (CC-BY 4.0)",
        "attribution_terms": "Cite TERRA Research Manuscript (2026).",
        "rights_status": "Resolved (Original Work)"
    },
    # 5. Evaluation Records
    {
        "id": "terra_expanded_eval_raw",
        "category": "Evaluation Records (Team-Created Derivative)",
        "path": r"terra_expanded_eval_raw.json",
        "archive_target_path": "evaluations/terra_expanded_eval_raw.json",
        "description": "Canonical LLM-as-judge evaluation records for 140 queries across 3 runs (1,260 evaluations), with per-metric Likert scores, timings, and token audits.",
        "source": "TERRA Evaluation Harness (LLaMA 3.3 70B & Qwen 235B Judges)",
        "license": "Creative Commons Attribution 4.0 International (CC-BY 4.0)",
        "attribution_terms": "Cite TERRA Research Manuscript (2026).",
        "rights_status": "Resolved (Original Work)"
    },
    {
        "id": "terra_expanded_generations",
        "category": "Telemetry & Generations (Team-Created Derivative)",
        "path": r"terra_expanded_generations.json",
        "archive_target_path": "evaluations/terra_expanded_generations.json",
        "description": "Raw generation texts, context windows, retrieved citation chains, and router execution logs for 1,260 pipeline executions.",
        "source": "TERRA Generation Harness",
        "license": "Creative Commons Attribution 4.0 International (CC-BY 4.0)",
        "attribution_terms": "Cite TERRA Research Manuscript (2026).",
        "rights_status": "Resolved (Original Work)"
    },
    {
        "id": "terra_true_ablation_pilot_raw",
        "category": "Evaluation Records (Team-Created Derivative)",
        "path": r"terra_true_ablation_pilot_raw.json",
        "archive_target_path": "evaluations/terra_true_ablation_pilot_raw.json",
        "description": "True component ablation study records (Full TERRA, w/o EEG, w/o NLI, w/o Router) across 35 queries x 4 configs x 5 runs (700 evaluations).",
        "source": "TERRA Ablation Harness",
        "license": "Creative Commons Attribution 4.0 International (CC-BY 4.0)",
        "attribution_terms": "Cite TERRA Research Manuscript (2026).",
        "rights_status": "Resolved (Original Work)"
    },
    {
        "id": "terra_true_ablation_pilot_generations",
        "category": "Telemetry & Generations (Team-Created Derivative)",
        "path": r"terra_true_ablation_pilot_generations.json",
        "archive_target_path": "evaluations/terra_true_ablation_pilot_generations.json",
        "description": "Complete raw texts, retrieved contexts, and stage latencies for 700 ablation runs.",
        "source": "TERRA Ablation Harness",
        "license": "Creative Commons Attribution 4.0 International (CC-BY 4.0)",
        "attribution_terms": "Cite TERRA Research Manuscript (2026).",
        "rights_status": "Resolved (Original Work)"
    },
    {
        "id": "terra_baselines_eval_raw",
        "category": "Evaluation Records (Team-Created Derivative)",
        "path": r"terra_baselines_eval_raw.json",
        "archive_target_path": "evaluations/terra_baselines_eval_raw.json",
        "description": "Comparative baseline evaluations across TERRA, GraphRAG-Adapted, HippoRAG-Adapted, Flat Vector RAG, and Direct LLM on the 350-query benchmark.",
        "source": "TERRA Comparative Baselines Harness",
        "license": "Creative Commons Attribution 4.0 International (CC-BY 4.0)",
        "attribution_terms": "Cite TERRA Research Manuscript (2026).",
        "rights_status": "Resolved (Original Work)"
    }
]

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()

def main():
    print("Computing cryptographic SHA-256 checksums and building release manifest...")
    manifest_records = []
    
    for item in ARTIFACT_DEFINITIONS:
        full_path = os.path.join(ROOT_DIR, item["path"])
        if not os.path.exists(full_path):
            print(f"WAITING: {item['path']} does not exist yet (may still be compiling/zipping).")
            return False
        
        sz = os.path.getsize(full_path)
        print(f"Hashing {item['id']} ({sz / (1024*1024):.2f} MB)...")
        sha = compute_sha256(full_path)
        
        record = {
            "id": item["id"],
            "category": item["category"],
            "relative_path": item["path"],
            "archive_target_path": item["archive_target_path"],
            "size_bytes": sz,
            "size_mb": round(sz / (1024 * 1024), 2),
            "sha256": sha,
            "description": item["description"],
            "source": item["source"],
            "license": item["license"],
            "attribution_terms": item["attribution_terms"],
            "rights_status": item["rights_status"]
        }
        manifest_records.append(record)

    output = {
        "manifest_version": "1.0.0",
        "release_tag": "v1.0.0",
        "release_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "project_name": "TERRA: Temporal Evolution and Reasoning-Trace RAG",
        "github_repository": "https://github.com/zaforsaadik7/TERRA-Temporal-Evolution-and-Reasoning-Trace-RAG",
        "stable_release_url": "https://github.com/zaforsaadik7/TERRA-Temporal-Evolution-and-Reasoning-Trace-RAG/releases/tag/v1.0.0",
        "kaggle_dataset_url": "https://www.kaggle.com/datasets/zaforsaadik/terra-scotus-legal-benchmark",
        "total_artifacts": len(manifest_records),
        "total_size_bytes": sum(r["size_bytes"] for r in manifest_records),
        "total_size_gb": round(sum(r["size_bytes"] for r in manifest_records) / (1024**3), 3),
        "artifacts": manifest_records
    }

    # Write JSON manifest
    json_path = os.path.join(ROOT_DIR, "RELEASE_MANIFEST_v1.0.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    print(f"Wrote {json_path}")

    # Write Markdown manifest
    md_path = os.path.join(ROOT_DIR, "RELEASE_MANIFEST_v1.0.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# TERRA Research Release Manifest v1.0.0\n\n")
        f.write(f"**Release Date:** {output['release_date']}  \n")
        f.write(f"**Release Tag:** `v1.0.0`  \n")
        f.write(f"**Kaggle Dataset Archive:** [{output['kaggle_dataset_url']}]({output['kaggle_dataset_url']})  \n")
        f.write(f"**GitHub Release Tag:** [{output['stable_release_url']}]({output['stable_release_url']})  \n")
        f.write(f"**Total Released Volume:** {output['total_size_gb']} GB across {output['total_artifacts']} canonical artifacts\n\n")
        f.write("---\n\n")
        f.write("## 1. Verified Cryptographic Checksums & Artifact Catalog\n\n")
        f.write("| Artifact ID | Category | Archive Path | Size (MB) | SHA-256 Checksum | License |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- | :--- |\n")
        for r in manifest_records:
            f.write(f"| `{r['id']}` | {r['category']} | `{r['archive_target_path']}` | {r['size_mb']} MB | `{r['sha256']}` | {r['license']} |\n")
        f.write("\n---\n\n")
        f.write("## 2. Licensing and Attribution Framework\n\n")
        f.write("### A. Public Domain Source Material (U.S. Federal Opinions)\n")
        f.write("- **Artifact:** `corpus_20k_scotus/scotus_20k_opinions.zip`\n")
        f.write("- **Legal Status:** Under 17 U.S.C. § 105, works of the United States Government, including Supreme Court judicial opinions, are in the public domain and free of copyright restrictions.\n")
        f.write("- **Source Attribution:** Harvested and cross-verified via the open APIs of **CourtListener (Free Law Project)** (https://www.courtlistener.com) and the **Harvard Caselaw Access Project (CAP)** (https://case.law).\n\n")
        f.write("### B. Team-Created Derivatives (Benchmarks, Graphs, and Evaluations)\n")
        f.write("- **Artifacts:** `terra_350_benchmark.json`, `terra_eeg_index_20k.json`, selection manifests, and all raw evaluation/telemetry logs.\n")
        f.write("- **License:** Creative Commons Attribution 4.0 International (CC-BY 4.0).\n")
        f.write("- **Attribution Requirement:** Users must cite the TERRA Research Paper: *TERRA: Temporal Evolution and Reasoning-Trace RAG for Non-Stationary Legal Precedent* (2026).\n\n")
        f.write("### C. Software Codebase\n")
        f.write("- **License:** MIT License for all execution engines, baseline runners, router classifiers, and evaluation scripts.\n")

    print(f"Wrote {md_path}")
    return True

if __name__ == "__main__":
    main()

