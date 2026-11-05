# Timestamp evidence transcription correction

The first source/cache record was reserialized through JavaScript numbers. Windows UTC ticks exceed JavaScript's exact integer range, so source_cache_before.json rounded its timestamp integers. Hashes and byte sizes were unaffected. It is preserved but must not be used for exact tick comparisons.

source_cache_before_exact.json preserves the original PowerShell output text directly, without numeric reserialization. All 11 source files were subsequently checked against that original record: exact ticks, sizes and SHA-256 match. Example: original/current SQLite ticks 639275971477598404, versus rounded transcription 639275971477598500. Thus the post-copy stop was an evidence-formatting defect, not demonstrated source drift.

No database was opened before this was resolved. The full copy had already passed per-file byte parity; no copy retry or source mutation was performed. Subsequent evidence exports timestamps as strings.
