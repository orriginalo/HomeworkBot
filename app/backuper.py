from app.database.models import Groups, Homework
from app.database.requests.groups import update_group, get_group_by_name
from app.database.requests.homework import get_homeworks
from app.browser_driver import driver
from utils.logger import logger
from utils.timetable_downloader import download_timetable
from utils.timetable_parser import parse_timetable
from utils.db_subject_populator import populate_schedule
from utils.group_subjects_parser import get_group_unique_subjects
from app.database.requests.groups import get_all_groups
import shutil
import datetime
import os

def create_db_backup():

  all_backup_files = os.listdir("./data/backups/databases")
  all_backup_files.sort()

  if len(all_backup_files) > 48:
    os.remove(f"./data/backups/databases/{all_backup_files[0]}")

  source_file = 'Database.db'  # Путь к файлу для резервного копирования
  backup_dir = './data/backups/databases'  # Путь к директории для сохранения резервной копии
  
  # Создаем имя для резервной копии с текущей датой и временем
  backup_name = f'backup_Database_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
  backup_path = os.path.join(backup_dir, backup_name)

  # Копируем файл
  shutil.copy2(source_file, backup_path)
  
  return backup_path
  
# @scheduler.add_job("interval", seconds = 1)
async def create_backups():
  logger.info("Database backuped")
  create_db_backup()

async def update_timetable_job():
  groups = await get_all_groups(Groups.is_equipped == True)
  download_timetable(driver, [group["name"] for group in groups])
  for group in groups:
    group_name = group["name"]
    parse_timetable(f"./data/timetables/html/{group_name.lower()}-timetable.html", "./data/timetables/timetables.json", add_groupname_to_json=True, group_name=group_name)
    necessary_subjects = await get_homeworks(Homework.group_id == group["uid"])
    necessary_subjects = [homework["subject"] for homework in necessary_subjects]
    necessary_subjects = set(necessary_subjects)
    print(necessary_subjects)
    group_subjects = get_group_unique_subjects(group_name, "./data/timetables/timetables.json")
    print(group_subjects)
    for subject in group_subjects:
      print(subject, end=" ")
      if subject not in necessary_subjects:
        print("| Added")
        necessary_subjects.add(subject)
      else:
        print("| Already added")
  
    necessary_subjects = list(necessary_subjects)
    necessary_subjects.sort()
    await update_group(group["uid"], subjects=necessary_subjects)

  await populate_schedule()