from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.database.requests import log
from other_scripts.timetable_downloader import download_timetable
from other_scripts.timetable_parser import parse_timetable
import shutil
import datetime
import os

scheduler = AsyncIOScheduler()

def create_db_backup():

  all_backup_files = os.listdir("./data/backups/databases")
  all_backup_files.sort()

  if len(all_backup_files) > 6:
    os.remove(f"./data/backups/databases/{all_backup_files[0]}")

  source_file = 'Database.db'  # Путь к файлу для резервного копирования
  backup_dir = './data/backups/databases'  # Путь к директории для сохранения резервной копии
  
  # Создаем имя для резервной копии с текущей датой и временем
  backup_name = f'backup_Database_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
  backup_path = os.path.join(backup_dir, backup_name)

  # Копируем файл
  shutil.copy2(source_file, backup_path)
  
  return backup_path

def create_html_backup():
  for file in os.listdir("./"):
    if file.endswith(".html"):
      shutil.copy2(file, "./data/backups/html_schedules")
  
# @scheduler.add_job("interval", seconds = 1)
async def create_backups():
  await log("Database backuped", "BACKUP")
  create_db_backup()
  create_html_backup()

async def download_timetable_job():
  download_timetable()
  await log("Timetable downloaded", "BACKUP")
  parse_timetable("./data/timetables/timetable.html", "./data/timetables/timetables.json")
  await log("Timetable parsed", "BACKUP")

async def schedule_backup():
  try:
    scheduler.add_job(create_backups, 'interval', hours=1)
    print("Scheduler backups added")
    scheduler.add_job(download_timetable_job, 'interval', hours=12)
    print("Scheduler timetable added")
    download_timetable_job()
    scheduler.start()
  except Exception:
    log("Database backuping ERROR", "BACKUP")
    


