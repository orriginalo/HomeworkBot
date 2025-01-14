from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.database.requests import log
from app.backuper import create_backups, download_timetable_job
from app.database.requests import get_all_users_with_notifications

scheduler = AsyncIOScheduler()

async def start_scheduler():
    try:
        scheduler.add_job(create_backups, 'interval', hours=1)
        scheduler.add_job(download_timetable_job, 'interval', hours=12)
        scheduler.start()
    except Exception as e:
        print("Error: "+str(e))
        await log("Scheduler ERROR", "SCHEDULER")