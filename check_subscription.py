#!/usr/bin/env python3
"""Сторож: сообщает, когда ссылку подписки пора менять.

В подписке на iPhone зашита верхняя граница SUBSCRIPTION_FINISH. Как только
портал начинает отдавать занятия за ней (появился новый семестр), календарь
на телефоне тихо обрывается — про это и предупреждаем.
"""
import re
import subprocess
import sys

SUBSCRIPTION_FINISH = "20270301"          # что стоит в ссылке подписки
TITLE = "Пора обновить ссылку подписки на расписание"

ics = open("schedule.ics", encoding="utf-8").read()
dates = sorted(m[:8] for m in re.findall(r"DTSTART:(\d{8})", ics))
if not dates:
    sys.exit("в schedule.ics нет событий")

last = dates[-1]
print(f"последнее занятие: {last}, граница подписки: {SUBSCRIPTION_FINISH}")
if last <= SUBSCRIPTION_FINISH:
    print("менять ссылку пока не нужно")
    sys.exit(0)

existing = subprocess.run(
    ["gh", "issue", "list", "--state", "open", "--search", TITLE, "--json", "title"],
    capture_output=True, text=True,
).stdout
if TITLE in existing:
    print("issue уже открыт")
    sys.exit(0)

body = f"""Портал начал отдавать занятия после {SUBSCRIPTION_FINISH[:4]}-{SUBSCRIPTION_FINISH[4:6]}-{SUBSCRIPTION_FINISH[6:]},
а в подписке на iPhone стоит эта дата как верхняя граница. Всё, что позже,
в календарь не попадёт.

Последнее занятие в ленте: {last[:4]}-{last[4:6]}-{last[6:]}

Что сделать: в подписке заменить ссылку на

    https://portal.unn.ru/ruzapi/schedule/group/52664.ics?finish=<новая дата>

Предел портала можно спросить у него самого — он называет его в тексте
ошибки 422, если запросить заведомо далёкую дату. И не забыть обновить
SUBSCRIPTION_FINISH в этом файле.
"""
subprocess.run(["gh", "issue", "create", "--title", TITLE, "--body", body], check=True)
print("issue создан")
