from flask import Blueprint, jsonify, request
from monitoring import metrics_store, token_tracker
from monitoring.ragas_eval import run_ragas_eval_safe

monitoring_bp = Blueprint("monitoring", __name__)


# ─── GET /api/monitoring/metrics ──────────────────────────────────
@monitoring_bp.route("/metrics", methods=["GET"])
def get_metrics():
    """
    Returns aggregated Ragas metrics + token usage totals.
    """
    agg    = metrics_store.get_aggregate()
    tokens = token_tracker.get_totals()
    return jsonify({
        "ragas":   agg,
        "tokens":  tokens,
    })


# ─── GET /api/monitoring/history ──────────────────────────────────
@monitoring_bp.route("/history", methods=["GET"])
def get_history():
    """
    Returns the last N query evaluation records.
    Query param: ?n=20
    """
    n = min(int(request.args.get("n", 20)), 100)
    records = metrics_store.get_recent(n)
    return jsonify({"history": list(reversed(records))})  # newest first


# ─── GET /api/monitoring/token-usage ──────────────────────────────
@monitoring_bp.route("/token-usage", methods=["GET"])
def get_token_usage():
    return jsonify(token_tracker.get_totals())


# ─── POST /api/monitoring/evaluate ────────────────────────────────
@monitoring_bp.route("/evaluate", methods=["POST"])
def manual_evaluate():
    """
    On-demand Ragas evaluation for a question/answer/contexts triple.
    Body: { question, answer, contexts: [...] }
    """
    data     = request.get_json()
    question = data.get("question", "")
    answer   = data.get("answer", "")
    contexts = data.get("contexts", [])

    if not question or not answer:
        return jsonify({"error": "question and answer are required"}), 400

    scores = run_ragas_eval_safe(question, answer, contexts)
    return jsonify(scores)


# ─── DELETE /api/monitoring/reset ─────────────────────────────────
@monitoring_bp.route("/reset", methods=["DELETE"])
def reset_metrics():
    """Reset all accumulated metrics (useful for testing)."""
    token_tracker.reset()
    return jsonify({"message": "Metrics reset"})
