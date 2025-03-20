from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from utils.backuper import create_backups
from utils.timetable.updater import update_timetable
from utils.log import logger

scheduler = AsyncIOScheduler()


async def start_scheduler(bot: Bot):
    try:
        scheduler.add_job(create_backups, "interval", hours=1)
        scheduler.add_job(update_timetable, "interval", hours=6)
        scheduler.start()
    except Exception as e:
        logger.exception(f"Error starting scheduler: {e}")
