import re

from app.database.queries.group import add_group
from selenium.webdriver.support import expected_conditions as EC

from dotenv import load_dotenv
from app.requests.utils import fetch_all_groups
from config import settings

load_dotenv()

# Логин и пароль из .env
login = settings.ULSTU_LOGIN
password = settings.ULSTU_PASSWORD

async def parse_groups_and_add_to_db():
    groups_list: list[str] = await fetch_all_groups()

    for group in groups_list:
        try:
          match = re.search(r'\d', group)
          course: str = None
          if match:
            course: str = match.group()
          await add_group(group.lower(), int(course))
        except Exception as e:
          print("Error adding group: ", group, "| Error: ", e)

    return groups_list