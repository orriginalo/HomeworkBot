from sqlalchemy import Boolean, cast, func
from app.database.models import User
from app.database.requests.group import get_group_by_id
from app.database.requests.user import get_user_by_id, get_users
from utils.timetable.downloader import download_timetable
from utils.log import logger
from aiogram.types import FSInputFile
from app.browser_driver import driver
from aiogram import Bot
from datetime import datetime, timedelta
from rich import print
import pdfplumber
import os
import requests
from bs4 import BeautifulSoup
import re
from utils.log import logger
import app.keyboards as kb

already_sended = False

async def check_changes_job(bot: Bot):
  global already_sended
  pdf_url = get_pdf_url_from_page()
  download_pdf_from_url(pdf_url)
  filename = check_if_exists_changes_pdf_to_tomorrow()
  if filename and not already_sended:
    logger.info(f"Changes for tomorrow found: {filename}")
    await send_changes_to_users(bot)
    already_sended = True
    



def check_if_exists_changes_pdf_to_tomorrow():
  path_to_files = "./data/changes"
  files = os.listdir(path_to_files)
  
  tomorrow_date = (datetime.today() + timedelta(days=1)).strftime("%d.%m.%y")
  
  for file in files:
    if file.endswith(".pdf"):
      file_date = file.replace("changes_", "").replace(".pdf", "")
      if file_date == tomorrow_date:
        return file
  return None

def download_pdf_from_url(url: str):
  changes_date = get_changes_date(url)
  
  if not url:
    logger.error("PDF file not found.")
    return
  else:
    logger.debug(f"URL to the PDF file found: {url}")

  response = requests.get(url)
  if response.status_code != 200:
    logger.error(f"Failed to download the PDF file. Status code: {response.status_code}")
    return
  
  path_to_file = f"./data/changes/changes_{changes_date}.pdf"
  with open(path_to_file, 'wb') as f:
    f.write(response.content)
  logger.debug(f"PDF file is successfully saved as {path_to_file}")


async def send_changes_to_users(bot: Bot):
  logger.info("Sending changes to users")

  users_with_setting = await get_users(User.settings['send_changes_updated'].as_boolean() == True)
  print(users_with_setting)
  for user in users_with_setting:
    group = await get_group_by_id(user["group_id"])
    if check_if_group_in_changes(group["name"]):
      await bot.send_message(user["tg_id"],
        f"🔔 Появились изменения на завтрашний день.\n<b>Группа {group["name"]} есть в списке изменений!</b>\n",
        parse_mode="html")
    else:
      await bot.send_message(user["tg_id"],
        f"🔔 Появились изменения на завтрашний день.\n<i>Группы {group["name"]} нету в списке изменений. 😢</i>",
        parse_mode="html")

def check_if_group_in_changes(group_name: str):
  group_name = group_name.lower()
  tomorrow_date = (datetime.today() + timedelta(days=1)).strftime("%d.%m.%y")
  with pdfplumber.open(f"./data/changes/changes_{tomorrow_date}.pdf") as pdf:
    for page in pdf.pages:
      text = page.extract_text().lower()
      text = text.splitlines()
      for line in text:
        if group_name in line and ("прием" not in line) and ("подготовка" not in line) and ("пересдача" not in line) and ("консультация" not in line) and ("профориентационное" not in line):
          return True
  return False
          

def get_changes_date(url: str):

    file_name = url.split('/')[-1]

    date_match = re.search(r'\d{2}\.\d{2}\.\d{2}', file_name)

    if date_match:
        date = date_match.group(0)
        return date
    else:
        logger.debug(f"Date not found in the file name: {file_name}")
        return None

def get_pdf_url_from_page():
    url = "https://ulstu.ru/education/kei/student/schedule/"

    logger.debug(f"Getting a page with URL: {url}")
    response = requests.get(url)
    if response.status_code != 200:
        logger.error(f"It was not possible to get a page. Status code: {response.status_code}")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')

    scripts = soup.find_all('script', type='application/javascript')
    for script in scripts:
        script_content = script.string
        if script_content and "PDFStart" in script_content:
            match = re.search(r"PDFStart\(['\"]([^'\"]+)['\"]\)", script_content)
            if match:
                pdf_url = match.group(1)
                full_pdf_url = requests.compat.urljoin(url, pdf_url)
                return full_pdf_url

    return None
