#!/usr/bin/env python3
import os
import sys
import glob
import json
import base64
import tempfile
import subprocess
from datetime import datetime, time as dtime, timedelta

BASE_DIR = os.path.expanduser('~/youtube-uploader')
PENDING_DIR = os.path.join(BASE_DIR, 'pending')
UPLOADED_DIR = os.path.join(BASE_DIR, 'uploaded')
HISTORY_FILE = os.path.join(BASE_DIR, 'history.json')
DASHBOARD_FILE = os.path.expanduser('~/Desktop/Студия_Shorts/3_Аналитика_и_Дашборд/Дашборд_Shorts.html')
FFMPEG = '/opt/homebrew/bin/ffmpeg'

TIME_SLOTS = [
    (11, 0),   # 11:00
    (14, 30),  # 14:30
    (18, 0),   # 18:00
    (21, 30),  # 21:30
]

def get_next_slot():
    now = datetime.now()
    today = now.date()
    for h, m in TIME_SLOTS:
        t = datetime.combine(today, dtime(h, m))
        if t > now:
            return t
    tomorrow = today + timedelta(days=1)
    return datetime.combine(tomorrow, dtime(TIME_SLOTS[0][0], TIME_SLOTS[0][1]))

def extract_thumbnail_base64(filepath):
    if not os.path.exists(FFMPEG) or not os.path.exists(filepath):
        return ""
    try:
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            tmp_path = tmp.name
        cmd = [
            FFMPEG, '-y', '-ss', '00:00:02.0', '-i', filepath,
            '-vframes', '1',
            '-vf', 'scale=200:356:force_original_aspect_ratio=decrease',
            '-q:v', '3',
            tmp_path
        ]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
        if res.returncode == 0 and os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
            with open(tmp_path, 'rb') as f:
                encoded = base64.b64encode(f.read()).decode('utf-8')
            try:
                os.remove(tmp_path)
            except OSError:
                pass
            return f"data:image/jpeg;base64,{encoded}"
        try:
            os.remove(tmp_path)
        except OSError:
            pass
    except Exception:
        pass
    return ""

def build_dashboard():
    pending_files = sorted(
        glob.glob(os.path.join(PENDING_DIR, '*.mp4')) + glob.glob(os.path.join(PENDING_DIR, '*.mov')),
        key=lambda x: int(os.path.splitext(os.path.basename(x))[0]) if os.path.splitext(os.path.basename(x))[0].isdigit() else 9999
    )
    
    history = {}
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except Exception:
            pass
            
    uploads = history.get('uploads', [])
    total_views = sum(u.get('views', 0) for u in uploads)
    avg_views = int(total_views / max(1, len(uploads)))
    
    next_slot = get_next_slot()
    schedule_forecast = []
    
    curr = next_slot
    for i, f in enumerate(pending_files[:8]):
        fname = os.path.basename(f)
        # Extract thumbnail for top 4 cards
        thumb_b64 = extract_thumbnail_base64(f) if i < 4 else ""
        schedule_forecast.append({
            'filename': fname,
            'slot_time': curr.strftime('%d.%m в %H:%M'),
            'thumb': thumb_b64
        })
        # Advance slot
        found_next = False
        today_date = curr.date()
        for h, m in TIME_SLOTS:
            slot_candidate = datetime.combine(today_date, dtime(h, m))
            if slot_candidate > curr:
                curr = slot_candidate
                found_next = True
                break
        if not found_next:
            curr = datetime.combine(today_date + timedelta(days=1), dtime(TIME_SLOTS[0][0], TIME_SLOTS[0][1]))

    next_slot_iso = next_slot.isoformat()
    now_str = datetime.now().strftime('%d.%m.%Y %H:%M')

    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Shorts Studio — BlwSmex Dashboard</title>
<style>
  :root {{
    --bg: #0b0f19;
    --card-bg: rgba(23, 28, 44, 0.7);
    --border: rgba(255, 255, 255, 0.08);
    --text: #f8fafc;
    --text-muted: #94a3b8;
    --accent: #6366f1;
    --accent-glow: rgba(99, 102, 241, 0.35);
    --green: #10b981;
    --pink: #ec4899;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, sans-serif; }}
  body {{
    background: radial-gradient(circle at 10% 20%, #171b33 0%, var(--bg) 100%);
    color: var(--text);
    min-height: 100vh;
    padding: 30px;
    display: flex;
    justify-content: center;
  }}
  .container {{ max-width: 1080px; width: 100%; }}
  
  header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 25px;
    padding-bottom: 20px;
    border-bottom: 1px solid var(--border);
  }}
  .brand {{ display: flex; align-items: center; gap: 14px; }}
  .brand-logo {{
    width: 44px; height: 44px; background: linear-gradient(135deg, #ef4444, #dc2626);
    border-radius: 12px; display: flex; align-items: center; justify-content: center;
    box-shadow: 0 4px 18px rgba(239, 68, 68, 0.4); font-size: 20px; color: #fff;
  }}
  h1 {{ font-size: 24px; font-weight: 700; letter-spacing: -0.5px; }}
  
  .status-badge {{
    display: inline-flex; align-items: center; gap: 8px;
    background: rgba(16, 185, 129, 0.15); color: #34d399;
    padding: 7px 16px; border-radius: 20px; font-size: 13px; font-weight: 600;
    border: 1px solid rgba(16, 185, 129, 0.3);
  }}
  .dot {{ width: 8px; height: 8px; background: #34d399; border-radius: 50%; animation: pulse 2s infinite; }}
  @keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.3; }} }}

  .grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 25px; }}
  .card {{
    background: var(--card-bg); backdrop-filter: blur(20px);
    border: 1px solid var(--border); border-radius: 18px;
    padding: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.25);
  }}
  .card-title {{ font-size: 12px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 8px; font-weight: 600; }}
  .card-val {{ font-size: 28px; font-weight: 800; color: #fff; letter-spacing: -0.5px; }}
  .card-sub {{ font-size: 12px; color: var(--text-muted); margin-top: 6px; }}

  .timer-banner {{
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.18), rgba(236, 72, 153, 0.15));
    border: 1px solid rgba(99, 102, 241, 0.35); border-radius: 20px;
    padding: 25px 30px; margin-bottom: 30px; display: flex; justify-content: space-between; align-items: center;
    box-shadow: 0 15px 35px rgba(99, 102, 241, 0.12);
  }}
  .timer-info h2 {{ font-size: 19px; margin-bottom: 6px; }}
  .timer-info p {{ font-size: 14px; color: var(--text-muted); }}
  .countdown {{ font-size: 42px; font-weight: 800; font-variant-numeric: tabular-nums; letter-spacing: -1px; color: #c7d2fe; text-shadow: 0 0 25px var(--accent-glow); }}

  .section-title {{ font-size: 18px; font-weight: 700; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }}

  .visual-queue {{
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 30px;
  }}
  .queue-card {{
    background: var(--card-bg); border: 1px solid var(--border); border-radius: 16px;
    overflow: hidden; display: flex; flex-direction: column; transition: transform 0.2s;
  }}
  .queue-card:hover {{ transform: translateY(-3px); border-color: rgba(99, 102, 241, 0.5); }}
  .queue-thumb {{
    width: 100%; aspect-ratio: 9/16; max-height: 180px; object-fit: cover; background: #1e293b;
    display: flex; align-items: center; justify-content: center; color: var(--text-muted); font-size: 13px;
  }}
  .queue-body {{ padding: 14px; }}
  .queue-fname {{ font-weight: 700; font-size: 15px; margin-bottom: 4px; }}
  .queue-slot {{ font-size: 12px; color: #38bdf8; font-weight: 600; }}

  table {{ width: 100%; border-collapse: collapse; }}
  th {{ text-align: left; padding: 12px 16px; font-size: 12px; color: var(--text-muted); text-transform: uppercase; border-bottom: 1px solid var(--border); }}
  td {{ padding: 14px 16px; font-size: 14px; border-bottom: 1px solid rgba(255, 255, 255, 0.04); vertical-align: middle; }}
  tr:hover td {{ background: rgba(255, 255, 255, 0.02); }}
  .badge-views {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 700; background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }}
  a.yt-link {{ color: #60a5fa; text-decoration: none; font-weight: 600; }}
  a.yt-link:hover {{ text-decoration: underline; }}

  .actions {{ display: flex; gap: 14px; margin-top: 30px; flex-wrap: wrap; }}
  .btn {{
    background: var(--card-bg); border: 1px solid var(--border); color: #fff;
    padding: 12px 22px; border-radius: 12px; text-decoration: none; font-size: 14px;
    font-weight: 600; cursor: pointer; transition: all 0.2s; display: inline-flex; align-items: center; gap: 8px;
  }}
  .btn:hover {{ background: rgba(255,255,255,0.08); border-color: rgba(255,255,255,0.25); transform: translateY(-1px); }}
  .btn-primary {{ background: linear-gradient(135deg, #6366f1, #4f46e5); border: none; box-shadow: 0 4px 18px rgba(99, 102, 241, 0.4); }}
  .btn-primary:hover {{ box-shadow: 0 6px 25px rgba(99, 102, 241, 0.6); }}
</style>
</head>
<body>
<div class="container">
  <header>
    <div class="brand">
      <div class="brand-logo">▶</div>
      <div>
        <h1>YouTube Shorts Studio</h1>
        <div style="font-size: 13px; color: var(--text-muted); margin-top: 3px;">Канал: <strong style="color: #fff;">BlwSmex</strong> • Обновлено: {now_str}</div>
      </div>
    </div>
    <div class="status-badge"><div class="dot"></div> Автопостинг активен (4 в день)</div>
  </header>

  <div class="grid">
    <div class="card">
      <div class="card-title">Видео в очереди</div>
      <div class="card-val" style="color: #38bdf8;">{len(pending_files)}</div>
      <div class="card-sub">Хватит на {round(len(pending_files)/4, 1)} дн. автопостинга</div>
    </div>
    <div class="card">
      <div class="card-title">Темп публикации</div>
      <div class="card-val" style="color: #a78bfa;">4 <span style="font-size: 16px; font-weight: 400; color: var(--text-muted);">/ день</span></div>
      <div class="card-sub">11:00 • 14:30 • 18:00 • 21:30</div>
    </div>
    <div class="card">
      <div class="card-title">Всего просмотров</div>
      <div class="card-val" style="color: #34d399;">{total_views:,}</div>
      <div class="card-sub">Среднее: {avg_views:,} на ролик</div>
    </div>
    <div class="card">
      <div class="card-title">Уникализация</div>
      <div class="card-val" style="color: #fb7185;">100%</div>
      <div class="card-sub">Заголовки + Теги + Разброс мин</div>
    </div>
  </div>

  <div class="timer-banner">
    <div class="timer-info">
      <h2>Следующая публикация</h2>
      <p>Слот: <strong style="color: #fff;">{next_slot.strftime('%d.%m.%Y в %H:%M')}</strong> (±1-14 мин для защиты от спам-фильтра)</p>
    </div>
    <div class="countdown" id="timer">--:--:--</div>
  </div>

  <div class="section-title">🎬 Ближайшие премьеры из очереди</div>
  <div class="visual-queue">
"""
    for item in schedule_forecast[:4]:
        thumb_tag = f'<img class="queue-thumb" src="{item["thumb"]}" alt="preview">' if item['thumb'] else '<div class="queue-thumb">🎬 Превью</div>'
        html += f"""    <div class="queue-card">
      {thumb_tag}
      <div class="queue-body">
        <div class="queue-fname">{item['filename']}</div>
        <div class="queue-slot">🕒 {item['slot_time']}</div>
      </div>
    </div>\n"""

    html += """  </div>

  <div class="card">
    <div class="section-title">📈 Опубликованные ролики (Каталог BlwSmex)</div>
    <table>
      <thead>
        <tr>
          <th>Название ролика</th>
          <th>Просмотры</th>
          <th>Дата выхода</th>
          <th>Ссылка</th>
        </tr>
      </thead>
      <tbody>
"""
    for u in reversed(uploads):
        vid = u.get('video_id', '')
        title = u.get('title', 'Без названия')
        views = u.get('views', 0)
        uploaded_at = u.get('uploaded_at', '')
        try:
            dt = datetime.fromisoformat(uploaded_at).strftime('%d.%m %H:%M')
        except Exception:
            dt = uploaded_at
        views_badge = f'<span class="badge-views">🔥 {views:,}</span>' if views > 0 else '<span style="color: #38bdf8; font-weight: 600;">🚀 В эфире</span>'
        html += f"""        <tr>
          <td><strong>{title}</strong></td>
          <td>{views_badge}</td>
          <td style="color: var(--text-muted);">{dt}</td>
          <td><a class="yt-link" href="https://youtube.com/shorts/{vid}" target="_blank">Смотреть ↗</a></td>
        </tr>\n"""

    html += f"""      </tbody>
    </table>
  </div>

  <div class="actions">
    <a class="btn btn-primary" href="https://studio.youtube.com/channel/UCgItPibXiyzYy21qMQ07aUQ/videos/short" target="_blank">🎬 YouTube Studio</a>
    <a class="btn" href="file:///Users/tim/youtube-uploader/pending" target="_blank">📁 Папка очереди</a>
    <a class="btn" href="file:///Users/tim/Desktop" target="_blank">🖥 Рабочий стол</a>
  </div>
</div>

<script>
  const targetIso = "{next_slot_iso}";
  const targetTime = new Date(targetIso).getTime();

  function updateTimer() {{
    const now = new Date().getTime();
    const diff = targetTime - now;

    if (diff <= 0) {{
      document.getElementById('timer').innerText = "Публикация...";
      return;
    }}

    const hours = Math.floor(diff / (1000 * 60 * 60));
    const mins = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    const secs = Math.floor((diff % (1000 * 60)) / 1000);

    const pad = n => n.toString().padStart(2, '0');
    document.getElementById('timer').innerText = `${{pad(hours)}}:${{pad(mins)}}:${{pad(secs)}}`;
  }}

  updateTimer();
  setInterval(updateTimer, 1000);
</script>
</body>
</html>
"""
    with open(DASHBOARD_FILE, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Dashboard updated at {DASHBOARD_FILE} with thumbnails and stats!")

if __name__ == '__main__':
    build_dashboard()
