import requests
from bs4 import BeautifulSoup

url = "https://ulstu.ru/upload/iblock/b7e/kp6udz7ne9gpgu54q30ug3gcxaql00f1/Izmeneniya-na-09.12.24-_2_.pdf"

response = requests.get(url)
with open("./app/changes_maker/test.pdf", 'wb') as f:
    f.write(response.content)
