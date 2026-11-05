"""Phase 3 Batch 03 (PROPOSAL): Table XXI Panel A and section VII-M regenerated from canonical v2 (R13, with the R32 fast-path and R31 pre-retrieval statements in that section).
Byte-preserving and fail-closed (see ERRATUM_01_line_endings.md). Usage: python -X utf8 p3b3_apply.py <src_dir> <phase3_corrections_b3.tex> <diff_out> [--check-only]
Pre-state = Batch 02 rev1 post-state. Writes nothing unless every pre-hash matches and every edit occurs exactly once."""
import difflib, hashlib, os, shutil, sys
SRC, CORR, DIFF = sys.argv[1:4]
CHECK = '--check-only' in sys.argv
sha = lambda b: hashlib.sha256(b).hexdigest()
PRE = {'main.tex': 'af093e96eeaf6fe76cd7fc1e0838b7bbf88ae8910ed83bd35ce86862bde8aa55',
       'tables/table_computational_budget.tex': '4960a2eb32696d87@@'}
EDITS = {'main.tex': [('\\input{phase3_corrections_b2} % Phase 3 Batch 02 overrides (R28; R10)\n',
  '\\input{phase3_corrections_b2} % Phase 3 Batch 02 overrides (R28; R10)\n\\input{phase3_corrections_b3} % Phase 3 Batch 03 overrides (R13; Table XXI, section VII-M)\n'),
 ('end-to-end and decoupled component latencies, effective token volumes, and financial costs across all',
  'end-to-end and stage latencies, effective token volumes, and modelled financial costs across all'),
 ('Across the 350-query benchmark, TERRA performs \\TerraOperationsTotalCount\\ operations (\\TerraOperationsPerQuery\\ per query; operations counted where a stage recorded non-zero time) at '
  '\\TerraDeployedCostPerThousand\\ per 1,000 queries under the deployed configuration (Gemma~3 12B router; Llama~3.3 70B NLI grader and generator).',
  'Across the 350-query benchmark, TERRA performs \\TerraOperationsTotalCount\\ operations (\\TerraOperationsPerQuery\\ per query; operations counted where a stage recorded non-zero time) at a '
  'modelled \\TerraDeployedCostPerThousand\\ per 1,000 queries under the deployed configuration (Gemma~3 12B router; Llama~3.3 70B NLI grader and generator). The cost is modelled from token-count '
  'estimates at list prices, not metered; it prices a grader call for every Category~B--D query (twice for refused Category~C and~D queries) and none for Category~A, although Category~A recorded '
  'grading time. Pricing one grader call only where the recorded grading time was at least 1~ms gives \\$4.66 per 1,000 queries instead.'),
 ('Critically, both Category~C (unanswerable out-of-domain probes) and Category~D (adversarial overruling pairs) operate under an identical deterministic self-correction mechanism:\n'
  '\\begin{itemize}\n'
  '    \\item \\textbf{Passing Entailment (Attempt~1 Resolution):} Queries that satisfy NLI entailment on the initial attempt require $1\\text{ retrieval} + 1\\text{ NLI verification} + 1\\text{ '
  'generator invocation} = 4\\text{ operations}$. This path is taken by $\\TerraCatCPassNliGenCount$ queries in Category~C ($\\TerraCatCPassNliGenCount \\times 4 = \\TerraCatCPassNliOps\\text{ '
  'operations}$) and $\\TerraCatDPassNliGenCount$ queries in Category~D ($\\TerraCatDPassNliGenCount \\times 4 = \\TerraCatDPassNliOps\\text{ operations}$).\n'
  '    \\item \\textbf{Failing Entailment (Attempt~2 Halting):} Queries failing entailment on Attempt~1 trigger an expanded retrieval query and undergo a second NLI verification attempt; when '
  'Attempt~2 likewise fails, generation halts in a deterministic safety refusal ($2\\text{ retrievals} + 2\\text{ NLI verifications} + 0\\text{ generator invocations} = 5\\text{ operations}$). This '
  'trajectory is executed by $\\TerraCatCFailNliHaltedCount$ post-retrieval halted queries in Category~C ($\\TerraCatCFailNliHaltedCount \\times 5 = \\TerraCatCFailNliOps\\text{ operations}$) and '
  '$\\TerraCatDFailNliHaltedCount$ post-retrieval halted queries in Category~D ($\\TerraCatDFailNliHaltedCount \\times 5 = \\TerraCatDFailNliOps\\text{ operations}$).\n'
  '    \\item \\textbf{Pre-Retrieval Interceptions (Category~C):} In Category~C, $\\TerraCatCPreFilterExceedingHaltedCount$ out-of-domain queries exceed the geometric proximity boundary ($d_{L2} '
  '\\ge 1.30$) and are terminated immediately pre-retrieval, incurring only $1\\text{ operation}$ each ($\\TerraCatCPreFilterExceedingHaltedCount \\times 1 = \\TerraCatCPreFilterHaltedOps\\text{ '
  'operations}$). A single borderline probe (\\texttt{C069}, $d_{L2}=1.366$) proceeds directly to the generator with empty context ($1\\text{ pre-filter} + 1\\text{ generator} = '
  '\\TerraCatCBorderlineOps\\text{ operations}$).\n'
  '\\end{itemize}\n'
  'Summing these operational paths yields exact integer closure: $\\TerraCatCPreFilterHaltedOps + \\TerraCatCBorderlineOps + \\TerraCatCFailNliOps + \\TerraCatCPassNliOps = '
  '\\TerraCatCTotalOps\\text{ operations}$ on Category~C (averaging $\\TerraCatCTotalOpsPerQuery$ ops/query) and $\\TerraCatDFailNliOps + \\TerraCatDPassNliOps = \\TerraCatDTotalOps\\text{ '
  'operations}$ on Category~D (averaging $\\TerraCatDTotalOpsPerQuery$ ops/query). Combined with Category~A ($\\TerraCatATotalOps\\text{ operations}$) and Category~B ($\\TerraCatBTotalOps\\text{ '
  'operations}$), TERRA executes $\\TerraBenchmarkTotalOpsFormatted\\text{ operations}$ ($\\TerraOverallTotalOpsPerQuery$ ops/query).',
  'These counts are measured from recorded stage times, not taken from a design model. In the canonical run, Category~A (the nominal fast path) recorded retrieval and NLI-grader time on all 100 '
  'queries and invoked the generator on \\TerraCatAGenCallsFormatted; Category~B recorded all four stages on all 100 queries and invoked the generator on \\TerraCatBGenCallsFormatted; Category~C '
  'recorded routing, retrieval and grading time on all 75 queries but no generation, because all 75 were refused, and for 74 of them the recorded grading time was under 1~ms and the retrieved '
  'context was empty, which is consistent with a deterministic empty-context rejection rather than an LLM grading call; Category~D recorded all three pre-generation stages on all 75 queries and '
  'invoked the generator on \\TerraCatDGenCallsFormatted, the other 46 queries being refused (7 of them with an empty context). This yields \\TerraCatATotalOps, \\TerraCatBTotalOps, '
  '\\TerraCatCTotalOps\\ and \\TerraCatDTotalOps\\ operations on Categories~A--D (\\TerraCatATotalOpsPerQuery, \\TerraCatBTotalOpsPerQuery, \\TerraCatCTotalOpsPerQuery\\ and '
  '\\TerraCatDTotalOpsPerQuery\\ per query) and \\TerraBenchmarkTotalOpsFormatted\\ in total (\\TerraOverallTotalOpsPerQuery\\ per query). A design-level model in which out-of-domain queries beyond '
  'the geometric boundary are terminated before retrieval is not what the deployed run did: every Category~C query recorded retrieval time (at least 178~ms excluding routing), so the threshold '
  'analysis in Panel~B describes an offline calibration of a candidate pre-filter.'),
 ('Importantly, while TERRA executes more sequential pipeline stages than single-shot baselines, it invokes the computationally expensive 70B parameter generator on only '
  '$\\TerraOverallGenCallsCount$ of the 350 benchmark queries ($\\TerraOverallGenCallsPct$), achieving a $\\TerraOverallGenCallsReductionPct$ reduction in active 70B generator calls compared to '
  'comparative baselines ($350/350$). This reduction is driven by epistemic refusal on Category~C ($\\TerraCatCGenCallsFormatted$) and adversarial safety halting on Category~D '
  '($\\TerraCatDGenCallsFormatted$). We frame this generator-call reduction not as an alternative metric for call parity, but as one important mitigating factor in aggregate serving efficiency.',
  'Importantly, while TERRA executes more sequential pipeline stages than single-shot baselines, it invokes the generator on only \\TerraOverallGenCallsCount\\ of the 350 benchmark queries '
  '(\\TerraOverallGenCallsPct), a \\TerraOverallGenCallsReductionPct\\ reduction in active generator calls compared to the single-shot baselines ($350/350$). The reduction comes from refusals: '
  'Category~C made no generator calls (\\TerraCatCGenCallsFormatted), Category~D made \\TerraCatDGenCallsFormatted, and the refusals on Categories~A and~B also skip generation. It is not a reduction '
  "in total 70B-model use: the NLI grader is also a Llama~3.3 70B model and recorded at least 1~ms of grading time on 276 of the 350 queries, so TERRA's generator and grader calls together exceed "
  "the baselines' one call per query. We frame the generator-call reduction not as an alternative metric for call parity, but as one mitigating factor in aggregate serving efficiency."),
 ('an operational cost of $\\TerraCatBTotalCostPerThousand$ per 1,000 queries', 'a modelled cost of $\\TerraCatBTotalCostPerThousand$ per 1,000 queries'),
 ('expending $\\sim \\TerraHardPathMedianSeconds\\text{ s}$ and approximately one cent per query to secure complete doctrinal authority is an operationally sound trade-off.',
  'expending $\\sim \\TerraHardPathMedianSeconds\\text{ s}$ and roughly $\\TerraCatBPerQueryCost$ per query (modelled) to recover the full precedent path on $\\CatBTerraFullPathCount$ of the '
  'Category~B queries is, in our judgement, a defensible trade-off.'),
 ('\\subsubsection{Decoupled Wall-Clock Latency Profiling}', '\\subsubsection{Stage Latency Profiling}'),
 ('Panel~A decouples end-to-end wall-clock latency into four isolated execution stages, reconciling with reported benchmark totals within $0.02\\text{ ms}$:',
  'Panel~A reports mean stage times from the logged timing fields. For hard-route queries (Categories~B--D, 240 of 350) the logged retrieval timer is cumulative and includes routing time (the two '
  'correlate at $r=0.999$ across those queries, and the difference is always at least 178~ms), so retrieval is taken as logged retrieval time minus routing time; for fast-route queries the timers '
  'are separate. NLI grading and generation are the logged values. The stages sum exactly to the end-to-end time for Category~A and the single-shot baselines. For Categories~B--D they leave a '
  'remainder that is not attributed to any stage and whose cause was not established (mean $\\TerraCatBRemainderMS\\text{ ms}$, $\\TerraCatCRemainderMS\\text{ ms}$ and $\\TerraCatDRemainderMS\\text{ '
  'ms}$, respectively), so the columns do not reconcile exactly to the end-to-end means:'),
 ('    \\item \\textbf{Isolated Graph Retrieval:} Pure graph retrieval latency (isolated from query routing) averages $\\TerraOverallDecoupledRetrievalMS\\text{ ms}$ overall, rising to '
  '$\\TerraCatBDecoupledRetrievalMS\\text{ ms}$ on Category~B multi-hop BFS traversal, while Category~A fast path bypasses retrieval entirely ($\\TerraCatADecoupledRetrievalMS\\text{ ms}$).',
  '    \\item \\textbf{Graph Retrieval:} Retrieval latency, isolated from routing, averages $\\TerraOverallDecoupledRetrievalMS\\text{ ms}$ overall ($\\TerraCatADecoupledRetrievalMS\\text{ ms}$ on '
  'Category~A, $\\TerraCatBDecoupledRetrievalMS\\text{ ms}$ on Category~B, $\\TerraCatCDecoupledRetrievalMS\\text{ ms}$ on Category~C and $\\TerraCatDDecoupledRetrievalMS\\text{ ms}$ on Category~D). '
  'The Category~A fast path does not bypass retrieval: all 100 Category~A queries recorded retrieval time.'),
 ('    \\item \\textbf{NLI Smart Grader Verification:} Entailment grading consumes $\\TerraOverallDecoupledNliMS\\text{ ms}$ overall ($\\TerraCatBDecoupledNliMS\\text{ ms}$ on Category~B, '
  '$\\TerraCatCDecoupledNliMS\\text{ ms}$ on Category~C, and $\\TerraCatDDecoupledNliMS\\text{ ms}$ on Category~D). Notably, Category~D registers higher mean NLI latency than Category~C '
  '($\\TerraCatDDecoupledNliMS\\text{ ms}$ vs. $\\TerraCatCDecoupledNliMS\\text{ ms}$). Trace analysis reveals that this asymmetry is driven by prompt context volume rather than attempt count: '
  'Category~D queries retrieve dense overruled precedents and citation dockets (averaging $\\TerraCatDMeanRawChars$ raw / $\\TerraCatDMeanClampedChars$ clamped characters per query) requiring full '
  'attention processing over long sequences on the 70B model, whereas Category~C unanswerable probes retrieve sparse or empty candidate texts (averaging $\\TerraCatCMeanRawChars$ raw / '
  '$\\TerraCatCMeanClampedChars$ clamped characters).',
  '    \\item \\textbf{NLI Smart Grader Verification:} Logged grading time averages $\\TerraOverallDecoupledNliMS\\text{ ms}$ overall ($\\TerraCatADecoupledNliMS\\text{ ms}$ on Category~A, '
  "$\\TerraCatBDecoupledNliMS\\text{ ms}$ on Category~B, $\\TerraCatCDecoupledNliMS\\text{ ms}$ on Category~C and $\\TerraCatDDecoupledNliMS\\text{ ms}$ on Category~D). Category~C's low mean "
  'reflects its contexts: 74 of 75 Category~C queries retrieved an empty context (mean $\\TerraCatCMeanRawChars$ characters across all 75) and recorded grading time under 1~ms, consistent with a '
  'deterministic rejection rather than an LLM call. Category~D contexts are longer (mean $\\TerraCatDMeanRawChars$ characters, none above the 60{,}000-character clamp), and its grading time is '
  'correspondingly higher.'),
 ('on Category~C, generator latency collapses to $\\TerraCatCDecoupledGenerationMS\\text{ ms}$ because $\\TerraCatCPreFilterExceedingHaltedCount$ queries are intercepted pre-retrieval and '
  '$\\TerraCatCFailNliHaltedCount$ are halted at the NLI gate.',
  'on Category~C, generator latency is $\\TerraCatCDecoupledGenerationMS\\text{ ms}$ because no Category~C query reached the generator.'),
 ("Under TERRA's operational threshold $\\tau=1.30$, the pre-filter functions with zero false refusal while intercepting $\\TerraGateTPRTauOneThreeZero$ ($\\TerraGateTPRCountTauOneThreeZero$) of "
  'out-of-domain probes before retrieval. The remaining $\\TerraGateFNRTauOneThreeZero$ ($\\TerraGateFNRCountTauOneThreeZero$) of out-of-domain queries slip past the pre-filter and enter retrieval; '
  'however, these deferred queries are subsequently intercepted by downstream NLI entailment grading, which halts generation in a safe refusal. We emphasize that geometric proximity serves strictly '
  'as an \\textit{optional coarse pre-filter} to conserve retrieval and grading compute on obvious out-of-domain inputs; embedding distance metrics do not prove legal validity or domain membership, '
  'which remains the exclusive operational responsibility of the downstream NLI Smart Grader.',
  'At the configured threshold $\\tau=1.30$, the offline calibration shows zero in-domain false refusal and flags $\\TerraGateTPRTauOneThreeZero$ ($\\TerraGateTPRCountTauOneThreeZero$) of the '
  'out-of-domain probes by distance alone; the remaining $\\TerraGateFNRTauOneThreeZero$ ($\\TerraGateFNRCountTauOneThreeZero$) fall below the threshold. This is a calibration of a candidate '
  'pre-filter, not a description of the deployed run: in the canonical run every Category~C query recorded retrieval time (at least 178~ms excluding routing), so no query was terminated before '
  'retrieval, and all 75 Category~C queries were refused downstream, 74 of them on an empty retrieved context with a recorded grading time under 1~ms. Geometric proximity is an \\textit{optional '
  'coarse pre-filter} intended to conserve retrieval and grading compute on obvious out-of-domain inputs; embedding distance does not prove legal validity or domain membership.'),
 ('At the operational threshold $\\tau = 1.30$, geometric pre-filtering achieves $\\TerraGateFPRTauOneThreeZero$ in-domain false refusal ($\\TerraGateFPRCountTauOneThreeZero$) while intercepting '
  '$\\TerraGateTPRTauOneThreeZero$ ($\\TerraGateTPRCountTauOneThreeZero$) of out-of-domain probes pre-retrieval.',
  'At the configured threshold $\\tau = 1.30$, the offline calibration gives $\\TerraGateFPRTauOneThreeZero$ in-domain false refusal ($\\TerraGateFPRCountTauOneThreeZero$) and flags '
  '$\\TerraGateTPRTauOneThreeZero$ ($\\TerraGateTPRCountTauOneThreeZero$) of the out-of-domain probes by distance; the deployed run did not terminate any query before retrieval.'),
 ('that saves retrieval and NLI compute on obvious outliers, while downstream NLI entailment verification serves as the indispensable primary safety firewall.',
  'that could save retrieval and NLI compute on obvious outliers. In the canonical run, 81 of the 139 refusals occurred on an empty retrieved context (74 in Category~C and 7 in Category~D) and 58 on '
  'a non-empty context (2, 16, 1 and 39 in Categories~A--D).')],
         'tables/table_computational_budget.tex': [('Decoupled Component Latency Breakdown, and Geometric Gate Calibration', 'Stage Latency Breakdown, and Geometric Gate Calibration'),
 ('end-to-end and decoupled component latencies (wall-clock ms), effective prompt/completion tokens, and total pipeline financial costs.',
  'end-to-end and stage latencies (wall-clock ms), effective prompt/completion tokens, and modelled pipeline financial costs (token estimates at list prices, not metered).'),
 ('\\textbf{Decoupled Component Latency Breakdown (Mean ms)}', '\\textbf{Stage Latency (Mean ms)}'),
 ('\\textbf{Prompt / Compl.} & \\textbf{1k Queries} \\\\', '\\textbf{Prompt / Compl.} & \\textbf{1k Queries (Modelled)} \\\\'),
 ('Computational profiling, sequential operations, and latency decoupling across $N=350$ queries evaluated on \\texttt{terra\\_baselines\\_eval\\_raw.json}. Total operations per query account for '
  'all discrete algorithmic and model execution stages. Both Category C and Category D execute identical deterministic self-correction mechanics: queries clearing NLI entailment resolve on Attempt 1 '
  '(1 retrieval + 1 NLI verification + 1 generator call = 4 operations), whereas queries failing entailment trigger expanded retrieval before halting on Attempt 2 (2 retrievals + 2 NLI verifications '
  '+ 0 generator calls = 5 operations). Category C includes 40 queries halted pre-retrieval by the geometric pre-filter (1 operation each) and 1 borderline query (\\texttt{C069}, 2 operations), '
  'yielding an average of \\TerraCatCTotalOpsPerQuery\\ ops/query (\\TerraBenchmarkTotalOpsFormatted\\ total operations across the benchmark, averaging \\TerraOverallTotalOpsPerQuery\\ ops/query). '
  'Component latencies are decoupled from query ingestion: isolated retrieval duration reflects subtraction of double-counted routing latency (Category B isolated retrieval is 668.5 ms), matching '
  "total benchmark latency within 0.02 ms. Category D's higher mean NLI latency (\\TerraCatDDecoupledNliMS\\ ms vs. \\TerraCatCDecoupledNliMS\\ ms in Category C) is driven by prompt context scale "
  '(mean 268,682 raw / 15,969 clamped characters of dense precedent vs. 7,231 raw / 801 clamped characters of sparse out-of-domain text), requiring greater prefill compute on the 70B model under '
  'identical 2-attempt logic. Financial costs fold in Gemma 3 12B routing (\\$0.15/1M tokens), local zero-cost deterministic retrieval (\\$0.00), and LLaMA 3.3 70B NLI grading and generation '
  '(\\$0.60/1M tokens).',
  'Computational profiling and stage latencies across $N=350$ queries from the canonical v2 evaluation (\\texttt{data/terra\\_canonical\\_v2\\_eval.json}). Operations per query count each stage '
  '(routing, retrieval, NLI grading, generation) that recorded non-zero time. Generator calls count queries with non-zero generation time. Routing, NLI grading and generation are means of the logged '
  'timing fields. Retrieval is the logged retrieval time minus routing time for hard-route queries (whose retrieval timer includes routing) and the logged value otherwise. The stages sum to the '
  'end-to-end time for Category~A and the single-shot baselines; for Categories~B--D a remainder not attributed to any stage averages \\TerraCatBRemainderMS, \\TerraCatCRemainderMS\\ and '
  '\\TerraCatDRemainderMS\\ ms. Category~A recorded retrieval and NLI-grader time on every query. Category~C recorded no generation; for 74 of 75 queries the context was empty and the recorded '
  'grading time was under 1~ms. Costs are modelled, not metered: token counts are estimated from character or word counts, Gemma 3 12B routing is priced at \\$0.15/1M tokens and LLaMA 3.3 70B '
  'grading and generation at \\$0.60/1M tokens, a grader call is priced for every Category~B--D query (twice for refused Category~C and~D queries) and none for Category~A, and retrieval is priced at '
  '\\$0.00. Pricing one grader call only where the recorded grading time was at least 1~ms gives \\$4.66 per 1,000 queries overall instead of \\TerraDeployedCostPerThousand.'),
 ('\\textbf{TERRA Operational Setting: Zero false refusal on valid law; 54.7\\% OOD pre-filtered.}',
  '\\textbf{Configured threshold: zero false refusal on valid law; 54.7\\% of OOD probes flagged (offline calibration).}')]}
out, diff = {}, []
for f, eds in EDITS.items():
    raw = open(os.path.join(SRC, f), 'rb').read()
    pre = PRE[f].rstrip('@')
    if not sha(raw).startswith(pre): sys.exit(f'FAIL-CLOSED: pre-hash mismatch for {f}')
    txt = raw.decode('utf-8')
    for a, b in eds:
        cands = [(a, b)] + ([(a.replace('\n', '\r\n'), b.replace('\n', '\r\n'))] if '\n' in a else [])
        hits = [(x, y) for x, y in cands if txt.count(x) == 1]
        if len(hits) != 1: sys.exit(f'FAIL-CLOSED: {f}: edit not matched exactly once: {a[:80]!r}')
        txt = txt.replace(*hits[0])
    out[f] = txt.encode('utf-8')
    diff += difflib.unified_diff(raw.decode('utf-8').splitlines(True), txt.splitlines(True), f'a/{f}', f'b/{f}')
mt, tt = out['main.tex'].decode('utf-8'), out['tables/table_computational_budget.tex'].decode('utf-8')
for bad in ('generator latency collapses to', 'C069', 'one cent', 'Isolated Graph Retrieval', 'bypasses retrieval entirely', 'reconciling with reported', 'Decoupled Wall-Clock', 'Logged Stage', 'TerraCatCPreFilterExceedingHaltedCount', 'TerraCatCFailNliHaltedCount', 'indispensable primary safety firewall', 'before retrieval. The remaining', 'operational responsibility of the downstream'):
    assert bad not in mt, f'post-condition: {bad!r} still in main.tex'
for bad in ('C069', 'terra_baselines_eval_raw', '268,682', 'Decoupled Component', 'TERRA Operational Setting', 'Logged Stage'):
    assert bad not in tt, f'post-condition: {bad!r} still in the table'
for f, b in out.items():
    before = open(os.path.join(SRC, f), 'rb').read(); c0, c1 = before.count(b'\r\n'), b.count(b'\r\n')
    print('%s: CRLF %d -> %d, bare LF %d -> %d, sha256 %s' % (f, c0, c1, before.count(b'\n') - c0, b.count(b'\n') - c1, sha(b)))
diff += difflib.unified_diff([], open(CORR, encoding='utf-8').read().splitlines(True), '/dev/null', 'b/phase3_corrections_b3.tex')
open(DIFF, 'w', encoding='utf-8', newline='').writelines(diff)
if CHECK: print('CHECK-ONLY: nothing written'); sys.exit(0)
for f, b in out.items(): open(os.path.join(SRC, f), 'wb').write(b)
shutil.copyfile(CORR, os.path.join(SRC, 'phase3_corrections_b3.tex'))
print('WRITTEN')
