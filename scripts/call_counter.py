"""
scripts/call_counter.py - Outbound Model Call Counter, Telemetry Logger, and Hard-Cap Guard (Tasks A4, C4, D4, D5)
================================================================================================================
Intercepts and counts every outbound model call by type:
  - router
  - grader/NLI
  - generation
  - judge

Enforces a hard cap of <= 120 calls in pilot mode (Round 10 limit), raising RuntimeError if exceeded.
Records fine-grained per-call telemetry to logs/call_telemetry_<suite or pilot>.jsonl with unique call_id.
Single choke-point counting: patches Completions.create once with deduplication and re-entrancy protection.
Atomic saves: on PermissionError retries os.replace up to 10 times with 0.3s backoff and fsync fallback.
Generates logs/pilot_call_counts.txt and logs/call_breakdown_pilot.txt.
"""

import os
import json
import time
import uuid
import inspect
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_STATE_FILE = (ROOT / "scratch" / "pilot_call_counts.json").resolve()
DEFAULT_LOG_FILE = (ROOT / "logs" / "pilot_call_counts.txt").resolve()

_ACTIVE_COUNTER = None
_LOCK = threading.Lock()
_CURRENT_CONTEXT = {
    "query_id": "N/A",
    "arm": "N/A",
    "suite": "obscure",
    "is_pilot": False,
    "run_id": "default",
    "mode": "live"
}

_CALL_STATE = threading.local()
_PROCESSED_CALL_IDS = set()
_PATCHED_COMPLETIONS_CREATE = False

def set_call_context(query_id: str = None, arm: str = None, suite: str = None, is_pilot: bool = None, run_id: str = None, mode: str = None):
    with _LOCK:
        if query_id is not None:
            _CURRENT_CONTEXT["query_id"] = query_id
        if arm is not None:
            _CURRENT_CONTEXT["arm"] = arm
        if suite is not None:
            _CURRENT_CONTEXT["suite"] = suite
        if is_pilot is not None:
            _CURRENT_CONTEXT["is_pilot"] = is_pilot
        if run_id is not None:
            _CURRENT_CONTEXT["run_id"] = run_id
        if mode is not None:
            _CURRENT_CONTEXT["mode"] = mode

def get_call_context() -> dict:
    with _LOCK:
        return dict(_CURRENT_CONTEXT)

class ModelCallCounter:
    def __init__(self, is_pilot: bool = False, max_cap: int = None, state_file: Path = None):
        self.is_pilot = is_pilot
        self.max_cap = (120 if is_pilot else 700) if max_cap is None else max_cap
        self.state_file = Path(state_file) if state_file is not None else DEFAULT_STATE_FILE
        self.counts = {
            "router": 0,
            "grader/NLI": 0,
            "generation": 0,
            "judge": 0
        }
        self.load_state()

    def reset(self):
        with _LOCK:
            self.counts = {
                "router": 0,
                "grader/NLI": 0,
                "generation": 0,
                "judge": 0
            }
            self.save_state()

    def load_state(self):
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for k in self.counts:
                        self.counts[k] = data.get(k, 0)
            except Exception:
                pass

    def save_state(self):
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        temp = self.state_file.with_suffix(".tmp")
        with open(temp, "w", encoding="utf-8") as f:
            json.dump(self.counts, f, indent=2)
            f.flush()
            try:
                os.fsync(f.fileno())
            except Exception:
                pass

        for attempt in range(10):
            try:
                os.replace(temp, self.state_file)
                return
            except PermissionError:
                if attempt < 9:
                    time.sleep(0.3)
                else:
                    try:
                        with open(self.state_file, "w", encoding="utf-8") as f:
                            json.dump(self.counts, f, indent=2)
                            f.flush()
                            try:
                                os.fsync(f.fileno())
                            except Exception:
                                pass
                        return
                    except Exception:
                        pass
                    raise

    def classify_call(self, model: str, messages: list, extra_kwargs: dict) -> str:
        m_lower = (model or "").lower()
        if m_lower in ["databricks-qwen3-next-80b-a3b-instruct", "databricks-gpt-oss-120b"]:
            return "judge"

        content_str = ""
        for m in (messages or []):
            if isinstance(m, dict) and "content" in m:
                c = m["content"]
                if isinstance(c, str):
                    content_str += c + " "
            elif isinstance(m, str):
                content_str += m + " "

        if "expert Supreme Court judicial evaluator" in content_str or "SCORING CRITERIA AND TAXONOMY" in content_str:
            return "judge"

        extra_str = str(extra_kwargs or "")
        if "RoutingDecision" in extra_str or "Routing Decision" in content_str or "ROUTER PROMPT" in content_str:
            return "router"
        if "router" in m_lower or "gemma-3-12b" in m_lower:
            return "router"

        if "GradeDecision" in extra_str or "GradeDecision" in content_str or "VERIFIER EVALUATION PROMPT" in content_str or "confidence_score" in content_str or "factual accuracy" in content_str:
            return "grader/NLI"
        if "grader" in m_lower or "gemma-4-26b" in m_lower:
            return "grader/NLI"

        return "generation"

    def record_call(self, model: str, messages: list, extra_kwargs: dict):
        with _LOCK:
            self.load_state()
            call_type = self.classify_call(model, messages, extra_kwargs)
            self.counts[call_type] = self.counts.get(call_type, 0) + 1
            total = sum(self.counts.values())
            self.save_state()

            if total > self.max_cap:
                mode_str = "PILOT" if self.is_pilot else "FULL RUN"
                raise RuntimeError(
                    f"[{mode_str} CALL CAP EXCEEDED] Total outbound model calls ({total}) exceeded hard cap of {self.max_cap}! "
                    f"Breakdown: {self.counts}"
                )
            return call_type, total

    def log_telemetry(self, call_type: str, model_requested: str, calling_func: str, latency_ms: float, tokens: dict, call_id: str = None):
        ctx = get_call_context()
        suite = ctx.get("suite", "obscure")
        is_pilot = ctx.get("is_pilot", self.is_pilot)
        mode = ctx.get("mode", "live")
        
        # Determine test vs live mode
        if (
            mode == "test"
            or calling_func == "run_offline_unit_tests"
            or "test" in str(calling_func).lower()
            or str(suite).startswith("test")
        ):
            mode = "test"
            
        run_id = ctx.get("run_id") or ("test_run" if mode == "test" else f"live_{suite}")
        
        telemetry_filename = f"call_telemetry_{'pilot' if is_pilot else suite}.jsonl"
        if mode == "test":
            telemetry_path = ROOT / "logs" / "test_telemetry" / telemetry_filename
        else:
            telemetry_path = ROOT / "logs" / telemetry_filename
            
        telemetry_path.parent.mkdir(parents=True, exist_ok=True)
        
        record = {
            "call_id": call_id or f"call_{uuid.uuid4().hex[:12]}",
            "run_id": run_id,
            "mode": mode,
            "timestamp": time.time(),
            "query_id": ctx.get("query_id", "N/A"),
            "arm": ctx.get("arm", "N/A"),
            "call_type": call_type,
            "model_requested": model_requested,
            "calling_function": calling_func,
            "latency_ms": latency_ms,
            "tokens": tokens
        }
        
        with _LOCK:
            with open(telemetry_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")

    def write_log(self, log_path: Path = DEFAULT_LOG_FILE):
        with _LOCK:
            self.load_state()
            log_path = Path(log_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            total = sum(self.counts.values())
            lines = [
                "=" * 80,
                "PILOT OUTBOUND MODEL CALL AUDIT TRAIL (TASKS A4, C4, D5)",
                "=" * 80,
                f"Pilot Mode Active : {self.is_pilot}",
                f"Hard Cap Limit    : {self.max_cap}",
                "",
                "CALL BREAKDOWN BY TYPE:",
                f"  - router        : {self.counts.get('router', 0):>4}",
                f"  - grader/NLI    : {self.counts.get('grader/NLI', 0):>4}",
                f"  - generation    : {self.counts.get('generation', 0):>4}",
                f"  - judge         : {self.counts.get('judge', 0):>4}",
                "-" * 80,
                f"TOTAL CALLS       : {total:>4}",
                f"VERDICT           : {'PASSED (Within cap)' if total <= self.max_cap else 'FAILED (Exceeded cap)'}",
                "=" * 80,
                ""
            ]
            log_path.write_text("\n".join(lines), encoding="utf-8")
            print(f"[CALL COUNTER] Wrote call audit trail to {log_path.resolve()} (Total calls: {total})")

    def write_breakdown_report(self, log_path: Path = None, telemetry_path: Path = None, run_id: str = None):
        ctx = get_call_context()
        suite = ctx.get("suite", "obscure")
        is_pilot = ctx.get("is_pilot", self.is_pilot)
        target_run_id = run_id or ctx.get("run_id")
        
        if telemetry_path is None:
            telemetry_path = ROOT / "logs" / f"call_telemetry_{'pilot' if is_pilot else suite}.jsonl"
        if log_path is None:
            log_path = ROOT / "logs" / f"call_breakdown_{'pilot' if is_pilot else suite}.txt"
            
        counts_by_arm_func = {}
        if telemetry_path.exists():
            with open(telemetry_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                        if target_run_id and rec.get("run_id") and rec.get("run_id") != target_run_id:
                            continue
                        arm = rec.get("arm", "N/A")
                        func = rec.get("calling_function", "unknown")
                        ctype = rec.get("call_type", "unknown")
                        key = (arm, func, ctype)
                        counts_by_arm_func[key] = counts_by_arm_func.get(key, 0) + 1
                    except Exception:
                        pass

        lines = [
            "=" * 90,
            f"PILOT CALL BREAKDOWN BY (ARM, CALLING FUNCTION, CALL TYPE)",
            "=" * 90,
            f"Telemetry Source: {telemetry_path.resolve()}",
            "",
            f"{'Arm':<24} | {'Calling Function':<35} | {'Type':<12} | {'Count':<6}",
            "-" * 90
        ]
        
        total_calls = 0
        for (arm, func, ctype), cnt in sorted(counts_by_arm_func.items()):
            lines.append(f"{arm:<24} | {func:<35} | {ctype:<12} | {cnt:>5}")
            total_calls += cnt
            
        lines.append("-" * 90)
        lines.append(f"TOTAL LOGGED CALLS: {total_calls}")
        lines.append("=" * 90)
        lines.append("")
        
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"[CALL COUNTER] Wrote detailed call breakdown to {log_path.resolve()} ({total_calls} calls accounted for)")


def inspect_calling_function() -> str:
    """Walks back stack to find the original domain caller outside call_counter and openai."""
    calling_func = "unknown"
    skip_funcs = {
        "inspect_calling_function", "create", "_call", "call_with_retry", 
        "wrapper", "generate_content_with_retry_openai", "__call__", "dispatch_counted_call"
    }
    try:
        stack = inspect.stack()
        for frame_info in stack:
            func = frame_info.function
            module = inspect.getmodule(frame_info.frame)
            mod_name = module.__name__ if module else ""
            if "call_counter" not in mod_name and "openai" not in mod_name:
                if func not in skip_funcs:
                    calling_func = func
                    break
    except Exception:
        pass
    return calling_func


def dispatch_counted_call(original_create_fn, instance, *args, **kwargs):
    """
    Task D5: Single choke point for model call interception.
    Guarantees that re-entrant calls on the same thread are not double-counted,
    assigns unique call_ids, and dedupes execution.
    """
    global _ACTIVE_COUNTER
    counter = get_active_counter()
    if counter is None:
        if instance is not None:
            return original_create_fn(instance, *args, **kwargs)
        return original_create_fn(*args, **kwargs)

    # Re-entrancy guard: if thread is already inside an intercepted create(), bypass counting
    if getattr(_CALL_STATE, "in_call", False):
        if instance is not None:
            return original_create_fn(instance, *args, **kwargs)
        return original_create_fn(*args, **kwargs)

    call_id = f"call_{uuid.uuid4().hex[:12]}"
    with _LOCK:
        if call_id in _PROCESSED_CALL_IDS:
            if instance is not None:
                return original_create_fn(instance, *args, **kwargs)
            return original_create_fn(*args, **kwargs)
        _PROCESSED_CALL_IDS.add(call_id)

    _CALL_STATE.in_call = True
    try:
        model = kwargs.get("model", "")
        messages = kwargs.get("messages", [])
        extra = {k: v for k, v in kwargs.items() if k not in ["model", "messages"]}

        call_type, total = counter.record_call(model, messages, extra)
        calling_func = inspect_calling_function()

        t0 = time.time()
        if instance is not None:
            resp = original_create_fn(instance, *args, **kwargs)
        else:
            resp = original_create_fn(*args, **kwargs)
        latency_ms = round((time.time() - t0) * 1000, 2)

        tokens = None
        usage = getattr(resp, "usage", None)
        if usage:
            tokens = {
                "prompt_tokens": getattr(usage, "prompt_tokens", None),
                "completion_tokens": getattr(usage, "completion_tokens", None),
                "total_tokens": getattr(usage, "total_tokens", None)
            }

        counter.log_telemetry(
            call_type=call_type,
            model_requested=model,
            calling_func=calling_func,
            latency_ms=latency_ms,
            tokens=tokens,
            call_id=call_id
        )
        return resp
    finally:
        _CALL_STATE.in_call = False


def patch_completions_create_once():
    """Patches openai.resources.chat.completions.Completions.create exactly once."""
    global _PATCHED_COMPLETIONS_CREATE
    if _PATCHED_COMPLETIONS_CREATE:
        return
    try:
        from openai.resources.chat.completions import Completions
        if not getattr(Completions.create, "_is_counting_patched", False):
            orig_create = Completions.create
            def patched_create(self, *args, **kwargs):
                return dispatch_counted_call(orig_create, self, *args, **kwargs)
            patched_create._is_counting_patched = True
            Completions.create = patched_create
            _PATCHED_COMPLETIONS_CREATE = True
    except Exception:
        pass


class CountingChatCompletions:
    def __init__(self, original_completions, counter: ModelCallCounter):
        self._original = original_completions
        self._counter = counter

    def create(self, *args, **kwargs):
        return dispatch_counted_call(self._original.create, None, *args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._original, name)


class CountingChat:
    def __init__(self, original_chat, counter: ModelCallCounter):
        self._original = original_chat
        self._counter = counter
        self.completions = CountingChatCompletions(original_chat.completions, counter)

    def __getattr__(self, name):
        return getattr(self._original, name)


def wrap_client_with_counter(client, is_pilot: bool = False, reset_state: bool = False, max_cap: int = None, state_file: Path = None) -> object:
    global _ACTIVE_COUNTER
    if max_cap is None:
        max_cap = 120 if is_pilot else 700
    if state_file is None:
        state_file = DEFAULT_STATE_FILE
    if _ACTIVE_COUNTER is None:
        _ACTIVE_COUNTER = ModelCallCounter(is_pilot=is_pilot, max_cap=max_cap, state_file=state_file)
    else:
        _ACTIVE_COUNTER.is_pilot = is_pilot
        _ACTIVE_COUNTER.max_cap = max_cap
        _ACTIVE_COUNTER.state_file = Path(state_file)

    if reset_state:
        _ACTIVE_COUNTER.reset()

    patch_completions_create_once()

    # Prevent re-wrapping the same client instance
    if getattr(client, "_is_counter_wrapped", False):
        return client
    try:
        client._is_counter_wrapped = True
    except Exception:
        pass

    if hasattr(client, "chat") and hasattr(client.chat, "completions"):
        orig_create = client.chat.completions.create
        if not getattr(orig_create, "_is_counting_patched", False):
            def instance_create(*args, **kwargs):
                return dispatch_counted_call(orig_create, None, *args, **kwargs)
            instance_create._is_counting_patched = True
            try:
                client.chat.completions.create = instance_create
            except Exception:
                client.chat = CountingChat(client.chat, _ACTIVE_COUNTER)
    return client

def get_active_counter() -> ModelCallCounter:
    global _ACTIVE_COUNTER
    return _ACTIVE_COUNTER

def set_active_counter(counter: ModelCallCounter):
    global _ACTIVE_COUNTER
    _ACTIVE_COUNTER = counter
