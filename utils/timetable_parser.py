from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import json
import os
from variables import prefixes_map, subjects_map
START_STUDY_WEEK_NUM = 34 # Неделя с которой началась учеба в 2024 году

ADDED_WEEKS = 20 # В переходе на 2 семестр 2024/2025 срезали 20 недель (теперь над расписанием пишется неделя начиная с 1)

remove_all_before_dot = False

replace_subject_to_short = True

short_subjects = {
    "основы безопасности и защиты родины": "ОБЗР",
}

# Вы можете задать значение ключа на "" чтобы префикс был удален
# prefix_map = {
#     "пр.": "",
#     "лек.": "",
#     "лаб.": "лаб."
# }

def process_subject_name(subject: str, subjects_map: dict, prefixes_map: dict = None) -> str:
    """
    Обрабатывает название предмета, заменяя префиксы и длинные названия.
    
    :param subject: Название предмета из расписания.
    :param subjects_map: Словарь с заменами названий предметов.
    :param prefixes_map: Словарь с заменами префиксов.
    :return: Обработанное название.
    """
    
    if subject.startswith("Лаб.Информатика"):
        subject = subject.replace("Лаб.Информатика", "Информатика")
        
    # Разделяем префикс и основной текст
    if '.' in subject:
        prefix, main_subject = subject.split('.', 1)
        prefix += '.'  # Восстанавливаем точку
    else:
        prefix, main_subject = '', subject

    # Заменяем префикс, если флаг включен
    if prefixes_map is not None:
        prefix = prefixes_map.get(prefix, prefix)
    
    if subjects_map is not None:
        main_subject = subjects_map.get(main_subject.strip().lower(), main_subject)
        
    # Соединяем обработанный префикс и основной текст
    if len(list(prefix)) > 0:
        if list(prefix)[-1] == ".":
            return f"{prefix}{main_subject}".strip()
    return f"{prefix} {main_subject}".strip()

def get_monday_timestamp(week_number: int, year: int) -> int:
    """
    Возвращает округленный timestamp понедельника указанной недели, учитывая переход на следующий год.

    :param week_number: Номер недели (1 и выше).
    :param year: Год, с которого начинается расчет.
    :return: Округленный до целого timestamp понедельника.
    """
    # Определяем первый день года
    first_day_of_year = datetime(year, 1, 1)
    
    # Определяем смещение до первого понедельника года
    days_to_monday = (7 - first_day_of_year.weekday()) % 7
    first_monday = first_day_of_year + timedelta(days=days_to_monday)
    
    # Вычисляем целевой понедельник
    target_monday = first_monday + timedelta(weeks=week_number - 1)
    
    # Если целевой понедельник относится к следующему году, обновляем year
    if target_monday.year > year:
        year = target_monday.year
    
    return round(target_monday.timestamp())

def get_iterable_text(soup_find_text):
  return [text.strip() for text in soup_find_text.splitlines() if text.strip()] if len(soup_find_text) > 2 else []

def parse_timetable(html_file: str, json_file: str = None, add_groupname_to_json: bool = False, group_name: str = None):

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
        week_num_real = int(week_num) + ADDED_WEEKS - 1 #
        week_num_real = str(week_num_real)
        if add_groupname_to_json:
            timetable[group_name] = {}
            timetable[group_name][week_num_real] = {}
        else:
            timetable[week_num_real] = {}
        
        # Секция соответствующих дней недели
        week_container = week_section.find_next("div", class_="container")
        day_rows = week_container.find_all("div", class_="row")
        
        day_rows.pop(0)

        first_day_of_the_week = get_monday_timestamp(int(week_num) + START_STUDY_WEEK_NUM + ADDED_WEEKS, 2024)
        for day_row in day_rows:
            day_col = day_row.find("div", class_="table-header-col")
            if not day_col:
                continue  # Пропуск строки, если это не день
            
            # date = datetime.fromtimestamp(first_day_of_the_week).strftime("%d/%m/%Y, %H:%M:%S")
            date = first_day_of_the_week
            date = str(date)
            if add_groupname_to_json:
                timetable[group_name][week_num_real][date] = {}
            else:
                timetable[week_num_real][date] = {}

            first_day_of_the_week += 86400
            
            # Колонки пар
            pair_cols = day_row.find_all("div", class_="table-col")
            for pair_index, pair_col in enumerate(pair_cols, start=1):
                pair_label = f"{pair_index}"
                cell_text_it: list = get_iterable_text(pair_col.text)

                subject = "-"
                if len(cell_text_it) >= 3:
                    subject = cell_text_it[2]


                # Заменяем длинные названия на более короткие
                # if replace_subject_to_short:
                #     subject = short_subjects.get(subject.replace("пр.", "").lower(), subject)

                # if do_process_prefixes:
                #     subject = process_subject_name(subject)

                subject = process_subject_name(subject, subjects_map=subjects_map, prefixes_map=prefixes_map)

                if add_groupname_to_json:
                    timetable[group_name][week_num_real][date][pair_label] = subject
                else:
                    timetable[week_num_real][date][pair_label] = subject
    
    if json_file is not None:
        with open(json_file, "w", encoding="utf-8") as file:
            json.dump(timetable, file, ensure_ascii=False, indent=4)
        print(f"Расписание сохранено в {json_file}")

    return timetable