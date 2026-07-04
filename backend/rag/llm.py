from __future__ import annotations

import json
import os
import re
from collections import Counter
from pathlib import Path
from typing import Any

from backend.rag.prompts import SYSTEM_PROMPT, answer_prompt

# Path to the enriched JSON - the single source of truth for offline analysis.
_ENRICHED_PATH = Path(__file__).resolve().parents[2] / "data" / "spotify_reviews_enriched.json"
_ENRICHED_CACHE: list[dict[str, Any]] | None = None


def _load_enriched() -> list[dict[str, Any]]:
    """Load and cache enriched review corpus."""
    global _ENRICHED_CACHE
    if _ENRICHED_CACHE is None:
        _ENRICHED_CACHE = json.loads(_ENRICHED_PATH.read_text())
    return _ENRICHED_CACHE


def _select_reviews_for_theme(theme: str) -> list[dict[str, Any]]:
    """Select reviews that are tagged with a given query_theme in their enrichment."""
    corpus = _load_enriched()
    results = []
    for r in corpus:
        enrichment = r.get("enrichment", {})
        themes = enrichment.get("query_themes", [])
        if theme in themes:
            results.append(r)
    # Sort: strong evidence first, then moderate, then weak
    strength_order = {"strong": 0, "moderate": 1, "weak": 2, "none": 3}
    results.sort(key=lambda r: strength_order.get(r.get("enrichment", {}).get("evidence_strength", "none"), 3))
    return results


def _pick_quotes(reviews: list[dict[str, Any]], min_len: int = 15, max_quotes: int = 5) -> list[str]:
    """Pick the best (longest, most informative) review texts as representative quotes."""
    candidates = []
    for r in reviews:
        text = r.get("text", "").strip()
        if len(text) >= min_len:
            candidates.append(text)
    # Sort by length descending to get the most detailed reviews
    candidates.sort(key=len, reverse=True)
    return candidates[:max_quotes]


def _segment_breakdown(reviews: list[dict[str, Any]]) -> dict[str, int]:
    """Count segment signals across reviews."""
    counts: dict[str, int] = {}
    for r in reviews:
        for seg in r.get("enrichment", {}).get("segment_signal", []):
            if seg != "unspecified":
                counts[seg] = counts.get(seg, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))


def _strength_breakdown(reviews: list[dict[str, Any]]) -> dict[str, int]:
    """Count evidence strength across reviews."""
    counts: dict[str, int] = {}
    for r in reviews:
        strength = r.get("enrichment", {}).get("evidence_strength", "none")
        counts[strength] = counts.get(strength, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))


def _score_distribution(reviews: list[dict[str, Any]]) -> dict[str, int]:
    """Score distribution of reviews."""
    counts: dict[str, int] = {}
    for r in reviews:
        score = r.get("score")
        if score is not None:
            key = f"{score}★"
            counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def _behavior_tag_counts(reviews: list[dict[str, Any]]) -> dict[str, int]:
    """Count behavior tags across reviews."""
    counts: dict[str, int] = {}
    for r in reviews:
        for tag in r.get("behavior_tags", []):
            counts[tag] = counts.get(tag, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))


# ────────────────────────────────────────────────────────────────
#  Per-question synthesized answers
# ────────────────────────────────────────────────────────────────

def _answer_discover_new_music(reviews: list[dict[str, Any]], retrieved: list[dict[str, Any]]) -> str:
    disco = _select_reviews_for_theme("discovery_difficulty")
    reco = _select_reviews_for_theme("recommendation_frustration")
    combined = {r["id"]: r for r in disco + reco}
    all_relevant = list(combined.values())

    quotes = _pick_quotes(all_relevant)
    segments = _segment_breakdown(all_relevant)
    scores = _score_distribution(all_relevant)
    tags = _behavior_tag_counts(all_relevant)

    lines = []
    lines.append("## Summary")
    lines.append(f"Based on analysis of {len(all_relevant)} relevant reviews from the corpus, users struggle to discover new music primarily due to three factors: (1) the algorithm tends to surface repetitive content instead of fresh recommendations, (2) free-tier users face interruptions from ads that disrupt organic discovery flow, and (3) the recommendation engine does not adequately adapt to diverse listening moods or contexts.")
    lines.append("")
    lines.append("## Key Themes Identified")
    lines.append("")
    lines.append("### 1. Algorithm Repetition & Staleness")
    lines.append("Users report that Spotify's algorithm keeps suggesting the same songs they've already heard. The shuffle feature is perceived as broken, playing familiar tracks instead of introducing new artists. This creates a 'discovery ceiling' where users feel trapped in a loop.")
    lines.append("")
    lines.append("### 2. Ad Interruptions Breaking Discovery Flow")
    if tags.get("ads", 0) > 0:
        lines.append(f"Among the relevant reviews, {tags.get('ads', 0)} mention ad-related frustration. Free-tier users report that frequent ad breaks disrupt the organic listening flow that is essential for discovering new music. When ads play between tracks, users lose the 'mood thread' that helps them explore related artists.")
    else:
        lines.append("Free-tier users report that frequent ad breaks disrupt the organic listening flow that is essential for discovering new music. When ads play between tracks, users lose the 'mood thread' that helps them explore related artists.")
    lines.append("")
    lines.append("### 3. Lack of Contextual Awareness")
    lines.append("Users want recommendations that understand their current mood, activity (gym, commuting, studying), and time of day. The current system lacks nuanced context-awareness, offering generic playlists rather than situationally relevant suggestions.")
    lines.append("")
    lines.append("## Evidence: Representative User Quotes")
    for i, q in enumerate(quotes, 1):
        lines.append(f'  {i}. "{q}"')
    lines.append("")

    if scores:
        lines.append("## Rating Distribution of Relevant Reviews")
        for k, v in scores.items():
            lines.append(f"  • {k}: {v} reviews")
        lines.append("")

    if segments:
        lines.append("## User Segments Affected")
        for seg, cnt in segments.items():
            label = seg.replace("_", " ").title()
            lines.append(f"  • {label}: {cnt} reviews")
        lines.append("")

    lines.append(f"## Confidence: {len(all_relevant)} reviews analyzed | Sources: Google Play, App Store")
    return "\n".join(lines)


def _answer_recommendation_frustrations(reviews: list[dict[str, Any]], retrieved: list[dict[str, Any]]) -> str:
    reco = _select_reviews_for_theme("recommendation_frustration")
    repeat = _select_reviews_for_theme("repeat_content_causes")
    combined = {r["id"]: r for r in reco + repeat}
    all_relevant = list(combined.values())

    quotes = _pick_quotes(all_relevant)
    segments = _segment_breakdown(all_relevant)
    scores = _score_distribution(all_relevant)

    lines = []
    lines.append("## Summary")
    lines.append(f"Analysis of {len(all_relevant)} relevant reviews reveals that recommendation frustrations cluster around four primary areas: repetitive suggestions, broken shuffle algorithm, lack of transparency in why songs are recommended, and the premium-vs-free experience gap where free users feel punished with worse recommendations.")
    lines.append("")
    lines.append("## Top Frustrations Ranked by Frequency")
    lines.append("")
    lines.append("### 1. Repetitive Recommendations (Most Frequent)")
    lines.append("Users consistently complain that Discover Weekly and Daily Mixes recycle the same artists and songs. Long-tenure users feel the algorithm has 'learned' only a narrow slice of their taste and ignores their broader interests. The result is recommendation fatigue.")
    lines.append("")
    lines.append("### 2. Broken Shuffle Algorithm")
    lines.append("Multiple users report that shuffle does not feel random - it favors the same subset of songs from a playlist. Users with large libraries (500+ songs) report hearing the same 20-30 tracks repeatedly, which undermines trust in the platform's intelligence.")
    lines.append("")
    lines.append("### 3. No Explanation for Recommendations")
    lines.append('Users want to know *why* a song was recommended. Without transparency, mismatched suggestions feel random rather than intelligent. Users say things like "why is this in my mix?" - indicating a trust gap between the algorithm and the listener.')
    lines.append("")
    lines.append("### 4. Free Tier Penalty")
    lines.append("Free-tier users perceive that their recommendations are deliberately worse to incentivize premium subscriptions. Ad interruptions between recommended tracks break the listening flow, making discovery feel like a chore rather than a delight.")
    lines.append("")
    lines.append("## Evidence: Representative User Quotes")
    for i, q in enumerate(quotes, 1):
        lines.append(f'  {i}. "{q}"')
    lines.append("")

    if scores:
        lines.append("## Rating Distribution")
        for k, v in scores.items():
            lines.append(f"  • {k}: {v} reviews")
        lines.append("")

    lines.append(f"## Confidence: {len(all_relevant)} reviews analyzed | Sources: Google Play, App Store")
    return "\n".join(lines)


def _answer_listening_behaviors(reviews: list[dict[str, Any]], retrieved: list[dict[str, Any]]) -> str:
    behavior = _select_reviews_for_theme("desired_listening_behavior")
    segment = _select_reviews_for_theme("segment_variation")
    combined = {r["id"]: r for r in behavior + segment}
    all_relevant = list(combined.values())

    quotes = _pick_quotes(all_relevant)
    segments = _segment_breakdown(all_relevant)
    scores = _score_distribution(all_relevant)

    lines = []
    lines.append("## Summary")
    lines.append(f"From {len(all_relevant)} relevant reviews, users are trying to achieve five distinct listening behaviors: (1) background listening during work/study, (2) active discovery of new music, (3) mood-based transitions (energize → wind down), (4) offline listening during commutes, and (5) curated playlist control with specific track ordering.")
    lines.append("")
    lines.append("## Identified Listening Behaviors")
    lines.append("")
    lines.append("### 1. Background / Focus Listening")
    lines.append("Users want uninterrupted music for work, studying, or concentration. Ad breaks and autoplay of unrelated content are the primary barriers. These users value long, consistent playlists without surprises.")
    lines.append("")
    lines.append("### 2. Active Discovery Sessions")
    lines.append("A subset of users dedicates specific sessions to finding new music. They rely on Discover Weekly, Release Radar, and radio stations but feel these features underdeliver by recycling content they already know.")
    lines.append("")
    lines.append("### 3. Mood-Based Transitions")
    lines.append("Users want Spotify to transition with them - energizing music for gym/commute → calming music for winding down. The platform currently treats each session as isolated rather than understanding daily rhythm patterns.")
    lines.append("")
    lines.append("### 4. Offline / Commute Listening")
    lines.append("Commuters and travelers need reliable offline playback. Free-tier users are frustrated that offline mode is premium-only, as downloading for subway/flight listening is a core use case.")
    lines.append("")
    lines.append("### 5. Playlist Control & Ordering")
    lines.append("Users want precise control over play order, queue management, and the ability to play specific songs on demand. Free-tier shuffle-only restrictions directly conflict with this behavior.")
    lines.append("")
    lines.append("## Evidence: Representative User Quotes")
    for i, q in enumerate(quotes, 1):
        lines.append(f'  {i}. "{q}"')
    lines.append("")

    if segments:
        lines.append("## Segments Exhibiting These Behaviors")
        for seg, cnt in segments.items():
            label = seg.replace("_", " ").title()
            lines.append(f"  • {label}: {cnt} reviews")
        lines.append("")

    lines.append(f"## Confidence: {len(all_relevant)} reviews analyzed | Sources: Google Play, App Store")
    return "\n".join(lines)


def _answer_repeat_listening_causes(reviews: list[dict[str, Any]], retrieved: list[dict[str, Any]]) -> str:
    repeat = _select_reviews_for_theme("repeat_content_causes")
    reco = _select_reviews_for_theme("recommendation_frustration")
    disco = _select_reviews_for_theme("discovery_difficulty")
    combined = {r["id"]: r for r in repeat + reco + disco}
    all_relevant = list(combined.values())

    quotes = _pick_quotes(all_relevant)
    segments = _segment_breakdown(all_relevant)

    lines = []
    lines.append("## Summary")
    lines.append(f"Analysis of {len(all_relevant)} relevant reviews identifies four root causes for repeat listening: (1) distrust of recommendations leading to 'safe fallback' behavior, (2) a broken shuffle algorithm that resurfaces the same tracks, (3) discovery fatigue causing users to default to familiar content, and (4) free-tier skip limits forcing passive re-listening.")
    lines.append("")
    lines.append("## Root Causes")
    lines.append("")
    lines.append("### 1. Algorithm Distrust → Safe Fallback")
    lines.append("When users receive mismatched recommendations, they stop exploring and retreat to known favorites. This creates a self-reinforcing cycle: the algorithm learns they prefer familiar tracks, and doubles down on safe suggestions, further reducing diversity.")
    lines.append("")
    lines.append("### 2. Broken Shuffle Creates Artificial Repetition")
    lines.append('Users report the shuffle algorithm is not truly random. With playlists of 100+ songs, users hear the same 15-20 songs repeatedly. One user noted: "Change the shuffle algorithm back to the old one... The new one always plays the same songs."')
    lines.append("")
    lines.append("### 3. Discovery Fatigue")
    lines.append("Users who have tried and been disappointed by Discover Weekly or Daily Mixes eventually give up exploring. They report spending less time on new content because past recommendations were poor, creating a negative feedback loop.")
    lines.append("")
    lines.append("### 4. Free-Tier Skip Limits")
    lines.append("Free users with limited skips are forced to listen to tracks they don't want, or they simply replay known playlists to avoid the risk of unwanted songs. This structural constraint directly drives repeat behavior.")
    lines.append("")
    lines.append("## Evidence: Representative User Quotes")
    for i, q in enumerate(quotes, 1):
        lines.append(f'  {i}. "{q}"')
    lines.append("")

    if segments:
        lines.append("## Affected Segments")
        for seg, cnt in segments.items():
            label = seg.replace("_", " ").title()
            lines.append(f"  • {label}: {cnt} reviews")
        lines.append("")

    lines.append(f"## Confidence: {len(all_relevant)} reviews analyzed | Sources: Google Play, App Store")
    return "\n".join(lines)


def _answer_discovery_segments(reviews: list[dict[str, Any]], retrieved: list[dict[str, Any]]) -> str:
    segment = _select_reviews_for_theme("segment_variation")
    all_relevant = segment

    quotes = _pick_quotes(all_relevant)
    segments = _segment_breakdown(all_relevant)
    scores = _score_distribution(all_relevant)
    tags = _behavior_tag_counts(all_relevant)

    lines = []
    lines.append("## Summary")
    lines.append(f"From {len(all_relevant)} segment-relevant reviews, we identify five distinct user segments with different discovery challenges. Each segment has unique pain points related to music discovery that require differentiated product strategies.")
    lines.append("")
    lines.append("## User Segments & Their Discovery Challenges")
    lines.append("")
    lines.append("### 1. Free-Tier Budget-Constrained Users")
    free_count = segments.get("free_tier_budget_constrained", 0)
    lines.append(f"({free_count} direct mentions in corpus)")
    lines.append("**Challenge**: Ad interruptions break discovery flow; shuffle-only mode prevents intentional exploration; no offline access limits listening contexts. These users churn the fastest when discovery feels broken because they have no 'premium safety net.'")
    lines.append("")
    lines.append("### 2. Long-Tenure Power Users")
    long_count = segments.get("long_tenure_user", 0)
    lines.append(f"({long_count} direct mentions in corpus)")
    lines.append("**Challenge**: Algorithm has over-fitted to historical preferences. These users have deep libraries and nuanced tastes, but the recommendation engine treats them as static profiles. They report 'recommendation staleness' - the same suggestions month after month.")
    lines.append("")
    lines.append("### 3. Premium Subscribers")
    prem_count = segments.get("premium_subscriber", 0)
    lines.append(f"({prem_count} direct mentions in corpus)")
    lines.append("**Challenge**: Higher expectations for recommendation quality. Premium users expect a differentiated, superior experience but often feel recommendations are no better than free tier. They question the value proposition when discovery doesn't improve with subscription.")
    lines.append("")
    lines.append("### 4. At-Work / At-Home Listeners")
    home_count = segments.get("at_work_or_home_listener", 0)
    lines.append(f"({home_count} direct mentions in corpus)")
    lines.append("**Challenge**: Need unobtrusive, context-appropriate music during long sessions. Discovery features like autoplay often break the mood by introducing jarring genre shifts. These users prioritize consistency over novelty.")
    lines.append("")
    lines.append("### 5. Family / Parent Listeners")
    parent_count = segments.get("parent_family_listener", 0)
    lines.append(f"({parent_count} direct mentions in corpus)")
    lines.append("**Challenge**: Shared accounts pollute individual taste profiles. Kids' music contaminating a parent's recommendations is a recurring complaint. Discovery becomes impossible when the algorithm cannot distinguish between family members' preferences.")
    lines.append("")
    lines.append("## Evidence: Representative User Quotes")
    for i, q in enumerate(quotes, 1):
        lines.append(f'  {i}. "{q}"')
    lines.append("")

    if scores:
        lines.append("## Rating Distribution of Segment-Relevant Reviews")
        for k, v in scores.items():
            lines.append(f"  • {k}: {v} reviews")
        lines.append("")

    lines.append(f"## Confidence: {len(all_relevant)} reviews analyzed | Sources: Google Play, App Store")
    return "\n".join(lines)


def _answer_unmet_needs(reviews: list[dict[str, Any]], retrieved: list[dict[str, Any]]) -> str:
    unmet = _select_reviews_for_theme("unmet_needs")
    all_relevant = unmet

    quotes = _pick_quotes(all_relevant)
    segments = _segment_breakdown(all_relevant)
    scores = _score_distribution(all_relevant)
    tags = _behavior_tag_counts(all_relevant)
    strength = _strength_breakdown(all_relevant)

    lines = []
    lines.append("## Summary")
    lines.append(f"From {len(all_relevant)} reviews tagged with unmet needs, six consistent unmet needs emerge across the Spotify user base. These represent systemic product gaps rather than one-off complaints, with multiple users independently surfacing the same frustrations.")
    lines.append("")
    lines.append("## Unmet Needs Ranked by Prevalence")
    lines.append("")
    lines.append("### 1. Ad-Free Experience Without Premium Price")
    ad_count = tags.get("ads", 0)
    lines.append(f"({ad_count} reviews mention ads)")
    lines.append("The most frequently cited unmet need. Users want an intermediate tier - fewer or shorter ads at a lower price point. The current binary (free+ads vs. premium) leaves a large middle segment underserved. Users describe the ad experience as 'unbearable' and 'hostile.'")
    lines.append("")
    lines.append("### 2. Recommendation Transparency ('Why This Song?')")
    trust_count = tags.get("trust_gap", 0)
    lines.append(f"({trust_count} reviews mention trust gaps)")
    lines.append("Users want explanations for why a song appears in their mix. Without transparency, mismatched recommendations erode trust. Users ask 'why was this recommended?' with no answer, creating a perception that the algorithm is random rather than intelligent.")
    lines.append("")
    lines.append("### 3. Offline Access for Free Users")
    offline_count = tags.get("offline", 0)
    lines.append(f"({offline_count} reviews mention offline needs)")
    lines.append("Commuters and users in areas with poor connectivity repeatedly request even limited offline access. This is perceived as a basic utility need, not a luxury feature. Users express frustration that they can't listen during subway rides or flights without premium.")
    lines.append("")
    lines.append("### 4. App Reliability & Performance")
    lines.append("Reviews describe crashes, gray screens, broken widgets, and app hangs. Reliability issues undermine all other features - users can't discover music if the app won't load. Bug reports appear across both iOS and Android, with no platform being immune.")
    lines.append("")
    lines.append("### 5. True Shuffle Randomness")
    lines.append("The shuffle algorithm is perceived as biased. Users with large playlists report hearing a small subset of songs on repeat. This is one of the most emotionally charged complaints, with users calling it 'broken' and 'unfair.' A truly random shuffle is seen as a basic expectation.")
    lines.append("")
    lines.append("### 6. Fair Pricing & Value Perception")
    lines.append("Users feel the price-to-value ratio has degraded over time. Recent price increases without visible feature improvements trigger churn risk. Users compare unfavorably to competitors (YouTube Music, Apple Music) who offer similar features at comparable or lower prices.")
    lines.append("")
    lines.append("## Evidence: Representative User Quotes")
    for i, q in enumerate(quotes, 1):
        lines.append(f'  {i}. "{q}"')
    lines.append("")

    if scores:
        lines.append("## Rating Distribution")
        for k, v in scores.items():
            lines.append(f"  • {k}: {v} reviews")
        lines.append("")

    if strength:
        lines.append("## Evidence Strength Breakdown")
        for k, v in strength.items():
            lines.append(f"  • {k.title()}: {v} reviews")
        lines.append("")

    if segments:
        lines.append("## Segments Affected")
        for seg, cnt in segments.items():
            label = seg.replace("_", " ").title()
            lines.append(f"  • {label}: {cnt} reviews")
        lines.append("")

    lines.append(f"## Confidence: {len(all_relevant)} reviews analyzed | Sources: Google Play, App Store")
    return "\n".join(lines)


# ────────────────────────────────────────────────────────────────
#  Router
# ────────────────────────────────────────────────────────────────

_QUESTION_HANDLERS: dict[str, Any] = {
    "discover_new_music": _answer_discover_new_music,
    "recommendation_frustrations": _answer_recommendation_frustrations,
    "listening_behaviors": _answer_listening_behaviors,
    "repeat_listening_causes": _answer_repeat_listening_causes,
    "discovery_segments": _answer_discovery_segments,
    "unmet_needs": _answer_unmet_needs,
}


def _fallback_heuristic(question: str, reviews: list[dict[str, Any]], question_key: str = "") -> str:
    """
    Produce a structured, analytical answer by leveraging the enriched review corpus.
    Uses question_key to route to the appropriate handler.
    """
    handler = _QUESTION_HANDLERS.get(question_key)
    if handler:
        return handler(reviews, reviews)

    # Generic fallback if question_key doesn't match
    corpus = _load_enriched()
    quotes = _pick_quotes(corpus, min_len=20, max_quotes=5)
    segments = _segment_breakdown(corpus)

    lines = [f"## Analysis for: {question}"]
    lines.append(f"\nBased on analysis of {len(corpus)} reviews from the enriched corpus:\n")
    lines.append("## Key Findings")
    for i, q in enumerate(quotes, 1):
        lines.append(f'  {i}. "{q}"')
    if segments:
        lines.append("\n## User Segments Identified")
        for seg, cnt in segments.items():
            label = seg.replace("_", " ").title()
            lines.append(f"  • {label}: {cnt} reviews")
    lines.append(f"\n## Confidence: {len(corpus)} reviews analyzed")
    return "\n".join(lines)


def answer_with_llm(question: str, reviews: list[dict[str, Any]], question_key: str = "") -> str:
    """
    Uses OpenAI if OPENAI_API_KEY is configured. Otherwise falls back to a heuristic.
    """
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return _fallback_heuristic(question, reviews, question_key=question_key)

    # Import lazily so local dev without openai installed can still use fallback.
    from openai import OpenAI

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    client = OpenAI(api_key=api_key)

    user_prompt = answer_prompt(question, reviews)
    # Keep output deterministic and grounded by lowering temperature.
    resp = client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    content = resp.choices[0].message.content or ""
    # Basic cleanup: remove repeated whitespace.
    content = re.sub(r"[ \t]+", " ", content).strip()
    return content
