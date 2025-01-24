import asyncio
import datetime
from app.database.requests.media import add_media
from app.database.requests.user import add_user, get_user_by_id, update_user, get_users, get_users_with_notifications, get_users_with_role
from app.database.requests.homework import add_homework, get_homeworks_by_date, get_homework_by_id, del_homework, update_homework, get_homeworks_by_subject, reset_homework_deadline_by_id
from app.database.requests.other import sync_sequences
from app.database.requests.schedule import add_subject, get_schedule_by_week
from app.database.core import create_tables
from app.browser_driver import driver
from rich import print
import sqlite3

from utils.groups_parser import parse_groups_and_add_to_db





def get_users_from_sqlite():
    conn = sqlite3.connect("Database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    data = cursor.fetchall()
    conn.close()
    return data

def get_homeworks_from_sqlite():
    conn = sqlite3.connect("Database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM homeworks")
    data = cursor.fetchall()
    conn.close()
    return data

def get_schedule_from_sqlite():
    conn = sqlite3.connect("Database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM schedule")
    data = cursor.fetchall()
    conn.close()
    return data

def get_media_from_sqlite():
    conn = sqlite3.connect("Database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM media")
    data = cursor.fetchall()
    conn.close()
    return data

async def main():
  await create_tables(drop_tables=True)
  users = get_users_from_sqlite()
  
  print("Adding users...", end="")
  for user in users:
     await add_user(user[0], user[1], user[2], user[4], user[5], user[3])
  print(" | Done.")

  homeworks = get_homeworks_from_sqlite()
  print("Adding homeworks...", end="")
  for homework in homeworks:
    await add_homework(homework[2], homework[3], 1, 1, homework[1], to_date_ts=homework[4], uid=homework[0])
    # ! GROUP ID TEMPORARY IS 1
  print(" | Done.")

  schedule = get_schedule_from_sqlite()
  print("Adding schedule...", end="")
  for schedule in schedule:
    await add_subject(schedule[1], schedule[2], schedule[3], 313)
  print(" | Done.")
  
  media = get_media_from_sqlite()
  print("Adding media...", end="")
  for media in media:
    await add_media(media[0], media[1], media[2])
  print(" | Done.")

  print("Adding groups...", end="")
  await parse_groups_and_add_to_db(driver)
  print(" | Done.")

  print("Syncing sequences...", end="")
  await sync_sequences()
  print(" | Done.")

if __name__ == "__main__":
  asyncio.run(main())