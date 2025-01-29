from app.database.models import User
from app.database.requests.group import get_group_by_id
from app.database.requests.user import get_users
from utils.timetable.downloader import download_timetable
from utils.ulstuchanges.downloader import download_pdf
from utils.ulstuchanges.parser import check_if_changes_to_tomorrow
from utils.log import logger
from aiogram.types import FSInputFile
from app.browser_driver import driver
from aiogram import Bot

async def send_changes(bot: Bot):
    logger.info("Sending changes to users")

    users_with_setting = get_users(User.settings["send_changes_updated"] == True)
    for user_id in users_with_setting:
        await bot.send_message(user_id, caption=
                               f"""
                               🔔 Появились изменения на завтрашний день.
                               """
                               )
        # await bot.send_photo(user_id, photo, caption="Появились изменения на завтрашний день.")


def download_and_check():
    download_pdf()
    is_exists = check_if_changes_to_tomorrow()
    if is_exists:
        print(f"Changes for tomorrow found: {is_exists}")
    else:
        print("No changes for tomorrow")