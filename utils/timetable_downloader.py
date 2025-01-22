import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image

from rich import print
import json
from dotenv import load_dotenv
import os

load_dotenv()

# firefox_options = webdriver.ChromeOptions() # for local testing
firefox_options = webdriver.FirefoxOptions()
firefox_options.add_argument("--headless")  # Чтобы браузер работал без UI
firefox_options.add_argument("--disable-gpu")
firefox_options.add_argument("--window-size=1920,1600")

# Логин и пароль из .env
login = os.getenv("LOGIN")
password = os.getenv("PASSWORD")
# group = "Пдо-16"
# Настройки для Chrome

def download_timetable(group: str, make_screenshot: bool = False): # new

    driver = webdriver.Remote("http://selenium:4444/wd/hub", options=firefox_options) 
    # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=firefox_options)

    try:
        # Открываем страницу для логина
        driver.get("https://lk.ulstu.ru/?q=auth/login")
        
        # Ждём загрузки страницы
        time.sleep(2)
        
        # Находим элементы логина и пароля
        username_input = driver.find_element(By.NAME, "login")
        password_input = driver.find_element(By.NAME, "password")
        
        # Вводим логин и пароль
        username_input.send_keys(login)
        password_input.send_keys(password)
        
        # Отправляем форму
        password_input.send_keys(Keys.RETURN)
        
        # Ждём, пока сайт авторизует пользователя
        time.sleep(3)
        
        # Открываем страницу с расписанием
        driver.get(f"https://time.ulstu.ru/timetable?filter={group.lower()}")
        
        # Ждём загрузки страницы с расписанием
        time.sleep(3)
        
        crop_box=(370, 50, 1530, 800)
        # Убираем ненужные элементы с помощью JavaScript для того чтобы скриншот вмещал в себя все нужное
        if make_screenshot:
            driver.execute_script("""
                // Удаляем Header
                const header = document.querySelector('nav.navbar');
                if (header) header.remove();

                const layoutSelector = document.querySelector('.layout-panel');
                if (layoutSelector) layoutSelector.remove();

                // Удаляем поле для ввода группы
                const inputGroup = document.querySelector('.input-group');
                if (inputGroup) inputGroup.remove();

                // Удаляем надпись текущей недели
                const currentWeek = document.querySelector('.week');
                if (currentWeek) currentWeek.remove();

                // Удаляем первое расписание, если их два
                const weekNums = document.querySelectorAll('.week-num');
                if (weekNums.length > 1) {
                    weekNums[0].parentElement.remove();
                }
            """)
        
            week_num_element = driver.find_element(By.CLASS_NAME, "week-num")
    
    # Получаем родительский контейнер
            parent_container = week_num_element.find_element(By.XPATH, "./..")  # Поднимаемся на уровень выше в DOM

            rect: dict = parent_container.rect

            driver.execute_script("arguments[0].scrollIntoView();", parent_container)
            
            screenshot_path = f"./data/screenshots/{group.lower()}.png"
            driver.save_screenshot(screenshot_path)
            print(f"Скриншот сохранён: {screenshot_path}")
            
            margin = 35

            crop_box = (
                max(0, int(rect['x']) - margin),  # left с учётом отступа
                max(0, int(rect['y']) - margin - 65),  # top с учётом отступа
                int(rect['x'] + rect['width'] + margin),  # right с учётом отступа
                int(rect['y'] + rect['height'] + margin - 40)  # bottom с учётом отступа
            )
            print(f"Обрезка по координатам: {crop_box}")
            print(crop_box)
            image = Image.open(screenshot_path)
            cropped_image = image.crop(crop_box)
            cropped_image.save(screenshot_path)
            print(f"Обрезанный скриншот сохранён: {screenshot_path}")

        # Получаем HTML-код страницы
        page_html = driver.page_source
        
        # Сохраняем HTML в файл
        with open(f"./data/timetables/{group.lower()}-timetable.html", "w", encoding="utf-8") as file:
            file.write(page_html)
        print("HTML успешно сохранён!")

    finally:
        driver.quit()
