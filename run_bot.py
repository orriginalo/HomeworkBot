import datetime
from rich import print
from utils.logger import logger
from aiogram import Bot, Dispatcher
import asyncio
import os
from app.handlers import dp
from app.database.core import create_tables
from app.scheduler import start_scheduler
from app.database.requests.user import get_users_with_notifications
from utils.timetable_downloader import download_timetable
from aiogram.types import FSInputFile
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv
from app.browser_driver import driver

load_dotenv()

login = os.getenv('LOGIN')
password = os.getenv('PASSWORD')

API_KEY = os.getenv('API_KEY')

bot = Bot(token=API_KEY)
disp = Dispatcher()

notifications_scheduler = AsyncIOScheduler()

async def check_paths():
    paths = [
        "data",
        "data/backups",
        "data/backups/html_schedules",
        "data/backups/databases",
        "data/logs"
    ]
    for path in paths:
        try:
            os.makedirs(path, exist_ok=True)
        except Exception as e:
            logger.error(f"Error creating {path}: {e}")

async def send_new_timetable():
    logger.info("Sending new timetable")
    download_timetable(driver=driver, make_screenshot=True)

    photo = FSInputFile("./data/screenshots/timetable.png")
    for user_id in await get_users_with_notifications():
        await bot.send_photo(user_id, photo, caption="🔔 Новое расписание")


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
  await start_scheduler()
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