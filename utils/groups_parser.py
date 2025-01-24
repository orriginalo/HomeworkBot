import re

from bs4 import BeautifulSoup
from app.database.requests.groups import add_group
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import os
from dotenv import load_dotenv

load_dotenv()

# Логин и пароль из .env
login = os.getenv("LOGIN")
password = os.getenv("PASSWORD")

async def parse_groups_and_add_to_db(driver):
    driver.get("https://time.ulstu.ru/groups")
    element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "/html/body/div/div/div/div[2]/div/div[2]"))
    )
    soup = BeautifulSoup(driver.page_source, "lxml")
    groups_container = soup.find("div", class_="container-fluid")
    groups_list = [group.strip() for group in groups_container.text.split("\n") if group.strip()]
    driver.close()

    for group in groups_list:
        try:
          match = re.search(r'\d', group)
          course = None
          if match:
            course = match.group() 
          await add_group(group, int(course))
        except Exception as e:
          print("Error adding group: ", group, "| Error: ", e)

    return groups_list