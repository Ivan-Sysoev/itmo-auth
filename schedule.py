#!/usr/bin/env python
import json
from datetime import date, datetime, time

import requests

from constants import (
    ABBREVIATIONS,
    BASE_HEADERS,
    LOCAL_TIMEZONE,
    SCHEDULE_CACHE_PATH,
    SCHEDULE_EXPIRE_PERIOD,
    SCHEDULE_URL,
    TODAY,
    TOMORROW,
    CacheState,
    Messages,
)
from itmo_auth import ItmoAuth

auth = ItmoAuth()

def get_cached_response(target_date: date) -> tuple[ dict | None, CacheState | None ]:
    if not SCHEDULE_CACHE_PATH.exists():
        return (None, CacheState.EXPIRED)

    with open(SCHEDULE_CACHE_PATH, 'r', encoding='utf-8') as ifile:
        try:
            json_data = json.load(ifile)
        except json.decoder.JSONDecodeError:
            return (None, CacheState.EXPIRED) 

        cache_created_at = datetime.fromisoformat(json_data.get("cache_created_at"))
        cache_target_date = datetime.fromisoformat(json_data.get("cache_target_date")).date()
        cache_expire_time = cache_created_at + SCHEDULE_EXPIRE_PERIOD

        if (datetime.now(tz=LOCAL_TIMEZONE) >= cache_expire_time or target_date > cache_target_date):
            return (None, CacheState.EXPIRED)

        if (target_date != cache_target_date):
            return (None, CacheState.DIFFERENT_DATE)

        return (json_data, None)

def write_schedule_cache(json_data: dict | None, target_date: date) -> None:
    if not json_data:
        json_data = {
            "code": 0,
            "data": [],
            "message": None,
        }

    cache_created_at = datetime.now(tz=LOCAL_TIMEZONE)
    json_data["cache_created_at"] = cache_created_at.isoformat()
    json_data["cache_target_date"] = target_date.isoformat()

    with open(SCHEDULE_CACHE_PATH, 'w', encoding='utf-8') as ofile:
        json.dump(json_data, ofile, ensure_ascii=False, indent=4)
    
def make_request(target_date: date) -> dict:
    headers = {
        **BASE_HEADERS,
        "authorization": f"Bearer {auth.get_access_token()}",
    }

    str_date = target_date.strftime("%Y-%m-%d")

    params = {
        "date_start": str_date,
        "date_end": str_date,
    }

    json_response = requests.get(SCHEDULE_URL, params=params, headers=headers, timeout=10)

    return json_response.json()

def get_lessons(data) -> list[dict]:
    data = data.get("data", [])
    if len(data) == 0:
        return []

    lessons = data[0].get("lessons", [])

    if not lessons:
        return []

    return [
        {
            "name": lesson.get("subject"),
            "start_time": time.fromisoformat(lesson.get("time_start")),
            "end_time": time.fromisoformat(lesson.get("time_end")),
            "room": lesson.get("room")
        }
        for lesson in lessons
    ]

def use_abbreviation(name: str):
    return ABBREVIATIONS.get(name, name)

def format_lesson(lesson: dict | None, today: bool) -> str:
    if not lesson:
        return "Сегодня и завтра не пар"

    name = lesson["name"]
    room = lesson["room"]
    start_time = lesson["start_time"].strftime("%H:%M")

    name = use_abbreviation(name)
    return ("[Завтра]" if not today else "") + f"[ {name} ] {start_time} " + (f"(ауд. {room})" if room else "(Online)")

def find_next_lesson(lessons: list[dict], today: bool) -> dict | None:
    if not lessons:
        return None
    
    if today:
        cur_time = datetime.now(tz=LOCAL_TIMEZONE).time()
        for lesson in lessons:
            if cur_time <= lesson["start_time"]:
                return lesson
        return None

    # Taking first tomorrow lesson
    return lessons[0]

def get_next_lesson() -> str:
    for target_date in (TODAY, TOMORROW):
        response, cache_state = get_cached_response(target_date)

        if cache_state == CacheState.DIFFERENT_DATE:
            continue

        if cache_state == CacheState.EXPIRED:
            try:
                response = make_request(target_date)
            except requests.RequestException:
                return Messages.NETWORK_ERROR

        lessons = get_lessons(response)
        next_lesson = find_next_lesson(lessons, target_date == TODAY)

        if next_lesson:
            if cache_state == CacheState.EXPIRED:
                write_schedule_cache(response, target_date)
            return format_lesson(next_lesson, target_date == TODAY)

    write_schedule_cache(None, target_date)
    return Messages.NO_LESSONS_MSG

def main():
    print(get_next_lesson())

if __name__ == "__main__":
    main()
