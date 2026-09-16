from datetime import timedelta
from pathlib import Path

# itmo_auth
TOKEN_URL         = "https://id.itmo.ru/auth/realms/itmo/protocol/openid-connect/token"
CLIENT_ID         = "student-personal-cabinet"
PROJECT_DIR       = Path(__file__).resolve().parent
TOKEN_FILE        = PROJECT_DIR / ".itmo_tokens.json"
SAFETY_MARGIN_SEC = 30  # обновляем чуть раньше формального истечения

# schedule
BASE_HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "ru",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "referer": "https://my.itmo.ru/",
    "user-agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36"
    ),
}

SCHEDULE_URL           = "https://my.itmo.ru/api/schedule/schedule/personal"
SCHEDULE_EXPIRE_PERIOD = timedelta(hours=3)
SCHEDULE_CACHE_PATH    = PROJECT_DIR / "schedule_cache.json"
