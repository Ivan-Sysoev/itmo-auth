#!/usr/bin/env python
from datetime import date, time, datetime

import requests

from itmo_auth import ItmoAuth
from dracula_colors import *

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

def get_lessons(data):
    res = []
    lessons = data.get("data", [])[0].get("lessons", [])
    if not lessons:
        raise RuntimeError("Cannot parse lessons")

    for lesson in lessons:
        res.append({
            "name": lesson.get("subject"),
            "start_time": time.fromisoformat(lesson.get("time_start")),
            "end_time": time.fromisoformat(lesson.get("time_end")),
            "room": lesson.get("room"),
        })

    return res

def get_next_lesson(lessons):
    cur_time = datetime.now().time()
    for lesson in lessons:
        if cur_time <= lesson["start_time"]:
            return lesson
    return None

def format_lesson(lesson: dict | None) -> str:
    if not lesson:
        return "There is no next lesson"

    name = lesson["name"]
    room = lesson["room"]
    start_time = lesson["start_time"].strftime("%H:%M")

    return (
        f"[ {name} ]"
        f" {start_time}"
        f" (ауд. {room})"
    )

def main():
    today = date.today().strftime("%Y-%m-%d")

    try:
        response = make_request(today, today)
        lessons = get_lessons(response.json())
    except Exception as e:
        print(e)
        return

    next_lesson = get_next_lesson(lessons)
    print(format_lesson(next_lesson))

if __name__ == "__main__":
    main()
