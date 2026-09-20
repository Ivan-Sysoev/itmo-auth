#!/usr/bin/env python
import json
from datetime import date, datetime, time
from typing import Dict, List, Tuple

import requests

from constants import (
    BASE_HEADERS,
    SCHEDULE_CACHE_PATH,
    SCHEDULE_EXPIRE_PERIOD,
    SCHEDULE_URL,
    TODAY,
    TOMORROW,
    CacheState,
)

from itmo_auth import ItmoAuth

auth = ItmoAuth()

def get_cached_response(target_date: date) -> Tuple[ Dict | None, CacheState | None ]:
    if not SCHEDULE_CACHE_PATH.exists():
        return (None, CacheState.EXPIRED)

    with open(SCHEDULE_CACHE_PATH, 'r', encoding='utf-8') as ifile:
        json_data = json.load(ifile)
        cache_last_update_time = datetime.fromisoformat(json_data.get("cache_last_update_time"))
        cache_target_date      = datetime.fromisoformat(json_data.get("cache_target_date")).date()
        cache_expire_time      = cache_last_update_time + SCHEDULE_EXPIRE_PERIOD

        if (datetime.now() >= cache_expire_time or target_date > cache_target_date):
            return (None, CacheState.EXPIRED)

        if (target_date != cache_target_date):
            return (None, CacheState.DIFFERENT_DATE)

        return (json_data, None)

def write_schedule_cache(json_data: Dict | None, target_date: date) -> None:
    if not json_data:
        return

    cache_last_update_time              = datetime.now()
    json_data["cache_last_update_time"] = cache_last_update_time.isoformat()
    json_data["cache_target_date"]      = target_date.isoformat()

    with open(SCHEDULE_CACHE_PATH, 'w', encoding='utf-8') as ofile:
        json.dump(json_data, ofile, ensure_ascii=False, indent=4)
    
def make_request(target_date: date) -> Dict:
    headers = {
        **BASE_HEADERS,
        "authorization": f"Bearer {auth.get_access_token()}",
    }

    str_date = target_date.strftime("%Y-%m-%d")

    params = {
        "date_start": str_date,
        "date_end": str_date,
    }

    try:
        json_response = requests.get(SCHEDULE_URL, params=params, headers=headers, timeout=10)
    except requests.RequestException as e:
        raise RuntimeError(f"Network Error: {e}")

    return json_response.json()

def get_lessons(data) -> List[Dict]:
    res = []
    lessons = data.get("data", [])[0].get("lessons", [])
    if not lessons:
        return []

    for lesson in lessons:
        res.append({
            "name": lesson.get("subject"),
            "start_time": time.fromisoformat(lesson.get("time_start")),
            "end_time": time.fromisoformat(lesson.get("time_end")),
            "room": lesson.get("room"),
        })

    return res

def format_lesson(lesson: dict | None, today: bool) -> str:
    if not lesson:
        return "There is no next lesson"

    name = lesson["name"]
    room = lesson["room"]
    start_time = lesson["start_time"].strftime("%H:%M")

    return ("[Завтра]" if not today else "") + f"[ {name} ] {start_time} " + (f"(ауд. {room})" if room else "(Online)")

def find_next_lesson(lessons: List[Dict], today: bool) -> dict | None:
    if not lessons:
        return None
    
    if today:
        cur_time = datetime.now().time()
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
            response = make_request(target_date)

        lessons = get_lessons(response)
        next_lesson = find_next_lesson(lessons, target_date == TODAY)

        if next_lesson:
            if cache_state == CacheState.EXPIRED:
                write_schedule_cache(response, target_date)
            return format_lesson(next_lesson, target_date == TODAY)

    return "There is no next lesson"

def main():
    # response, cache_state = get_cached_response(TODAY)
    # print(cache_state)
    print(get_next_lesson())

if __name__ == "__main__":
    main()
