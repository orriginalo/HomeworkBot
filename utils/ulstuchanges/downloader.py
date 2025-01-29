from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import re
from utils.log import logger

# "%d.%m.%y"

def get_changes_date(url: str):
    url = "https://ulstu.ru/upload/iblock/786/6x40enpeds67iiqvvybiqb265g93gs5s/Izmeneniya-na-29.01.25.pdf"

    file_name = url.split('/')[-1]

    date_match = re.search(r'\d{2}\.\d{2}\.\d{2}', file_name)

    if date_match:
        date = date_match.group(0)
        return date
    else:
        logger.debug(f"Date not found in the file name: {file_name}")
        return None

def get_pdf_url():
    url = "https://ulstu.ru/education/kei/student/schedule/"

    logger.debug(f"Getting a page with URL: {url}")
    response = requests.get(url)
    if response.status_code != 200:
        logger.error(f"It was not possible to get a page. Status code: {response.status_code}")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')

    scripts = soup.find_all('script', type='application/javascript')
    for script in scripts:
        script_content = script.string
        if script_content and "PDFStart" in script_content:
            match = re.search(r"PDFStart\(['\"]([^'\"]+)['\"]\)", script_content)
            if match:
                pdf_url = match.group(1)
                full_pdf_url = requests.compat.urljoin(url, pdf_url)
                return full_pdf_url

    return None

def download_pdf():
    pdf_url = get_pdf_url()
    changes_date = get_changes_date(pdf_url)
    
    if not pdf_url:
        logger.error("PDF file not found.")
        return
    else:
        logger.debug(f"URL to the PDF file found: {pdf_url}")

    response = requests.get(pdf_url)
    if response.status_code != 200:
        logger.error(f"Failed to download the PDF file. Status code: {response.status_code}")
        return
    
    path_to_file = f"./data/changes/changes_{changes_date}.pdf"
    with open(path_to_file, 'wb') as f:
        f.write(response.content)
    logger.debug(f"PDF file is successfully saved as {path_to_file}")