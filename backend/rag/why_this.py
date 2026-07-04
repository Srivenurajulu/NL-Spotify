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
        "default": "Similar layered vocals to Fleet Foxes, with cinematic folk production - fits listeners who gravitate toward textured, atmospheric indie.",
        "wind-down": "Perfect for winding down - Bon Iver's slow, cinematic build mirrors the calm vocal textures you engage with in evening sessions.",
        "focus": "Gentle folk instrumentation keeps the energy low without being distracting - the vocal layers become ambient after a few listens.",
        "energy": "Atmospheric indie folk with a slow build that rewards patience - the crescendo at the midpoint is worth the wait.",
    },
    "track_2": {
        "default": "Instrumental electronic with minimal beats - Ólafur Arnalds' collaborative project strips away vocals to let rhythm and texture do the work.",
        "wind-down": "Low-energy electronic pulses that gradually dissolve into silence - designed for the transition from activity to rest.",
        "focus": "Pure instrumental focus music - the repeating patterns create a productive groove without lyrical distraction.",
        "energy": "Subtle rhythmic drive underneath ambient textures - enough movement to keep you present without demanding attention.",
    },
    "track_3": {
        "default": "Mellow electronic with no lyrics - fits evening listening patterns, similar downtempo feel to Tom Misch instrumentals.",
        "wind-down": "Night-time electronic at a gentle pace - recommended because evening sessions consistently lean toward lyric-free, downtempo tracks.",
        "focus": "Clean electronic production with enough rhythmic structure to maintain concentration - no vocals to compete with your thoughts.",
        "energy": "More rhythmic drive than pure ambient - gives you movement and groove without demanding full attention.",
    },
    "track_4": {
        "default": "Sparse, minimal guitar over quiet rhythm - a palette cleanser at 2:07 that resets between heavier tracks, similar to James Blake's stripped-back moments.",
        "wind-down": "The xx at their most restrained - just interlocking guitar and bass, creating space rather than filling it. Perfect transitional energy.",
        "focus": "At 2:07, it's a micro-break - too short to derail focus, long enough to reset your ears between deep-work sessions.",
        "energy": "Minimal indie pop that proves less is more - the empty space in this track carries as much weight as the notes.",
    },
    "track_5": {
        "default": "Scientifically designed to reduce anxiety - the 8-minute ambient arc mirrors Brian Eno's approach to generative, slowly evolving sound.",
        "wind-down": "Deep-calm instrumental that unfolds gradually - the tempo slows from 60 to 50 BPM across 8 minutes, physically lowering heart rate.",
        "focus": "Extended ambient piece that creates a sound cocoon - ideal for deep work sessions where you need to block out the world.",
        "energy": "The longest pick at 8:09 - an ambient journey rather than a song. Best experienced as a single uninterrupted arc.",
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
