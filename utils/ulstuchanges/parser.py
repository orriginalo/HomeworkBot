from datetime import datetime, timedelta
from rich import print
import os

# "%d.%m.%y"

def check_if_changes_to_tomorrow():
  path_to_files = "./data/changes"
  files = os.listdir(path_to_files)
  
  tomorrow_date = (datetime.today() + timedelta(days=1)).strftime("%d.%m.%y")
  
  for file in files:
    if file.endswith(".pdf"):
      file_date = file.replace("changes_", "").replace(".pdf", "")
      if file_date == tomorrow_date:
        return file
  return None
      
print(check_if_changes_to_tomorrow())