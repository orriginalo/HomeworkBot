from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from utils.backuper import create_backups
from utils.timetable.updater import update_timetable
from utils.timetable.sender import send_new_timetable
from utils.changes import check_changes_job
from utils.log import logger
scheduler = AsyncIOScheduler()

async def start_scheduler(bot: Bot):
    try:
        scheduler.add_job(create_backups, 'interval', hours=1)
        scheduler.add_job(update_timetable, 'interval', hours=6)
        # scheduler.add_job(check_changes_job, 'interval', minutes=5, args=[bot])
        await check_changes_job(bot)
        # scheduler.add_job(send_new_timetable, CronTrigger(day_of_week="sun", hour=16, minute=00), args=[bot])
        scheduler.start()
    except Exception as e:
        logger.exception(f"Error starting scheduler: {e}")