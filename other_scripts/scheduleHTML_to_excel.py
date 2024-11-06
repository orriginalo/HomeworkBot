import pandas as pd
import re
from datetime import datetime
from bs4 import BeautifulSoup

# Для удачной генерации нужно удалить все лишние расписания кроме нужного (от корня будут >1 <div>, нужно чтобы остался один)
# А также удалить верхнюю строку с "пара/время" (Удалить самый первый )

df = pd.DataFrame(columns=['День недели', '1', '2', '3', '4', '5', '6', '7', '8', 'Дата'])

day = datetime.now().day
month = datetime.now().month
year = datetime.now().year

monday_day = int(input("Введите день понедельника на этой неделе: "))
monday_month = int(input("Введите месяц понедельника на этой неделе: "))
monday_year = int(input("Введите год понедельника на этой неделе: "))

i = -1

pretty_date = f"{monday_day}-{monday_month}-{monday_year}"

with open("schedule.html", encoding="utf-8") as f:
  html = f.read()

soup = BeautifulSoup(html, "lxml")

rows = soup.find_all("div", class_="row")

for row in rows: # Для каждой строки в строках
  i += 1
  cells = list(row.children)
  classes = []
  weekday = row.find("div", class_="table-header-col").text.strip()
  for cell in cells:
    if cell.name == "div" and cell.has_attr("class") and cell["class"][0] == "table-col table-desktop-col":
      classes.append("-")
    if cell.name == "div" and cell.has_attr("class") and cell["class"][0] == "table-col":
      search = re.search(R"(?<=\bпр\.)\s*(\w+)", cell.find_all("div")[1].text.strip().replace("\n", ""))

      subject = search.group() if search else "-"
      match subject:
        case "Основы":
          subject = "ОБЗР"
        case "Физическая":
          subject = "Физическая культура"
        case "Иностранный":
          subject = "Иностранный язык"
        case "Русский":
          subject = "Русский язык"
      classes.append(subject if search else "-")
  print(classes)

  new_data = pd.DataFrame({
      'День недели': [weekday],
      '1': [classes[0]],
      '2': [classes[1]],
      '3': [classes[2]],
      '4': [classes[3]],
      '5': [classes[4]],
      '6': [classes[5]],
      '7': [classes[6]],
      '8': [classes[7]],
      'Дата': [f"{monday_day+i}/{monday_month}/{monday_year}"],
    })
  
  df = pd.concat([df, new_data], ignore_index=True)
  df.to_excel(f'schedule-{pretty_date}.xlsx', index=False)