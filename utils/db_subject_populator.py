import re
from datetime import datetime
import datetime as dt
from bs4 import BeautifulSoup
import sqlite3 as sql
import json
from app.database.queries.group import get_group_by_name
from app.database.queries.schedule import add_subject, del_schedule_by_week, check_exists_subject

# 34 + СУПЕРЧИСЛО

day = datetime.now().day
month = datetime.now().month
year = datetime.now().year

import datetime

def get_monday_timestamp(week_number, year=2024):
    # Находим первую дату года
    first_day_of_year = dt.datetime(year, 1, 1)
    # Находим первый понедельник года
    first_monday = first_day_of_year + dt.timedelta(days=(7 - first_day_of_year.weekday()) % 7)
    # Вычисляем дату понедельника нужной недели
    monday_of_week = first_monday + dt.timedelta(weeks=week_number - 1)
    # Возвращаем timestamp понедельника
    return int(monday_of_week.timestamp())

def get_iterable_text(soup_find_text):
  return [text.strip() for text in soup_find_text.splitlines() if text.strip()]

async def populate_schedule():
  timetable_json = json.load(open("./data/timetables/timetables.json", "r", encoding="utf-8"))

# Проход по JSON
  # for week, days in timetable_json.items():
  #   await del_schedule_by_week(int(week))
  #   for timestamp, lessons in days.items():
  #     for pair_number, subject in lessons.items():
  #       if subject != "-" and await check_exists_subject(subject, int(timestamp)) == False:
  #         await add_subject(int(timestamp), subject, int(week))
  for group, weeks in timetable_json.items():
    print(group)
    group = await get_group_by_name(group)
    for week, days in weeks.items():
      await del_schedule_by_week(int(week), group.uid)
      for timestamp, lessons in days.items():
        for pair_number, subject in lessons.items():
          if subject != "-" and await check_exists_subject(subject, int(timestamp), group.uid) == False:
            await add_subject(int(timestamp), subject, int(week), group.uid)