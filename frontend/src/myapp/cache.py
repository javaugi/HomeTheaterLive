
import json
from pathlib import Path

CACHE_DIR = Path.home() / ".myhometheater_cache"
CACHE_DIR.mkdir(exist_ok=True)

def save(key, data):
    (CACHE_DIR / key).write_text(json.dumps(data))

def load(key):
    path = CACHE_DIR / key
    return json.loads(path.read_text()) if path.exists() else None
