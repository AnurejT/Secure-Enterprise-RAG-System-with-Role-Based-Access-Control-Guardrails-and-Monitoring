"""
backend/monitoring/repository.py
Thread-safe in-memory store for Ragas evaluation records and token usage.
Moved from repositories/metrics_repo.py.
"""
import threading
from collections import defaultdict
from datetime import datetime

# ── Token pricing (Groq — llama-3.1-8b-instant) ──────────────────────
_PRICE_PER_1M = {
    "prompt_tokens":     0.05,
    "completion_tokens": 0.08,
}

# ── Thread-safe state ────────────────────────────────────────────────
_lock = threading.Lock()

_eval_entries: list = []   # last 200 Ragas evaluation records

_token_totals: dict = {
    "prompt_tokens":     0,
    "completion_tokens": 0,
    "total_tokens":      0,
    "total_cost_usd":    0.0,
    "call_count":        0,
}
_recent_calls: list = []   # last 50 LLM calls


# ─────────────────────────── TOKEN TRACKING ──────────────────────────

def record_token_usage(usage: dict, role: str = "unknown", query_preview: str = "") -> None:
    if not usage:
        return

    pt = usage.get("prompt_tokens", 0)
    ct = usage.get("completion_tokens", 0)
    tt = usage.get("total_tokens", pt + ct)
    cost = pt / 1_000_000 * _PRICE_PER_1M["prompt_tokens"] + \
           ct / 1_000_000 * _PRICE_PER_1M["completion_tokens"]

    with _lock:
        _token_totals["prompt_tokens"]     += pt
        _token_totals["completion_tokens"] += ct
        _token_totals["total_tokens"]      += tt
        _token_totals["total_cost_usd"]    += cost
        _token_totals["call_count"]        += 1

        _recent_calls.append({
            "timestamp":        datetime.utcnow().isoformat() + "Z",
            "role":             role,
            "query_preview":    query_preview[:80],
            "prompt_tokens":    pt,
            "completion_tokens": ct,
            "total_tokens":     tt,
            "cost_usd":         round(cost, 6),
        })
        if len(_recent_calls) > 50:
            _recent_calls.pop(0)


def get_token_totals() -> dict:
    with _lock:
        return {**_token_totals, "total_cost_usd": round(_token_totals["total_cost_usd"], 6)}


def get_recent_calls(n: int = 20) -> list:
    with _lock:
        return list(_recent_calls[-n:])


# ─────────────────────────── EVAL RECORDS ────────────────────────────

def record_eval(
    query:       str,
    answer:      str,
    role:        str,
    scores:      dict,
    token_usage: dict  = None,
    latency_ms:  float = None,
) -> None:
    entry = {
        "timestamp":         datetime.utcnow().isoformat() + "Z",
        "role":              role,
        "query_preview":     query[:100],
        "answer_preview":    answer[:150],
        "answer_relevancy":  scores.get("answer_relevancy"),
        "faithfulness":      scores.get("faithfulness"),
        "context_relevancy": scores.get("context_relevancy"),
        "ragas_error":       scores.get("error"),
        "prompt_tokens":     (token_usage or {}).get("prompt_tokens"),
        "completion_tokens": (token_usage or {}).get("completion_tokens"),
        "total_tokens":      (token_usage or {}).get("total_tokens"),
        "latency_ms":        latency_ms,
    }
    with _lock:
        _eval_entries.append(entry)
        if len(_eval_entries) > 200:
            _eval_entries.pop(0)


def get_recent_evals(n: int = 30) -> list:
    with _lock:
        return list(_eval_entries[-n:])


def get_aggregate() -> dict:
    with _lock:
        if not _eval_entries:
            return {
                "total_queries":          0,
                "avg_answer_relevancy":   None,
                "avg_faithfulness":       None,
                "avg_context_relevancy":  None,
                "by_role":                {},
            }

        def safe_avg(vals):
            filtered = [v for v in vals if v is not None]
            return round(sum(filtered) / len(filtered), 4) if filtered else None

        ar = [e["answer_relevancy"]  for e in _eval_entries]
        ff = [e["faithfulness"]      for e in _eval_entries]
        cp = [e["context_relevancy"] for e in _eval_entries]

        by_role = defaultdict(lambda: {"count": 0, "ar": [], "ff": [], "cp": []})
        for e in _eval_entries:
            r = e["role"]
            by_role[r]["count"] += 1
            by_role[r]["ar"].append(e["answer_relevancy"])
            by_role[r]["ff"].append(e["faithfulness"])
            by_role[r]["cp"].append(e["context_relevancy"])

        role_summary = {
            role: {
                "count":                    d["count"],
                "avg_answer_relevancy":     safe_avg(d["ar"]),
                "avg_faithfulness":         safe_avg(d["ff"]),
                "avg_context_relevancy":    safe_avg(d["cp"]),
            }
            for role, d in by_role.items()
        }

        return {
            "total_queries":         len(_eval_entries),
            "avg_answer_relevancy":  safe_avg(ar),
            "avg_faithfulness":      safe_avg(ff),
            "avg_context_relevancy": safe_avg(cp),
            "by_role":               role_summary,
        }


def reset() -> None:
    with _lock:
        _eval_entries.clear()
        _recent_calls.clear()
        for k in _token_totals:
            _token_totals[k] = 0 if isinstance(_token_totals[k], int) else 0.0
