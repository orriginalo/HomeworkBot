import time
import re

from bs4 import BeautifulSoup
from app.database.requests.groups import add_group
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

import os
from dotenv import load_dotenv

load_dotenv()

firefox_options = webdriver.ChromeOptions() # for local testing
# firefox_options = webdriver.FirefoxOptions()
firefox_options.add_argument("--headless")
firefox_options.add_argument("--disable-gpu")
firefox_options.add_argument("--window-size=1920,1600")

# Логин и пароль из .env
login = os.getenv("LOGIN")
password = os.getenv("PASSWORD")

async def parse_groups_and_add_to_db():

    # driver = webdriver.Remote("http://selenium:4444/wd/hub", options=firefox_options)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=firefox_options)

    try:
        driver.get("https://lk.ulstu.ru/?q=auth/login")
        driver.find_element(By.ID, "login").send_keys(login)
        driver.find_element(By.ID, "password").send_keys(password, Keys.RETURN)
    except Exception as e:
        print("Error: ", e)

    time.sleep(1.5)
    driver.get("https://time.ulstu.ru/groups")
    time.sleep(2)
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