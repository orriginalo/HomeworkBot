from datetime import datetime
import datetime as dt
from app.database.queries.group import get_group_by_name
from app.database.queries.schedule import add_subject, del_schedule_by_week, check_exists_subject
from utils.timetable.subjects_process import process_subject_name
from variables import subjects_map, prefixes_map

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

async def populate_schedule(timetable: dict):
  for group, weeks in timetable.items():
    print(group)
    group = await get_group_by_name(group)
    for group_name, week in timetable.items():
      for week_num, day in week.items():
        await del_schedule_by_week(int(week_num), group.uid)
        for day_timestamp, pairs in day.items():
          for pair, variants in pairs.items():
            for variant_num, pair_info in variants.items():
              subject = pair_info["subject"]
              if subject != "-" and await check_exists_subject(subject, int(day_timestamp), group.uid) == False:
                await add_subject(
                  timestamp=int(day_timestamp),
                  subject=process_subject_name(subject, subjects_map, prefixes_map),
                  teacher=pair_info["teacher"],
                  cabinet=pair_info["cabinet"],
                  week_number=int(week_num),
                  group_id=group.uid
                  )