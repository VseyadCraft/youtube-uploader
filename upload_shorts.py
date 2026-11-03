#!/usr/bin/env python3
import warnings
warnings.filterwarnings('ignore')
import os
import sys
import glob
import json
import time
import random
import shutil
import tempfile
import subprocess
import socket
import ssl
import http.client
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

def wait_for_internet(timeout=120):
    """Ждёт восстановления интернет-соединения (особенно важно при выходе Mac из сна)."""
    start_time = time.time()
    targets = [("8.8.8.8", 53), ("1.1.1.1", 53), ("www.googleapis.com", 443)]
    while time.time() - start_time < timeout:
        for host, port in targets:
            try:
                s = socket.create_connection((host, port), timeout=3)
                s.close()
                return True
            except OSError:
                continue
        time.sleep(2)
    return False

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

BASE_DIR = os.path.expanduser('~/youtube-uploader')
PENDING_DIR = os.path.join(BASE_DIR, 'pending')
UPLOADED_DIR = os.path.join(BASE_DIR, 'uploaded')
CLIENT_SECRETS_FILE = os.path.join(BASE_DIR, 'client_secrets.json')
TOKEN_FILE = os.path.join(BASE_DIR, 'token.json')
HISTORY_FILE = os.path.join(BASE_DIR, 'history.json')

# Minimum cooldown between automatic uploads (hours) to protect against spam detection
COOLDOWN_HOURS = 2.5

TITLE_TEMPLATES = {
    'Попробовал обратную съёмку': [
        'Попробовал обратную съёмку ✨ Смотри до конца!',
        'Попробовал обратную съёмку 🔥 Часть {n}',
        'Попробовал обратную съёмку... Результат просто космос! ✨',
        'Попробовал обратную съёмку 🎯 Идеальный реверс',
        'Попробовал обратную съёмку 👀 Залип на 10 минут!',
        'Попробовал обратную съёмку... Как это возможно? 🤯',
        'Попробовал обратную съёмку ⚡️ Эпичный трюк',
        'Попробовал обратную съёмку — магия или ловкость? 🔮',
        'Попробовал обратную съёмку 💫 Чистый кайф для глаз',
        'Попробовал обратную съёмку (Не моргай!) 🧘‍♂️',
        'Попробовал обратную съёмку 🚀 Нереальная ловкость!',
        'Попробовал обратную съёмку... Попробуй повторить! 🏆'
    ],
    'Это гипнотизирует': [
        'Это гипнотизирует... Чистый релакс 🧘‍♂️',
        'Это гипнотизирует ✨ Залипательно на 100%',
        'Это гипнотизирует 🔥 Часть {n}',
        'Это реально гипнотизирует 😵‍💫 Оторваться невозможно!',
        'Это гипнотизирует 💫 Чистый кайф для глаз',
        'Это гипнотизирует... Смотри со звуком! 🎧',
        'Это гипнотизирует ⚡️ Не моргай!',
        'Это гипнотизирует 🔮 Залип на весь день',
        'Это гипнотизирует 👀 Идеальная плавность',
        'Это гипнотизирует 🎯 Самое залипательное видео',
        'Это гипнотизирует 🤤 Релаксация для мозга',
        'Это гипнотизирует... Смотри до последней секунды! ✨'
    ],
    'Не могу перестать смотреть': [
        'Не могу перестать смотреть... Чистый ASMR 🎧',
        'Не могу перестать смотреть ✨ Идеальный цикл',
        'Не могу перестать смотреть 🔥 Часть {n}',
        'Не могу перестать смотреть... Сколько раз пересмотрел? 👀',
        'Не могу перестать смотреть 💫 Залипательно до мурашек',
        'Не могу перестать смотреть 🎯 Лучший момент дня',
        'Не могу перестать смотреть 🧘 Мозг просто отключается',
        'Не могу перестать смотреть 😱 В конце самое залипательное',
        'Не могу перестать смотреть 🔮 Настоящий гипноз',
        'Не могу перестать смотреть ⚡️ Попробуй оторваться',
        'Не могу перестать смотреть... Это шедевр! 🏆',
        'Не могу перестать смотреть 🤤 Залип на повторе'
    ],
    'Сколько тут бусин?': [
        'Сколько тут бусин? Угадай в комментариях! 👇',
        'Сколько тут бусин? Я насчитал больше 50! 🔮',
        'Сколько тут бусин? 🔥 Раунд {n}',
        'Сколько тут бусин? (95% ошибаются!) 🤯',
        'Сколько тут бусин? Считаем вместе! 👀',
        'Сколько тут бусин? 🎯 Проверь свою внимательность',
        'Сколько тут бусин? ✨ Пиши догадки в комменты!',
        'Сколько тут бусин? А правильный ответ в конце! 🤫',
        'Сколько тут бусин? 💫 Кто первый угадает?',
        'Сколько тут бусин? ⚡️ Сложнее, чем кажется!',
        'Сколько тут бусин? 🧠 Тест на внимательность!',
        'Сколько тут бусин? У тебя получилось сосчитать? 🧐'
    ]
}

GENERIC_TEMPLATES = [
    '{base} ✨ Смотри до конца!',
    '{base} 🔥 Часть {n}',
    '{base}... Залипательно на 100% 👀',
    '{base} 🎯 Лучший момент',
    '{base}... Чистый ASMR 🎧',
    '{base} ⚡️ Оторваться невозможно!',
    '{base} 💫 Полный релакс',
    '{base} (В конце самое интересное) 😱'
]

# Dynamic calls-to-action to rotate in description
DESCRIPTION_CTAS = [
    "А сколько насчитал ты? Напиши в комментариях! 👇🔥",
    "Залип или пролистал? Напиши честно в комменты! 👀👇",
    "Поставь лайк, если досмотрел до конца! ❤️✨",
    "Смотри со звуком для максимального эффекта 🎧✨",
    "Напиши в комментариях, на какой секунде залип! ⏱️🔥",
    "Угадай, сколько здесь бусин, и проверь себя! 🔮👇",
    "Как тебе результат? Оцени от 1 до 10 в комментах! 💬⭐"
]

CORE_TAGS = ['shorts', 'шортс', 'бусины', 'satisfying', 'oddlysatisfying']

TAG_POOL = [
    'залипательно', 'релакс', 'асмр', 'fyp', 'viral',
    'тренды', 'рекомендации', 'тикток', 'гипноз', 'реверс',
    'трюки', 'эксперименты', 'топ', 'залипательное видео'
]

def load_history(filepath=None):
    target_file = filepath or HISTORY_FILE
    if os.path.exists(target_file):
        try:
            with open(target_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {
        'last_uploaded_at': None,
        'base_counts': {
            'Попробовал обратную съёмку': 3,
            'Это гипнотизирует': 2,
            'Не могу перестать смотреть': 2,
            'Сколько тут бусин?': 2
        },
        'used_titles': [
            'Попробовал обратную съёмку #shorts',
            'Это гипнотизирует #shorts',
            'Не могу перестать смотреть #shorts',
            'Сколько тут бусин? #shorts',
            'Попробовал обратную съёмку... Результат просто космос! ✨ #shorts'
        ],
        'uploads': []
    }

def save_history(history, filepath=None):
    target_file = filepath or HISTORY_FILE
    os.makedirs(os.path.dirname(os.path.abspath(target_file)), exist_ok=True)
    with open(target_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def get_authenticated_service(channel=None):
    token_file = TOKEN_FILE
    if channel:
        ch_token = os.path.join(BASE_DIR, 'channels', channel, 'token.json')
        if os.path.exists(ch_token):
            token_file = ch_token
            print(f"🔑 Используется токен канала [{channel}]: {token_file}")

    creds = None
    if os.path.exists(token_file):
        try:
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
        except Exception:
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Обновляю токен авторизации...")
            for attempt in range(1, 6):
                try:
                    creds.refresh(Request())
                    break
                except Exception as e:
                    if attempt == 5:
                        raise e
                    print(f"⚠️ Ошибка обновления токена ({e}), повтор {attempt}/5 через {attempt * 3}с...", flush=True)
                    wait_for_internet(timeout=30)
                    time.sleep(attempt * 3)
        else:
            if not os.path.exists(CLIENT_SECRETS_FILE):
                print(f"\n[ОШИБКА] Файл ключей не найден: {CLIENT_SECRETS_FILE}")
                sys.exit(1)
            print("\nОткрываю браузер для однократной авторизации в Google...")
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=8080)
        
        with open(token_file, 'w') as token:
            token.write(creds.to_json())
        print("Авторизация успешна, токен сохранён!\n")

    return build('youtube', 'v3', credentials=creds)

def extract_title_from_video(filepath):
    ocr_bin = os.path.join(BASE_DIR, 'ocr')
    if os.path.exists(ocr_bin):
        try:
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                tmp_path = tmp.name
            cmd_ffmpeg = [
                '/opt/homebrew/bin/ffmpeg', '-y', '-i', filepath,
                '-ss', '00:00:02.5', '-vframes', '1', tmp_path,
                '-loglevel', 'quiet'
            ]
            subprocess.run(cmd_ffmpeg, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
            if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
                res = subprocess.run([ocr_bin, tmp_path], capture_output=True, text=True, timeout=10)
                recognized = res.stdout.strip()
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
                if recognized and len(recognized) >= 3:
                    return recognized
        except Exception:
            pass
    return None

def generate_unique_title(filepath, history):
    filename = os.path.basename(filepath)
    name = os.path.splitext(filename)[0]
    
    recognized = extract_title_from_video(filepath)
    if recognized:
        raw_base = recognized
    else:
        import re
        raw_base = re.sub(r'^\d+[\s._-]+', '', name).strip()
        if not raw_base:
            raw_base = "Залипательное видео"

    matched_key = None
    for key in TITLE_TEMPLATES:
        if key.lower() in raw_base.lower() or raw_base.lower() in key.lower():
            matched_key = key
            break

    base_counts = history.setdefault('base_counts', {})
    used_titles = history.setdefault('used_titles', [])

    if matched_key:
        count = base_counts.get(matched_key, 0) + 1
        base_counts[matched_key] = count
        templates = TITLE_TEMPLATES[matched_key]
        idx = (count - 1) % len(templates)
        candidate = templates[idx].format(n=count)
    else:
        count = base_counts.get(raw_base, 0) + 1
        base_counts[raw_base] = count
        templates = GENERIC_TEMPLATES
        idx = (count - 1) % len(templates)
        candidate = templates[idx].format(base=raw_base, n=count)

    if '#шортс' not in candidate.lower() and '#shorts' not in candidate.lower():
        final_title = f"{candidate} #шортс"
    else:
        final_title = candidate

    final_title = final_title[:100]

    attempt = 1
    while final_title in used_titles:
        final_title = f"{candidate} [{count + attempt}] #шортс"[:100]
        attempt += 1

    used_titles.append(final_title)
    return final_title

def generate_dynamic_metadata(title):
    cta = random.choice(DESCRIPTION_CTAS)
    
    selected_pool = random.sample(TAG_POOL, min(10, len(TAG_POOL)))
    tags = CORE_TAGS + selected_pool
    
    hashtags = " ".join([f"#{t.replace(' ', '')}" for t in CORE_TAGS + selected_pool[:5]])
    
    description = (
        f"{title}\n\n"
        f"{cta}\n\n"
        f"Подпишись, чтобы не пропустить новые залипательные видео! ❤️\n\n"
        f"{hashtags}"
    )
    return description, tags

def upload_video(youtube, filepath, history, dry_run=False, history_file=None):
    filename = os.path.basename(filepath)
    meta_path = os.path.splitext(filepath)[0] + '.json'
    title, description, tags = None, None, None

    # 1. Сначала проверяем кастомный JSON от конвейера, чтобы не засорять history.json
    if os.path.exists(meta_path):
        try:
            with open(meta_path, 'r', encoding='utf-8') as f_meta:
                custom_meta = json.load(f_meta)
                title = custom_meta.get('title')
                description = custom_meta.get('description')
                tags = custom_meta.get('tags')
                print(f"📄 Загружены метаданные из {os.path.basename(meta_path)}")
        except Exception as e:
            print(f"[-] Не удалось прочесть метаданные: {e}")

    # 2. Генерируем шаблонное имя только если нет JSON
    if not title:
        title = generate_unique_title(filepath, history)
    if not description or not tags:
        gen_desc, gen_tags = generate_dynamic_metadata(title)
        description = description or gen_desc
        tags = tags or gen_tags
    
    print(f"\n==========================================")
    print(f"📹 Видео: {filename}")
    print(f"🎯 Название: {title}")
    print(f"💬 Описание:\n{description}")
    print(f"🚀 Режим: СРАЗУ PUBLIC (Мгновенно в ленту Shorts)")
    print(f"==========================================")
    
    if dry_run:
        print("[DRY-RUN] Симуляция завершена, загрузка пропущена.")
        return "dry-run-id"

    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags,
            'categoryId': '24' # Entertainment
        },
        'status': {
            'privacyStatus': 'public',
            'selfDeclaredMadeForKids': False
        }
    }
    
    media = MediaFileUpload(filepath, chunksize=1024*1024*2, resumable=True, mimetype='video/mp4')
    request = youtube.videos().insert(part=','.join(body.keys()), body=body, media_body=media)
    
    response = None
    max_retries = 10
    retries = 0
    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                print(f"Загрузка на YouTube: {progress}%", end='\r', flush=True)
            retries = 0  # Сброс счетчика при успешной передаче чанка
        except (socket.error, http.client.RemoteDisconnected, TimeoutError, ConnectionResetError, ssl.SSLError, HttpError, OSError) as e:
            if isinstance(e, HttpError) and e.resp.status in [400, 401, 403, 404]:
                raise e
            retries += 1
            if retries > max_retries:
                print(f"\n❌ Превышено максимальное число попыток загрузки ({max_retries}): {e}", flush=True)
                raise e
            backoff = min(60, 5 * (2 ** (retries - 1)))
            print(f"\n⚠️ Сбой передачи чанка ({e}). Повтор {retries}/{max_retries} через {backoff}с...", flush=True)
            wait_for_internet(timeout=60)
            time.sleep(backoff)
            
    video_id = response.get('id')
    print(f"\n✅ УСПЕШНО ОПУБЛИКОВАНО!")
    print(f"🔗 Ссылка на видео: https://youtube.com/shorts/{video_id}")
    
    # Update history
    now_iso = datetime.now().isoformat()
    history['last_uploaded_at'] = now_iso
    history.setdefault('uploads', []).append({
        'filename': filename,
        'video_id': video_id,
        'title': title,
        'uploaded_at': now_iso
    })
    save_history(history, filepath=history_file)
    
    # Auto-update desktop dashboard
    try:
        dash_py = os.path.join(BASE_DIR, 'generate_dashboard.py')
        if os.path.exists(dash_py):
            subprocess.run([sys.executable, dash_py], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass
    
    # Move file and accompanying json to uploaded/
    parent_dir = os.path.dirname(filepath)
    dest_dir = os.path.join(os.path.dirname(parent_dir), 'uploaded') if 'channels' in parent_dir else UPLOADED_DIR
    os.makedirs(dest_dir, exist_ok=True)
    
    dest_path = os.path.join(dest_dir, filename)
    shutil.move(filepath, dest_path)
    if os.path.exists(meta_path):
        try:
            shutil.move(meta_path, os.path.join(dest_dir, os.path.basename(meta_path)))
        except Exception:
            pass
    print(f"📦 Файл перемещён в: {dest_dir}")
    
    # Send native macOS notification
    try:
        safe_t = title[:40].replace('\\', ' ').replace('"', "'")
        msg = f"Опубликован ролик: {safe_t}... Пошли просмотры! 🚀"
        subprocess.run([
            'osascript', '-e',
            f'display notification "{msg}" with title "YouTube Shorts — Опубликовано!" sound name "Glass"'
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
    except Exception:
        pass

    return video_id

def main():
    os.makedirs(PENDING_DIR, exist_ok=True)
    os.makedirs(UPLOADED_DIR, exist_ok=True)
    
    dry_run = '--dry-run' in sys.argv
    force = '--force' in sys.argv
    
    # Check if target channel specified or if biribro queue has pending files
    channel_arg = None
    for i, a in enumerate(sys.argv):
        if a == '--channel' and i + 1 < len(sys.argv):
            channel_arg = sys.argv[i + 1]
            
    # Number of videos to upload (default: 1)
    batch_size = 1
    for arg in sys.argv[1:]:
        if arg.isdigit():
            batch_size = int(arg)
    
    biribro_pending = os.path.join(BASE_DIR, 'channels', 'biribro', 'pending')
    
    active_channel = None
    if channel_arg:
        active_channel = channel_arg
        scan_dir = os.path.join(BASE_DIR, 'channels', channel_arg, 'pending')
    else:
        root_files = glob.glob(os.path.join(PENDING_DIR, '*.mp4')) + glob.glob(os.path.join(PENDING_DIR, '*.mov'))
        biri_files = glob.glob(os.path.join(biribro_pending, '*.mp4')) + glob.glob(os.path.join(biribro_pending, '*.mov'))
        if not root_files and biri_files:
            active_channel = 'biribro'
            scan_dir = biribro_pending
            print(f"🎯 Основная очередь пуста, автопереключение на очередь [biribro]: {scan_dir}")
        else:
            active_channel = None
            scan_dir = PENDING_DIR
            print(f"🎯 Выбрана основная очередь (BlwSmex): {scan_dir}")
    
    files = sorted(glob.glob(os.path.join(scan_dir, '*.mp4')) + 
                   glob.glob(os.path.join(scan_dir, '*.mov')))
    
    if not files:
        print(f"В очереди нет новых видео ({scan_dir})")
        return

    history_path = os.path.join(BASE_DIR, 'channels', active_channel, 'history.json') if active_channel else HISTORY_FILE
    history = load_history(history_path)
    
    # Check cooldown if running automatically
    if not force and not dry_run:
        last_str = history.get('last_uploaded_at')
        if last_str:
            try:
                last_dt = datetime.fromisoformat(last_str)
                diff = datetime.now() - last_dt
                min_interval = timedelta(hours=COOLDOWN_HOURS)
                if diff < min_interval:
                    left = min_interval - diff
                    hours_left = round(left.total_seconds() / 3600, 1)
                    print(f"⏳ С момента прошлой публикации прошло {round(diff.total_seconds() / 3600, 1)} ч.")
                    print(f"🛡 Защита от спам-фильтра: следующая публикация через {hours_left} ч.")
                    print("Для ручной мгновенной публикации прямо сейчас используйте: run.sh --force")
                    return
            except Exception:
                pass

        # Human-like natural randomization: wait random 15 to 75 seconds (быстрый старт, пока ноутбук открыт)
        jitter_seconds = random.randint(15, 75)
        print(f"🎲 Имитация живого поведения автора: публикация начнётся через {jitter_seconds} сек...")
        time.sleep(jitter_seconds)

    if not dry_run:
        if not wait_for_internet(timeout=180):
            print("❌ Нет подключения к интернету в течение 3 минут. Пропуск слота.")
            return

    batch = files[:batch_size]
    print(f"📁 Видео в очереди: {len(files)}. Берем для публикации: {len(batch)}")
    
    if dry_run:
        youtube = None
    else:
        youtube = get_authenticated_service(channel=active_channel)
        
    for i, filepath in enumerate(batch, 1):
        try:
            upload_video(youtube, filepath, history, dry_run=dry_run, history_file=history_path)
        except Exception as e:
            print(f"❌ Ошибка при загрузке {filepath}: {e}")
            break
            
    remaining = len(files) - len(batch)
    print(f"\n🎉 Готово! Осталось роликов в очереди: {max(0, remaining)}")

if __name__ == '__main__':
    main()
