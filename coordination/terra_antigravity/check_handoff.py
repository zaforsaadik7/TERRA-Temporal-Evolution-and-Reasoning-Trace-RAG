"""Read-only identity check. Does not certify science, change state or authorize edits."""
from pathlib import Path
import hashlib
import json
import sys

root = Path(__file__).resolve().parents[2]
state = json.loads((Path(__file__).parent / "STATUS.json").read_text(encoding="utf-8"))
different = False
for artifact in state["codex_audited_artifacts"]:
    path = root / artifact["path"]
    if not path.is_file():
        print("MISSING", artifact["role"], str(path))
        different = True
        continue
    with path.open("rb") as handle:
        digest = hashlib.file_digest(handle, "sha256").hexdigest()
    match = digest == artifact["sha256"]
    print("MATCH" if match else "DIFFERENT", artifact["role"], digest, str(path))
    different |= not match
print("Antigravity acknowledgment:", state["antigravity_acknowledgment_received"])
print("Identity only. A difference requests reconciliation, not automatic rollback.")
sys.exit(1 if different else 0)
