"""Standalone -I -B bootstrap. Admission check precedes project imports/reads."""
ENTRY_ADMITTED = False


def main():
    if not ENTRY_ADMITTED:
        print('BLOCKED: cohort standalone entry/frozen trust root pending')
        return 2
    import sys
    from pathlib import Path
    # Explicit source root only; no ambient PYTHONPATH. This bootstrap itself
    # and the complete runtime must be pinned by the final external launcher.
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
    from scripts.matched_baseline.offline_cohort_production import main as run
    return run(sys.argv[1:])


if __name__=='__main__':raise SystemExit(main())
