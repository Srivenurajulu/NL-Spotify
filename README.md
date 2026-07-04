# NL-Spotify — Review Discovery Engine

Spotify review intelligence pipeline for the NextLeap Growth PM submission. Phase 0 ingests App Store and Google Play reviews into ChromaDB for downstream RAG.

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python backend/ingest/run_scrape.py
```

This scrapes **50 reviews** from each store:

- [Google Play Store](https://play.google.com/store/apps/details?id=com.spotify.music)
- [Apple App Store](https://apps.apple.com/us/app/spotify-music-and-podcasts/id324684580)

## Outputs

| File | Description |
|---|---|
| `data/reviews.json` | Combined normalized corpus (`id`, `source`, `date`, `text`, `url`, `behavior_tags`) |
| `data/raw/play_store_*.json` | Raw Play Store scrape snapshot |
| `data/raw/app_store_*.json` | Raw App Store scrape snapshot |
| `data/stats.json` | Corpus stats for the RDE UI |
| `data/chroma/` | Local ChromaDB vector store |

## Project Structure

```
backend/
  ingest/
    play_store.py      # google-play-scraper
    app_store.py       # iTunes RSS + App Store page fallback
    normalize.py       # shared schema + PII strip + behavior tags
    chroma_ingest.py   # vector store upsert
    run_scrape.py      # CLI entry point
```

## Next Phases

See `Finalone.md` for the full plan: hybrid RAG, Review Intelligence UI, and the "Why This" MVP.

## Review Discovery Engine (RAG)

This runs a small UI and API for answering the review questions in the dropdown.

### Run

```bash
cd /Users/srivenurajulu/Documents/NL-Spotify
source .venv/bin/activate
pip install fastapi uvicorn openai
uvicorn backend.api.server:app --reload --port 8000
```

Open: `http://localhost:8000`

### Environment variables

If `OPENAI_API_KEY` is set, an LLM will synthesize answers.
If it is not set, the system returns a heuristic answer based on retrieved excerpts.
