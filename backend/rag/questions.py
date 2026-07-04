from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReviewQuestion:
    key: str
    title: str
    # Use this as the semantic search query against Chroma.
    search_query: str
    # Used as the user-visible question text in the LLM prompt.
    prompt_question: str


QUESTIONS: dict[str, ReviewQuestion] = {
    "discover_new_music": ReviewQuestion(
        key="discover_new_music",
        title="Why do users struggle to discover new music?",
        search_query="discover new music recommendation discovery weekly discover why struggle",
        prompt_question="Why do users struggle to discover new music?",
    ),
    "recommendation_frustrations": ReviewQuestion(
        key="recommendation_frustrations",
        title="Most common frustrations with recommendations",
        search_query="recommendations frustration repeated songs same songs discover weekly skip ads explain why",
        prompt_question="What are the most common frustrations with recommendations?",
    ),
    "listening_behaviors": ReviewQuestion(
        key="listening_behaviors",
        title="Listening behaviors users are trying to achieve",
        search_query="listening behavior mood transition focus wind down commuting gym sleep autoplay radio",
        prompt_question="What listening behaviors are users trying to achieve?",
    ),
    "repeat_listening_causes": ReviewQuestion(
        key="repeat_listening_causes",
        title="Causes of repeatedly listening to the same content",
        search_query="repeat listen to same content repeats distrust safe fallback replay playlist weeks after miss",
        prompt_question="What causes users to repeatedly listen to the same content?",
    ),
    "discovery_segments": ReviewQuestion(
        key="discovery_segments",
        title="User segments with different discovery challenges",
        search_query="segment discovery challenge defensive fallback open time listeners skip within 15 seconds repeats",
        prompt_question="Which user segments experience different discovery challenges?",
    ),
    "unmet_needs": ReviewQuestion(
        key="unmet_needs",
        title="Unmet needs that emerge consistently",
        search_query="unmet need explanation why recommended reason trust poor repair mismatch",
        prompt_question="What unmet needs emerge consistently across reviews?",
    ),
}

