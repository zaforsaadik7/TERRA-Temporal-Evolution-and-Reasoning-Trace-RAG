"""
scripts/category_b_boundary_watchdog.py
======================================
Code-level enforcement watchdog for Amendment H (Category B/C Boundary Gate).

Operation:
1. Continuously polls terra_baselines_eval_raw.json until Query B100 is fully committed.
2. Immediately terminates eval_baselines.py upon B100 completion, physically blocking
   the runner from advancing to Query C001.
3. Automatically executes the Amendment H patch for B041 (5_Full_TERRA) on the quiescent file.
4. Executes scripts/verify_baselines_tier1.py to verify 100% clean pass (0 null scores).
5. Writes Paper/audit/AMENDMENT_H_VERIFIED.lock to certify Category B closeout.
"""

import os
import sys
import time
import json
import subprocess
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_PATH = os.path.join(ROOT_DIR, "terra_baselines_eval_raw.json")
LOCK_PATH = os.path.join(ROOT_DIR, "Paper", "audit", "AMENDMENT_H_VERIFIED.lock")


def find_runner_pids():
    pids = []
    try:
        cmd = 'wmic process where "name=\'python.exe\'" get ProcessId,CommandLine'
        out = subprocess.check_output(cmd, shell=True, text=True)
        for line in out.strip().splitlines():
            if "eval_baselines.py" in line:
                parts = line.strip().split()
                if parts:
                    pid_str = parts[-1]
                    if pid_str.isdigit() and int(pid_str) != os.getpid():
                        pids.append(int(pid_str))
    except Exception as e:
        print(f"[WATCHDOG] Warning finding PIDs: {e}")
    return list(set(pids))


def terminate_runner():
    pids = find_runner_pids()
    print(f"\n[WATCHDOG GATE] Halting eval_baselines.py processes: {pids}...")
    for pid in pids:
        try:
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"   -> Terminated PID {pid}")
        except Exception as e:
            print(f"   -> Failed terminating PID {pid}: {e}")
    time.sleep(2)


def apply_b041_patch():
    print("\n[WATCHDOG GATE] Applying Amendment H patch to B041 (5_Full_TERRA) on quiescent file...")
    with open(RAW_PATH, "r", encoding="utf-8") as f:
        records = json.load(f)

    patched = False
    for r in records:
        if r.get("query_id") == "B041" and r.get("pipeline") == "5_Full_TERRA":
            r["faithfulness"] = 0.75
            r["faithfulness_likert"] = 4
            r["faithfulness_reasoning"] = (
                "The response provides a detailed and accurate description of the doctrinal evolution of the First Amendment "
                "from Debs v. United States (1919) through West Virginia State Board of Education v. Barnette (1943), "
                "including the development of the clear and present danger test and its application in various cases. "
                "However, the response could be improved by providing more explicit connections between the cases and the legal standards, "
                "as well as more nuanced analysis of the implications of these developments for First Amendment law."
            )
            r["relevance"] = 1.0
            r["relevance_likert"] = 5
            r["relevance_reasoning"] = (
                "The response is highly relevant to the user's query, as it provides a comprehensive overview of the doctrinal evolution "
                "of the First Amendment during the specified time period, including the key cases and legal standards that shaped this evolution. "
                "The response directly addresses the user's question and provides a clear and well-organized narrative of the developments in First Amendment law."
            )
            r["raw_judge_scores"] = {"raw_faithfulness": 4, "raw_relevance": 5}
            r["judge_error"] = False
            r["_amendment_g_rejudged"] = True
            r["_amendment_h_patched"] = True
            patched = True
            print("   -> B041 (5_Full_TERRA) record cleanly updated in memory.")
            break

    if not patched:
        print("[WATCHDOG GATE] ERROR: B041 5_Full_TERRA record not found in raw file!")
        sys.exit(1)

    temp_path = f"{RAW_PATH}.tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    os.replace(temp_path, RAW_PATH)
    print(f"   -> Atomically saved {len(records)} records to {RAW_PATH}.")


def run_tier1_verification():
    print("\n[WATCHDOG GATE] Executing Tier 1 Verification Gate...")
    py_bin = sys.executable
    script_path = os.path.join(ROOT_DIR, "scripts", "verify_baselines_tier1.py")
    res = subprocess.run([py_bin, script_path], cwd=ROOT_DIR, capture_output=True, text=True)
    print(res.stdout)
    if res.returncode != 0:
        print(f"[WATCHDOG GATE] Tier 1 verification FAILED (exit code {res.returncode})!")
        sys.exit(res.returncode)
    print("[WATCHDOG GATE] Tier 1 Verification PASSED 100% CLEAN.")


def main():
    print("=" * 80)
    print("TERRA WORKSTREAM 1.2: CATEGORY B BOUNDARY WATCHDOG & AMENDMENT H GATE")
    print("=" * 80)
    print(f"Monitoring: {RAW_PATH}")
    print("Target: Query B100 completion (Hard Halt before Category C)\n")

    while True:
        try:
            if os.path.exists(RAW_PATH):
                with open(RAW_PATH, "r", encoding="utf-8") as f:
                    records = json.load(f)
                b_qids = sorted(list(set(r["query_id"] for r in records if r.get("query_id", "").startswith("B"))))
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Committed Cat B queries: {len(b_qids)}/100 (Latest: {b_qids[-1] if b_qids else 'None'})")

                if len(b_qids) >= 100 and "B100" in b_qids:
                    print("\n" + "!" * 80)
                    print("[BOUNDARY TRIPPED] Query B100 successfully committed!")
                    print("Executing hard stop before Category C begins...")
                    print("!" * 80)

                    # 1. Terminate runner
                    terminate_runner()

                    # 2. Patch B041 on quiescent file
                    apply_b041_patch()

                    # 3. Run Tier 1 verification
                    run_tier1_verification()

                    # 4. Write certification lockfile
                    os.makedirs(os.path.dirname(LOCK_PATH), exist_ok=True)
                    with open(LOCK_PATH, "w", encoding="utf-8") as f:
                        f.write(json.dumps({
                            "timestamp": datetime.now().isoformat(),
                            "category_b_status": "CLOSED_AND_CERTIFIED",
                            "total_cat_b_queries": 100,
                            "amendment_h_applied": True,
                            "tier1_status": "ALL_PASSED_100_PERCENT"
                        }, indent=2))
                    print(f"\n[WATCHDOG GATE] Lockfile written: {LOCK_PATH}")
                    print("=" * 80)
                    print(">>> CATEGORY B OFFICIALLY CERTIFIED & CLOSED. RUNNER HALTED CLEANLY. <<<")
                    print(">>> CATEGORY C AWAITS HUMAN PROTOCOL AUTHORIZATION. <<<")
                    print("=" * 80 + "\n")
                    break

        except Exception as e:
            print(f"[WATCHDOG] Polling error: {e}")

        time.sleep(5)


if __name__ == "__main__":
    main()
