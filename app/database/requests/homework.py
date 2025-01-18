from datetime import datetime
from rich import print
import aiosqlite
from app.variables import calculate_today
from app.database.requests.other import log

db_file = "Database.db"

async def add_homework(subject, task):
  from_date = int(datetime.timestamp(datetime.now()))
  from_date = datetime.fromtimestamp(from_date).strftime("%d/%m/%Y 00:00:00")
  from_date_rounded = datetime.timestamp(datetime.strptime(from_date, "%d/%m/%Y %H:%M:%S"))
  async with aiosqlite.connect(db_file) as conn:
    async with conn.execute("INSERT INTO homeworks (from_date, subject, task) VALUES (?, ?, ?)", (from_date_rounded, subject, task)) as cursor:
      homework_id = cursor.lastrowid
    await conn.commit()
    await log(f"{str(subject).capitalize()} homework added")
  return homework_id

async def get_homework_by_id(hw_id):
  async with aiosqlite.connect(db_file) as conn:
    async with conn.execute("SELECT subject, task FROM homeworks WHERE id = ?", (hw_id,)) as cursor:
      result = await cursor.fetchone()
  return result

async def delete_homework_by_id(hw_id):
  async with aiosqlite.connect(db_file) as conn:
    async with conn.execute("DELETE FROM homeworks WHERE id = ?", (hw_id,)) as cursor:
      pass
    await conn.commit()

async def get_tasks_by_date(timestamp):
    async with aiosqlite.connect(db_file) as conn:
        async with conn.execute("SELECT subject, task, id FROM homeworks WHERE to_date = ?", (timestamp,)) as cursor:
            results = await cursor.fetchall()
    return results if results else None

async def get_task_by_subject(subject):
    async with aiosqlite.connect(db_file) as conn:
        # Получаем последние два from_date для указанного предмета
        async with conn.execute("SELECT from_date FROM homeworks WHERE subject = ? ORDER BY from_date DESC LIMIT 2", (subject,)) as cursor:
          last_dates = await cursor.fetchall()
        
        # Извлекаем только значения from_date из кортежей
        last_dates = [date[0] for date in last_dates]
        
        if not last_dates:
          return []  # Если нет заданий, возвращаем пустой список

        # Получаем все задания, соответствующие последним двум from_date
        
        if len(last_dates) > 1:
          async with conn.execute("SELECT from_date, task, id FROM homeworks WHERE subject = ? AND from_date IN (?, ?)", (subject, last_dates[0], last_dates[1])) as cursor:
            tasks = await cursor.fetchall()
        else:
          async with conn.execute("SELECT from_date, task, id FROM homeworks WHERE subject = ? AND from_date = ?", (subject, last_dates[0])) as cursor:
            tasks = await cursor.fetchall()

    return tasks

async def update_homework_dates():
    await log("Updating homework to_date dates...")
    async with aiosqlite.connect(db_file) as conn:
        # Fetch all homework entries
        async with conn.execute("SELECT from_date, subject FROM homeworks WHERE to_date IS NULL") as cursor:
            homework_entries = await cursor.fetchall()
            # print(homework_entries)
        for from_date, subject in homework_entries:
            # Find the next class date for the subject
            async with conn.execute("SELECT MIN(timestamp) FROM schedule WHERE subject = ? AND timestamp > ?", (subject, from_date)) as cursor:
                next_class_date = await cursor.fetchone()

            if next_class_date[0] is not None:
                # Update the to_date in homeworks
                await conn.execute("UPDATE homeworks SET to_date = ? WHERE from_date = ? AND subject = ?", (next_class_date[0], from_date, subject))
        
        # Commit changes
        await conn.commit()

async def reset_homework_deadline_by_id(homework_id):
    await log(f"Resetting to_date for homework ID: {homework_id}...")
    current_timestamp = calculate_today()[1]  # Текущая дата в формате timestamp
    print(current_timestamp)

    async with aiosqlite.connect(db_file) as conn:
        # Получаем from_date и subject для указанного домашнего задания
        async with conn.execute("SELECT from_date, subject FROM homeworks WHERE id = ?", (homework_id,)) as cursor:
            homework_entry = await cursor.fetchone()

        if homework_entry is None:
            await log(f"No homework found with ID: {homework_id}")
            return  # Если домашнее задание не найдено, выходим из функции

        from_date, subject = homework_entry
        print(from_date, subject)
        # Находим ближайшую дату занятия для предмета относительно текущей даты
        async with conn.execute("SELECT MIN(timestamp) FROM schedule WHERE subject = ? AND timestamp > ?", 
                                (subject, current_timestamp)) as cursor:
            next_class_date = await cursor.fetchone()
            print(next_class_date)

        if next_class_date[0] is not None:
            # Сбрасываем to_date и устанавливаем ближайшую дату занятия
            await conn.execute("UPDATE homeworks SET to_date = ? WHERE id = ?", 
                               (next_class_date[0], homework_id))
            await log(f"Updated to_date for homework ID: {homework_id} to {next_class_date[0]}")

        # Фиксируем изменения
        await conn.commit()
    await log("Homework to_date has been reset and updated.")
    
async def get_homework_deadline_by_id(homework_id):
    async with aiosqlite.connect(db_file) as conn:
        async with conn.execute("SELECT to_date FROM homeworks WHERE id = ?", (homework_id,)) as cursor:
            result = await cursor.fetchone()
    return result[0] if result is not None else None