from utils.log import logger
import json
from utils.timetable.subjects_process import process_subject_name
from variables import prefixes_map, subjects_map


def get_group_unique_subjects(timetable: dict):
    group_subjects = []
    for group, week in timetable.items():
        for week_num, day in week.items():
            for day_timestamp, pairs in day.items():
                for pair, variants in pairs.items():
                    for variant_num, pair_info in variants.items():
                        group_subjects.append(
                            process_subject_name(
                                pair_info["subject"], subjects_map=subjects_map, prefixes_map=prefixes_map
                            )
                        )

    group_subjects.sort()
    return group_subjects
