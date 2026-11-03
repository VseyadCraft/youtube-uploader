#!/usr/bin/env python3
import os
import re
import json
import urllib.request
import subprocess

BASE_DIR = os.path.expanduser('~/youtube-uploader')
HISTORY_FILE = os.path.join(BASE_DIR, 'history.json')
DASHBOARD_SCRIPT = os.path.join(BASE_DIR, 'generate_dashboard.py')

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
# Optional local proxy if running, otherwise direct
proxy_url = os.environ.get('HTTP_PROXY') or os.environ.get('HTTPS_PROXY')
if proxy_url:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({'http': proxy_url, 'https': proxy_url}))
else:
    opener = urllib.request.build_opener()

def update_views():
    if not os.path.exists(HISTORY_FILE):
        print("Файл истории не найден")
        return
        
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    uploads = data.get('uploads', [])
    print(f"Обновляю просмотры для {len(uploads)} видео...")
    
    updated_count = 0
    for item in uploads:
        vid = item.get('video_id')
        if not vid:
            continue
        url = f'https://www.youtube.com/shorts/{vid}'
        try:
            req = urllib.request.Request(url, headers=headers)
            html = opener.open(req, timeout=4).read().decode('utf-8', errors='ignore')
            views_match = re.search(r'\"viewCount\":\s*\"(\d+)\"', html)
            if views_match:
                views = int(views_match.group(1))
                item['views'] = views
                updated_count += 1
                print(f"✓ {vid}: {views} просмотров")
        except Exception:
            pass
            
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    print(f"Готово! Обновлено записей: {updated_count}")
    
    # Refresh dashboard
    if os.path.exists(DASHBOARD_SCRIPT):
        subprocess.run(['python3', DASHBOARD_SCRIPT], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("Дашборд на рабочем столе обновлён!")

if __name__ == '__main__':
    update_views()
