from rich import print
import logging
from aiogram import Bot, Dispatcher
import asyncio
import os
from app.database.requests import log
from app.handlers import dp
from app.database.models import async_main
from app.backuper import schedule_backup, timetable_get
# from other_scripts.timetable_downloader import download_timetable
# from other_scripts.timetable_parser import parse_timetable
# from dotenv import load_dotenv

# load_dotenv()

from config import API_KEY

bot = Bot(token=API_KEY)
disp = Dispatcher()

async def check_paths():
  try:
    if os.path.exists("data") == False:
      os.mkdir("data")
  except FileExistsError:
    await log("Error creating ./data directory", "DIRCREATOR")

  try:
    if os.path.exists("data") == False:
      os.mkdir("data")
  except FileExistsError:
    await log("Error creating ./data directory", "DIRCREATOR")

  try:
    if os.path.exists("data\\backups") == False:
      os.mkdir("data/backups")
  except FileExistsError:
    await log("Error creating ./data/backups directory", "DIRCREATOR")

  try:
    if os.path.exists("data\\backups\\html_schedules") == False:
      os.mkdir("data/backups/html_schedules")
  except FileExistsError:
    await log("Error creating ./data/backups/html_schedules directory", "DIRCREATOR")

  try:
    if os.path.exists("data\\backups\\databases") == False:
      os.mkdir("data/backups/databases")
  except FileExistsError:
    await log("Error creating ./data/backups/databases directory", "DIRCREATOR")

  try:
    if os.path.exists("data\\logs") == False:
      os.mkdir("data/logs")
  except FileExistsError:
    await log("Error creating ./data/logs directory", "DIRCREATOR")

async def main():
  # await async_main()
  await check_paths()
  disp.include_router(dp)
  await log("Bot started", "RUNNER")
  await schedule_backup()
  await timetable_get()
  await disp.start_polling(bot)


if __name__ == "__main__":
  # logging.basicConfig(level=logging.INFO)
  try:
    asyncio.run(main())
  except (KeyboardInterrupt, SystemExit):
    asyncio.run(log("Bot stopped", "RUNNER"))
    print ("[bold red]Bot stopped")