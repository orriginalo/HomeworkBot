from app.database.models import Groups, Homework
from app.database.queries.group import update_group, get_group_by_name
from app.database.queries.homework import get_homeworks
from app.browser_driver import driver
from utils.log import logger
from utils.timetable.downloader import download_timetable
from utils.timetable.parser import parse_timetable
from utils.db_subject_populator import populate_schedule
from utils.group_subjects_parser import get_group_unique_subjects
from app.database.queries.group import get_all_groups
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
