#!/bin/bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# caffeinate -i -s prevents system from sleeping while uploading
exec /usr/bin/caffeinate -i -s "$DIR/venv/bin/python3" -u "$DIR/upload_shorts.py" "$@"

