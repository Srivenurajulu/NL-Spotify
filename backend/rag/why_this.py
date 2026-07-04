"""Why This - explanation generator, RAG verbatim retriever, and repair agent."""
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

TRACKS_PATH = Path(__file__).resolve().parents[2] / "data" / "dummy_tracks.json"

_tracks_cache: list[dict[str, Any]] | None = None


def _load_tracks() -> list[dict[str, Any]]:
    global _tracks_cache
    if _tracks_cache is None:
        _tracks_cache = json.loads(TRACKS_PATH.read_text())
    return _tracks_cache


# ────────────────────────────────────────────────────────────────
#  Pre-crafted "Why This" explanations (keyed by track_id)
#  3 variants per track: default, wind-down, focus/energy
# ────────────────────────────────────────────────────────────────

EXPLANATIONS: dict[str, dict[str, str]] = {
    "track_1": {
        "default": "High-BPM synth-pop that channels Daft Punk's retro-futurism - perfect for listeners seeking an immediate, driving rhythm.",
        "wind-down": "Usually too energetic for evening, but the atmospheric 80s synth production occasionally fits a late-night drive mood.",
        "focus": "The driving 171 BPM tempo and consistent synth loop create a strong momentum that powers through repetitive tasks.",
        "energy": "Pure adrenaline - the relentless beat and soaring vocals are exactly what you need to immediately lift your energy state.",
    },
    "track_2": {
        "default": "Cinematic and purely instrumental - Hans Zimmer's intricate organ arrangement provides a deep, immersive listening experience.",
        "wind-down": "The repeating, minimalist structure naturally slows your breathing, making it an ideal bridge between a busy day and sleep.",
        "focus": "Complex enough to block out the world, but with zero lyrics to compete with your internal monologue during deep work.",
        "energy": "The grand, sweeping crescendo builds a profound sense of scale and momentum without relying on heavy percussion.",
    },
    "track_3": {
        "default": "Lush, string-heavy R&B that strips away heavy beats in favor of Frank Ocean's distinct vocal texture and Daniel Caesar-like warmth.",
        "wind-down": "Incredibly mellow and soothing - the acoustic arrangement and gentle pacing make it a perfect anchor for evening relaxation.",
        "focus": "The organic instrumentation and smooth vocal delivery create a warm background ambiance that won't disrupt your concentration.",
        "energy": "A different kind of energy - it doesn't hype you up, but the rich, soulful groove provides a steady, uplifting undercurrent.",
    },
    "track_4": {
        "default": "A raw, piano-driven ballad that leans entirely into emotional resonance rather than production tricks, reminiscent of early Rex Orange County.",
        "wind-down": "Stripped-back and quiet - the melancholic piano and soft vocals fit perfectly into a reflective late-night listening session.",
        "focus": "The minimalist arrangement—just piano and voice—leaves plenty of mental space, though its emotional weight commands attention.",
        "energy": "A stark contrast to high-energy tracks, offering a sudden, intense emotional reset that grounds the listener instantly.",
    },
    "track_5": {
        "default": "Psychedelic, atmospheric hip-hop that prioritizes trippy textures and a slow, hypnotic groove over traditional rap cadences.",
        "wind-down": "The woozy, delayed synths and slowed-down tempo create a dreamlike state tailored for late-night decompression.",
        "focus": "The ambient, lo-fi beat loop provides a steady, hypnotic rhythm that fades perfectly into the background during creative work.",
        "energy": "Low-energy but highly immersive - it pulls you into its unique sonic atmosphere rather than pushing you forward.",
    },
}


# ────────────────────────────────────────────────────────────────
#  Pre-crafted "Listeners Said" quotes (from real corpus + interviews)
# ────────────────────────────────────────────────────────────────

LISTENER_QUOTES: dict[str, dict[str, str]] = {
    "track_1": {
        "text": "Just tell me WHY you picked something - 'because this artist collaborated with someone you saved last week' would be enough.",
        "source": "User Interview · Srivatsan (Frustrated Discoverer)",
    },
    "track_2": {
        "text": "The algorithm doesn't understand that my taste shifts based on context: gym music is completely different from my commute playlist.",
        "source": "User Interview · Syed (Churned Discoverer)",
    },
    "track_3": {
        "text": "When it misses, it misses badly, and there's no way to say 'not this mood right now' without skipping.",
        "source": "User Interview · Sakthi (Satisfied but curious)",
    },
    "track_4": {
        "text": "On a Sunday evening when I'm winding down, I don't want the high-energy workout music that I listened to that morning.",
        "source": "User Interview · Arun (Context-Seeking Discoverer)",
    },
    "track_5": {
        "text": "One bad week undoes three good ones in my head... it feels like shouting into a void when I skip something.",
        "source": "User Interview · Gourav (Inconsistency-Frustrated)",
    },
}

# Additional quotes from the scraped review corpus
CORPUS_QUOTES: list[dict[str, str]] = [
    {
        "text": "Spotify is like a bookshop owner who silently hands you a book with no explanation. Sometimes brilliant, sometimes baffling.",
        "source": "User Interview · Jonathan (Active Discoverer)",
    },
    {
        "text": "By the time the ad finishes, I've already lost interest and I skip. So the algorithm thinks I didn't like the song.",
        "source": "User Interview · Radhika (Satisfied Discoverer)",
    },
    {
        "text": "Shuffle sucks. Change the shuffle algorithm back to the old one from like a year ago when it was actually random.",
        "source": "Google Play Review · 2026",
    },
    {
        "text": "Could be exceptional. I really love this app but when I search for a certain songs search not found.",
        "source": "App Store Review · 2026",
    },
]


def _detect_context(user_context: str) -> str:
    """Map user context input to an explanation variant key."""
    if not user_context:
        return "default"
    ctx = user_context.lower()
    wind_down_kws = ["wind", "relax", "calm", "sleep", "evening", "night", "chill", "rest", "decompress"]
    focus_kws = ["focus", "work", "study", "concentrate", "deep work", "productive", "coding"]
    energy_kws = ["energy", "upbeat", "gym", "workout", "drive", "run", "morning", "pump"]
    if any(k in ctx for k in wind_down_kws):
        return "wind-down"
    if any(k in ctx for k in focus_kws):
        return "focus"
    if any(k in ctx for k in energy_kws):
        return "energy"
    return "default"


def get_tracks_with_explanations(user_context: str = "") -> list[dict[str, Any]]:
    """Load dummy tracks and attach Why This explanations + listener quotes."""
    tracks = json.loads(TRACKS_PATH.read_text())  # fresh copy
    context_key = _detect_context(user_context)

    for track in tracks:
        tid = track["id"]
        variants = EXPLANATIONS.get(tid, {})
        track["why_this"] = variants.get(context_key, variants.get("default", ""))
        track["listener_quote"] = LISTENER_QUOTES.get(tid, CORPUS_QUOTES[0])
        track["context_used"] = context_key

    return tracks


# ────────────────────────────────────────────────────────────────
#  Repair Agent
# ────────────────────────────────────────────────────────────────

# Maps feedback keywords → preferred track attributes
_FEEDBACK_MAP: dict[str, dict[str, Any]] = {
    "slow": {"prefer_energy": "medium", "avoid_tempo": "slow"},
    "boring": {"prefer_energy": "medium", "avoid_tempo": "slow"},
    "sleepy": {"prefer_energy": "medium", "avoid_tempo": "very slow"},
    "fast": {"prefer_energy": "low", "prefer_tempo": "slow"},
    "intense": {"prefer_energy": "very low", "prefer_tempo": "slow"},
    "loud": {"prefer_energy": "very low", "prefer_tempo": "slow"},
    "long": {"prefer_short": True},
    "generic": {"prefer_unique": True},
    "sad": {"prefer_energy": "medium"},
    "repetitive": {"prefer_unique": True},
}


def get_repair_track(feedback: str, skipped_ids: list[str]) -> dict[str, Any]:
    """
    After 2 consecutive skips, pick the best alternative track based on
    one-word feedback, avoiding already-skipped tracks.
    """
    tracks = _load_tracks()
    available = [t for t in tracks if t["id"] not in skipped_ids]
    if not available:
        # All tracks skipped - wrap around with the least recently skipped
        available = tracks[:1]

    feedback_lower = feedback.strip().lower().replace("too ", "")

    # Score each available track
    best_track = available[0]
    best_score = -1

    prefs = _FEEDBACK_MAP.get(feedback_lower, {})

    for track in available:
        score = 0
        if prefs.get("prefer_energy"):
            if track.get("energy") == prefs["prefer_energy"]:
                score += 3
        if prefs.get("avoid_tempo"):
            if track.get("tempo") != prefs["avoid_tempo"]:
                score += 2
        if prefs.get("prefer_tempo"):
            if track.get("tempo") == prefs["prefer_tempo"]:
                score += 2
        if prefs.get("prefer_short"):
            # Prefer shorter tracks
            dur_parts = track.get("duration", "99:99").split(":")
            mins = int(dur_parts[0])
            if mins <= 3:
                score += 3
        if prefs.get("prefer_unique"):
            # Prefer non-mainstream genres
            if track.get("genre") in ("Ambient", "Electronic"):
                score += 2
        if score > best_score:
            best_score = score
            best_track = track

    # Generate adjusted explanation
    adjustment_note = _generate_adjustment_note(feedback_lower, best_track)
    why_this = _generate_repair_explanation(feedback_lower, best_track)
    quote = random.choice(CORPUS_QUOTES)

    return {
        "track": best_track,
        "why_this": why_this,
        "adjustment_note": adjustment_note,
        "listener_quote": quote,
    }


def _generate_adjustment_note(feedback: str, track: dict[str, Any]) -> str:
    """Human-readable note about what was adjusted."""
    notes = {
        "slow": f"You said it was too slow - {track['title']} by {track['artist']} has more rhythmic movement at {track['tempo']} tempo.",
        "boring": f"Switching it up - {track['title']} brings a different texture with {track['genre'].lower()} production.",
        "sleepy": f"More energy this time - {track['title']} has a {track['energy']}-energy feel to keep you engaged.",
        "fast": f"Slowing it down - {track['title']} runs at {track['tempo']} tempo for a more relaxed pace.",
        "intense": f"Dialing back - {track['title']} is {track['energy']}-energy {track['genre'].lower()} that won't overwhelm.",
        "loud": f"Something quieter - {track['title']} by {track['artist']} keeps the volume and energy low.",
        "long": f"Shorter pick at {track['duration']} - {track['title']} is a quick listen that won't overstay.",
        "generic": f"Something more distinctive - {track['title']} by {track['artist']} has a unique {track['genre'].lower()} sound.",
        "repetitive": f"Breaking the pattern - {track['title']} is a {track['genre'].lower()} track from a completely different sonic world.",
    }
    return notes.get(feedback, f"Based on your feedback, here's {track['title']} by {track['artist']} - a different direction from what you skipped.")


def _generate_repair_explanation(feedback: str, track: dict[str, Any]) -> str:
    """Generate a Why This explanation specifically for the repair context."""
    mood = ", ".join(track.get("mood_tags", [])[:2])
    anchor = track.get("anchor_artist", "")
    return (
        f"Adjusted for you - {mood} energy with "
        f"{track['genre'].lower()} textures"
        f"{f', in the vein of {anchor}' if anchor else ''}. "
        f"This should be a better fit."
    )
