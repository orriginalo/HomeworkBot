from aiogram.types import FSInputFile
from app.database.models import User
from app.database.requests.group import get_group_by_id
from app.database.requests.user import get_users
from utils.log import logger
from utils.timetable.downloader import download_timetable
from app.browser_driver import driver

async def send_new_timetable(bot):
    logger.info("Sending new timetable")

    photo = FSInputFile("./data/screenshots/timetable.png")
    users_with_notifications = await get_users(User.settings["send_timetable_new_week"] == True)
    groups: set = set()
    for user in users_with_notifications:
      groups.add(await get_group_by_id(user['group_id']))

    groups = list(groups)
    download_timetable(driver=driver, groups=groups, make_screenshot=True)
    for user_id in users_with_notifications:
        await bot.send_photo(user_id, photo, caption="🔔 Новое расписание")