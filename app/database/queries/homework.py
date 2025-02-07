from typing import List, Optional
from sqlalchemy import and_, func, select
from app.database.db_setup import session
from app.database.models import Homework, Schedule
from utils.log import logger
from datetime import datetime, timedelta
from app.database.schemas import HomeworkSchema

async def add_homework(subject: str, task: str, group_id: int, added_by: int, from_date_ts: int, to_date_ts: int = None, **kwargs):
  try:
    async with session() as s:
      homework = Homework(
        from_date=datetime.datetime.fromtimestamp(from_date_ts), 
        subject=subject, 
        task=task,
        group_id=group_id, 
        added_by=added_by,
        to_date=datetime.datetime.fromtimestamp(to_date_ts) if to_date_ts else None
      )
      
      for key, value in kwargs.items():
        if value is not None:
          setattr(homework, key, value)

      s.add(homework)
      await s.commit()
      
      await s.refresh(homework)
      return HomeworkSchema(**homework.__dict__)

  except Exception as e:
    logger.exception(f"Error adding homework: {e}")

  
async def del_homework(homework_id: int):
  try:
    async with session() as s:

      if not isinstance(homework_id, int):
        homework_id = int(homework_id)
      print(type(homework_id))

      stmt = select(Homework).where(Homework.uid == homework_id)
      result = await s.execute(stmt)
      homework = result.scalar_one_or_none()
      if homework:
        await s.delete(homework)
        await s.commit()
      else:
        logger.debug(f"Homework with uid={homework_id} not found.")
  except Exception as e:
    logger.exception(f"Error deleting homework {homework_id}: {e}")

async def get_homeworks(*filters):
  async with session() as s:
    stmt = select(Homework)
    if filters:
      stmt = stmt.where(and_(*filters))
    result = await s.execute(stmt)
    homeworks = result.scalars().all()
    homeworks = [HomeworkSchema(**homework.__dict__) for homework in homeworks]
    return homeworks

async def get_homework_by_id(homework_id: int):
  try:
    async with session() as s:
      stmt = select(Homework).where(Homework.uid == homework_id)
      result = await s.execute(stmt)
      homework = result.scalar_one_or_none()
      return HomeworkSchema(**homework.__dict__) if homework else None
  except Exception as e:
    logger.exception(f"Error getting homework by ID {homework_id}: {e}")
    return None
  
async def get_homeworks_by_date(to_date: datetime, group_id: int = None):
  try:
    async with session() as s:
      stmt = select(Homework).where(
        Homework.to_date >= to_date,
        Homework.to_date < to_date + datetime.timedelta(seconds=1)
      )
      if group_id:
        stmt = stmt.where(Homework.group_id == group_id)
        
      result = await s.execute(stmt)
      homeworks = result.scalars().all()
      homeworks = [HomeworkSchema(**homework.__dict__) for homework in homeworks]
      return homeworks
    
  except Exception as e:
    logger.exception(f"Error getting homework by date {to_date.strftime('%d.%m.%Y')}: {e}")
    return None

async def get_homeworks_by_subject(subject: str, limit_last_two: Optional[bool] = False, group_id: int = None) -> List[HomeworkSchema] | None:
  try:
    async with session() as s:
      stmt = select(Homework).where(Homework.subject == subject)
      
      if limit_last_two:
        stmt = stmt.order_by(Homework.created_at.desc()).limit(2)

      if group_id:
        stmt = stmt.where(Homework.group_id == group_id)

      result = await s.execute(stmt)
      homeworks = result.scalars().all()
      homeworks = [HomeworkSchema(**homework.__dict__) for homework in homeworks]
      return homeworks

  except Exception as e:
    logger.exception(f"Error getting homework by subject {subject}: {e}")
    return None

  
async def update_homework(homework_id: int, **kwargs):
  try:
    async with session() as s:
      stmt = select(Homework).where(Homework.uid == homework_id)
      homework = await s.execute(stmt)
      homework = homework.scalar_one()
      for key, value in kwargs.items():
        if value is not None:
          setattr(homework, key, value)
      await s.commit()
      return HomeworkSchema(**homework.__dict__)
  except Exception as e:
    logger.exception(f"Error updating homework {homework_id}: {e}")
    return None

async def update_homework_dates():
  try:
    async with session() as s:
      stmt = select(Homework).where(Homework.to_date == None)
      result = await s.execute(stmt)
      homework = result.scalars().all()
      for h in homework:
        # Ищем все возможные даты занятия для предмета
        stmt = select(Schedule).where(Schedule.subject == h.subject, Schedule.timestamp > h.from_date)
        next_class_dates = await s.execute(stmt)
        next_class_dates = next_class_dates.scalars().all()  # получаем все возможные даты
        
        if next_class_dates:
          # Например, можно выбрать первую или последнюю дату
          next_class_date = min(next_class_dates, key=lambda x: x.timestamp)  # выбираем ближайшую дату
          h.to_date = next_class_date.timestamp
      await s.commit()
  except Exception as e:
    logger.exception(f"Error updating homework dates: {e}")

async def reset_homework_deadline_by_id(homework_id: int):
  try:
    async with session() as s:
      stmt = select(Homework).where(Homework.uid == homework_id)
      homework = await s.execute(stmt)
      homework = homework.scalar_one_or_none()
      if homework:
        # Find the next class date for the subject
        stmt = select(Schedule).where(Schedule.subject == homework.subject, Schedule.timestamp > homework.from_date)
        next_class_date = await s.execute(stmt)
        next_class_date = next_class_date.scalar_one_or_none()
        if next_class_date:
          homework.to_date = next_class_date.timestamp
          await s.commit()
  except Exception as e:
    logger.exception(f"Error resetting homework deadline by ID {homework_id}: {e}")