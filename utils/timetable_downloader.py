import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image

from rich import print
import json
from dotenv import load_dotenv
import os

load_dotenv()

login = os.getenv("LOGIN")
password = os.getenv("PASSWORD")

def download_timetable(driver, groups: list[str], make_screenshot: bool = False): # new
    try:
        for group in groups:
            # Открываем страницу с расписанием
            print(f"https://time.ulstu.ru/timetable?filter={group.lower()}")
            driver.get(f"https://time.ulstu.ru/timetable?filter={group.lower()}")
            
            # Ждём загрузки страницы с расписанием
            
            crop_box=(370, 50, 1530, 800)
            
            try:
                parent_container = WebDriverWait(driver, 2).until(
                    EC.visibility_of_all_elements_located((By.XPATH, "/html/body/div/div/div/div[2]/div/div[3]"))
                )
            except:
                pass

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

            # Сохраняем HTML в файл
            with open(f"./data/timetables/{group.lower()}-timetable.html", "w", encoding="utf-8") as file:
                file.write(page_html)
            print("HTML успешно сохранён!")

    except Exception as e:
        logging.error(f"Error downloading timetable for group {group}: {str(e)}")

