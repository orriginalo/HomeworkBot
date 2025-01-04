import re
from datetime import datetime
import datetime as dt
from bs4 import BeautifulSoup
import sqlite3 as sql
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


def add_subject(timestamp, subject, weeknum):
  conn = sql.connect("Database.db")
  cursor = conn.cursor()
  cursor.execute("INSERT INTO schedule (timestamp, subject, weeknumber) VALUES (?, ?, ?)", (timestamp, subject, weeknum))
  conn.commit()
  conn.close()

def get_iterable_text(soup_find_text):
  return [text.strip() for text in soup_find_text.splitlines() if text.strip()]

def populate_schedule(file_name:str):
  with open(file_name, encoding="utf-8") as f:
    html = f.read()

  soup = BeautifulSoup(html, "lxml")

  edu_week_number = int(re.search(r"(\d+)", soup.find('div', class_="week-num").text).group().strip())

  delete_old(edu_week_number)
  rows = soup.find_all("div", class_="row")

  i = 0

  global_week_number = dt.datetime.fromtimestamp(get_monday_timestamp(35)) + dt.timedelta(weeks=edu_week_number)
  timestamp = datetime.datetime.timestamp(global_week_number)

# global_week_number = get_weeknumber(SUPERWEEKNUMBER + dt.timedelta(weeks=current_edu_week_number))
#   timestamp = get_monday_timestamp(global_week_number)
  print(f"Week number: {global_week_number}")

  for row in rows: # Для каждой строки в строках


    date = 0
    cells = list(row.children)
    classes = []
    weekday = row.find("div", class_="table-header-col").text.strip()
    for cell in cells:
      cell_iterable_text = get_iterable_text(cell.text)

      if cell.name == "div" and cell.has_attr("class") and cell["class"][0] == "table-col table-desktop-col":
        classes.append("-")

      elif len(cell_iterable_text) > 2:
        print(cell_iterable_text)
        if "пр." in cell_iterable_text[2]:
          subject = cell_iterable_text[2].replace("пр.", "")
          if subject not in classes:
            # Обозначения предметов (также изменить в app.variables.py)
            if subject == "Основы безопасности и защиты Родины":
              subject = "ОБЗР"
            classes.append(subject)
            add_subject(timestamp, subject, edu_week_number)
            print(f"{datetime.datetime.fromtimestamp(timestamp)} {subject}")
    timestamp += 86400
    

# populate_schedule("schedule-12.html")