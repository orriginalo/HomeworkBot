from datetime import datetime, timedelta
from rich import print
import os

# "%d.%m.%y"

def check_downloaded_changes():
  path_to_files = "./data/changes"
  files = os.listdir(path_to_files)
  
  # today_date = datetime.today().strftime("%d.%m.%y")
  tomorrow_date = (datetime.today() + timedelta(days=1)).strftime("%d.%m.%y")
  
  for file in files:
    if file.endswith(".pdf"):
      file_date = file.replace("changes_", "").replace(".pdf", "")
      if file_date == tomorrow_date:
        return file
  return None
      
print(check_downloaded_changes())