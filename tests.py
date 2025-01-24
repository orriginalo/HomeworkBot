import asyncio
from app.database.requests.groups import *
from app.database.requests.media import *
from app.database.requests.user import *
from app.database.requests.homework import *
from app.database.requests.schedule import *
from app.browser_driver import driver
from utils.groups_parser import parse_groups_and_add_to_db
from utils.db_subject_populator import populate_schedule
from rich import print

from app.database.core import create_tables

async def tests():
  
  # await populate_schedule()

  print("USERS")
  # print(await get_user_by_id(1522039516)) # WORKING
 
  # print(await get_users_with_notifications()) # WORKING

  # print(await get_users_with_role(2)) # WORKING

  # print(await get_users()) # WORKING

  print("HOMEWORKS")

  # print("get_homeworks_by_date")
  # print(await get_homeworks_by_date(1734465600)) # WORKING

  # print("get_homework_by_id")
  # print(await get_homework_by_id(1)) # WORKING

  # print("get_homeworks_by_subject")
  # print(await get_homeworks_by_subject("Математика")) # WORKING

  # print("del_homework")
  # print(await del_homework(6)) # WORKING

  # print("update_homework") 
  # print(await update_homework(3, subject="test", task="test")) # WORKING

  # print(await reset_homework_deadline_by_id(1)) #

  # print("add_homework")
  # print(await add_homework("subjectt", "task", 1, 1, 1677721600)) # WORKING

  print("SCHEDULE")

  # print("get_schedule_by_week")
  # print(await get_schedule_by_week(20)) # WORKING

  # print(await add_subject(1677721600, "test", 1)) # WORKING

  print("MEDIA")
  # print(await add_media(1, "test", "test")) # WORKING

  # print("get_media_by_id")
  # print(await get_media_by_id(39))

  print("GROUPS")

  # print(await get_all_groups())

  # group = await get_group_by_name("пдо-16")
  # print(group["subjects"])

async def main():
  await create_tables(drop_tables=True)
  await parse_groups_and_add_to_db(driver)

if __name__ == "__main__":
  # asyncio.run(tests())
  asyncio.run(main())