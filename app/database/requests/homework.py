from sqlalchemy import select
from app.database.db_setup import session
from app.database.models import Homework, Schedule
import logging
import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def add_homework(subject: str, task: str, group_id: int, added_by: int, from_date_ts: int):
  try:
    async with session() as s:
      homework = Homework(
        from_date=datetime.datetime.fromtimestamp(from_date_ts), 
        subject=subject, 
        task=task,
        group_id=group_id, 
        added_by=added_by,
        to_date=None
      )
      s.add(homework)
      await s.commit()
      return homework
  except Exception as e:
    logger.error(f"Error adding homework: {e}")
    return None
  
async def del_homework(homework_id: int):
  try:
    async with session() as s:
      stmt = select(Homework).where(Homework.uid == homework_id)
      result = await s.execute(stmt)
      homework = result.scalar_one_or_none()
      if homework:
        s.delete(homework)
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
      return homework
  except Exception as e:
    logger.error(f"Error getting homework by ID {homework_id}: {e}")
    return None
  
async def get_homeworks_by_date(to_date: int):
  try:
    async with session() as s:
      stmt = select(Homework).where(Homework.to_date == to_date)
      result = await s.execute(stmt).scalars().all()
      homework = result.scalars().all()
      return homework
  except Exception as e:
    logger.error(f"Error getting homework by date {to_date}: {e}")
    return None
  
async def get_homeworks_by_subject(subject: str):
  try:
    async with session() as s:
      stmt = select(Homework).where(Homework.subject == subject)
      result = await s.execute(stmt)
      homework = result.scalars().all()
      return homework
  except Exception as e:
    logger.error(f"Error getting homework by subject {subject}: {e}")
    return None
  
async def update_homework(homework_id: int, **kwargs):
  try:
    async with session() as s:
      stmt = select(Homework).where(Homework.uid == homework_id)
      homework = await s.execute(stmt).scalar_one()
      for key, value in kwargs.items():
        if value is not None:
          setattr(homework, key, value)
      await s.commit()
      return homework
  except Exception as e:
    logger.error(f"Error updating homework {homework_id}: {e}")
    return None
# async def update_homework_dates():
#     await log("Updating homework to_date dates...")
#     async with aiosqlite.connect(db_file) as conn:
#         # Fetch all homework entries
#         async with conn.execute("SELECT from_date, subject FROM homeworks WHERE to_date IS NULL") as cursor:
#             homework_entries = await cursor.fetchall()
#             # print(homework_entries)
#         for from_date, subject in homework_entries:
#             # Find the next class date for the subject
#             async with conn.execute("SELECT MIN(timestamp) FROM schedule WHERE subject = ? AND timestamp > ?", (subject, from_date)) as cursor:
#                 next_class_date = await cursor.fetchone()

#             if next_class_date[0] is not None:
#                 # Update the to_date in homeworks
#                 await conn.execute("UPDATE homeworks SET to_date = ? WHERE from_date = ? AND subject = ?", (next_class_date[0], from_date, subject))
        
#         # Commit changes
#         await conn.commit()

async def update_homework_dates():
  try:
    async with session() as s:
      stmt = select(Homework).where(Homework.to_date == None)
      homework = await s.execute(stmt).scalars().all()
      for h in homework:
        # Find the next class date for the subject
        stmt = select(Schedule).where(Schedule.subject == h.subject, Schedule.timestamp > h.from_date)
        next_class_date = await s.execute(stmt).scalar_one_or_none()
        if next_class_date:
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