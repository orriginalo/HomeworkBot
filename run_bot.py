from rich import print
import asyncio
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.types import FSInputFile

from app.handlers import dp
from app.database.models import User
from app.database.core import create_tables
from app.scheduler import start_scheduler
from app.database.requests.user import get_users
from app.database.requests.group import *

from utils.log import logger
from utils.timetable.downloader import download_timetable
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.browser_driver import driver

load_dotenv()

login = os.getenv('LOGIN')
password = os.getenv('PASSWORD')

API_KEY = os.getenv('API_KEY')

bot = Bot(token=API_KEY)
disp = Dispatcher()

notifications_scheduler = AsyncIOScheduler()

async def check_paths():
    folder_paths = [
      "data/backups",
      "data/databases",
      "data/database",
      "data/logs",
      "data/screenshots",
      "data/timetables/html",
      "data/changes"
    ]
    file_paths = [
      "data/timetables/timetables.json",
      "data/timetables/all-timetables.json"
    ]
    for path in folder_paths:
        try:
            os.makedirs(path, exist_ok=True)
        except Exception as e:
            logger.exception(f"Error creating {path}: {e}")


async def main():
  await create_tables()
  logger.info("Tables created")

  await check_paths()
  logger.info("Paths checked")

  disp.include_router(dp)
  logger.info("Dispatcher included")

  # notifications_scheduler.add_job(send_new_timetable, CronTrigger(day_of_week="sun", hour=16, minute=00)) 
  # notifications_scheduler.add_job(send_new_timetable, 'interval', seconds=30)
  # await send_new_timetable()
  notifications_scheduler.start()
  await start_scheduler(bot)
  logger.info("Schedulers started")

  driver.auth(login, password)
  logger.info("Driver authenticated")

  logger.info("Bot started")
  await disp.start_polling(bot)

if __name__ == "__main__":
  logger.info("Bot starting...")
  try:
    asyncio.run(main())
  except (KeyboardInterrupt, SystemExit):
    logger.info("Bot stopping...")
    driver.quit()
    print ("[bold red]Bot stopped")