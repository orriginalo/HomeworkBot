from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.database.requests import log
from other_scripts.timetable_downloader import download_timetable
from other_scripts.timetable_parser import parse_timetable
from other_scripts.db_subject_populator import populate_schedule
import shutil
import datetime
import os

scheduler1 = AsyncIOScheduler()
scheduler2 = AsyncIOScheduler()

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
  print("Starting downloading the timetable...")
  download_timetable()
  print("Downloading Ended")
  print("Parsing Started")
  parse_timetable("./data/timetables/timetable.html", "./data/timetables/timetables.json")
  print("Parsing Ended")
  print("Populating Started")
  populate_schedule()
  print("Populating Ended")
  

async def schedule_backup():
  try:
    scheduler1.add_job(create_backups, 'interval', hours=1)
    print("Scheduler backups added")
    scheduler1.start()
  except Exception:
    await log("Database backuping ERROR", "BACKUP")

async def timetable_get():
  try:
    scheduler2.add_job(download_timetable_job, 'interval', seconds=30)
    await download_timetable_job()
    scheduler2.start()
  except Exception as e:
    print("Error: "+str(e))
    log("Timetable downloading ERROR", "BACKUP")

    


