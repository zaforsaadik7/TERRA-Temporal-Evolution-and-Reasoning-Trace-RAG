# Finalization phase and duplicate-work correction

Report auditing now begins explicitly in CLEANUP after the owned child tree and
rule have been resolved, allowing the reserved finalization window as intended.
Test asserts CLEANUP precedes report auditing.

packet_body materializes the immutable validated command once rather than three
times; encode_packet hashes the body it has already validated rather than rebuilding
it. The strict regenerated-form/approval checks are unchanged. Test asserts one
command-view construction. This is pure duplicate-work removal, no skipped file
or data validation. R03's prior snapshots/results remain preserved.
