from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from datetime import datetime, timedelta

from app.database.queries.homework import get_homeworks_by_date, update_homework_dates
from app.database.queries.media import get_media_by_id
from app.database.queries.user import get_user_by_id
from app.services.utils import send_media


import variables as var


async def send_hw_by_date(message: Message, date: datetime, state: FSMContext):
    user = await get_user_by_id(message.from_user.id)

    sent_message = await message.answer(f"⏳ Обновляю информацию...")
    await update_homework_dates()

    date = date.replace(hour=0, minute=0, second=0, microsecond=0)
    homeworks = await get_homeworks_by_date(date, group_id=user.group.uid)
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    after_tomorrow = today + timedelta(days=2)

    day_text = None
    match date:
        case _ if date == today:
            day_text = "сегодня"
        case _ if date == tomorrow:
            day_text = "завтра"
        case _ if date == after_tomorrow:
            day_text = "послезавтра"

    if homeworks is None or len(homeworks) == 0:
        await sent_message.edit_text(f"📭 <b>Заданий на {day_text} нет!</b>", parse_mode="HTML")
    else:
        await sent_message.edit_text(f"Домашнее задание на <b>{await var.get_day_month(date)}</b>:", parse_mode="html")
        for homework in homeworks:
            media = await get_media_by_id(homework.uid)
            if media:
                await send_media(
                    message.chat.id,
                    message.bot,
                    media,
                    f"<b>{homework.subject}</b>"
                    + (
                        f' <span class="tg-spoiler">id {homework.uid}</span>'
                        if user.settings["change_ids_visibility"] == True
                        else ""
                    )
                    + f"\n\n{str(homework.task)}",
                    parse_mode="html",
                )
            else:
                await message.answer(
                    f"<b>{homework.subject}</b>"
                    + (
                        f' <span class="tg-spoiler">id {homework.uid}</span>'
                        if user.settings["change_ids_visibility"] == True
                        else ""
                    )
                    + f"\n\n{homework.task}",
                    parse_mode="html",
                )
        await state.clear()
