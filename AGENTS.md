# YouTube Shorts Uploader (`~/youtube-uploader`)

Автономный загрузчик YouTube Shorts: YouTube Data API v3 (resumable upload чанками по 2 МБ), локальный Swift OCR (`Apple Vision`), антиспам-интервалы (минимум 2.5 ч) и локальный HTML-дашборд.

## Ключевые файлы и папки
- `upload_shorts.py` — основной загрузчик, роутинг очередей и ретраи.
- `run.sh` — точка входа планировщика (`./run.sh --force` для внеочередной публикации).
- `auth_biribro.py`, `generate_dashboard.py`, `refresh_views.py` — OAuth канала `biribro`, генерация дашборда, обновление просмотров.
- `ocr.swift` / бинарник `ocr` — нативный Vision OCR для извлечения хуков из кадров.
- `channels/` (`BlwSmex`, `biribro`), `pending/`, `uploaded/`, `for_reupload/`, `logs/`.

## Проверка и расписание
- Перед живыми прогонами проверять через: `./venv/bin/python3 upload_shorts.py --dry-run`
- LaunchAgent `~/Library/LaunchAgents/com.tim.shorts-uploader.plist` запускает `run.sh` ежедневно в `11:00`, `14:30`, `18:00`, `21:30`.
- Диагностика: `tail -n 50 logs/scheduler.log logs/scheduler_err.log` и `launchctl print gui/$(id -u)/com.tim.shorts-uploader`.

## Безопасность и Git
- **НИКОГДА** не выводить в логи/чат и не коммитить: `client_secrets.json`, `token.json`, `channels/**/token.json`, `.env`, `history.json`, `schedule_state.json`, бинарник `ocr`, а также `pending/`, `uploaded/`, `for_reupload/`, `logs/`, `venv/`.
