#!/usr/bin/env python
from constants import (
    BASE_HEADERS,
    SCHEDULE_URL,
    SCHEDULE_EXPIRE_PERIOD,
    SCHEDULE_CACHE_PATH,
    TODAY,
    TOMORROW
)

from datetime import (
    time,
    datetime,
    date
)

import json
import requests

from itmo_auth import (
    ItmoAuth,
)

auth = ItmoAuth()

def get_cached_response(target_date: date):
    if not SCHEDULE_CACHE_PATH.exists():
        return None

    with open(SCHEDULE_CACHE_PATH, 'r', encoding='utf-8') as ifile:
        json_data = json.load(ifile)
        cache_last_update_time = datetime.fromisoformat(json_data.get("cache_last_update_time"))
        cache_expire_time = cache_last_update_time + SCHEDULE_EXPIRE_PERIOD

        if (target_date != cache_last_update_time.date() or datetime.now() >= cache_expire_time):
            return None
        
        return json_data

def write_schedule_cache(json_data):
    cache_last_update_time = datetime.now()
    json_data["cache_last_update_time"] = cache_last_update_time.isoformat()
    with open(SCHEDULE_CACHE_PATH, 'w', encoding='utf-8') as ofile:
        json.dump(json_data, ofile, ensure_ascii=False, indent=4)
    
def make_request(target_date: date):
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

def get_lessons(data):
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

def get_next_today_lesson(lessons):
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

    return f"[ {name} ] {start_time} " + (f"(ауд. {room})" if room else "(Online)")

def get_next_lesson(lessons, today: bool) -> dict | None:
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

def get_schedule():
    for target_date in (TODAY, TOMORROW):
        update_cache = False
        response = get_cached_response(target_date)
        if not response:
            update_cache = True
            response = make_request(target_date)

        lessons = get_lessons(response)
        next_lesson = get_next_lesson(lessons, target_date == TODAY)

        if next_lesson:
            if update_cache:
                write_schedule_cache(response)
            return next_lesson

    return None

def main():
    lesson_output = get_schedule()
    print(format_lesson(lesson_output))

if __name__ == "__main__":
    main()
