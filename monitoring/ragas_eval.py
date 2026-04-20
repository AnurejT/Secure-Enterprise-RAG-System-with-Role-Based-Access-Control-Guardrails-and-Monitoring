"""
Ragas Evaluation Module — configured to use Groq + HuggingFace (no OpenAI needed)

Metrics:
  - Answer Relevancy   (needs: question + answer + embeddings)
  - Faithfulness       (needs: question + answer + contexts + LLM)
  - Context Relevancy  (needs: question + contexts + LLM)
                        ↑ replaces context_precision which requires ground_truth
"""

import os
from typing import List
from dotenv import load_dotenv

load_dotenv()


def _build_ragas_llm():
    """Create a Ragas-compatible wrapper around ChatGroq."""
    from ragas.llms import LangchainLLMWrapper
    from langchain_groq import ChatGroq

    llm = ChatGroq(
        temperature=0,
        model="llama-3.1-8b-instant",
        groq_api_key=os.getenv("GROQ_API_KEY"),
    )
    return LangchainLLMWrapper(llm)


def _build_ragas_embeddings():
    """Create a Ragas-compatible wrapper around HuggingFace embeddings (already in venv)."""
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from langchain_huggingface import HuggingFaceEmbeddings

    emb = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return LangchainEmbeddingsWrapper(emb)


def run_ragas_eval(question: str, answer: str, contexts: List[str]) -> dict:
    """
    Run Ragas metrics using Groq + HuggingFace — no OpenAI key required.

    Returns:
        {
            "answer_relevancy":  float | None,
            "faithfulness":      float | None,
            "context_relevancy": float | None,
            "error":             str | None,
        }
    """
    try:
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import answer_relevancy, faithfulness, context_relevancy

        ragas_llm = _build_ragas_llm()
        ragas_emb = _build_ragas_embeddings()

        # Attach custom LLM + embeddings to each metric
        answer_relevancy.llm        = ragas_llm
        answer_relevancy.embeddings = ragas_emb

        faithfulness.llm            = ragas_llm

        context_relevancy.llm       = ragas_llm

        data = {
            "question": [question],
            "answer":   [answer],
            "contexts": [contexts if contexts else [""]],
        }

        dataset = Dataset.from_dict(data)

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


def _safe_float(val) -> float | None:
    try:
        f = float(val)
        return round(f, 4) if f == f else None   # NaN check
    except (TypeError, ValueError):
        return None


def run_ragas_eval_safe(question: str, answer: str, contexts: List[str]) -> dict:
    """Non-crashing wrapper — always returns a dict regardless of errors."""
    try:
        return run_ragas_eval(question, answer, contexts)
    except Exception as e:
        return {
            "answer_relevancy":  None,
            "faithfulness":      None,
            "context_relevancy": None,
            "error": str(e)[:200],
        }
