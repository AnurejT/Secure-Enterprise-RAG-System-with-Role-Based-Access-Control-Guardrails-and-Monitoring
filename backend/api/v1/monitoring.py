"""
backend/api/v1/monitoring.py
Monitoring blueprint — Ragas metrics, token usage, manual eval, reset.
Renamed from monitoring_routes.py; imports updated to monitoring.repository.
"""
from flask import Blueprint, jsonify, request

from backend.monitoring import repository
from backend.monitoring.evaluator import run_ragas_eval_safe

monitoring_bp = Blueprint("monitoring", __name__)


@monitoring_bp.route("/metrics", methods=["GET"])
def get_metrics():
    return jsonify({
        "ragas":  repository.get_aggregate(),
        "tokens": repository.get_token_totals(),
    })


@monitoring_bp.route("/history", methods=["GET"])
def get_history():
    n = min(int(request.args.get("n", 20)), 100)
    return jsonify({"history": list(reversed(repository.get_recent_evals(n)))})


@monitoring_bp.route("/token-usage", methods=["GET"])
def get_token_usage():
    return jsonify(repository.get_token_totals())


@monitoring_bp.route("/evaluate", methods=["POST"])
def manual_evaluate():
    data     = request.get_json() or {}
    question = data.get("question", "")
    answer   = data.get("answer", "")
    contexts = data.get("contexts", [])
    if not question or not answer:
        return jsonify({"error": "question and answer are required"}), 400
    return jsonify(run_ragas_eval_safe(question, answer, contexts))


@monitoring_bp.route("/reset", methods=["DELETE"])
def reset_metrics():
    repository.reset()
    return jsonify({"message": "Metrics reset"})
