from rich import print
import logging
from aiogram import Bot, Dispatcher
import asyncio
import os
from app.database.requests.other import log
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

async def send_new_timetable():
    await log("Sending new timetable", "NOTIFICATIONS")
    download_timetable(driver=driver, make_screenshot=True)

    photo = FSInputFile("./data/screenshots/timetable.png")
    for user_id in await get_users_with_notifications():
        await bot.send_photo(user_id, photo, caption="🔔 Новое расписание")


async def main():
  logging.info("Bot starting...")

  await create_tables()
  logging.info("Tables created")

  await check_paths()
  logging.info("Paths checked")

  disp.include_router(dp)
  logging.info("Dispatcher included")

  # notifications_scheduler.add_job(send_new_timetable, CronTrigger(day_of_week="sun", hour=16, minute=00)) 
  # notifications_scheduler.add_job(send_new_timetable, 'interval', seconds=30)
  # await send_new_timetable()
  notifications_scheduler.start()
  await start_scheduler()
  logging.info("Schedulers started")

  driver.auth(login, password)
  logging.info("Driver authenticated")

  logging.info("Bot started")
  await log("Bot started", "RUNNER")
  await disp.start_polling(bot)


if __name__ == "__main__":
  logging.basicConfig(
    level=logging.INFO,
    filename="data/logs/bot.log",
    filemode="a",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%d.%m.%Y %H:%M:%S",
    encoding="utf-8"
    )
  try:
    asyncio.run(main())
  except (KeyboardInterrupt, SystemExit):
    asyncio.run(log("Bot stopping...", "RUNNER"))
    logging.info("Bot stopping...")
    driver.quit()
    print ("[bold red]Bot stopped")