"""
backend/monitoring/evaluator.py
Ragas evaluation using Groq + HuggingFace — no OpenAI key required.
"""
import os
from typing import List

from backend.core.config import GROQ_API_KEY, GROQ_MODEL, EMBEDDING_MODEL


def _build_ragas_llm():
    from ragas.llms import LangchainLLMWrapper
    from langchain_groq import ChatGroq
    return LangchainLLMWrapper(
        ChatGroq(temperature=0, model=GROQ_MODEL, groq_api_key=GROQ_API_KEY)
    )


def _build_ragas_embeddings():
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from langchain_huggingface import HuggingFaceEmbeddings
    return LangchainEmbeddingsWrapper(HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL))


def _safe_float(val) -> float | None:
    try:
        f = float(val)
        return round(f, 4) if f == f else None
    except (TypeError, ValueError):
        return None


def run_ragas_eval(question: str, answer: str, contexts: List[str]) -> dict:
    try:
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import answer_relevancy, faithfulness, context_relevancy

        ragas_llm = _build_ragas_llm()
        ragas_emb = _build_ragas_embeddings()

        answer_relevancy.llm        = ragas_llm
        answer_relevancy.embeddings = ragas_emb
        faithfulness.llm            = ragas_llm
        context_relevancy.llm       = ragas_llm

        dataset = Dataset.from_dict({
            "question": [question],
            "answer":   [answer],
            "contexts": [contexts if contexts else [""]],
        })

        result = evaluate(
            dataset,
            metrics=[answer_relevancy, faithfulness, context_relevancy],
            raise_exceptions=False,
        )
        scores = result.to_pandas().iloc[0].to_dict()

        return {
            "answer_relevancy":  _safe_float(scores.get("answer_relevancy")),
            "faithfulness":      _safe_float(scores.get("faithfulness")),
            "context_relevancy": _safe_float(scores.get("context_relevancy")),
            "error": None,
        }

    except Exception as e:
        print(f"[Ragas] Evaluation error: {e}")
        return {
            "answer_relevancy":  None,
            "faithfulness":      None,
            "context_relevancy": None,
            "error": str(e)[:200],
        }


def run_ragas_eval_safe(question: str, answer: str, contexts: List[str]) -> dict:
    """Non-crashing wrapper — always returns a dict."""
    try:
        return run_ragas_eval(question, answer, contexts)
    except Exception as e:
        return {
            "answer_relevancy":  None,
            "faithfulness":      None,
            "context_relevancy": None,
            "error": str(e)[:200],
        }
