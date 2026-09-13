#!/usr/bin/env python
"""
Пример кода, который использует ItmoAuth() для получение расписания на сегодня.
"""

import json
import requests
from datetime import date

from itmo_auth import ItmoAuth

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

SCHEDULE_URL = "https://my.itmo.ru/api/schedule/schedule/personal"

auth = ItmoAuth()

def make_request(date_start: str, date_end: str):
    headers = {**BASE_HEADERS, "authorization": f"Bearer {auth.get_access_token()}"}
    params = {"date_start": date_start, "date_end": date_end}
    try:
        response = requests.get(SCHEDULE_URL, params=params, headers=headers, timeout=10)
    except requests.RequestException as e:
        raise RuntimeError(f"Network Error: {e}")
    return response

def main():
    today = date.today()
    target_date = today.strftime("%Y-%m-%d")

    try:
        response = make_request(target_date, target_date)
        print(json.dumps(response.json(), indent=4))
    except Exception as e:
        print(e)

if __name__ == "__main__":
    main()
