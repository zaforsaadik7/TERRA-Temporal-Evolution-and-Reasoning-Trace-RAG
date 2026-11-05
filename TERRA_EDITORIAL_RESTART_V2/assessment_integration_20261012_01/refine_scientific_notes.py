from pathlib import Path
src=Path(__file__).parent/'candidate_src'
p=src/'supplement_tables/table_full_fdr_family.tex'
t=p.read_text(encoding='utf-8')
t=t.replace(r'\fontsize{6.5pt}{7.2pt}\selectfont',r'\footnotesize')
a=t.index('Ranks 5--7 indicate'); b=t.index('\n',a)
t=t[:a]+r'''The sign of $\Delta$ and the significance column identify the direction of each comparison; these observational contrasts do not isolate an architectural cause. Category D continuous faithfulness comparisons occupy ranks 6, 13, 16 and 17, and are distinct from the eight-test Holm-adjusted secondary family of discrete refusals and safe handling in the main paper. Confidence intervals in rows 2, 6 and 12--17 retain historical bootstrap values whose original resampling settings could not be verified; these intervals are not independently reproduced.'''+t[b:]
p.write_text(t,encoding='utf-8')
p=src/'supplement_tables/table_temporal_leakage_probe.tex'
t=p.read_text(encoding='utf-8')
t=t.replace('Preregistered Paired Hypothesis Tests','Exploratory Paired Contrasts')
t=t.replace(r'\textbf{Supported}: $+38.0\%$ Legal Accuracy',r'$+38.0\%$ automated HLCR label difference')
t=t.replace('Full $N=50$ bounds add bounded missing-pair contributions', 'The reported full $N=50$ sensitivity envelopes add extreme missing-pair contributions')
t=t.replace('across all $2^{85}$ feasible permutations','under assumed binary assignments, not observed outcomes')
t=t.replace('bounded under the stated extreme-assignment calculation across all $2^{85}$ feasible missingness assignments.', 'shown by the reported extreme envelopes; these bounds do not identify the missing outcomes or certify legal correctness.')
t=t.replace('due to refusal collapse.', 'alongside a high refusal rate; this does not isolate refusal as the causal explanation.')
t=t.replace('because', 'alongside')
p.write_text(t,encoding='utf-8')
p=src/'supplement_limitations.tex'
t=p.read_text(encoding='utf-8').replace('Aggregate Table~IX sensitivity results',r'Aggregate Table~\ref{tab:sensitivity_raw_vs_clamped} sensitivity results')
p.write_text(t,encoding='utf-8')
