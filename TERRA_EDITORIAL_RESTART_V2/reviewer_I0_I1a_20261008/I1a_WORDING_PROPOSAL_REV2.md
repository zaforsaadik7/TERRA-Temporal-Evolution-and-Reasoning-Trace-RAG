# I1a exact wording proposal rev2 — not applied

Author: Codex. 8 October 2026. Addresses Claude-0099. Retain rev1; this addendum supersedes its threshold/configuration instructions. Line-210, line-205/equation clarification, line-182 and line-651 replacements from rev1 remain as written. Main baseline remains 49107cfec13dcd51ec269d53e877984f855d0a7487092991881047576d018275. No manuscript change or build.

## Code evidence and boundary

Read-only examination of ask_terra.py, SHA256 0cca5cf440a1299853c37899647465b5f1f843803898e630d8d5402a3d9fffbb:
- is_query_in_domain (lines 279–298) accepts a title substring match first; otherwise it queries one nearest neighbour and returns true only when distance < 1.3. It returns false otherwise, including on caught errors.
- traffic_cop_router calls that helper and puts the resulting IN-DOMAIN/OUT-OF-DOMAIN flag into its prompt. This is not an automatic pre-retrieval refusal.
- EASY retrieval at line 757 queries two neighbours and reads documents, not a distance cutoff.
- HARD retrieval at lines 935 onward queries neighbours with the civil_rights category filter and reads documents/metadata. The threshold is not used there as an acceptance test in the inspected retrieval path.
- The calibration generator separately flags distance >= tau.

These observations establish current source semantics, not authenticated historical code. The apparent < versus >= conflict describes opposite sides of a domain flag, not competing thresholds. The <=1.3 text should be corrected to strict < and assigned to the domain helper, not erased as a configuration detail. No claim of a historical distance-based retrieval cutoff is warranted by these source observations.

## Exact line 126 replacement

\item \textbf{Traffic Cop Routing with a Coarse Domain Flag:} an SLM-driven complexity router with a domain-relevance flag derived from a title match or nearest-neighbour proximity ($d_{L2}<1.3$ in the current source). This flag is not itself an early-refusal rule; the canonical evaluation terminated no query before retrieval (Sections~\ref{subsec:computational-budget} and~\ref{subsec:firewall-analysis}).

This describes the current source's OR logic rather than an ambiguous “+ Title Match”. No separate title-only diagnostic is claimed.

## Exact line 649 opening replacement

Replace only its first sentence with:
“The design intended the Domain Boundary Firewall to use a coarse proximity flag: the distance-only calibration flags scores at or above $\tau=1.30$, whereas the current domain helper accepts scores below that threshold or an indexed-title match.”

Keep the subsequent preliminary 50-query 10,009-opinion observations and existing canonical refusal/pilot findings unchanged. Rev1 line 651 explicitly warns that historical units/configuration are unreconciled, and removes the unsupported density inference. No historical-number certification is added.

## Exact line 326 configuration correction

Replace “and TERRA traverses the directed chronological graph by BFS ($k=2$, $d=2$, hub cap 50, $d_{L2} \le 1.3$)” with:
“and TERRA traverses the directed chronological graph by BFS ($k=2$, $d=2$, hub cap 50); the current source separately uses a strict $d_{L2}<1.3$ proximity check in its domain-relevance helper, with a title-match alternative”.

## Exact line 353 model/retrieval correction

Replace “\TraceEmbeddingDimensions\ dimensions, Euclidean $L_2$, ChromaDB PersistentClient, top-$k=2$, $d_{L2} \le 1.3$” with:
“\TraceEmbeddingDimensions\ dimensions, ChromaDB PersistentClient with its $L_2$ index setting, top-$k=2$; the current domain helper uses a title match or $d_{L2}<1.3$ proximity”.

The line-205 clarification defines raw squared-L2 units for calibration. Normalization remains unverified; neutral wording does not assert its absence.

## User disposition and next gate

No removal of threshold configuration is now proposed. Changes correct its strictness, function and source-era qualification. Exact current source cannot prove which helper implementation was used historically. These caveats must survive compression.

Claude reviews rev1 retained text plus these exact replacements. After user approval of implementation: snapshot dependencies, apply only approved replacements, keep generated macros unchanged, compile, measure <=25 pages and inspect affected rendered pages. If over budget, stop and report; do not authorize extra compression implicitly. Return actual diff/PDF for audit. No additional API, run, statistics regeneration or canonical promotion.
