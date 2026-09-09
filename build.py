#!/usr/bin/env python3
"""Тянет расписание группы с портала ННГУ и кладёт рядом как schedule.ics."""
import datetime as dt
import json
import re
import sys
import urllib.request

GROUP_ID = "52664"
CAL_NAME = "Расписание 4523С1СТ3"
BASE = f"https://portal.unn.ru/ruzapi/schedule/group/{GROUP_ID}.ics"
OUT = "schedule.ics"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "unn-rasp-mirror/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def max_finish(start):
    """Портал сам называет свой предел в тексте ошибки 422 — спрашиваем его."""
    code, body = get(f"{BASE}?start={start}&finish=2099.01.01")
    if code == 200:
        return "2099.01.01"
    msg = json.loads(body).get("message", "")
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", msg)
    if not m:
        sys.exit(f"не удалось определить предел finish: {code} {msg!r}")
    return "{}.{}.{}".format(*m.groups())


def brand(ics):
    """Даём календарю имя и часовой пояс: времена в ленте без TZ."""
    extra = (
        f"X-WR-CALNAME:{CAL_NAME}\r\n"
        "X-WR-TIMEZONE:Europe/Moscow\r\n"
    ).encode()
    return ics.replace(b"VERSION:2.0\r\n", b"VERSION:2.0\r\n" + extra, 1)


def main():
    today = dt.date.today()
    start = (today - dt.timedelta(days=7)).strftime("%Y.%m.%d")
    finish = max_finish(start)

    code, body = get(f"{BASE}?start={start}&finish={finish}")
    if code != 200:
        sys.exit(f"портал ответил {code}: {body[:200]!r}")
    if not body.startswith(b"BEGIN:VCALENDAR"):
        sys.exit(f"это не календарь: {body[:200]!r}")

    body = brand(body)
    events = body.count(b"BEGIN:VEVENT")
    if events == 0:
        sys.exit("календарь пустой — не перезаписываю")

    with open(OUT, "wb") as f:
        f.write(body)
    print(f"{OUT}: {events} занятий, {start} — {finish}, {len(body)} байт")


if __name__ == "__main__":
    main()
