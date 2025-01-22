from app.database.models import Groups
from app.database.requests.other import log
from utils.timetable_downloader import download_timetable
from utils.timetable_parser import parse_timetable
from utils.db_subject_populator import populate_schedule
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
  await log("Database backuped", "BACKUP")
  create_db_backup()

async def download_timetable_job():
  groups = get_all_groups(Groups.is_equipped == True)
  groups = [group["name"] for group in groups]
  for group in groups:
    download_timetable(group)
    parse_timetable(f"./data/timetables/{group.lower()}-timetable.html", f"./data/timetables/timetables.json")
  await populate_schedule()