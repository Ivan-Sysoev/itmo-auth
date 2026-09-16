#!/usr/bin/env python
from constants import (
    BASE_HEADERS,
    SCHEDULE_URL,
    SCHEDULE_EXPIRE_PERIOD,
    SCHEDULE_CACHE_PATH
)

from datetime import (
    date,
    time,
    datetime,
    timedelta
)

import json
import requests

from itmo_auth import (
    ItmoAuth,
)

auth = ItmoAuth()

def get_cached_response():
    if not SCHEDULE_CACHE_PATH.exists():
        return None

    with open(SCHEDULE_CACHE_PATH, 'r', encoding='utf-8') as ifile:
        json_data = json.load(ifile)
        cache_expire_time = datetime.fromisoformat(json_data.get("cache_expire_time"))
        
        if (datetime.now() >= cache_expire_time):
            return None
        
        return json_data

def write_schedule_cache(json_data):
    cache_expire_time = datetime.now() + SCHEDULE_EXPIRE_PERIOD
    json_data["cache_expire_time"] = cache_expire_time.isoformat()
    with open(SCHEDULE_CACHE_PATH, 'w', encoding='utf-8') as ofile:
        json.dump(json_data, ofile, ensure_ascii=False, indent=4)
    
def make_request(date_start: str, date_end: str):
    print("Making requests")
    headers = {
        **BASE_HEADERS,
        "authorization": f"Bearer {auth.get_access_token()}",
    }

    params = {
        "date_start": date_start,
        "date_end": date_end,
    }

    try:
        json_response = requests.get(SCHEDULE_URL, params=params, headers=headers, timeout=10)
    except requests.RequestException as e:
        raise RuntimeError(f"Network Error: {e}")

    return json_response.json()

def get_schedule(date_start: str, date_end: str):
    json_response = get_cached_response()
    if not json_response:
        json_response = make_request(date_start, date_end)
        write_schedule_cache(json_response)
    return json_response

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

def get_next_lesson(date) -> dict | None:
    target_date   = date.strftime("%Y-%m-%d")
    json_response = get_schedule(target_date, target_date)
    lessons       = get_lessons(json_response)

    if not lessons:
        return None
    
    if date == date.today():
        return get_next_today_lesson(lessons)

    # Taking first tomorrow lesson
    return lessons[0]

def main():
    today    = date.today()
    tomorrow = date.today() + timedelta(days=1)

    # Trying for today
    lesson_output = get_next_lesson(today)
    
    # Trying for tomorrow
    if not lesson_output:
        lesson_output = get_next_lesson(tomorrow)

    print(format_lesson(lesson_output))

if __name__ == "__main__":
    main()
