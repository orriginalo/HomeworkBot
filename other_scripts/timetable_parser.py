from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import json
import os

START_STUDY_WEEK_NUM = 34 # Неделя с которой началась учеба в 2024 году

short_subjects = {
    "основы безопасности и защиты родины": "ОБЗР",
    # "физическая культура": "Физ-ра",
}


def calculate_timestamp(week1, week2, year, day):

    # Вычисляем дату начала первой недели года
    first_week_start = datetime(year, 1, 1) + timedelta(weeks=week1 - 1)
    
    # Вычисляем целевую дату, добавляя вторую неделю как timedelta
    target_date = first_week_start + timedelta(weeks=week2)
    
    # Устанавливаем день месяца
    target_date = target_date.replace(day=day)
    
    # Возвращаем timestamp
    return target_date.timestamp()

def get_iterable_text(soup_find_text):
  return [text.strip() for text in soup_find_text.splitlines() if text.strip()] if len(soup_find_text) > 2 else []

def parse_timetable(html_file: str, json_file: str = None):

    timetable = {}
    if json_file is not None:
        if not os.path.exists(json_file):
            with open(json_file, "w", encoding="utf-8") as file:
                file.write("{}")
        timetable = json.load(open(json_file, "r", encoding="utf-8")) # Загружаем расписание из json файла

    def clean_text(text):
        """Очистка текста от лишних символов."""
        return " ".join(text.split()).strip()

    with open(html_file, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "html.parser")

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
            day_name = int(calculate_timestamp(START_STUDY_WEEK_NUM, int(week_num), 2024, int(day_num)))
            timetable[week_num][day_name] = {}
            

            # Колонки пар
            pair_cols = day_row.find_all("div", class_="table-col")
            for pair_index, pair_col in enumerate(pair_cols, start=1):
                pair_label = f"{pair_index}"
                cell_text_it: list = get_iterable_text(pair_col.text)

                subject = "-"
                if len(cell_text_it) >= 3:
                    subject = cell_text_it[2]


                # Заменяем длинные названия на более короткие
                pr_in = False
                if "пр." in subject:
                    pr_in = True
                subject = short_subjects.get(subject.replace("пр.", "").lower(), subject)
                # if pr_in and "пр." not in subject:
                #     subject = f"пр.{subject}"
                subject = subject.replace("пр.", "") 

                timetable[week_num][day_name][pair_label] = subject
    
    if json_file is not None:
        with open(json_file, "w", encoding="utf-8") as file:
            json.dump(timetable, file, ensure_ascii=False, indent=4)
        print(f"Расписание сохранено в {json_file}")

    return timetable