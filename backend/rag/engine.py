from __future__ import annotations

from typing import Any

from backend.rag.llm import answer_with_llm
from backend.rag.questions import QUESTIONS
from backend.rag.retrieval import retrieve


def answer_review_question(question_key: str, n_results: int = 18) -> dict[str, Any]:
    """
    Runs retrieval + synthesis for one pre-defined question.
    """
    if question_key not in QUESTIONS:
        raise ValueError(f"Unknown question_key: {question_key}")

    q = QUESTIONS[question_key]
    retrieval = retrieve(q.search_query, n_results=n_results)

    # Make sure we always provide at least some evidence.
    reviews = retrieval.reviews[:n_results]
    if not reviews:
        return {
            "question": q.prompt_question,
            "answer": "No evidence could be retrieved from the current corpus.",
            "evidence_count": 0,
        }

    answer = answer_with_llm(q.prompt_question, reviews, question_key=question_key)
    return {
        "question": q.prompt_question,
        "answer": answer,
        "evidence_count": len(reviews),
    }
