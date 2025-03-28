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
from app.middlewares import AlbumMiddleware, GroupChecker, MsgLoggerMiddleware

from utils.log import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import settings

load_dotenv()

login = settings.ULSTU_LOGIN
password = settings.ULSTU_PASSWORD

bot = Bot(token=settings.API_KEY)
dp = Dispatcher()

# dp.message.middleware(AlbumMiddleware())
# dp.message.middleware(MsgLoggerMiddleware())
# dp.callback_query.middleware(MsgLoggerMiddleware())
# dp.message.filter(GroupChecker())

notifications_scheduler = AsyncIOScheduler()


async def check_paths():
    folder_paths = [
        "data/backups",
        "data/databases",
        "data/database",
        "data/logs",
        "data/screenshots",
        "data/timetables/html",
        "data/changes",
    ]
    file_paths = ["data/timetables/timetables.json", "data/timetables/all-timetables.json"]
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

    dp.include_routers(*routers)
    logger.info("Routers included")

    await start_scheduler(bot)
    logger.info("Schedulers started")

    logger.info("Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    logger.info("Bot starting...")
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopping...")
        print("[bold red]Bot stopped")
