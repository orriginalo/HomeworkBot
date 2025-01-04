from bs4 import BeautifulSoup
from rich import print
import re
from datetime import datetime, timedelta
import json

SUPERMONTHNUMBER = 34

from datetime import datetime, timedelta


def calculate_timestamp(week1, week2, year, day):
    # Вычисляем дату начала первой недели года
    first_week_start = datetime(year, 1, 1) + timedelta(weeks=week1 - 1)
    
    # Вычисляем целевую дату, добавляя вторую неделю как timedelta
    target_date = first_week_start + timedelta(weeks=week2)
    
    # Устанавливаем день месяца
    target_date = target_date.replace(day=day)
    
    # Возвращаем timestamp
    return target_date.timestamp()


def parse_timetable(html_file, json_file):
    current_timetables = json.load(open(json_file, "r", encoding="utf-8"))

    def clean_text(text):
        """Очистка текста от лишних символов."""
        return " ".join(text.split()).strip()

    with open(html_file, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "html.parser")

    timetable = current_timetables
    # Ищем все недели
    week_sections = soup.find_all("div", class_="week-num")
    
    for week_section in week_sections:
        re_week_name = re.findall(r'\d+', clean_text(week_section.text))
        week_num = re_week_name[0]
        timetable[week_num] = {}
        
        # Секция соответствующих дней недели
        week_container = week_section.find_next("div", class_="container")
        day_rows = week_container.find_all("div", class_="row")
        
        day_rows.pop(0)

        for day_row in day_rows:
            day_col = day_row.find("div", class_="table-header-col")
            if not day_col:
                continue  # Пропуск строки, если это не день
            
            day_num = re.findall(r'\d+', clean_text(day_col.text))
            day_num = day_num[0]
            # day_name = datetime.fromtimestamp(calculate_timestamp(SUPERMONTHNUMBER, int(week_name), 2024, int(day_num))).strftime("%d/%m/%Y, %H:%M:%S")
            day_name = int(calculate_timestamp(SUPERMONTHNUMBER, int(week_num), 2024, int(day_num)))
            timetable[week_num][day_name] = {}
            

            # Колонки пар
            pair_cols = day_row.find_all("div", class_="table-col")
            for pair_index, pair_col in enumerate(pair_cols, start=1):
                pair_label = f"{pair_index}"
                
                # Получение информации о предмете
                subject_parts = pair_col.find_all(text=True)
                cleaned_subject = (clean_text(" ".join(subject_parts)) or "-").split(" ")
                if len(cleaned_subject) >= 5:
                  subject = cleaned_subject[4]
                  if ".Основы" in subject:
                      subject = subject.replace(".Основы", ".ОБЗР")
                  if ".Физическая" in subject:
                      subject = subject.replace(".Физическая", ".Физ-ра")
                  if "пр." in subject:
                      subject = subject.replace("пр.", "")
                  timetable[week_num][day_name][pair_label] = subject
                else:
                  timetable[week_num][day_name][pair_label] = "-"
    
    print(timetable)
    with open("./data/timetables/timetables.json", "w", encoding="utf-8") as file:
        json.dump(timetable, file, ensure_ascii=False, indent=4)
    return timetable