import pandas as pd
from rich import print
from datetime import datetime
from app.excel_maker.db_requests import get_homeworks, get_users, get_schedule
import os

homeworks_columns = ["id", "Дата (Когда задано)", "Предмет", "Домашнее задание", "Дата сдачи" ]
users_columns = ["Телеграм id", "Никнейм", "Роль"]
schedule_columns = ["Дата", "Предмет", "Номер недели"]

all_columns = [homeworks_columns, users_columns, schedule_columns]
sheet_names = ["Домашние задания", "Пользователи", "Расписание пар"]

excel_filename = "domashkabot info.xlsx"

weekdays_ru = {
    'Monday': 'Понедельник',
    'Tuesday': 'Вторник',
    'Wednesday': 'Среда',
    'Thursday': 'Четверг',
    'Friday': 'Пятница',
    'Saturday': 'Суббота',
    'Sunday': 'Воскресенье'
}

def get_db():
    """
    Возвращает DataFrame с базой данных
    """
    try:
        # Чтение всех листов из Excel файла
        df_dict = pd.read_excel(excel_filename, sheet_name=None)
        return df_dict

    except FileNotFoundError:

        # Создание нового Excel файла с тремя листами
        with pd.ExcelWriter(excel_filename) as writer:
            for i in range(3):
                df = pd.DataFrame(columns=all_columns[i])
                df.to_excel(writer, index=False, sheet_name=sheet_names[i])
        
        return {sheet_names[i]: pd.DataFrame(columns=all_columns[i]) for i in range(3)}

def append_db(data: list, df_dict: dict, sheet_name: str):
    new_data = None
    
    match sheet_name:
        case "Домашние задания":
            new_data = pd.DataFrame({
                "id": [data[0]],
                "Дата (Когда задано)": [data[1]],
                "Предмет": [data[2]],
                "Домашнее задание": [data[3]],
                "Дата сдачи": [data[4]],
            })
        case "Пользователи":
            new_data = pd.DataFrame({
                "Телеграм id": [data[0]],
                "Никнейм": [data[1]],
                "Роль": [data[2]]
            })
        case "Расписание пар":
            new_data = pd.DataFrame({
                "Дата": [data[0]],
                "Предмет": [data[1]],
                "Номер недели": [data[2]]
            })

    # Обновление DataFrame для соответствующего листа
    df_dict[sheet_name] = pd.concat([df_dict[sheet_name], new_data], ignore_index=True)

    # Сохранение всех DataFrame обратно в Excel
    with pd.ExcelWriter(excel_filename) as writer:
        for name, df in df_dict.items():
            df.to_excel(writer, index=False, sheet_name=name)

def db_to_excel():
  for homework in get_homeworks():
      from_date = datetime.fromtimestamp(homework[1]).strftime("%d/%m/%Y")
      to_date = datetime.fromtimestamp(homework[4]).strftime("%d/%m/%Y") if homework[4] is not None else ""
      append_db([homework[0], from_date, homework[2], homework[3], to_date], get_db(), "Домашние задания")

  for user in get_users():
      append_db([user[0], user[2], user[1]], get_db(), "Пользователи")

  for schedule in get_schedule():
      date = datetime.fromtimestamp(schedule[0]).strftime("%d/%m/%Y")
      append_db([date, schedule[1], schedule[2]], get_db(), "Расписание пар")


def create_schedule():
  if os.path.exists(excel_filename):
    os.remove(excel_filename)
  get_db()
  db_to_excel()
