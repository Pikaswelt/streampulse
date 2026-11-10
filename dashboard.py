"""
StreamPulse Anime High-Quality Live Dashboard
Ultra-sleek cyberpunk anime interface with Cloudflare Tunnel support.
"""

import os
import re
import json
import urllib.parse
from pathlib import Path
from flask import Flask, render_template_string, jsonify, send_from_directory

app = Flask(__name__)
BASE_DIR = Path("/root/streampulse")
OUTPUT_DIR = BASE_DIR / "output"
SCREENSHOTS_DIR = OUTPUT_DIR / "screenshots"
LIVE_FEED_FILE = OUTPUT_DIR / "live_feed.md"
RUNNER_LOG_FILE = OUTPUT_DIR / "stream_runner.log"

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>⚡ StreamPulse Live | NTE 1.4 Special Program</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Rajdhani:wght@500;600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-dark: #070913;
      --bg-card: rgba(16, 20, 38, 0.85);
      --border-neon: #a855f7;
      --cyan-neon: #06b6d4;
      --magenta-neon: #f43f5e;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    
    body {
      background-color: var(--bg-dark);
      background-image: 
        radial-gradient(circle at 15% 15%, rgba(168, 85, 247, 0.15) 0%, transparent 45%),
        radial-gradient(circle at 85% 85%, rgba(6, 182, 212, 0.12) 0%, transparent 50%);
      color: var(--text-main);
      font-family: 'Inter', sans-serif;
      min-height: 100vh;
      padding-bottom: 60px;
    }

    header {
      background: rgba(10, 14, 28, 0.95);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid rgba(168, 85, 247, 0.3);
      padding: 18px 24px;
      position: sticky;
      top: 0;
      z-index: 100;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    }

    .logo-container {
      display: flex;
      align-items: center;
      gap: 14px;
    }

    .logo-badge {
      background: linear-gradient(135deg, #a855f7, #06b6d4);
      color: #fff;
      font-family: 'Orbitron', sans-serif;
      font-weight: 900;
      font-size: 14px;
      padding: 6px 12px;
      border-radius: 8px;
      letter-spacing: 1px;
      box-shadow: 0 0 15px rgba(168, 85, 247, 0.6);
    }

    .header-title {
      font-family: 'Rajdhani', sans-serif;
      font-size: 22px;
      font-weight: 700;
      color: #fff;
      text-transform: uppercase;
      letter-spacing: 1.5px;
    }

    .header-title span {
      color: var(--cyan-neon);
      text-shadow: 0 0 10px rgba(6, 182, 212, 0.5);
    }

    .live-status {
      display: flex;
      align-items: center;
      gap: 10px;
      background: rgba(244, 63, 94, 0.15);
      border: 1px solid rgba(244, 63, 94, 0.4);
      padding: 6px 14px;
      border-radius: 20px;
      font-family: 'Orbitron', sans-serif;
      font-size: 12px;
      color: #fca5a5;
    }

    .live-dot {
      width: 10px;
      height: 10px;
      background-color: var(--magenta-neon);
      border-radius: 50%;
      box-shadow: 0 0 10px var(--magenta-neon);
      animation: pulse 1.5s infinite;
    }

    @keyframes pulse {
      0% { transform: scale(0.95); opacity: 0.8; }
      50% { transform: scale(1.3); opacity: 1; }
      100% { transform: scale(0.95); opacity: 0.8; }
    }

    .container {
      max-width: 1200px;
      margin: 30px auto;
      padding: 0 20px;
      display: grid;
      grid-template-columns: 1fr 340px;
      gap: 28px;
    }

    @media (max-width: 900px) {
      .container { grid-template-columns: 1fr; }
    }

    /* Main Feed */
    .feed-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
    }

    .feed-title {
      font-family: 'Rajdhani', sans-serif;
      font-size: 24px;
      font-weight: 700;
      letter-spacing: 1px;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .feed-title::before {
      content: '';
      display: inline-block;
      width: 4px;
      height: 20px;
      background: var(--cyan-neon);
      border-radius: 2px;
      box-shadow: 0 0 10px var(--cyan-neon);
    }

    .cards-container {
      display: flex;
      flex-direction: column;
      gap: 24px;
    }

    .update-card {
      background: var(--bg-card);
      border: 1px solid rgba(168, 85, 247, 0.25);
      border-radius: 14px;
      padding: 20px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
      transition: all 0.3s ease;
      position: relative;
      overflow: hidden;
    }

    .update-card:hover {
      border-color: var(--cyan-neon);
      transform: translateY(-2px);
      box-shadow: 0 12px 36px rgba(6, 182, 212, 0.2);
    }

    .card-top {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 14px;
    }

    .card-time {
      font-family: 'Orbitron', sans-serif;
      font-size: 12px;
      color: var(--cyan-neon);
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .badge-highlight {
      background: rgba(168, 85, 247, 0.2);
      border: 1px solid rgba(168, 85, 247, 0.5);
      color: #d8b4fe;
      font-size: 11px;
      padding: 3px 8px;
      border-radius: 6px;
      font-weight: 600;
      text-transform: uppercase;
    }

    .card-text {
      font-size: 16px;
      line-height: 1.6;
      color: #e2e8f0;
      margin-bottom: 16px;
      padding-left: 12px;
      border-left: 3px solid var(--border-neon);
    }

    .card-image-wrapper {
      margin-bottom: 16px;
      border-radius: 10px;
      overflow: hidden;
      border: 1px solid rgba(255, 255, 255, 0.1);
      background: #000;
    }

    .card-image {
      width: 100%;
      max-height: 420px;
      object-fit: cover;
      display: block;
      transition: transform 0.3s ease;
    }

    .card-image:hover {
      transform: scale(1.02);
    }

    .card-actions {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
    }

    .btn-x {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: #000;
      color: #fff;
      border: 1px solid rgba(255, 255, 255, 0.2);
      padding: 8px 16px;
      border-radius: 8px;
      text-decoration: none;
      font-weight: 600;
      font-size: 13px;
      transition: all 0.2s;
    }

    .btn-x:hover {
      background: #1d9bf0;
      border-color: #1d9bf0;
      box-shadow: 0 0 15px rgba(29, 155, 240, 0.5);
    }

    .btn-copy {
      background: rgba(255, 255, 255, 0.06);
      border: 1px solid rgba(255, 255, 255, 0.15);
      color: #cbd5e1;
      padding: 8px 14px;
      border-radius: 8px;
      cursor: pointer;
      font-size: 13px;
      font-weight: 500;
      transition: all 0.2s;
    }

    .btn-copy:hover {
      background: rgba(255, 255, 255, 0.15);
      color: #fff;
    }

    /* Sidebar */
    .sidebar {
      display: flex;
      flex-direction: column;
      gap: 20px;
    }

    .widget-box {
      background: var(--bg-card);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 14px;
      padding: 20px;
      box-shadow: 0 6px 24px rgba(0, 0, 0, 0.3);
    }

    .widget-title {
      font-family: 'Rajdhani', sans-serif;
      font-size: 18px;
      font-weight: 700;
      color: #fff;
      margin-bottom: 14px;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .redeem-code-card {
      background: rgba(168, 85, 247, 0.15);
      border: 1px dashed var(--border-neon);
      border-radius: 8px;
      padding: 12px;
      margin-bottom: 10px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .code-text {
      font-family: 'Orbitron', monospace;
      font-weight: 700;
      color: #fbcfe8;
      font-size: 15px;
      letter-spacing: 1px;
    }

    .info-list {
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: 10px;
      font-size: 13px;
      color: var(--text-muted);
    }

    .info-list strong { color: #fff; }

    .pulse-terminal {
      background: #000;
      border: 1px solid rgba(6, 182, 212, 0.3);
      border-radius: 8px;
      padding: 12px;
      font-family: monospace;
      font-size: 11px;
      color: #38bdf8;
      max-height: 220px;
      overflow-y: auto;
      white-space: pre-wrap;
      line-height: 1.4;
    }

    .empty-state {
      text-align: center;
      padding: 40px 20px;
      color: var(--text-muted);
      border: 1px dashed rgba(255,255,255,0.1);
      border-radius: 12px;
    }
  </style>
</head>
<body>

  <header>
    <div class="logo-container">
      <div class="logo-badge">⚡ STREAMPULSE</div>
      <div class="header-title">NTE 1.4 <span>SPECIAL PROGRAM</span></div>
    </div>
    <div class="live-status">
      <div class="live-dot"></div>
      <span id="live-text">STREAMING LIVE</span>
    </div>
  </header>

  <div class="container">
    <!-- Left Main Feed -->
    <main>
      <div class="feed-header">
        <h2 class="feed-title">Real-Time AI Highlights & Posts</h2>
        <span style="font-size: 12px; color: var(--text-muted);" id="auto-refresh-indicator">Auto-refresh: 3s</span>
      </div>

      <div class="cards-container" id="updates-list">
        <div class="empty-state">
          <p>Listening to live stream audio and preparing first highlight cards...</p>
        </div>
      </div>
    </main>

    <!-- Right Sidebar -->
    <aside class="sidebar">
      <!-- Redeem Codes Tracker -->
      <div class="widget-box">
        <h3 class="widget-title">🎁 Redeem Codes</h3>
        <div id="redeem-codes-container">
          <p style="font-size: 12px; color: var(--text-muted);">Codes will appear here as soon as they drop in the stream!</p>
        </div>
      </div>

      <!-- Stream Meta -->
      <div class="widget-box">
        <h3 class="widget-title">ℹ️ Event Details</h3>
        <ul class="info-list">
          <li><strong>Event:</strong> Neverness to Everness v1.4</li>
          <li><strong>Title:</strong> For Whom the Verses Mourn</li>
          <li><strong>Zero API Cost:</strong> faster-whisper (int8)</li>
          <li><strong>Encrypted Tunnel:</strong> Cloudflare Edge</li>
        </ul>
      </div>

      <!-- Live Terminal Output -->
      <div class="widget-box">
        <h3 class="widget-title">📟 StreamPulse Terminal</h3>
        <div class="pulse-terminal" id="terminal-output">Loading runner logs...</div>
      </div>
    </aside>
  </div>

  <script>
    async function fetchUpdates() {
      try {
        const res = await fetch('/api/updates');
        const data = await res.json();
        
        // Render Feed Cards
        const container = document.getElementById('updates-list');
        if (data.items && data.items.length > 0) {
          container.innerHTML = data.items.map(item => `
            <div class="update-card">
              <div class="card-top">
                <div class="card-time">⏱ ${item.timestamp}</div>
                <div class="badge-highlight">LIVE HIGHLIGHT</div>
              </div>
              <div class="card-text">${escapeHtml(item.text)}</div>
              ${item.image ? `
                <div class="card-image-wrapper">
                  <img src="/screenshots/${item.image}" class="card-image" alt="Live Frame">
                </div>
              ` : ''}
              <div class="card-actions">
                <a href="${item.intent_url}" target="_blank" class="btn-x">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                  </svg>
                  1-Click Post to X
                </a>
                <button class="btn-copy" onclick="navigator.clipboard.writeText('${escapeJs(item.text)}')">Copy Text</button>
              </div>
            </div>
          `).join('');
        }

        // Render Terminal
        if (data.logs) {
          const term = document.getElementById('terminal-output');
          term.textContent = data.logs;
          term.scrollTop = term.scrollHeight;
        }

      } catch (err) {
        console.error('Update fetch error:', err);
      }
    }

    function escapeHtml(text) {
      return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
    }

    function escapeJs(text) {
      return text.replace(/'/g, "\\'").replace(/\\n/g, ' ');
    }

    setInterval(fetchUpdates, 3000);
    fetchUpdates();
  </script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route("/screenshots/<path:filename>")
def serve_screenshot(filename):
    return send_from_directory(str(SCREENSHOTS_DIR), filename)


@app.route("/api/updates")
def api_updates():
    items = []
    if LIVE_FEED_FILE.exists():
        content = LIVE_FEED_FILE.read_text(encoding="utf-8")
        raw_sections = content.split("### ⚡ Highlight at ")
        for sec in raw_sections[1:]:
            lines = sec.strip().splitlines()
            if not lines:
                continue
            timestamp = lines[0].strip()
            
            # Extract quote / tweet text
            text_lines = []
            image_name = None
            for line in lines[1:]:
                if line.startswith("> "):
                    text_lines.append(line[2:].strip())
                elif line.startswith("![Stream Snapshot](screenshots/"):
                    match = re.search(r"screenshots/([^)]+)", line)
                    if match:
                        image_name = match.group(1)

            tweet_text = " ".join(text_lines)
            if tweet_text:
                encoded = urllib.parse.quote(tweet_text)
                intent_url = f"https://twitter.com/intent/tweet?text={encoded}"
                items.insert(0, {
                    "timestamp": timestamp,
                    "text": tweet_text,
                    "image": image_name,
                    "intent_url": intent_url
                })

    # Read latest logs
    logs = ""
    if RUNNER_LOG_FILE.exists():
        try:
            log_lines = RUNNER_LOG_FILE.read_text(encoding="utf-8").splitlines()
            logs = "\n".join(log_lines[-25:])
        except Exception:
            pass

    return jsonify({"items": items, "logs": logs})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
