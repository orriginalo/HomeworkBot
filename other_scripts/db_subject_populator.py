import re
from datetime import datetime
import datetime as dt
from bs4 import BeautifulSoup
import sqlite3 as sql
import json
# Для удачной генерации нужно удалить все лишние расписания кроме нужного (от корня будут >1 <div>, нужно чтобы остался один)
# А также удалить верхнюю строку с "пара/время" (Удалить самый первый )

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

def delete_old(weeknum):
  conn = sql.connect("Database.db")
  cursor = conn.cursor()
  cursor.execute("DELETE FROM schedule WHERE weeknumber = ?", (weeknum,))
  conn.commit()
  conn.close()


def add_subject(timestamp:int, subject:str, weeknum:int):
  conn = sql.connect("Database.db")
  cursor = conn.cursor()
  cursor.execute("INSERT INTO schedule (timestamp, subject, weeknumber) VALUES (?, ?, ?)", (timestamp, subject, weeknum))
  conn.commit()
  conn.close()

def check_exists_subject(subject:str, timestamp:int):
  conn = sql.connect("Database.db")
  cursor = conn.cursor()
  cursor.execute("SELECT id FROM schedule WHERE subject = ? AND timestamp = ?", (subject, timestamp))
  result = cursor.fetchone()
  conn.close()
  return True if result else False

def get_iterable_text(soup_find_text):
  return [text.strip() for text in soup_find_text.splitlines() if text.strip()]

def populate_schedule():
  timetable_json = json.load(open("./data/timetables/timetables.json", "r", encoding="utf-8"))

# Проход по JSON
  for week, days in timetable_json.items():
    delete_old(week)
    for timestamp, lessons in days.items():
      for pair_number, subject in lessons.items():
        if subject != "-" and check_exists_subject(subject, int(timestamp)) == False:
          add_subject(int(timestamp), subject, int(week))


# populate_schedule()
# populate_schedule("schedule-12.html")