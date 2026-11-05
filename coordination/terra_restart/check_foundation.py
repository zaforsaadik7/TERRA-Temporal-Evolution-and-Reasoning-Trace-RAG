"""Read-only handoff check. Does not authorize work or certify the paper."""

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "coordination" / "terra_restart"


def verify_entry(root, entry):
    relative = Path(entry["path"])
    if relative.is_absolute():
        return False, "absolute manifest path rejected"
    target = (root / relative).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError:
        return False, "manifest path leaves project"
    if not target.is_file():
        return False, "missing file"
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    if digest != entry["sha256"].lower():
        return False, f"SHA256 mismatch: {digest}"
    return True, digest


def main():
    errors = []
    manifest = json.loads((BASE / "evidence_manifest.json").read_text(encoding="utf-8"))
    status = json.loads((BASE / "STATUS.json").read_text(encoding="utf-8"))
    required = [
        ROOT / "CLAUDE.md", ROOT / "AGENTS.md", BASE / "START_HERE.md",
        BASE / "PROTOCOL.md", BASE / "FINDINGS_REGISTER.md",
        BASE / "templates" / "PEER_MESSAGE.md", BASE / "templates" / "CHECKPOINT.md",
        BASE / "templates" / "AUDIT_RESPONSE.md", BASE / "templates" / "JOINT_DECISION.md",
        BASE / "claude_to_codex" / "README.md", BASE / "decisions" / "README.md",
        BASE / "user_authorizations" / "README.md",
        BASE / status["latest_codex_message"],
    ]
    for path in required:
        if not path.is_file():
            errors.append(f"Required foundation file missing: {path.relative_to(ROOT)}")
    for entry in manifest["artifacts"]:
        okay, detail = verify_entry(ROOT, entry)
        print(f"{'MATCH' if okay else 'FAIL'} {entry['path']}: {detail}")
        if not okay:
            errors.append(f"Artifact failure: {entry['path']}")
    review = (ROOT / "docs" / "TERRA_COMPARATIVE_REVIEWER_ASSESSMENT.md").read_text(encoding="utf-8")
    index = (BASE / "FINDINGS_REGISTER.md").read_text(encoding="utf-8")
    for number in range(1, 16):
        finding = f"R{number:02d}"
        if f"### {finding} " not in review or f"## {finding} " not in index:
            errors.append(f"Finding missing from review/index: {finding}")
    if status["collaboration_model"] != "peer-to-peer":
        errors.append("Unexpected collaboration model")
    try:
        import pymupdf
    except ImportError:
        print("NOT CHECKED: PDF page counts (pymupdf unavailable; no installation attempted)")
    else:
        for entry in manifest["artifacts"]:
            if "pages" not in entry:
                continue
            with pymupdf.open(ROOT / entry["path"]) as pdf:
                count = len(pdf)
            print(f"PAGES {entry['path']}: {count}")
            if count != entry["pages"]:
                errors.append(f"Page-count mismatch: {entry['path']}")
    print(f"Execution phase indexed: {status['execution_phase_authorized']!r}; verify actual user authorization separately.")
    if errors:
        for error in errors:
            print(f"ERROR {error}")
        print("FOUNDATION CHECK FAILED — do not rely on an inconsistent handoff.")
        return 1
    print("FOUNDATION CHECK PASSED — file handoff only; no scientific certification or execution approval.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
