from rich import print
import logging
from aiogram import Bot, Dispatcher
import asyncio
import os
from app.database.requests import log
from app.handlers import dp
from app.database.models import async_main
from app.backuper import schedule_backup

from config import API_KEY

bot = Bot(token=API_KEY)
disp = Dispatcher()

async def check_paths():
  try:
    if os.path.exists("data") == False:
      os.mkdir("data")
    if os.path.exists("data\\backups") == False:
      os.mkdir("data/backups")
    if os.path.exists("data\\backups\\html_schedules") == False:
      os.mkdir("data/backups/html_schedules")
    if os.path.exists("data\\backups\\databases") == False:
      os.mkdir("data/backups/databases")
    if os.path.exists("data\\logs") == False:
      os.mkdir("data/logs")
  except FileExistsError:
    await log("Error creating directories", "DIRCREATOR")


async def main():
  # await async_main()
  await check_paths()
  disp.include_router(dp)
  await log("Bot started", "RUNNER")
  await schedule_backup()
  await disp.start_polling(bot)


if __name__ == "__main__":
  # logging.basicConfig(level=logging.INFO)
  try:
    asyncio.run(main())
  except (KeyboardInterrupt, SystemExit):
    asyncio.run(log("Bot stopped", "RUNNER"))
    print ("[bold red]Bot stopped")
