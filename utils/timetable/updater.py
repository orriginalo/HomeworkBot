from app.database.schemas import GroupSchema
from app.requests.timetable import fetch_timetable
from utils.db_subject_populator import populate_schedule
from utils.group_subjects_parser import get_group_unique_subjects
from utils.log import logger

from app.database.models import Groups, Homework
from app.database.queries.homework import get_homeworks
from app.database.queries.group import get_all_groups, get_group_by_name, update_group


async def update_timetable(for_all: bool = True, group_name: str = None):
    groups: list[GroupSchema] = None
    if for_all:
        groups = await get_all_groups(Groups.is_equipped == True)
        logger.info(f"Updating timetables for groups: {[group.name for group in groups]}...")
    else:
        groups = [await get_group_by_name(group_name)]
        logger.info(f"Updating timetable for one group: {group_name}...")

    if groups:
        for group in groups:
            group_name = group.name
            timetable = await fetch_timetable(group_name)
            if timetable:
                necessary_subjects = await get_homeworks(Homework.group_uid == group.uid)
                necessary_subjects = [homework.subject for homework in necessary_subjects]
                necessary_subjects = set(necessary_subjects)
                group_subjects = get_group_unique_subjects(timetable)
                for subject in group_subjects:
                    if subject not in necessary_subjects:
                        necessary_subjects.add(subject)
                    else:
                        pass

                necessary_subjects = list(necessary_subjects)
                necessary_subjects.sort()
                if len(necessary_subjects) <= 0:
                    raise Exception("No subjects found in timetable")
                await update_group(group.uid, subjects=necessary_subjects)

                await populate_schedule(timetable)
    else:
        logger.error(f"Error updating timetable for groups: {[group.name for group in groups]}...")
