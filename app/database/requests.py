from datetime import datetime
from rich import print
import aiosqlite
import asyncio
import aiofiles

db_file = "Database.db"

"""
0 - bomj
1 - Default
2 - Adder
3 - Admin
4 - /op
"""

async def log(message, category = "DATABASE"):
    async with aiofiles.open(f"./data/logs/{datetime.now().strftime('%Y-%m-%d')}.log", "a", encoding="utf-8") as f:
        await f.write(f"{await get_cur_time()} - [{category}]: {message}\n")
    print(f"[orange1]{await get_cur_time()}[/orange1] - [{category}]: {message}")

# LOG CARTEGORIES:
# [DATABASE] - Database requests
# [BACKUP] - Database backuping
# [RUNNER] - Bot runner
# [MSGLOGGER] - Message logger
# [DIRCREATOR] - Directory creator
# [FILEMANAGER] - File manager


async def get_cur_time():
  return await asyncio.get_event_loop().run_in_executor(None, lambda: datetime.now().strftime("%H:%M:%S"))

async def db_is_empty():
  async with aiosqlite.connect(db_file) as conn:
    async with conn.execute("SELECT CASE WHEN EXISTS (SELECT 1 FROM homeworks) THEN 1 ELSE 0 END") as cursor:
      result = await cursor.fetchone()
  if result is None:
    return True
  return False

## USER GET , ADD , DEL
async def check_exists_user(user_id):
  async with aiosqlite.connect(db_file) as conn:
    async with conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)) as cursor:
      result = await cursor.fetchone()
  if result is None:
    return False
  return True

async def get_user_role(user_id):
  async with aiosqlite.connect(db_file) as conn:
    async with conn.execute("SELECT role FROM users WHERE id = ?", (user_id,)) as cursor:
      role = await cursor.fetchone()
  if role is None:
    return role
  return role[0]

async def add_new_user(user_id, role):
  async with aiosqlite.connect(db_file) as conn:
    if await check_exists_user(user_id) == True:
      return
    async with conn.execute("INSERT INTO users (id, role) VALUES (?, ?)", (user_id, role)) as cursor:
      pass
    await conn.commit()
    await log(f"User {user_id} added with {role} role")

async def del_user(user_id):
  async with aiosqlite.connect(db_file) as conn:
    async with conn.execute("DELETE FROM users WHERE id = ?", (user_id,)) as cursor:
      pass
    await conn.commit()
    await log(f"User {user_id} deleted")

async def change_user_role(user_id, role):
  old_role = 0
  async with aiosqlite.connect(db_file) as conn:
    if await check_exists_user(user_id) == False:
      await add_new_user(user_id, 0)
    old_role = await get_user_role(user_id)
    async with conn.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id)) as cursor:
      await conn.commit()
    await log(f"User {user_id} role {old_role} changed to {role}")

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

async def get_all_users_with_role(role):
  result_users = []
  async with aiosqlite.connect(db_file) as conn:
    async with conn.execute("SELECT id FROM users WHERE role = ?", (role,)) as cursor:
      result = await cursor.fetchall()
  for user in result:
    result_users.append(user[0])
  return result_users

async def get_admins_chatid():
   async with aiosqlite.connect(db_file) as conn:
    async with conn.execute("SELECT id FROM users WHERE role = 3 OR role = 4") as cursor:
      result = await cursor.fetchall()
   return result

# from_date = int(datetime.timestamp(datetime.now()))
# from_date = datetime.fromtimestamp(from_date).strftime("%d/%m/%Y 00:00:00")
# from_date_rounded = datetime.timestamp(datetime.strptime(from_date, "%d/%m/%Y %H:%M:%S"))
# print(from_date_rounded)
# print(datetime.fromtimestamp(from_date_rounded))
async def get_task_by_subject(subject):
    async with aiosqlite.connect(db_file) as conn:
        async with conn.execute("SELECT from_date, task, id FROM homeworks WHERE subject = ? ORDER BY id DESC LIMIT 2", (subject,)) as cursor:
            tasks = await cursor.fetchall()
    return tasks

async def get_tasks_by_date(timestamp):
    async with aiosqlite.connect(db_file) as conn:
        async with conn.execute("SELECT subject, task, id FROM homeworks WHERE to_date = ?", (timestamp,)) as cursor:
            results = await cursor.fetchall()
    return results if results else None

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

async def add_media_to_db(homework_id, media_id, media_type = None):
  async with aiosqlite.connect(db_file) as conn:
    async with conn.execute("INSERT INTO media (homework_id, media_id, media_type) VALUES (?, ?, ?)", (homework_id, media_id, media_type)) as cursor:
      pass
    await conn.commit()

async def get_all_media_by_id(homework_id):
  async with aiosqlite.connect(db_file) as conn:
    async with conn.execute("SELECT media_id, media_type FROM media WHERE homework_id = ?", (homework_id,)) as cursor:
      result = await cursor.fetchall()
  return result if len(result) > 0 else None

async def delete_media_by_id(homework_id):
  async with aiosqlite.connect(db_file) as conn:
    async with conn.execute("DELETE FROM media WHERE homework_id = ?", (homework_id,)) as cursor:
      pass
    await conn.commit()

