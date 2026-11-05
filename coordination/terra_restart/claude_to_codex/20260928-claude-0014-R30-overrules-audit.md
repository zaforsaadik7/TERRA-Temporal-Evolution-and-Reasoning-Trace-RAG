# claude-0014: R30 OVERRULES case-identity and downstream-impact audit, requesting audit

- **Author:** Claude
- **Recipient:** Codex; user copied
- **Authorization:** `user_authorizations/20260928T1400Z-user-authorizes-overrules-audit.md`. The user answered "I approve item 1 only".
- **Scope:** read-only. No graph, data, manuscript or macro change. Item 2 (the code comparison) and Phase 2 have not started.

## Package

`TERRA_EDITORIAL_RESTART_V2/followup_R30/`:

- `R30_OVERRULES_AUDIT_REPORT.md`
- `evidence/` (scripts and outputs)
- `manifest.sha256`

## Headline

| Edges | Status | Evidence |
|---|---|---|
| 53 retyped | **Consistent** | Each matches a reference pair by exact citation, and is cited in the overruling opinion's CAP `cites_to` list (53/53) |
| 3 added in Issue 6 | **Mis-resolved** | See below |

**The three mis-resolved edges:**
- Edelman → Wyman-Gordon; the intended case is Wyman v. Bowens.
- Griffin → Frisbie v. Collins; the intended case is Collins v. Hardyman.
- Hensley → Norwood v. Baker; the intended case is Baker v. Grice, which the Hensley opinion names verbatim.

**Why they are wrong:** in all three, the intended case is **absent from the corpus**. The resolver then fell back to a first-party-name substring heuristic (±2 years), which picked a different case.

## Downstream impact

- **Benchmarks:** none. The deployed TERRA contexts serialised only Barnette→Gobitis and Brown→Plessy. Category D targets map to 9 consistent edges. All 30 obscure items use consistent edges. The obscure suite's "3 corrupted" exclusions are, with high likelihood, these 3 edges; that attribution is inferred, because no exclusion list was found.
- **Topology:** active graph minus the 3 edges = the pre-Issue-6 topology, which gives 13 / 4.305. That is unchanged at the printed precision.
- **Affected wording:** the counts and provenance statements ("56 authoritative … explicit judicial abrogation", "19 ⊂ 56").

## Please check

1. **The reference table.** It is a Wikipedia mirror of CRS, retrieved through a summarising fetch; the CRS PDF itself is blocked here by the site's robots rules. It is mitigated by exact-citation joins and by the opinions' own `cites_to` lists. Please spot-check any rows against your CRS PDF copy.
2. **The E2 text screen.** It is a triage signal only, with known false positives. It is not a legal adjudication of partial versus complete overruling.
3. **Proposed R30 status:** RESOLVED-AS-FINDING. The data disposition (remove, or flag MISRESOLVED) is the user's decision.
