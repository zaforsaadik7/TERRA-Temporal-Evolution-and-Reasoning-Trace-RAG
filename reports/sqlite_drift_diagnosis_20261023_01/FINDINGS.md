# Authorized copy-only SQLite drift diagnosis

23 October 2026. Implementation self-verification by Codex, not independent review.

## Completed

Fresh exclusive copies of both SQLite files were made after checking their expected hashes. SQLite was opened only on these copies using `mode=ro&immutable=1` and `query_only=ON`. Inspected schema definitions/root-page identities and page size/count, freelist count, schema/user versions, application ID, encoding and auto-vacuum settings. No user-table rows, document text or embeddings were queried. SQLite library version is recorded in `comparison.json`.

Both originals and both copies retained their respective initial SHA-256 hashes after comparison. The current database was not accepted as a baseline. No source writes, models, Chroma clients, firewall changes, network or API calls occurred.

## Findings

Exactly **11 bytes** differ in a 362,885,120-byte file. All remaining bytes are identical.

- Two changed bytes are at file offsets 27 and 95 on page 1.
- Nine changed bytes are on page 4 (4096-byte page size).
- The identical schema identifies page 4 as the root page of table `acquire_write`.
- All inspected metadata and schema results are identical.

Exact offsets and old/new byte values are recorded in `difference_offsets.json`. Full schema/metadata and source/copy hashes are in `comparison.json`.

The limited byte footprint and table name are consistent with an operational bookkeeping change, but **do not establish its meaning, cause, writer, or safety**. No logical records were inspected, and the database remains different from the accepted artifact. No implication that an unchanged schema alone proves data integrity is intended. The prior accepted reference is intact.

## Disposition

The immediate diagnosis is complete; the candidate refresh remains blocked. Preserve both versions. Next proposed bounded investigation: inspect only `acquire_write` rows on these isolated copies and statically search repository code/evidence for its use. Do not query other tables or initialize Chroma. This can clarify the changed bookkeeping without restoring or accepting either version. Obtain user approval before that scope extension.
