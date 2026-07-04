from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from backend.rag.engine import answer_review_question
from backend.rag.questions import QUESTIONS
from backend.rag.retrieval import retrieve
from backend.rag.why_this import get_tracks_with_explanations, get_repair_track
from backend.rag.llm import answer_with_llm


# ── Request models ───────────────────────────────────────────────

class AskRequest(BaseModel):
    question_key: str = ""
    question_text: str = ""


class RepairRequest(BaseModel):
    feedback: str
    skipped_ids: list[str] = []


# ── App ──────────────────────────────────────────────────────────

app = FastAPI(title="NL-Spotify - Why This + Review Discovery Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── API routes ───────────────────────────────────────────────────

@app.get("/api/questions")
def get_questions():
    return [{"key": k, "title": v.title} for k, v in QUESTIONS.items()]


@app.get("/api/tracks")
def get_tracks(context: str = ""):
    return get_tracks_with_explanations(context)


@app.post("/api/ask")
def ask(req: AskRequest) -> dict[str, Any]:
    if req.question_key:
        return answer_review_question(req.question_key)
    elif req.question_text:
        retrieval = retrieve(req.question_text, n_results=18)
        reviews = retrieval.reviews[:18]
        answer = answer_with_llm(req.question_text, reviews, question_key="")
        return {"question": req.question_text, "answer": answer, "evidence_count": len(reviews)}
    return {"error": "Provide question_key or question_text"}


@app.post("/api/repair")
def repair(req: RepairRequest) -> dict[str, Any]:
    return get_repair_track(req.feedback, req.skipped_ids)


# ── Main page ────────────────────────────────────────────────────

MAIN_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>Spotify - Discovery</title>
  <meta name="description" content="AI-powered music discovery with explanations, proof, and repair - a premium Spotify experience.">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --bg-primary: #0c0604;
      --bg-warm: #110907;
      --bg-card: rgba(40, 22, 12, 0.55);
      --bg-card-hover: rgba(55, 30, 16, 0.65);
      --bg-elevated: rgba(50, 28, 14, 0.8);
      --bg-glass: rgba(60, 30, 15, 0.25);
      --text-primary: #faf0e6;
      --text-secondary: #c4a882;
      --text-subdued: #7a5c3e;
      --accent-red: #c0392b;
      --accent-red-bright: #e74c3c;
      --accent-red-glow: rgba(192, 57, 43, 0.35);
      --accent-gold: #d4a017;
      --accent-gold-light: #f0c040;
      --accent-gold-warm: #c8922a;
      --accent-gold-glow: rgba(212, 160, 23, 0.3);
      --accent-brown: #5c3a1e;
      --accent-brown-light: #8b5e3c;
      --accent-brown-warm: #a0704a;
      --border-glass: rgba(212, 160, 23, 0.12);
      --border-warm: rgba(192, 57, 43, 0.15);
      --radius-sm: 8px;
      --radius-md: 14px;
      --radius-lg: 20px;
      --radius-xl: 28px;
      --shadow-glass: 0 8px 32px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.05);
      --shadow-glow-gold: 0 4px 30px rgba(212, 160, 23, 0.15);
      --shadow-glow-red: 0 4px 30px rgba(192, 57, 43, 0.12);
      --transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      --transition-spring: 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
    }
    html { scroll-behavior: smooth; }
    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif;
      background: var(--bg-primary);
      background-image:
        radial-gradient(ellipse 80% 60% at 50% 0%, rgba(192,57,43,0.08) 0%, transparent 50%),
        radial-gradient(ellipse 60% 40% at 80% 100%, rgba(212,160,23,0.06) 0%, transparent 50%),
        radial-gradient(ellipse 50% 50% at 10% 60%, rgba(92,58,30,0.08) 0%, transparent 50%);
      background-attachment: fixed;
      color: var(--text-primary);
      min-height: 100vh;
      line-height: 1.6;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
    }

    /* ── Liquid Glass Utility ──────────────── */
    .glass {
      background: var(--bg-glass);
      backdrop-filter: blur(40px) saturate(180%);
      -webkit-backdrop-filter: blur(40px) saturate(180%);
      border: 1px solid var(--border-glass);
      box-shadow: var(--shadow-glass);
    }

    /* ── Header ───────────────────────────── */
    header {
      position: sticky; top: 0; z-index: 100;
      display: flex; align-items: center; justify-content: space-between;
      padding: 14px 32px;
      background: rgba(12, 6, 4, 0.75);
      backdrop-filter: blur(50px) saturate(200%);
      -webkit-backdrop-filter: blur(50px) saturate(200%);
      border-bottom: 1px solid rgba(212,160,23,0.08);
    }
    .logo {
      display: flex; align-items: center; gap: 10px;
      font-size: 24px; font-weight: 900; letter-spacing: -0.5px;
    }
    .logo-icon {
      width: 36px; height: 36px; border-radius: 50%;
      background: linear-gradient(135deg, var(--accent-red), var(--accent-gold));
      display: flex; align-items: center; justify-content: center;
      font-size: 18px; color: #fff;
      box-shadow: 0 2px 12px rgba(192,57,43,0.3);
      animation: logoPulse 3s ease-in-out infinite;
    }
    @keyframes logoPulse {
      0%,100% { box-shadow: 0 2px 12px rgba(192,57,43,0.3); }
      50% { box-shadow: 0 2px 20px rgba(192,57,43,0.5), 0 0 40px rgba(212,160,23,0.15); }
    }
    .logo-text {
      background: linear-gradient(135deg, var(--accent-red-bright), var(--accent-gold), var(--accent-gold-light));
      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
      background-clip: text;
      background-size: 200% 200%;
      animation: gradientShift 4s ease-in-out infinite;
    }
    @keyframes gradientShift {
      0%,100% { background-position: 0% 50%; }
      50% { background-position: 100% 50%; }
    }
    .header-actions { display: flex; gap: 12px; align-items: center; }
    .btn-rde {
      padding: 10px 22px; border-radius: var(--radius-xl);
      border: 1.5px solid var(--accent-gold-warm);
      background: rgba(212,160,23,0.08);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      color: var(--accent-gold-light);
      font-family: inherit; font-size: 13px; font-weight: 600;
      cursor: pointer; transition: all var(--transition); letter-spacing: 0.3px;
    }
    .btn-rde:hover {
      background: linear-gradient(135deg, var(--accent-gold), var(--accent-gold-light));
      color: #1a0c04; border-color: transparent;
      box-shadow: var(--shadow-glow-gold);
      transform: translateY(-1px);
    }
    .stats-pill {
      font-size: 11px; color: var(--text-subdued);
      padding: 6px 14px; border-radius: var(--radius-xl);
      background: rgba(92,58,30,0.2);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid rgba(212,160,23,0.08);
    }

    /* ── Main Content ─────────────────────── */
    main { max-width: 900px; margin: 0 auto; padding: 36px 24px 100px; }
    .section-header {
      display: flex; align-items: center; justify-content: space-between;
      margin-bottom: 24px; flex-wrap: wrap; gap: 12px;
    }
    .section-header h1 {
      font-size: 28px; font-weight: 800; letter-spacing: -0.5px;
      display: flex; align-items: center; gap: 10px;
    }
    .section-header h1 .fire { font-size: 24px; }
    .section-header h1 .count {
      color: var(--text-subdued); font-weight: 400; font-size: 20px;
    }
    .context-bar {
      display: flex; gap: 12px; align-items: center; margin-bottom: 32px; flex-wrap: wrap;
    }
    .context-bar input {
      flex: 1; min-width: 220px; padding: 14px 22px;
      border-radius: var(--radius-xl);
      border: 1px solid var(--border-glass);
      background: rgba(40, 22, 12, 0.4);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      color: var(--text-primary);
      font-family: inherit; font-size: 14px;
      transition: all var(--transition);
    }
    .context-bar input:focus {
      outline: none;
      border-color: var(--accent-gold);
      box-shadow: 0 0 0 3px rgba(212,160,23,0.12), var(--shadow-glow-gold);
    }
    .context-bar input::placeholder { color: var(--text-subdued); }
    .btn-refresh {
      padding: 14px 28px; border-radius: var(--radius-xl); border: none;
      background: linear-gradient(135deg, var(--accent-red), var(--accent-red-bright));
      color: #fff;
      font-family: inherit; font-size: 14px; font-weight: 700;
      cursor: pointer; transition: all var(--transition);
      box-shadow: 0 4px 16px rgba(192,57,43,0.25);
      letter-spacing: 0.3px;
    }
    .btn-refresh:hover {
      transform: translateY(-2px) scale(1.02);
      box-shadow: 0 6px 24px rgba(192,57,43,0.4);
    }
    .btn-refresh:active { transform: translateY(0) scale(0.98); }

    /* ── Track Cards ──────────────────────── */
    .track-list { display: flex; flex-direction: column; gap: 20px; }
    .track-card {
      display: flex; gap: 22px; padding: 24px;
      background: var(--bg-card);
      backdrop-filter: blur(40px) saturate(160%);
      -webkit-backdrop-filter: blur(40px) saturate(160%);
      border-radius: var(--radius-lg);
      border: 1px solid var(--border-glass);
      box-shadow: var(--shadow-glass);
      transition: all var(--transition);
      animation: fadeSlideIn 0.5s cubic-bezier(0.4, 0, 0.2, 1) both;
      position: relative;
      overflow: hidden;
    }
    .track-card::before {
      content: '';
      position: absolute; top: 0; left: 0; right: 0; height: 1px;
      background: linear-gradient(90deg, transparent, rgba(212,160,23,0.2), rgba(192,57,43,0.15), transparent);
    }
    .track-card:hover {
      background: var(--bg-card-hover);
      border-color: rgba(212,160,23,0.2);
      transform: translateY(-3px);
      box-shadow: var(--shadow-glass), var(--shadow-glow-gold);
    }
    .track-card.playing {
      border-color: var(--accent-gold);
      box-shadow: var(--shadow-glass), 0 0 40px rgba(212,160,23,0.2);
    }
    .track-card.playing::after {
      content: '♪';
      position: absolute; top: 12px; right: 16px;
      font-size: 18px; color: var(--accent-gold);
      animation: musicNote 1.5s ease-in-out infinite;
    }
    @keyframes musicNote {
      0%,100% { opacity: 0.5; transform: translateY(0) rotate(0deg); }
      50% { opacity: 1; transform: translateY(-4px) rotate(8deg); }
    }
    .track-card.saved .btn-save { color: var(--accent-gold) !important; border-color: var(--accent-gold) !important; }
    .track-card.skipped { opacity: 0.25; pointer-events: none; filter: grayscale(0.6); }
    @keyframes fadeSlideIn {
      from { opacity: 0; transform: translateY(20px) scale(0.98); }
      to { opacity: 1; transform: translateY(0) scale(1); }
    }

    /* ── Track Art (Vinyl Style) ──────────── */
    .track-art {
      width: 100px; height: 100px; border-radius: var(--radius-md);
      flex-shrink: 0; position: relative; overflow: hidden;
      box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    }
    .track-art::after {
      content: '';
      position: absolute; inset: 0;
      background: radial-gradient(circle at 50% 50%,
        transparent 25%,
        rgba(0,0,0,0.08) 26%,
        transparent 27%,
        transparent 49%,
        rgba(0,0,0,0.06) 50%,
        transparent 51%
      );
      border-radius: inherit;
      pointer-events: none;
    }
    .track-art-inner {
      width: 100%; height: 100%;
      display: flex; align-items: center; justify-content: center;
      font-size: 32px; font-weight: 900;
      color: rgba(255,255,255,0.85);
      text-shadow: 0 2px 12px rgba(0,0,0,0.6);
      letter-spacing: -1px;
    }
    .track-info { flex: 1; min-width: 0; }
    .track-title-row {
      display: flex; align-items: baseline; gap: 10px;
      margin-bottom: 4px;
    }
    .track-title {
      font-size: 18px; font-weight: 700;
      white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
      letter-spacing: -0.3px;
    }
    .track-artist {
      font-size: 14px; color: var(--accent-gold-warm);
      font-weight: 500; white-space: nowrap;
    }
    .track-meta {
      font-size: 12px; color: var(--text-subdued); margin-top: 2px;
      display: flex; align-items: center; gap: 6px;
    }
    .track-meta .dot { width: 3px; height: 3px; border-radius: 50%; background: var(--text-subdued); display: inline-block; }

    /* ── Why This Section (Enhanced) ──────── */
    .why-this-section {
      margin-top: 14px; padding: 16px 18px;
      background: linear-gradient(135deg, rgba(212,160,23,0.08), rgba(192,57,43,0.04));
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border-radius: var(--radius-md);
      border: 1px solid rgba(212,160,23,0.12);
      border-left: 3px solid var(--accent-gold);
      position: relative;
      transition: all var(--transition);
    }
    .why-this-section:hover {
      background: linear-gradient(135deg, rgba(212,160,23,0.12), rgba(192,57,43,0.06));
      border-color: rgba(212,160,23,0.2);
      box-shadow: 0 2px 16px rgba(212,160,23,0.08);
    }
    .why-this-label {
      font-size: 10px; font-weight: 800; letter-spacing: 1.5px;
      text-transform: uppercase; margin-bottom: 6px;
      display: flex; align-items: center; gap: 6px;
    }
    .why-this-label .icon { font-size: 13px; }
    .why-this-label .label-text {
      background: linear-gradient(90deg, var(--accent-gold), var(--accent-gold-light));
      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    .why-this-text {
      font-size: 14px; color: var(--text-secondary); line-height: 1.7;
      font-weight: 400;
    }

    /* ── Listeners Said Section (Enhanced) ── */
    .listeners-section {
      margin-top: 10px; padding: 14px 18px;
      background: linear-gradient(135deg, rgba(192,57,43,0.06), rgba(92,58,30,0.08));
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border-radius: var(--radius-md);
      border: 1px solid rgba(192,57,43,0.1);
      border-left: 3px solid var(--accent-red);
      position: relative;
      transition: all var(--transition);
    }
    .listeners-section:hover {
      background: linear-gradient(135deg, rgba(192,57,43,0.1), rgba(92,58,30,0.12));
      border-color: rgba(192,57,43,0.18);
      box-shadow: 0 2px 16px rgba(192,57,43,0.06);
    }
    .listeners-label {
      font-size: 10px; font-weight: 800; letter-spacing: 1.5px;
      text-transform: uppercase; margin-bottom: 6px;
      display: flex; align-items: center; gap: 6px;
    }
    .listeners-label .icon { font-size: 13px; }
    .listeners-label .label-text {
      background: linear-gradient(90deg, var(--accent-red), var(--accent-red-bright));
      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    .listeners-text {
      font-size: 13px; color: var(--text-secondary);
      font-style: italic; line-height: 1.6;
      padding-left: 12px;
      border-left: 2px solid rgba(192,57,43,0.15);
      margin-left: 2px;
    }
    .listeners-source {
      font-size: 11px; color: var(--text-subdued); margin-top: 6px;
      font-style: normal; font-weight: 500;
      display: flex; align-items: center; gap: 4px;
    }
    .listeners-source .src-icon { font-size: 10px; }

    /* ── Action Buttons ──────────────────── */
    .track-actions { display: flex; gap: 10px; margin-top: 16px; }
    .track-actions button {
      padding: 9px 22px; border-radius: var(--radius-xl); border: none;
      font-family: inherit; font-size: 12px; font-weight: 700;
      cursor: pointer; transition: all var(--transition);
      display: flex; align-items: center; gap: 6px;
      letter-spacing: 0.3px;
    }
    .btn-play {
      background: linear-gradient(135deg, var(--accent-red), var(--accent-red-bright));
      color: #fff;
      box-shadow: 0 2px 12px rgba(192,57,43,0.2);
    }
    .btn-play:hover {
      transform: translateY(-1px) scale(1.05);
      box-shadow: 0 4px 20px rgba(192,57,43,0.35);
    }
    .btn-save {
      background: rgba(212,160,23,0.08);
      color: var(--text-secondary);
      border: 1px solid rgba(212,160,23,0.15) !important;
      backdrop-filter: blur(8px);
      -webkit-backdrop-filter: blur(8px);
    }
    .btn-save:hover {
      color: var(--accent-gold-light);
      border-color: var(--accent-gold) !important;
      background: rgba(212,160,23,0.15);
    }
    .btn-skip {
      background: rgba(92,58,30,0.1);
      color: var(--text-subdued);
      border: 1px solid rgba(92,58,30,0.2) !important;
    }
    .btn-skip:hover {
      color: var(--accent-red-bright);
      border-color: var(--accent-red) !important;
      background: rgba(192,57,43,0.08);
    }

    /* ── Repair Modal ────────────────────── */
    .modal-overlay {
      position: fixed; inset: 0; z-index: 200;
      background: rgba(0,0,0,0.6);
      backdrop-filter: blur(24px) saturate(180%);
      -webkit-backdrop-filter: blur(24px) saturate(180%);
      display: flex; align-items: center; justify-content: center;
      opacity: 0; pointer-events: none; transition: opacity 0.35s;
    }
    .modal-overlay.visible { opacity: 1; pointer-events: all; }
    .modal-box {
      background: rgba(40, 22, 12, 0.85);
      backdrop-filter: blur(60px) saturate(200%);
      -webkit-backdrop-filter: blur(60px) saturate(200%);
      border-radius: var(--radius-lg);
      padding: 40px 36px; max-width: 440px; width: 90%;
      border: 1px solid var(--border-glass);
      box-shadow: 0 24px 80px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.05);
      transform: scale(0.95); transition: transform 0.35s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .modal-overlay.visible .modal-box { transform: scale(1); }
    .modal-box.wide { max-width: 850px; padding: 48px; }
    
    .ai-rationale-header { text-align: center; margin-bottom: 32px; }
    .ai-rationale-header h3 { font-size: 28px; margin-bottom: 12px; }
    .ai-rationale-header p { font-size: 16px; color: var(--text-secondary); max-width: 600px; margin: 0 auto; line-height: 1.5; }
    
    .ai-rationale-list { 
      margin-top: 24px; 
      display: grid; 
      grid-template-columns: repeat(3, 1fr); 
      gap: 24px; 
      text-align: left; 
    }
    
    .ai-rationale-item {
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: var(--radius-md);
      padding: 24px;
      transition: all 0.3s ease;
      position: relative;
      overflow: hidden;
    }
    
    .ai-rationale-item::before {
      content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
      background: linear-gradient(90deg, transparent, var(--accent-gold), transparent);
      opacity: 0; transition: opacity 0.3s ease;
    }
    
    .ai-rationale-item:hover {
      background: rgba(255, 255, 255, 0.06);
      transform: translateY(-4px);
      box-shadow: 0 12px 24px rgba(0,0,0,0.3);
    }
    
    .ai-rationale-item:hover::before { opacity: 1; }
    
    .ai-icon-wrapper {
      font-size: 28px; margin-bottom: 16px; display: inline-block;
      background: rgba(212,160,23,0.1);
      padding: 12px; border-radius: 50%;
      border: 1px solid rgba(212,160,23,0.2);
    }
    
    .ai-rationale-item h4 { 
      color: var(--text-primary); 
      margin: 0 0 12px 0; 
      font-size: 16px; 
      font-weight: 700; 
      line-height: 1.3;
    }
    
    .ai-rationale-item p { 
      color: var(--text-secondary); 
      margin: 0; 
      font-size: 14px; 
      line-height: 1.6; 
    }

    @media (max-width: 768px) {
      .ai-rationale-list { grid-template-columns: 1fr; }
    }
    .modal-overlay.visible .modal-box { transform: scale(1) translateY(0); }
    .modal-box h3 {
      font-size: 22px; font-weight: 800; margin-bottom: 8px;
      background: linear-gradient(135deg, var(--accent-gold), var(--accent-red-bright));
      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    .modal-box p { font-size: 14px; color: var(--text-secondary); margin-bottom: 24px; }
    .modal-box input {
      width: 100%; padding: 14px 20px;
      border-radius: var(--radius-md);
      border: 1px solid var(--border-glass);
      background: rgba(92,58,30,0.2);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      color: var(--text-primary);
      font-family: inherit; font-size: 15px; text-align: center;
      margin-bottom: 20px; transition: all var(--transition);
    }
    .modal-box input:focus {
      outline: none;
      border-color: var(--accent-gold);
      box-shadow: 0 0 0 3px rgba(212,160,23,0.12);
    }
    .modal-box input::placeholder { color: var(--text-subdued); }
    .modal-actions { display: flex; gap: 12px; justify-content: center; }
    .modal-actions button {
      padding: 12px 28px; border-radius: var(--radius-xl); border: none;
      font-family: inherit; font-size: 14px; font-weight: 700; cursor: pointer;
      transition: all var(--transition);
    }
    .btn-repair-submit {
      background: linear-gradient(135deg, var(--accent-gold), var(--accent-gold-light));
      color: #1a0c04;
      box-shadow: 0 4px 16px rgba(212,160,23,0.25);
    }
    .btn-repair-submit:hover {
      transform: translateY(-1px);
      box-shadow: 0 6px 24px rgba(212,160,23,0.4);
    }
    .btn-repair-dismiss {
      background: rgba(92,58,30,0.15);
      color: var(--text-subdued);
      border: 1px solid rgba(92,58,30,0.25) !important;
    }
    .btn-repair-dismiss:hover { color: var(--text-primary); background: rgba(92,58,30,0.25); }

    /* ── Repair Result Card ──────────────── */
    .repair-result {
      margin-top: 24px; padding: 24px;
      background: linear-gradient(135deg, rgba(212,160,23,0.08), rgba(192,57,43,0.04));
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      border-radius: var(--radius-lg);
      border: 1px solid rgba(212,160,23,0.2);
      box-shadow: var(--shadow-glow-gold);
      animation: fadeSlideIn 0.5s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .repair-note {
      font-size: 13px; font-weight: 700; margin-bottom: 14px;
      display: flex; align-items: center; gap: 8px;
      background: linear-gradient(90deg, var(--accent-gold), var(--accent-gold-light));
      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
      background-clip: text;
    }

    /* ── RDE Overlay ─────────────────────── */
    .rde-overlay {
      position: fixed; inset: 0; z-index: 150;
      background: rgba(12, 6, 4, 0.92);
      backdrop-filter: blur(30px) saturate(180%);
      -webkit-backdrop-filter: blur(30px) saturate(180%);
      display: flex; flex-direction: column;
      opacity: 0; pointer-events: none;
      transition: opacity 0.4s;
      overflow-y: auto;
    }
    .rde-overlay.visible { opacity: 1; pointer-events: all; }
    .rde-header {
      position: sticky; top: 0; z-index: 10;
      display: flex; align-items: center; justify-content: space-between;
      padding: 16px 32px;
      background: rgba(12, 6, 4, 0.85);
      backdrop-filter: blur(40px);
      -webkit-backdrop-filter: blur(40px);
      border-bottom: 1px solid rgba(212,160,23,0.1);
    }
    .rde-title {
      font-size: 22px; font-weight: 800;
      background: linear-gradient(90deg, var(--accent-red-bright), var(--accent-gold), var(--accent-gold-light));
      -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    }
    .btn-back {
      padding: 10px 22px; border-radius: var(--radius-xl);
      border: 1px solid rgba(212,160,23,0.15);
      background: rgba(92,58,30,0.1);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      color: var(--text-secondary);
      font-family: inherit; font-size: 13px; font-weight: 500; cursor: pointer;
      transition: all var(--transition);
    }
    .btn-back:hover {
      color: var(--text-primary);
      border-color: rgba(212,160,23,0.3);
      background: rgba(92,58,30,0.2);
    }
    .rde-body {
      max-width: 900px; width: 100%; margin: 0 auto;
      padding: 36px 24px 80px;
    }
    .rde-subtitle {
      text-align: center; font-size: 14px; color: var(--text-subdued);
      margin-bottom: 32px;
    }

    /* ── RDE Workflow Section ─────────────── */
    .rde-workflow {
      display: flex; flex-direction: column; align-items: center;
      justify-content: center; padding: 60px 20px;
      text-align: center;
    }
    .rde-workflow.hidden { display: none; }
    .btn-run-workflow {
      padding: 18px 44px; border-radius: var(--radius-xl); border: none;
      background: linear-gradient(135deg, var(--accent-red), var(--accent-gold));
      color: #fff; font-family: inherit; font-size: 16px; font-weight: 800;
      cursor: pointer; transition: all var(--transition);
      box-shadow: 0 6px 24px rgba(192,57,43,0.3);
      letter-spacing: 0.5px;
      display: flex; align-items: center; gap: 10px;
    }
    .btn-run-workflow:hover {
      transform: translateY(-3px) scale(1.04);
      box-shadow: 0 8px 32px rgba(192,57,43,0.45);
    }
    .btn-run-workflow:active { transform: translateY(0) scale(0.97); }
    .btn-run-workflow.hidden { display: none; }

    .workflow-spinner-area {
      display: none; flex-direction: column; align-items: center; gap: 24px;
    }
    .workflow-spinner-area.visible { display: flex; }
    .workflow-spinner {
      width: 56px; height: 56px; border-radius: 50%;
      border: 4px solid rgba(212,160,23,0.15);
      border-top: 4px solid var(--accent-gold);
      animation: spinRotate 1s linear infinite;
    }
    @keyframes spinRotate {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
    .workflow-message {
      font-size: 16px; font-weight: 600; color: var(--accent-gold);
      letter-spacing: 0.3px;
    }
    .workflow-success {
      display: none; flex-direction: column; align-items: center; gap: 16px;
      animation: fadeSlideIn 0.6s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .workflow-success.visible { display: flex; }
    .workflow-success-icon {
      width: 64px; height: 64px; border-radius: 50%;
      background: linear-gradient(135deg, rgba(46,204,113,0.15), rgba(46,204,113,0.05));
      border: 2px solid rgba(46,204,113,0.4);
      display: flex; align-items: center; justify-content: center;
      font-size: 28px;
    }
    .workflow-success-text {
      font-size: 18px; font-weight: 700;
      color: #2ecc71;
    }

    .rde-controls {
      display: none; gap: 12px; flex-wrap: wrap;
      align-items: center; justify-content: center; margin-bottom: 16px;
    }
    .rde-controls.visible {
      display: flex;
      animation: fadeSlideIn 0.5s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .rde-controls select {
      flex: 1; min-width: 260px; max-width: 420px;
      padding: 12px 16px; border-radius: var(--radius-md);
      border: 1px solid rgba(212,160,23,0.2);
      background: rgba(40, 22, 12, 0.6);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      color: var(--text-primary);
      font-family: inherit; font-size: 14px;
    }
    .rde-controls select:focus { outline: none; border-color: var(--accent-gold); }
    .btn-analyze {
      padding: 12px 28px; border-radius: var(--radius-md); border: none;
      background: linear-gradient(135deg, var(--accent-red), var(--accent-gold));
      color: #fff; font-family: inherit; font-size: 14px; font-weight: 700;
      cursor: pointer; transition: all var(--transition);
      box-shadow: 0 4px 16px rgba(192,57,43,0.2);
      letter-spacing: 0.3px;
    }
    .btn-analyze:hover {
      transform: translateY(-2px) scale(1.03);
      box-shadow: 0 6px 24px rgba(192,57,43,0.35);
    }

    .rde-status {
      text-align: center; font-size: 14px; color: var(--accent-gold);
      margin: 18px 0; min-height: 22px;
    }
    .rde-answer {
      background: rgba(40, 22, 12, 0.5);
      backdrop-filter: blur(30px);
      -webkit-backdrop-filter: blur(30px);
      border-radius: var(--radius-lg);
      border: 1px solid rgba(212,160,23,0.12);
      overflow: hidden; display: none;
      animation: fadeSlideIn 0.5s cubic-bezier(0.4, 0, 0.2, 1);
      box-shadow: var(--shadow-glass);
    }
    .rde-answer.visible { display: block; }
    .rde-answer-header {
      padding: 16px 24px; font-weight: 700; font-size: 15px;
      background: linear-gradient(90deg, rgba(192,57,43,0.08), rgba(212,160,23,0.06));
      border-bottom: 1px solid rgba(212,160,23,0.08);
      background: linear-gradient(90deg, var(--accent-gold), var(--accent-red-bright));
      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    .rde-answer-body {
      padding: 24px; line-height: 1.75; font-size: 14px; color: var(--text-secondary);
    }
    .rde-answer-body h2 {
      font-size: 17px; font-weight: 700;
      margin: 24px 0 10px; padding-bottom: 6px;
      border-bottom: 1px solid rgba(212,160,23,0.1);
      background: linear-gradient(90deg, var(--accent-gold), var(--accent-gold-light));
      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    .rde-answer-body h2:first-child { margin-top: 0; }
    .rde-answer-body h3 {
      font-size: 14px; font-weight: 600; color: var(--accent-brown-warm);
      margin: 16px 0 6px;
    }
    .rde-answer-body p { margin: 6px 0 12px; }
    .rde-answer-body ul { padding-left: 20px; margin: 6px 0 12px; }
    .rde-answer-body li { margin-bottom: 6px; }
    .rde-answer-body blockquote {
      border-left: 3px solid var(--accent-gold);
      padding: 10px 18px; margin: 10px 0;
      background: rgba(212,160,23,0.04);
      border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
      font-style: italic; color: var(--text-secondary);
    }

    /* ── Loading ──────────────────────────── */
    .loading-bar {
      display: flex; align-items: center; justify-content: center;
      gap: 10px; padding: 60px; color: var(--text-subdued);
      font-size: 14px;
    }
    .dot-pulse { display: flex; gap: 5px; }
    .dot-pulse span {
      width: 8px; height: 8px; border-radius: 50%;
      background: linear-gradient(135deg, var(--accent-red), var(--accent-gold));
      animation: pulse 1.4s ease-in-out infinite;
    }
    .dot-pulse span:nth-child(2) { animation-delay: 0.2s; }
    .dot-pulse span:nth-child(3) { animation-delay: 0.4s; }
    @keyframes pulse {
      0%,100% { opacity: 0.2; transform: scale(0.7); }
      50% { opacity: 1; transform: scale(1.3); }
    }

    /* ── Scrollbar ────────────────────────── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb {
      background: rgba(212,160,23,0.15);
      border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover { background: rgba(212,160,23,0.3); }

    /* ── Responsive ──────────────────────── */
    @media (max-width: 640px) {
      header { padding: 12px 16px; }
      .logo { font-size: 20px; }
      .logo-icon { width: 30px; height: 30px; font-size: 15px; }
      main { padding: 24px 16px 80px; }
      .section-header h1 { font-size: 22px; }
      .track-card { flex-direction: column; gap: 16px; padding: 20px; }
      .track-art { width: 100%; height: 160px; border-radius: var(--radius-md); }
      .rde-body { padding: 24px 16px; }
      .rde-controls { flex-direction: column; }
      .rde-controls select { max-width: 100%; min-width: 100%; }
    }
  </style>
</head>
<body>

  <!-- ─── Header ─────────────────────────────────── -->
  <header>
    <div class="logo">
      <div class="logo-icon">♪</div>
      <span class="logo-text">Spotify</span>
    </div>
    <div class="header-actions">
      <span class="stats-pill" id="statsPill">100 reviews · 2 sources</span>
      <button class="btn-rde" id="showAiRationale" onclick="showAIModal()" style="margin-right: 12px; background: rgba(192, 57, 43, 0.1); border-color: rgba(192, 57, 43, 0.3); color: var(--accent-red-bright);">✨ Why AI?</button>
      <button class="btn-rde" id="openRDE" onclick="showRDE()">Discovery Engine</button>
    </div>
  </header>

  <!-- ─── Main: Why This ─────────────────────────── -->
  <main id="whyThisView">
    <div class="section-header">
      <h1><span class="fire">🔥</span> Your Picks · <span class="count" id="trackCount">5 Tracks</span></h1>
    </div>
    <div class="context-bar">
      <input type="text" id="moodInput" placeholder="What mood are you in? e.g. wind-down, focus, energy (optional)">
      <button class="btn-refresh" onclick="loadTracks()">Refresh</button>
    </div>
    <div id="trackList" class="track-list">
      <div class="loading-bar">
        <div class="dot-pulse"><span></span><span></span><span></span></div>
        <span>Loading tracks…</span>
      </div>
    </div>
  </main>

  <!-- ─── Repair Modal ───────────────────────────── -->
  <div class="modal-overlay" id="repairModal">
    <div class="modal-box">
      <h3>🎯 Not landing?</h3>
      <p>Tell us in one word what's off - we'll adjust.</p>
      <input type="text" id="repairInput" placeholder="e.g., too slow, boring, intense">
      <div class="modal-actions">
        <button class="btn-repair-submit" onclick="submitRepair()">Adjust</button>
        <button class="btn-repair-dismiss" onclick="dismissRepair()">No thanks</button>
      </div>
    </div>
  </div>

  <!-- ─── AI Rationale Modal ──────────────────────── -->
  <div class="modal-overlay" id="aiModal">
    <div class="modal-box wide">
      
      <div class="ai-rationale-header">
        <h3>🤖 Why AI is Uniquely Suited</h3>
        <p>Our research shows this is a <strong>trust</strong> problem, not just an accuracy problem. Here is why Generative AI + RAG is required to solve it.</p>
      </div>
      
      <div class="ai-rationale-list">
        <div class="ai-rationale-item">
          <div class="ai-icon-wrapper">📉</div>
          <h4>Why traditional systems fail</h4>
          <p>Collaborative filtering is excellent at predicting vectors, but it operates as a "black box." It silently hands users tracks without explaining <em>why</em>. When it misses, it fails silently—leaving the user with no recourse other than skipping.</p>
        </div>
        
        <div class="ai-rationale-item">
          <div class="ai-icon-wrapper">🔓</div>
          <h4>What Gen-AI + RAG unlocks</h4>
          <p>AI bridges the communication gap by translating vector similarities into natural language ("Similar layered vocals to Fleet Foxes"). RAG provides <strong>peer proof at scale</strong> by instantly retrieving real user reviews. AI also enables natural language repair (e.g., "too slow").</p>
        </div>
        
        <div class="ai-rationale-item">
          <div class="ai-icon-wrapper">✨</div>
          <h4>How the UX changes</h4>
          <p>It transforms passive consumption into a transparent dialogue. By providing an explanation ("Why This"), we build trust <em>before</em> play. When a miss happens, the repair prompt turns a frustrating exit into a constructive feedback loop.</p>
        </div>
      </div>

      <div class="modal-actions" style="margin-top: 40px; justify-content: center;">
        <button class="btn-repair-dismiss" onclick="dismissAIModal()" style="padding: 12px 32px; font-size: 15px;">Close Panel</button>
      </div>
    </div>
  </div>

  <!-- ─── RDE Overlay ────────────────────────────── -->
  <div class="rde-overlay" id="rdeOverlay">
    <div class="rde-header">
      <div class="rde-title">Review Discovery Engine</div>
      <button class="btn-back" onclick="hideRDE()">← Back to Spotify</button>
    </div>
    <div class="rde-body">
      <div class="rde-subtitle">RAG-powered insights from 100 Spotify user reviews - Google Play &amp; App Store</div>

      <!-- Workflow Section -->
      <div class="rde-workflow" id="rdeWorkflow">
        <button class="btn-run-workflow" id="btnRunWorkflow" onclick="runWorkflow()">🚀 Run Workflow to Scrape Reviews</button>
        <div class="workflow-spinner-area" id="workflowSpinner">
          <div class="workflow-spinner"></div>
          <div class="workflow-message">Running scrapper to fetch reviews…</div>
        </div>
        <div class="workflow-success" id="workflowSuccess">
          <div class="workflow-success-icon">✓</div>
          <div class="workflow-success-text">Fetched reviews</div>
        </div>
      </div>

      <!-- Query Controls (hidden until workflow completes) -->
      <div class="rde-controls" id="rdeControls">
        <select id="rdeSelect"></select>
        <button class="btn-analyze" onclick="analyzeRDE()">Analyze</button>
      </div>

      <div class="rde-status" id="rdeStatus"></div>
      <div class="rde-answer" id="rdeAnswer">
        <div class="rde-answer-header" id="rdeAnswerHeader"></div>
        <div class="rde-answer-body" id="rdeAnswerBody"></div>
      </div>
    </div>
  </div>

  <!-- ─── JavaScript ─────────────────────────────── -->
  <script>
    // ── State ──────────────────────────────
    const state = {
      tracks: [],
      consecutiveSkips: 0,
      skippedIds: [],
      savedIds: [],
      playingId: null,
      workflowDone: false,
    };

    // ── Init ───────────────────────────────
    document.addEventListener('DOMContentLoaded', () => {
      loadTracks();
      loadRDEQuestions();
    });

    // ── Track Loading ──────────────────────
    async function loadTracks() {
      const list = document.getElementById('trackList');
      list.innerHTML = '<div class="loading-bar"><div class="dot-pulse"><span></span><span></span><span></span></div><span>Loading tracks…</span></div>';

      const ctx = document.getElementById('moodInput').value.trim();
      const url = ctx ? `/api/tracks?context=${encodeURIComponent(ctx)}` : '/api/tracks';

      try {
        const resp = await fetch(url);
        const tracks = await resp.json();
        state.tracks = tracks;
        state.consecutiveSkips = 0;
        state.skippedIds = [];
        state.playingId = null;
        document.getElementById('trackCount').textContent = tracks.length + ' Tracks';
        renderTracks(tracks);
      } catch (err) {
        list.innerHTML = '<div class="loading-bar" style="color:var(--accent-red-bright)">Failed to load tracks</div>';
      }
    }

    function renderTracks(tracks) {
      const list = document.getElementById('trackList');
      list.innerHTML = '';
      tracks.forEach((t, idx) => {
        const card = document.createElement('div');
        card.className = 'track-card';
        card.id = `card-${t.id}`;
        card.style.animationDelay = `${idx * 0.1}s`;
        if (state.savedIds.includes(t.id)) card.classList.add('saved');
        if (state.skippedIds.includes(t.id)) card.classList.add('skipped');
        if (state.playingId === t.id) card.classList.add('playing');

        const colors = t.art_colors || ['#5c3a1e','#c0392b','#d4a017'];
        const initial = t.title.charAt(0).toUpperCase();

        card.innerHTML = `
          <div class="track-art" style="background: linear-gradient(135deg, ${colors[0]}, ${colors[1]}, ${colors[2]});">
            <div class="track-art-inner">${initial}</div>
          </div>
          <div class="track-info">
            <div class="track-title-row">
              <div class="track-title">${t.title}</div>
              <span class="track-artist">- ${t.artist}</span>
            </div>
            <div class="track-meta">${t.genre} <span class="dot"></span> ${t.duration} <span class="dot"></span> ${t.album} (${t.year})</div>
            <div class="why-this-section">
              <div class="why-this-label"><span class="icon">✦</span> <span class="label-text">WHY THIS</span></div>
              <div class="why-this-text">${t.why_this}</div>
            </div>
            <div class="listeners-section">
              <div class="listeners-label"><span class="icon">💬</span> <span class="label-text">LISTENERS SAID</span></div>
              <div class="listeners-text">"${t.listener_quote.text}"</div>
              <div class="listeners-source"><span class="src-icon">📍</span> ${t.listener_quote.source}</div>
            </div>
            <div class="track-actions">
              <button class="btn-play" onclick="playTrack('${t.id}')">▶ Play</button>
              <button class="btn-save" onclick="saveTrack('${t.id}')">♡ Save</button>
              <button class="btn-skip" onclick="skipTrack('${t.id}')">✕ Skip</button>
            </div>
          </div>
        `;
        list.appendChild(card);
      });
    }

    // ── Track Actions ──────────────────────
    function playTrack(id) {
      state.consecutiveSkips = 0;
      state.playingId = id;
      renderTracks(state.tracks);
    }

    function saveTrack(id) {
      if (!state.savedIds.includes(id)) state.savedIds.push(id);
      renderTracks(state.tracks);
    }

    function skipTrack(id) {
      if (!state.skippedIds.includes(id)) state.skippedIds.push(id);
      state.consecutiveSkips++;
      state.playingId = null;
      renderTracks(state.tracks);

      // After 2 consecutive skips → repair prompt
      if (state.consecutiveSkips >= 2) {
        setTimeout(() => showRepair(), 400);
      }
    }

    // ── Repair Flow ────────────────────────
    function showRepair() {
      document.getElementById('repairModal').classList.add('visible');
      document.getElementById('repairInput').value = '';
      document.getElementById('repairInput').focus();
    }

    function dismissRepair() {
      document.getElementById('repairModal').classList.remove('visible');
      state.consecutiveSkips = 0;
    }

    async function submitRepair() {
      const feedback = document.getElementById('repairInput').value.trim();
      if (!feedback) return;

      document.getElementById('repairModal').classList.remove('visible');

      const resp = await fetch('/api/repair', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ feedback, skipped_ids: state.skippedIds }),
      });
      const data = await resp.json();
      state.consecutiveSkips = 0;

      // Show the repair result as a special card
      const list = document.getElementById('trackList');
      const repairDiv = document.createElement('div');
      repairDiv.className = 'repair-result';
      const t = data.track;
      const colors = t.art_colors || ['#5c3a1e','#c0392b','#d4a017'];
      repairDiv.innerHTML = `
        <div class="repair-note">🔄 ${data.adjustment_note}</div>
        <div class="track-card" style="margin:0;border-color:rgba(212,160,23,0.3);">
          <div class="track-art" style="background: linear-gradient(135deg, ${colors[0]}, ${colors[1]}, ${colors[2]});">
            <div class="track-art-inner">${t.title.charAt(0)}</div>
          </div>
          <div class="track-info">
            <div class="track-title-row">
              <div class="track-title">${t.title}</div>
              <span class="track-artist">- ${t.artist}</span>
            </div>
            <div class="track-meta">${t.genre} <span class="dot"></span> ${t.duration} <span class="dot"></span> ${t.album} (${t.year})</div>
            <div class="why-this-section">
              <div class="why-this-label"><span class="icon">✦</span> <span class="label-text">WHY THIS - ADJUSTED</span></div>
              <div class="why-this-text">${data.why_this}</div>
            </div>
            <div class="listeners-section">
              <div class="listeners-label"><span class="icon">💬</span> <span class="label-text">LISTENERS SAID</span></div>
              <div class="listeners-text">"${data.listener_quote.text}"</div>
              <div class="listeners-source"><span class="src-icon">📍</span> ${data.listener_quote.source}</div>
            </div>
            <div class="track-actions">
              <button class="btn-play" onclick="playTrack('${t.id}')">▶ Play</button>
              <button class="btn-save" onclick="saveTrack('${t.id}')">♡ Save</button>
            </div>
          </div>
        </div>
      `;
      list.prepend(repairDiv);
      repairDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    // ── RDE View ───────────────────────────
    function showRDE() {
      document.getElementById('rdeOverlay').classList.add('visible');
      // Reset workflow state each time the overlay opens
      if (!state.workflowDone) {
        document.getElementById('rdeWorkflow').classList.remove('hidden');
        document.getElementById('btnRunWorkflow').classList.remove('hidden');
        document.getElementById('workflowSpinner').classList.remove('visible');
        document.getElementById('workflowSuccess').classList.remove('visible');
        document.getElementById('rdeControls').classList.remove('visible');
        document.getElementById('rdeStatus').innerHTML = '';
        document.getElementById('rdeAnswer').classList.remove('visible');
      }
    }
    function hideRDE() { document.getElementById('rdeOverlay').classList.remove('visible'); }

    // ── Workflow ───────────────────────────
    function runWorkflow() {
      const btn = document.getElementById('btnRunWorkflow');
      const spinner = document.getElementById('workflowSpinner');
      const success = document.getElementById('workflowSuccess');
      const controls = document.getElementById('rdeControls');
      const workflow = document.getElementById('rdeWorkflow');

      // Hide button, show spinner
      btn.classList.add('hidden');
      spinner.classList.add('visible');

      // After 10 seconds, show success and then reveal queries
      setTimeout(() => {
        spinner.classList.remove('visible');
        success.classList.add('visible');

        // After a brief pause to read the success message, show the queries
        setTimeout(() => {
          workflow.classList.add('hidden');
          controls.classList.add('visible');
          state.workflowDone = true;
        }, 1500);
      }, 10000);
    }

    async function loadRDEQuestions() {
      try {
        const resp = await fetch('/api/questions');
        const questions = await resp.json();
        const sel = document.getElementById('rdeSelect');
        sel.innerHTML = questions.map(q => `<option value="${q.key}">${q.title}</option>`).join('');
      } catch (e) { console.error('Failed to load questions', e); }
    }

    function mdToHtml(md) {
      let html = md;
      html = html.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
      html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
      html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
      html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
      html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
      html = html.replace(/^  (\d+)\. "(.+)"$/gm, '<blockquote><strong>[$1]</strong> "$2"</blockquote>');
      html = html.replace(/^  [•] (.+)$/gm, '<li>$1</li>');
      html = html.replace(/((?:<li>.*<\/li>\n?)+)/g, '<ul>$1</ul>');
      const lines = html.split('\n');
      let result = [];
      for (let line of lines) {
        const trimmed = line.trim();
        if (trimmed === '') result.push('');
        else if (trimmed.startsWith('<')) result.push(trimmed);
        else result.push('<p>' + trimmed + '</p>');
      }
      return result.join('\n');
    }

    async function analyzeRDE() {
      const status = document.getElementById('rdeStatus');
      const answerBox = document.getElementById('rdeAnswer');
      const header = document.getElementById('rdeAnswerHeader');
      const body = document.getElementById('rdeAnswerBody');

      answerBox.classList.remove('visible');
      status.innerHTML = '<div class="dot-pulse" style="display:inline-flex;vertical-align:middle;margin-right:8px;"><span></span><span></span><span></span></div> Running RAG analysis…';

      const qKey = document.getElementById('rdeSelect').value;

      const payload = { question_key: qKey };

      try {
        const resp = await fetch('/api/ask', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        const data = await resp.json();
        status.innerHTML = `✅ Analysis complete - <strong>${data.evidence_count} evidence documents</strong> retrieved`;
        header.textContent = data.question;
        body.innerHTML = mdToHtml(data.answer);
        answerBox.classList.add('visible');
      } catch (e) {
        status.innerHTML = '❌ Analysis failed';
      }
    }

    // Enter key support
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        if (document.activeElement === document.getElementById('repairInput')) submitRepair();
        if (document.activeElement === document.getElementById('moodInput')) loadTracks();

      }
      if (e.key === 'Escape') {
        dismissRepair();
        hideRDE();
      }
    });
    /* ─── AI Modal Logic ────────────── */
    function showAIModal() {
      document.getElementById("aiModal").classList.add("visible");
    }
    function dismissAIModal() {
      document.getElementById("aiModal").classList.remove("visible");
    }
  </script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def index():
    return MAIN_HTML
