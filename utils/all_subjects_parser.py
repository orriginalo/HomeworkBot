from app.database.models import Groups
from app.database.requests.groups import get_all_groups, update_group
from utils.group_subjects_parser import get_group_unique_subjects
from utils.timetable_downloader import download_timetable
from app.browser_driver import driver
from utils.timetable_parser import parse_timetable

subjects = []

async def parse_all_subjects():
  groups = await get_all_groups()
  download_timetable(driver, [group["name"] for group in groups])
  for group in groups:
    group_name = group["name"]
    parse_timetable(f"./data/timetables/{group_name.lower()}-timetable.html", f"./data/timetables/all-timetables.json", add_groupname_to_json=True, group_name=group_name)
    subjects = get_group_unique_subjects(group_name)
    await update_group(group["uid"], subjects=subjects)