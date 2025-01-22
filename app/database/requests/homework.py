from typing import List, Optional
from sqlalchemy import func, select
from app.database.db_setup import session
from app.database.models import Homework, Schedule
import logging
import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
      return vars(homework)

  except Exception as e:
    logger.error(f"Error adding homework: {e}")

  
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
        logger.info(f"Homework with uid={homework_id} not found.")
  except Exception as e:
    logger.error(f"Error deleting homework {homework_id}: {e}")

async def get_homework_by_id(homework_id: int):
  try:
    async with session() as s:
      stmt = select(Homework).where(Homework.uid == homework_id)
      result = await s.execute(stmt)
      homework = result.scalar_one_or_none()
      return vars(homework)
  except Exception as e:
    logger.error(f"Error getting homework by ID {homework_id}: {e}")
    return None
  
async def get_homeworks_by_date(to_date_ts: int, group_id: int = None):
  hw_list = []
  try:
    async with session() as s:
      iso_time = datetime.datetime.fromtimestamp(to_date_ts).replace(microsecond=0)
      stmt = select(Homework).where(
        Homework.to_date >= iso_time,
        Homework.to_date < iso_time + datetime.timedelta(seconds=1)
      )
      if group_id:
        stmt = stmt.where(Homework.group_id == group_id)
        
      result = await s.execute(stmt)
      homework = result.scalars().all()
      for hw in homework:
        hw_list.append(vars(hw))
      return hw_list
  except Exception as e:
    logger.error(f"Error getting homework by date {to_date_ts}: {e}")
    return None

async def get_homeworks_by_subject(subject: str, limit_last_two: Optional[bool] = False, group_id: int = None) -> List[dict] | None:
  hw_list = []
  try:
    async with session() as s:
      stmt = select(Homework).where(Homework.subject == subject)
      
      if limit_last_two:
        stmt = stmt.order_by(Homework.from_date.desc()).limit(2)

      if group_id:
        stmt = stmt.where(Homework.group_id == group_id)

      result = await s.execute(stmt)
      homework = result.scalars().all()
      
      for hw in homework:
        hw.from_date = datetime.datetime.timestamp(hw.from_date)
        hw_list.append(vars(hw))
      
      return hw_list

  except Exception as e:
    logger.error(f"Error getting homework by subject {subject}: {e}")
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
      return homework
  except Exception as e:
    logger.error(f"Error updating homework {homework_id}: {e}")
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
    logger.error(f"Error updating homework dates: {e}")



# async def reset_homework_deadline_by_id(homework_id):
#     await log(f"Resetting to_date for homework ID: {homework_id}...")
#     current_timestamp = calculate_today()[1]  # Текущая дата в формате timestamp
#     print(current_timestamp)

#     async with aiosqlite.connect(db_file) as conn:
#         # Получаем from_date и subject для указанного домашнего задания
#         async with conn.execute("SELECT from_date, subject FROM homeworks WHERE id = ?", (homework_id,)) as cursor:
#             homework_entry = await cursor.fetchone()

#         if homework_entry is None:
#             await log(f"No homework found with ID: {homework_id}")
#             return  # Если домашнее задание не найдено, выходим из функции

#         from_date, subject = homework_entry
#         print(from_date, subject)
#         # Находим ближайшую дату занятия для предмета относительно текущей даты
#         async with conn.execute("SELECT MIN(timestamp) FROM schedule WHERE subject = ? AND timestamp > ?", 
#                                 (subject, current_timestamp)) as cursor:
#             next_class_date = await cursor.fetchone()
#             print(next_class_date)

#         if next_class_date[0] is not None:
#             # Сбрасываем to_date и устанавливаем ближайшую дату занятия
#             await conn.execute("UPDATE homeworks SET to_date = ? WHERE id = ?", 
#                                (next_class_date[0], homework_id))
#             await log(f"Updated to_date for homework ID: {homework_id} to {next_class_date[0]}")

#         # Фиксируем изменения
#         await conn.commit()
#     await log("Homework to_date has been reset and updated.")

async def reset_homework_deadline_by_id(homework_id: int):
  try:
    async with session() as s:
      stmt = select(Homework).where(Homework.uid == homework_id)
      homework = await s.execute(stmt).scalar_one_or_none()
      if homework:
        # Find the next class date for the subject
        stmt = select(Schedule).where(Schedule.subject == homework.subject, Schedule.timestamp > homework.from_date)
        next_class_date = await s.execute(stmt).scalar_one_or_none()
        if next_class_date:
          homework.to_date = next_class_date.timestamp
          await s.commit()
  except Exception as e:
    logger.error(f"Error resetting homework deadline by ID {homework_id}: {e}")