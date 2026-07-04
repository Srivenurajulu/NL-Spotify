from __future__ import annotations


SYSTEM_PROMPT = (
    "You are an analyst synthesizing evidence from user reviews. "
    "Use only the provided review excerpts as evidence. "
    "If the corpus is insufficient, say so explicitly."
)


def answer_prompt(question: str, reviews: list[dict]) -> str:
    """
    reviews items include: {text, url, source, date, score, author, country, behavior_tags}
    """
    preview_lines = []
    for i, r in enumerate(reviews, start=1):
        url = r.get("url") or ""
        source = r.get("source") or ""
        date = r.get("date") or ""
        score = r.get("score")
        score_str = str(score) if score is not None else ""
        preview_lines.append(
            f"[{i}] {source} {date} score={score_str} country={r.get('country','')}\n"
            f"URL: {url}\n"
            f"TEXT: {r.get('text','')}\n"
        )

    evidence_block = "\n".join(preview_lines)
    return (
        f"Question: {question}\n\n"
        "Evidence excerpts (use these as your only sources):\n"
        f"{evidence_block}\n"
        "\n"
        "Task:\n"
        "1) Provide a direct, concise answer (2 to 4 sentences).\n"
        "2) List 3 to 6 themes, each theme with a short explanation.\n"
        "3) Include 3 to 6 specific quotes or near-quotes from the evidence. "
        "For each quote, include the evidence index (like [2]) and the URL.\n"
        "4) Note any uncertainty due to limited reviews or missing sources.\n"
    )

