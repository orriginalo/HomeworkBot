from rich import print
import asyncio
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.types import FSInputFile

from app.handlers import routers
from app.database.models import User
from app.database.core import create_tables
from app.scheduler import start_scheduler
from app.database.queries.user import get_users
from app.database.queries.group import *

from utils.log import logger
from utils.timetable.downloader import download_timetable
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.browser_driver import driver
from config import settings

load_dotenv()

login = settings.ULSTU_LOGIN
password = settings.ULSTU_PASSWORD

bot = Bot(token=settings.API_KEY)
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
    # for path in file_paths:
    #     try:
    #         open(path, "w").close()
    #     except Exception as e:
    #         logger.exception(f"Error creating {path}: {e}")


async def main():
  await create_tables()
  logger.info("Tables created")

  await check_paths()
  logger.info("Paths checked")

  disp.include_routers(*routers)
  logger.info("Routers included")

  driver.auth(login, password)
  logger.info("Driver authenticated")

  await start_scheduler(bot)
  logger.info("Schedulers started")

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