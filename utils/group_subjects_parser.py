from utils.log import logger
import json
from utils.timetable_parser import process_subject_name
from variables import prefixes_map, subjects_map

def get_group_unique_subjects(group_name: str, from_json_path: str):
    try:
      with open(from_json_path, "r", encoding="utf-8") as file:
        timetable = json.load(file)
    except Exception as e:
      logger.error(f"Error reading timetables.json file: {e}")
      return []
    
    group_subjects = []
    try:
      # for group, weeks in timetable[group_name].items():
      for week, days in timetable[group_name].items():
        for timestamp, lessons in days.items():
          for pair_number, subject in lessons.items():
            if subject != "-" and subject not in group_subjects:
              group_subjects.append(process_subject_name(subject, subjects_map=subjects_map, prefixes_map=prefixes_map))

    except Exception as e:
      logger.error(f"Error parsing timetables.json file: {e}")
      return []
    
    group_subjects.sort()
    return group_subjects