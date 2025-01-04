import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from rich import print
import json
from dotenv import load_dotenv
import os

load_dotenv()

firefox_options = webdriver.FirefoxOptions()
firefox_options.add_argument("--headless")  # Чтобы браузер работал без UI
firefox_options.add_argument("--disable-gpu")

# Логин и пароль из .env
username = os.getenv("LOGIN")
password = os.getenv("PASSWORD")

# Настройки для Chrome

def download_timetable():

    driver = webdriver.Remote("http://selenium:4444/wd/hub", options=firefox_options)

    try:
        # Открываем страницу для логина
        driver.get("https://lk.ulstu.ru/?q=auth/login")
        
        # Ждём загрузки страницы
        time.sleep(2)
        
        # Находим элементы логина и пароля
        username_input = driver.find_element(By.NAME, "login")  # Название поля логина
        password_input = driver.find_element(By.NAME, "password")  # Название поля пароля
        
        # Вводим логин и пароль
        username_input.send_keys(username)
        password_input.send_keys(password)
        
        # Отправляем форму
        password_input.send_keys(Keys.RETURN)
        
        # Ждём, пока сайт авторизует пользователя
        time.sleep(1)  # Увеличьте время, если авторизация занимает больше времени
        
        # Открываем страницу с расписанием
        driver.get("https://time.ulstu.ru/timetable?filter=%D0%9F%D0%B4%D0%BE-16")
        
        # Ждём загрузки страницы с расписанием
        time.sleep(2)
        
        # Получаем HTML-код страницы
        page_html = driver.page_source
        
        # Сохраняем HTML в файл
        with open("./data/timetables/timetable.html", "w", encoding="utf-8") as file:
            file.write(page_html)

        print("HTML успешно сохранён!")

    finally:
        # Закрываем драйвер
        driver.quit()

download_timetable()