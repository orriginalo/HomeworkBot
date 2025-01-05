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
firefox_options.add_argument("--window-size=1920,1080")

# Логин и пароль из .env
login = os.getenv("LOGIN")
password = os.getenv("PASSWORD")
group = "Пдо-16"
# Настройки для Chrome

def download_timetable(make_screenshot=False, dst="./data/timetables/timetable.html"):

    driver = webdriver.Remote("http://selenium:4444/wd/hub", options=firefox_options)
    # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=firefox_options) # for local testing

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
        
        page_html = driver.page_source
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
        
            screenshot_path = "./data/screenshots/timetable.png" 
            driver.save_screenshot(screenshot_path)
            # print(f"Скриншот сохранён: {screenshot_path}")
            
            image = Image.open(screenshot_path)
            cropped_image = image.crop(crop_box)  # Обрезаем изображение
            cropped_image.save(screenshot_path)
            # print(f"Обрезанный скриншот сохранён: {screenshot_path}")
        # Получаем HTML-код страницы

        # Сохраняем HTML в файл
        with open("./data/timetables/timetable.html", "w", encoding="utf-8") as file:
            file.write(page_html)

        print("HTML successfully saved!")

    finally:
        # Закрываем драйвер
        driver.quit()

# download_timetable()