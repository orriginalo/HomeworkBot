from datetime import datetime, timedelta
import asyncio

allowed_subjects = ["Математика", "Информатика", "Физика", "Химия", "Биология", "География", "История", "Обществознание", "Литература", "Русский язык", "Иностранный язык- 1 п/г", "	Иностранный язык- 2 п/г", "ОБЗР"]
# , "Иностранный язык- 1 п/г", "	Иностранный язык- 2 п/г", "Основы безопасности и защиты Родины"
cur_month = datetime.now()

subjects_map = {
    "основы безопасности и защиты родины": "ОБЗР",
    "физическая культура": "Физ-ра",
}

# Вы можете задать значение ключа на "" чтобы префикс был удален
prefixes_map = {
    "пр.": "",
    "лек.": "",
}

def calculate_yesterday():
  """
  [0] - midnight datetime
  [1] - timestamp
  """
  yesterday_midnight = (datetime.now() - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
  yesterday_ts = int(yesterday_midnight.timestamp())

  return [yesterday_midnight, yesterday_ts]

def calculate_today():
  """
  [0] - midnight datetime
  [1] - timestamp
  """
  today_midnight = (datetime.now()).replace(hour=0,minute=0,second=0,microsecond=0)
  today_ts = int(today_midnight.timestamp())

  return [today_midnight, today_ts]


def calculate_tomorrow():
  """
  [0] - midnight datetime
  [1] - timestamp
  """
  tomorrow_midnight = (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
  tomorrow_ts = int(tomorrow_midnight.timestamp())

  return [tomorrow_midnight, tomorrow_ts]

def calculate_aftertomorrow():
  """
  [0] - midnight datetime
  [1] - timestamp
  """
  after_tomorrow_midnight = (datetime.now() + timedelta(days=2)).replace(hour=0, minute=0, second=0, microsecond=0)
  after_tomorrow_ts = int(after_tomorrow_midnight.timestamp())

  return [after_tomorrow_midnight, after_tomorrow_ts]


# Convert the datetime object to a timestamp

# print(yesterday)
cur_year = datetime.now()

months_words = {
  1: "января",
  2: "февраля",
  3: "марта",
  4: "апреля",
  5: "мая",
  6: "июня",
  7: "июля",
  8: "августа",
  9: "сентября",
  10: "октября",
  11: "ноября",
  12: "декабря"
}


async def get_day_month(timestamp):
  date = datetime.fromtimestamp(timestamp)
  return f"{date.strftime('%d')} {months_words[int(date.strftime('%m'))]}"

# print(asyncio.run(get_day_month(yesterday)))


# yesterday_date = datetime.fromtimestamp(int(yesterday))
# today_date = datetime.fromtimestamp(int(today))
# tomorrow_date = datetime.fromtimestamp(int(tomorrow))
# after_tommorow_date = datetime.fromtimestamp(int(after_tommorow))

# print(yesterday_date)
# print(today_date)
# print(tomorrow_date)
# print(after_tommorow_date)