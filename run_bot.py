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

from config import API_KEY

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
    download_timetable(make_screenshot=True)

    photo = FSInputFile("./data/screenshots/timetable.png")
    for user_id in await get_users_with_notifications():
        await bot.send_photo(user_id, photo, caption="🔔 Новое расписание")


async def main():
  await create_tables()
  await check_paths()
  disp.include_router(dp)
  await log("Bot started", "RUNNER")
  # notifications_scheduler.add_job(send_new_timetable, CronTrigger(day_of_week="sun", hour=16, minute=00)) 
  # notifications_scheduler.add_job(send_new_timetable, 'interval', seconds=30)
  # await send_new_timetable()
  notifications_scheduler.start()
  await start_scheduler()
  await disp.start_polling(bot)


if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO)
  try:
    asyncio.run(main())
  except (KeyboardInterrupt, SystemExit):
    asyncio.run(log("Bot stopped", "RUNNER"))
    print ("[bold red]Bot stopped")