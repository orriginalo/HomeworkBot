from app.database.db_setup import session
from app.database.models import Schedule
from sqlalchemy import select
from utils.log import logger
import datetime

from app.database.schemas import ScheduleSchema

async def add_subject(timestamp: int, subject: str, week_number: int, group_id: int):
  try:
    async with session() as s:
      schedule = Schedule(
        timestamp=datetime.datetime.fromtimestamp(timestamp), 
        subject=subject, 
        week_number=week_number,
        group_id=group_id
      )
      s.add(schedule)
      await s.commit()
      await s.refresh(schedule)
      return ScheduleSchema.model_validate(schedule, from_attributes=True)
    logger.debug(f"Schedule with week={week_number} and subject={subject} added.")
  except Exception as e:
    logger.exception(f"Error adding schedule: {e}")

async def get_schedule_by_week(week_number: int):
  try:
    async with session() as s:
      stmt = select(Schedule).where(Schedule.week_number == week_number)
      result = await s.execute(stmt)
      schedules = result.scalars().all()
      schedules = [ScheduleSchema.model_validate(schedule, from_attributes=True) for schedule in schedules]
      return schedules
  except Exception as e:
    logger.exception(f"Error getting schedule by week {week_number}: {e}")
    return None
  
async def del_schedule_by_week(week_number: int, group_id: int = None):
  try:
    async with session() as s:
      stmt = select(Schedule).where(Schedule.week_number == week_number)
      if group_id:
        stmt = stmt.where(Schedule.group_id == group_id)
        
      result = await s.execute(stmt)
      schedules = result.scalars().all()  # Получаем все записи для этой недели
      
      if schedules:
        for schedule in schedules:
          await s.delete(schedule)
        await s.commit()
        logger.debug(f"Schedules for week_number={week_number} deleted.")
      else:
        logger.debug(f"Schedule with week_number={week_number} not found.")
  except Exception as e:
    logger.exception(f"Error deleting schedule {week_number}: {e}")
    return None


async def check_exists_subject(subject: str, timestamp: int, group_id: int = None):
  async with session() as s:
    stmt = select(Schedule).where(Schedule.subject == subject, Schedule.timestamp == datetime.datetime.fromtimestamp(timestamp))
    if group_id:
      stmt = stmt.where(Schedule.group_id == group_id)
      
    result = await s.execute(stmt)
    schedule = result.scalar_one_or_none()
    if schedule:
      return True
    else:
      return False