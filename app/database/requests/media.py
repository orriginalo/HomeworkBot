import aiosqlite

db_file = "Database.db"

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