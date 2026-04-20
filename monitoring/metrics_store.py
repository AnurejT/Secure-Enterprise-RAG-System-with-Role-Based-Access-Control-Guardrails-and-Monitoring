"""
Metrics Store — in-memory store for per-query evaluation results.
Provides aggregates for the monitoring dashboard.
"""

import threading
from datetime import datetime
from collections import defaultdict

_lock    = threading.Lock()
_entries = []   # list of metric dicts


def record_eval(
    query:    str,
    answer:   str,
    role:     str,
    scores:   dict,
    token_usage: dict = None,
    latency_ms: float = None,
):
    """Store a completed query evaluation record."""
    entry = {
        "timestamp":        datetime.utcnow().isoformat() + "Z",
        "role":             role,
        "query_preview":    query[:100],
        "answer_preview":   answer[:150],
        "answer_relevancy": scores.get("answer_relevancy"),
        "faithfulness":     scores.get("faithfulness"),
        "context_relevancy": scores.get("context_relevancy"),
        "ragas_error":      scores.get("error"),
        "prompt_tokens":    (token_usage or {}).get("prompt_tokens"),
        "completion_tokens":(token_usage or {}).get("completion_tokens"),
        "total_tokens":     (token_usage or {}).get("total_tokens"),
        "latency_ms":       latency_ms,
    }
    with _lock:
        _entries.append(entry)
        if len(_entries) > 200:   # keep last 200
            _entries.pop(0)


def get_recent(n: int = 30) -> list:
    with _lock:
        return list(_entries[-n:])


def get_aggregate() -> dict:
    """Return averaged Ragas metrics and totals across all stored entries."""
    with _lock:
        if not _entries:
            return {
                "total_queries":     0,
                "avg_answer_relevancy":  None,
                "avg_faithfulness":      None,
                "avg_context_relevancy": None,
                "by_role":          {},
            }

        def safe_avg(vals):
            filtered = [v for v in vals if v is not None]
            return round(sum(filtered) / len(filtered), 4) if filtered else None

        ar  = [e["answer_relevancy"]  for e in _entries]
        ff  = [e["faithfulness"]      for e in _entries]
        cp  = [e["context_relevancy"] for e in _entries]

        # Per-role breakdown
        by_role = defaultdict(lambda: {"count": 0, "ar": [], "ff": [], "cp": []})
        for e in _entries:
            r = e["role"]
            by_role[r]["count"] += 1
            by_role[r]["ar"].append(e["answer_relevancy"])
            by_role[r]["ff"].append(e["faithfulness"])
            by_role[r]["cp"].append(e["context_relevancy"])

        role_summary = {}
        for role, d in by_role.items():
            role_summary[role] = {
                "count":             d["count"],
                "avg_answer_relevancy":  safe_avg(d["ar"]),
                "avg_faithfulness":      safe_avg(d["ff"]),
                "avg_context_relevancy": safe_avg(d["cp"]),
            }

        return {
            "total_queries":         len(_entries),
            "avg_answer_relevancy":  safe_avg(ar),
            "avg_faithfulness":      safe_avg(ff),
            "avg_context_relevancy": safe_avg(cp),
            "by_role":               role_summary,
        }
