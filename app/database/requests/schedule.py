from app.database.db_setup import session
from app.database.models import Schedule
from sqlalchemy import select
import logging
import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def add_subject(timestamp: int, subject: str, week_number: int):
  try:
    async with session() as s:
      schedule = Schedule(
        timestamp=datetime.datetime.fromtimestamp(timestamp), 
        subject=subject, 
        week_number=week_number
      )
      s.add(schedule)
      await s.commit()
      return schedule
  except Exception as e:
    logger.error(f"Error adding schedule: {e}")

async def get_schedule_by_week(week_number: int):
  try:
    async with session() as s:
      stmt = select(Schedule).where(Schedule.week_number == week_number)
      result = await s.execute(stmt)
      schedule = result.scalars().all()
      return schedule
  except Exception as e:
    logger.error(f"Error getting schedule by week {week_number}: {e}")
    return None