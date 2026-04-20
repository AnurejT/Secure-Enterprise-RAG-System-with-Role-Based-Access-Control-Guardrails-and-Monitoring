"""
Token Usage & Cost Tracker
Extracts token counts from Groq/LangChain response metadata and computes estimated cost.
"""

import threading
from datetime import datetime

# ─── Groq pricing (per 1M tokens, USD) ────────────────────────────
# llama-3.1-8b-instant pricing (approximate, check groq.com for latest)
PRICE_PER_1M = {
    "prompt_tokens":     0.05,   # $0.05 / 1M input tokens
    "completion_tokens": 0.08,   # $0.08 / 1M output tokens
}

# ─── Thread-safe in-memory accumulator ───────────────────────────
_lock  = threading.Lock()
_totals = {
    "prompt_tokens":     0,
    "completion_tokens": 0,
    "total_tokens":      0,
    "total_cost_usd":    0.0,
    "call_count":        0,
}
_last_calls = []   # ring buffer, last 50 calls


def record_usage(usage: dict, role: str = "unknown", query_preview: str = ""):
    """
    Call after every LLM invocation.
    `usage` should be the dict from response.response_metadata['token_usage']
    """
    if not usage:
        return

    prompt_tokens     = usage.get("prompt_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)
    total_tokens      = usage.get("total_tokens", prompt_tokens + completion_tokens)

    cost = (
        prompt_tokens     / 1_000_000 * PRICE_PER_1M["prompt_tokens"] +
        completion_tokens / 1_000_000 * PRICE_PER_1M["completion_tokens"]
    )

    with _lock:
        _totals["prompt_tokens"]     += prompt_tokens
        _totals["completion_tokens"] += completion_tokens
        _totals["total_tokens"]      += total_tokens
        _totals["total_cost_usd"]    += cost
        _totals["call_count"]        += 1

        _last_calls.append({
            "timestamp":        datetime.utcnow().isoformat() + "Z",
            "role":             role,
            "query_preview":    query_preview[:80],
            "prompt_tokens":    prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens":     total_tokens,
            "cost_usd":         round(cost, 6),
        })
        # Keep only last 50
        if len(_last_calls) > 50:
            _last_calls.pop(0)


def get_totals() -> dict:
    with _lock:
        return {**_totals, "total_cost_usd": round(_totals["total_cost_usd"], 6)}


def get_recent_calls(n: int = 20) -> list:
    with _lock:
        return list(_last_calls[-n:])


def reset():
    with _lock:
        for k in _totals:
            _totals[k] = 0 if isinstance(_totals[k], int) else 0.0
        _last_calls.clear()
