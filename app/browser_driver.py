from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

class Driver:
    def __init__(self, headless=True, remote=False):
        
        browser_options = None

        if remote:
          browser_options = webdriver.FirefoxOptions()
        else:
          browser_options = webdriver.ChromeOptions()
        
        if headless:
          browser_options.add_argument("--headless")
        browser_options.add_argument("--disable-gpu")
        browser_options.add_argument("--window-size=1920,1600")
        browser_options.add_argument("--no-sandbox")
        browser_options.add_argument("--disable-dev-shm-usage")

        # Инициализируем драйвер один раз при создании объекта
        self._driver = None
        if remote:
          self._driver = webdriver.Remote("http://selenium:4444/wd/hub", options=browser_options)
        else:
          self._driver = webdriver.Chrome(
              service=Service(ChromeDriverManager().install()),
              options=browser_options
          )
        self._wait = WebDriverWait(self._driver, 10)

    @property
    def driver(self):
        return self._driver
    
    def __getattr__(self, name):
      return getattr(self._driver, name)
    
    def auth(self, login: str, password: str) -> bool:
        try:
            self.driver.get("https://lk.ulstu.ru/?q=auth/login")
            
            # Явное ожидание вместо time.sleep
            login_field = self._wait.until(
                EC.presence_of_element_located((By.NAME, "login"))
            )
            password_field = self.driver.find_element(By.NAME, "password")

            login_field.send_keys(login)
            password_field.send_keys(password)
            password_field.send_keys(Keys.RETURN)

            # Проверка успешной авторизации
            self._wait.until(
                lambda d: d.current_url != "https://lk.ulstu.ru/?q=auth/login"
            )
            
            # Дополнительная проверка на наличие элемента личного кабинета
            self._wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".user-menu"))
            )
            return True
            
        except Exception as e:
            print(f"Authentication failed: {str(e)}")
            return False
        finally:
            # Не закрываем браузер здесь, чтобы можно было работать с ним после авторизации
            time.sleep(1)  # Краткая пауза для стабилизации

    def quit(self):
        """Закрыть браузер и завершить сессию"""
        if self._driver:
            self._driver.quit()

driver = Driver(headless=True, remote=True)