from datetime import datetime
from rich import print
import asyncio
import aiofiles
import aiosqlite

db_file = "Database.db"

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

async def get_admins_chatid():
   async with aiosqlite.connect(db_file) as conn:
    async with conn.execute("SELECT id FROM users WHERE role = 3 OR role = 4") as cursor:
      result = await cursor.fetchall()
   return result

async def get_notifications_by_id(user_id):
    async with aiosqlite.connect(db_file) as conn:
        async with conn.execute("SELECT notifications FROM users WHERE id = ?", (user_id,)) as cursor:
            result = await cursor.fetchone()
    return True if result[0] == 1 else False

async def set_notifications_by_id(user_id, notifications: bool):
    notifications = int(notifications)
    async with aiosqlite.connect(db_file) as conn:
        async with conn.execute("UPDATE users SET notifications = ? WHERE id = ?", (notifications, user_id)) as cursor:
            pass
        await conn.commit()