from app.database.models import Groups
from app.database.requests.groups import get_all_groups, update_group
from app.database.requests.subjects import add_subject_to_subjects
from utils.group_subjects_parser import get_group_unique_subjects
from utils.timetable_downloader import download_timetable
from app.browser_driver import driver
from utils.timetable_parser import parse_timetable
from dotenv import load_dotenv
import os
from rich import print

load_dotenv()

login = os.getenv("LOGIN")
password = os.getenv("PASSWORD")

subjects = []

async def parse_all_subjects():
  groups = await get_all_groups()
  print([group["name"] for group in groups])
  driver.auth(login, password)
  download_timetable(driver, [group["name"] for group in groups])
  for group in groups:
    group_name = group["name"]
    parse_timetable(f"./data/timetables/{group_name.lower()}-timetable.html", f"./data/timetables/all-timetables.json", add_groupname_to_json=True, group_name=group_name)
    subjects = get_group_unique_subjects(group_name)
    for subject in subjects:
      if subject not in subjects:
        subjects.append(subject)
  
  for subject in subjects:
    add_subject_to_subjects(subject)