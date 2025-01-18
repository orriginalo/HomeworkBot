from datetime import datetime
import aiosqlite
from app.database.requests.other import log

db_file = "Database.db"

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

async def add_new_user(user_id, role, username = None, firstname = None, lastname = None):
  async with aiosqlite.connect(db_file) as conn:
    if await check_exists_user(user_id) == True:
      return
    now = datetime.now()
    now_ts = int(datetime.timestamp(now))
    if username:
      async with conn.execute("INSERT INTO users (id, role, username, firstname, created_at) VALUES (?, ?, ?, ?, ?, ?)", (user_id, role, username, firstname, lastname, now_ts)) as cursor:
        pass
    else:
      async with conn.execute("INSERT INTO users (id, role, firstname, created_at) VALUES (?, ?, ?, ?, ?)", (user_id, role, firstname, lastname, now_ts)) as cursor:
        pass
    await conn.commit()
    await log(f"User {username} ({user_id}) added with {role} role")

async def update_user_info(user_id, username, firstname, lastname):
    async with aiosqlite.connect(db_file) as conn:
        async with conn.execute("UPDATE users SET username = ?, firstname = ?, lastname = ? WHERE id = ?", (username, firstname, lastname, user_id)) as cursor:
            pass
        await conn.commit()

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

async def get_all_users_with_role(role):
  result_users = []
  async with aiosqlite.connect(db_file) as conn:
    async with conn.execute("SELECT id FROM users WHERE role = ?", (role,)) as cursor:
      result = await cursor.fetchall()
  for user in result:
    result_users.append(user[0])
  return result_users

async def get_all_users():
  result_users = []
  async with aiosqlite.connect(db_file) as conn:
    async with conn.execute("SELECT id FROM users") as cursor:
      result = await cursor.fetchall()
  for user in result:
    result_users.append(user[0])
  return result_users

async def get_name_by_id(user_id):
  """
  [0] - firstname
  [1] - lastname
  """
  async with aiosqlite.connect(db_file) as conn:
    async with conn.execute("SELECT firstname, lastname FROM users WHERE id = ?", (user_id,)) as cursor:
      result = await cursor.fetchone()
  return result if result is not None else None

async def set_name_by_id(user_id, firstname, lastname):
  async with aiosqlite.connect(db_file) as conn:
    async with conn.execute("UPDATE users SET firstname = ?, lastname = ? WHERE id = ?", (firstname, lastname, user_id)) as cursor:
      pass
    await conn.commit()

async def get_username_by_id(user_id):
  async with aiosqlite.connect(db_file) as conn:
    async with conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)) as cursor:
      result = await cursor.fetchone()
  return result[0] if result is not None else None

async def set_username_by_id(user_id, username):
  async with aiosqlite.connect(db_file) as conn:
    async with conn.execute("UPDATE users SET username = ? WHERE id = ?", (username, user_id)) as cursor:
      pass
    await conn.commit()

async def get_all_users_with_notifications():
    users = []
    async with aiosqlite.connect(db_file) as conn:
        async with conn.execute("SELECT id FROM users WHERE notifications = 1") as cursor:
            result = await cursor.fetchall()
    for user in result:
        users.append(user[0])
    return users

async def get_user_notifications(user_id):
    async with aiosqlite.connect(db_file) as conn:
        async with conn.execute("SELECT notifications FROM users WHERE id = ?", (user_id,)) as cursor:
            result = await cursor.fetchone()
    return True if result[0] == 1 else False


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