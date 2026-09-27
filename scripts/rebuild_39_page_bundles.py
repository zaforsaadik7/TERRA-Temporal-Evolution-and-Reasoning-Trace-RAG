import hashlib
import json
import os
import shutil
import subprocess
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

OVERLEAF = [
    'main.tex', 'ref.bib', 'generated_stats.tex', 'generated_obscure_stats.tex',
    'generated_corpus_stats_20k.tex', 'figure_1_system_architecture.tex',
    'figure_2_hub_centrality.tex', 'figure_3_safety_rejection.tex',
    'tables/table_sensitivity_raw_vs_clamped.tex', 'tables/table_refusal_breakdown.tex',
    'tables/table_full_fdr_family.tex', 'tables/table_system_comparison.tex',
    'tables/table_temporal_leakage_probe.tex', 'tables/table_casefacts_eval.tex',
    'tables/table_clerc_eval.tex', 'tables/table_retrieval_eval.tex',
    'tables/table_computational_budget.tex', 'tables/table_router_eval.tex',
    'tables/table_citation_eval.tex', 'tables/table_obscure_overruled_eval.tex',
    'tables/table_temporal_update_stability.tex', 'tables/table_baseline_specifications.tex',
]

REPRO = [
    ('Paper/main.pdf', 'main.pdf'), ('Paper/main.tex', 'main.tex'),
    ('Paper/main.bbl', 'main.bbl'), ('Paper/ref.bib', 'ref.bib'),
    ('Paper/generated_stats.tex', 'generated_stats.tex'),
    ('Paper/generated_obscure_stats.tex', 'generated_obscure_stats.tex'),
    ('Paper/generated_corpus_stats_20k.tex', 'generated_corpus_stats_20k.tex'),
    ('Paper/figure_1_system_architecture.tex', 'figure_1_system_architecture.tex'),
    ('Paper/figure_2_hub_centrality.tex', 'figure_2_hub_centrality.tex'),
    ('Paper/figure_3_safety_rejection.tex', 'figure_3_safety_rejection.tex'),
    *[(f'Paper/{p}', p) for p in OVERLEAF[8:]],
    ('Paper/scripts/check_consistency.py', 'scripts/check_consistency.py'),
    ('Paper/scripts/generate_stats.py', 'scripts/generate_stats.py'),
    ('Paper/scripts/allowed_literals.txt', 'scripts/allowed_literals.txt'),
    ('scripts/rebuild_issue43_bundles.py', 'scripts/rebuild_issue43_bundles.py'),
    ('scripts/rebuild_39_page_bundles.py', 'scripts/rebuild_39_page_bundles.py'),
    ('ask_terra.py', 'ask_terra.py'), ('eval_terra.py', 'eval_terra.py'),
    ('scripts/ingest_20k_eeg_and_vector_db.py', 'scripts/ingest_20k_eeg_and_vector_db.py'),
    ('prompts/router_system_prompt.txt', 'prompts/router_system_prompt.txt'),
    ('prompts/fast_path_prompt.txt', 'prompts/fast_path_prompt.txt'),
    ('prompts/generator_system_prompt.txt', 'prompts/generator_system_prompt.txt'),
    ('prompts/nli_grader_prompt.txt', 'prompts/nli_grader_prompt.txt'),
    ('prompts/dual_judge_prompt.txt', 'prompts/dual_judge_prompt.txt'),
    ('configs/terra_config.json', 'configs/terra_config.json'),
    ('terra_350_benchmark.json', 'terra_350_benchmark.json'),
    ('dataset_20k_cap/terra_eeg_index_20k.json', 'dataset_20k_cap/terra_eeg_index_20k.json'),
    ('data/terra_eeg_edges_145k.tsv', 'data/terra_eeg_edges_145k.tsv'),
    ('data/doctrine_invalidation_pairs_19.json', 'data/doctrine_invalidation_pairs_19.json'),
    ('data/terra_canonical_v2_eval.json', 'data/terra_canonical_v2_eval.json'),
    ('data/obscure_overruled_benchmark.json', 'data/obscure_overruled_benchmark.json'),
    ('data/casefacts_eval_120.json', 'data/casefacts_eval_120.json'),
    ('data/casefacts_refusal_control_50.json', 'data/casefacts_refusal_control_50.json'),
    ('data/clerc_eval_120.json', 'data/clerc_eval_120.json'),
    ('data/clerc_refusal_control_50.json', 'data/clerc_refusal_control_50.json'),
    ('data/casehold_nli_eval_200.json', 'data/casehold_nli_eval_200.json'),
    ('data/terra_eeg_nli_eval_200.json', 'data/terra_eeg_nli_eval_200.json'),
    ('logs/issue43_closeout.txt', 'logs/issue43_closeout.txt'),
    ('logs/issue40_39page_closeout.txt', 'logs/issue40_39page_closeout.txt'),
]

def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()

def zip_files(out, files):
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for src, arc in files:
            z.write(src, arc)

def main():
    os.environ['SOURCE_DATE_EPOCH'] = '1780000000'
    ci = subprocess.run(['venv/Scripts/python.exe', 'Paper/scripts/check_consistency.py', '--target', 'Paper/'], text=True)
    if ci.returncode:
        raise SystemExit(ci.returncode)
    import fitz
    doc = fitz.open('Paper/main.pdf')
    assert len(doc) == 39, f'Expected 39 pages, got {len(doc)}'
    assert 'Appendix A' in doc[36].get_text()
    assert 'TABLE XXIII' in doc[37].get_text() and all(str(i) in doc[37].get_text() for i in range(1, 21))
    assert 'References' in doc[38].get_text() and '[27]' in doc[38].get_text()
    bad = [(i + 1, b[:4]) for i, p in enumerate(doc) for b in p.get_text('blocks') if b[1] < 0 or b[3] > 792 or b[0] < 0 or b[2] > 612]
    assert not bad, bad
    zip_files('Paper/overleaf_bundle.zip', [(f'Paper/{p}', p) for p in OVERLEAF])
    shutil.copyfile('Paper/overleaf_bundle.zip', 'TERRA_Overleaf_Bundle.zip')
    with open('logs/issue40_39page_closeout.txt', 'w', encoding='utf-8') as f:
        f.write('Issue #40 corrected closeout: 39-page canonical layout.\n')
        f.write('Appendix A precedes Table XXIII; Table XXIII precedes References.\n')
        f.write(f'Paper/main.pdf SHA256: {sha256("Paper/main.pdf")}\n')
        f.write('Geometry: 39 pages; zero out-of-page text blocks.\n')
    manifest = {
        'page_budget_invariant': 39,
        'appendix_table_page': 38,
        'references_page': 39,
        'files': [{'path': s, 'archive_path': a, 'sha256': sha256(s), 'bytes': os.path.getsize(s)} for s, a in REPRO],
    }
    manifest['files'] = [{'path': s, 'archive_path': a, 'sha256': sha256(s), 'bytes': os.path.getsize(s)} for s, a in REPRO]
    with open('logs/issue40_39page_reproducibility_manifest.json', 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    zip_files('TERRA_Reproducibility_Bundle.zip', REPRO + [('logs/issue40_39page_reproducibility_manifest.json', 'logs/issue40_39page_reproducibility_manifest.json')])
    print('PASS: 39-page PDF, appendix/table/reference order, CI, and bundles verified.')
    print('overleaf_sha256', sha256('Paper/overleaf_bundle.zip'))
    print('repro_sha256', sha256('TERRA_Reproducibility_Bundle.zip'))

if __name__ == '__main__':
    main()
