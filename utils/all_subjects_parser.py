from app.database.queries.group import get_all_groups
from app.database.queries.subjects import add_subject_to_subjects
from utils.group_subjects_parser import get_group_unique_subjects
from dotenv import load_dotenv
import os
from rich import print
from config import settings

load_dotenv()

login = settings.ULSTU_LOGIN
password = settings.ULSTU_PASSWORD


async def parse_all_subjects(
    driver, from_json_path: str, do_download_timetable: bool = True
):
    all_subjects = []
    groups = await get_all_groups()
    if do_download_timetable:
        driver.auth(login, password)
    for group in groups:
        group_name = group.name
        parse_timetable(
            f"./data/timetables/html/{group_name.lower()}-timetable.html",
            from_json_path,
            add_groupname_to_json=True,
            group_name=group_name,
        )
        subjects = get_group_unique_subjects(
            group_name, "./data/timetables/all-timetables.json"
        )
        for subject in subjects:
            if subject not in all_subjects:
                all_subjects.append(subject)

    all_subjects.sort()
    for subject in all_subjects:
        await add_subject_to_subjects(subject)
