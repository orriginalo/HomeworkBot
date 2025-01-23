import logging
import json
from utils.timetable_parser import process_subject_name
from variables import prefixes_map, subjects_map

def get_group_unique_subjects(group: str):
    try:
      with open(f"./data/timetables/timetables.json", "r", encoding="utf-8") as file:
        timetable = json.load(file)
    except Exception as e:
      logging.error(f"Error reading timetables.json file: {e}")
      return []
    
    try:
      group_subjects = []
      for week, days in timetable[group].items():
        for date, lessons in days.items():
          for pair_number, subject in lessons.items():
            pr_subject = process_subject_name(subject, subjects_map=subjects_map, prefixes_map=prefixes_map)
            if subject != "-" and pr_subject not in group_subjects:
              group_subjects.append(pr_subject)
    except Exception as e:
      logging.error(f"Error parsing timetables.json file: {e}")
      return []
    
    group_subjects.sort()
    return group_subjects