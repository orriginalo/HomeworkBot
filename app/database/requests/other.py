from datetime import datetime
from rich import print
import asyncio
import aiofiles
import aiosqlite
from sqlalchemy import text
from app.database.db_setup import session


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

async def sync_sequences():
  tables = ["users", "homeworks", "schedule", "media", "groups"]
  async with session() as s:
    for table in tables:
      stmt = text(f"""
      SELECT setval(
          pg_get_serial_sequence('{table}', 'uid'),
          (SELECT MAX(uid) FROM {table})
      )
      """)
      await s.execute(stmt)
    await s.commit()

