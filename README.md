# 🚀 YouTube Shorts Autonomous Uploader

> **Production-grade automated publishing system for YouTube Shorts.**  
> Features native Apple Vision OCR for automatic video recognition, dynamic metadata generation, anti-spam heuristics, and local real-time dashboard analytics.

---

## 🌟 Key Features

* **Resumable Chunked Uploads:** Uploads large videos in 2MB chunks with exponential backoff and automatic retry on network drops (`[Errno 60]` timeout protection).
* **On-Device Vision OCR:** Extracts video text hooks using a compiled Swift binary (`Apple Vision Framework`) directly from extracted video frames without external cloud APIs.
* **Smart Anti-Spam Scheduling:** Enforces randomized jitter intervals and minimum cooldown delays (2.5h) to maintain optimal algorithmic seed audience distribution.
* **Channel Queue Routing:** Automatically routes and switches between channels (`BlwSmex`, `biribro`) based on queue availability.
* **Interactive Desktop Dashboard:** Renders a clean, standalone dark-mode HTML dashboard (`generate_dashboard.py`) with real-time video statuses and direct links.

---

## 🛠 Architecture

```
                 ┌────────────────────────────────┐
                 │    Pending Video (MP4)         │
                 └───────────────┬────────────────┘
                                 │
           ┌─────────────────────┴─────────────────────┐
           ▼                                           ▼
 [Native Swift OCR]                          [Metadata Engine]
  Apple Vision Text Extractor                 Title & Tag Randomization
           │                                           │
           └─────────────────────┬─────────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │  YouTube Data API v3    │
                    │  Resumable Upload Loop  │
                    │  (OAuth2 Token Auto-Rx) │
                    └────────────┬────────────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
         [Uploaded Archive]          [Desktop Dashboard]
         moves to uploaded/          auto-refreshes HTML
```

---

## 📦 Quickstart

### Prerequisites
* Python 3.9+
* FFmpeg (`brew install ffmpeg`)
* Google Cloud Console Project with YouTube Data API v3 enabled.

### Setup
1. Clone the repository:
   ```bash
   git clone git@github.com:VseyadCraft/youtube-uploader.git
   cd youtube-uploader
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Place your OAuth credentials in `client_secrets.json` (ignored by Git for safety).
4. Run dry-run or live upload:
   ```bash
   # Dry-run test
   python3 upload_shorts.py --dry-run

   # Force immediate publication
   ./run.sh --force
   ```

---

## 🔒 Security
All OAuth tokens, client secrets, and media files are strictly excluded via `.gitignore`.

---

## 📜 License
MIT License. Created by [VseyadCraft](https://github.com/VseyadCraft).
