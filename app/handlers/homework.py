import aiogram
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import (
    Message,
    CallbackQuery,
    InputMediaPhoto,
    InputMediaVideo,
    InputMediaDocument,
    InputMedia,
    InputMediaAudio,
    ContentType as CT,
)
from aiogram.fsm.context import FSMContext

import app.keyboards as kb
from app.database.queries.group import get_group_by_id
from app.database.queries.homework import (
    add_homework,
    del_homework,
    get_homework_by_id,
    get_homeworks_by_date,
    get_homeworks_by_subject,
    reset_homework_deadline_by_id,
    update_homework_dates,
)
from app.database.queries.media import add_media, del_media, get_media_by_id
from app.database.queries.subjects import get_subject_by_id
from app.database.models import User
from app.database.queries.user import get_user_by_id, get_users
from app.middlewares import AlbumMiddleware, GroupChecker, MsgLoggerMiddleware

from datetime import datetime, timedelta

from app.services.utils import send_media
import variables as var

from app.services.homework import send_hw_by_date


class resetting_deadline(StatesGroup):
    hw_id = State()


class view_homework(StatesGroup):
    day = State()
    with_date = State()


class removing_homework(StatesGroup):
    hw_id = State()


class adding_homework(StatesGroup):
    subject = State()
    task = State()
    media_group = State()
    media_ids = State()
    media_types = State()


router = Router(name="Homework")

router.message.middleware(MsgLoggerMiddleware())
router.callback_query.middleware(MsgLoggerMiddleware())
router.message.middleware(AlbumMiddleware())
router.message.filter(GroupChecker())


@router.callback_query(F.data == "change_subject")
async def change_subject(call: CallbackQuery, state: FSMContext):
    user = await get_user_by_id(call.from_user.id)
    await state.set_state(adding_homework.subject)
    await call.message.delete()
    subjects = (await get_group_by_id(user.group.uid)).subjects
    await call.message.answer("🔄 Выберите предмет:", reply_markup=await kb.allowed_subjects_change_keyboard(subjects))


@router.callback_query(F.data == "change_task")
async def change_task(call: CallbackQuery, state: FSMContext):
    await state.set_state(adding_homework.task)
    await state.update_data(task=None)
    await call.message.delete()
    await call.message.answer("🔄 Введите домашнее задание:", reply_markup=ReplyKeyboardRemove())


@router.callback_query(F.data == "all_right")
async def add_homework_to_db(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    subject = data.get("subject")
    task = data.get("task")
    media = data.get("media_group")
    user = await get_user_by_id(call.from_user.id)

    homework = await add_homework(subject, task, user.group.uid, call.from_user.id, var.calculate_today()[1])

    if media:
        for media in data.get("media_group"):
            await add_media(homework.uid, media.media, media.type)

    await call.message.answer(
        f"✅ <b>Домашнее задание добавлено.</b>", parse_mode="html", reply_markup=await kb.get_start_keyboard(user)
    )  # в базу
    await call.message.delete()
    admins = await get_users(User.role == 4, User.group_uid == user.group.uid)
    admins += await get_users(User.role == 3, User.group_uid == user.group.uid)

    for admin in admins:
        if admin.tg_id != call.from_user.id:
            if media:
                await send_media(
                    admin.tg_id,
                    call.message.bot,
                    media,
                    f"🔔 Добавлено домашнее задание.\n*{subject}*:\n\n{task}\n\nОт [{call.from_user.id}](tg://user?id={call.from_user.id}) *\nid задания - {homework.uid}*",
                    parse_mode="Markdown",
                )
            else:
                await call.bot.send_message(
                    admin.tg_id,
                    f"🔔 Добавлено домашнее задание по\n*{subject}*:\n\n{task}\n\nОт [{call.from_user.id}](tg://user?id={call.from_user.id}) *\nid задания - {homework.id}*",
                    parse_mode="Markdown",
                )

    await state.clear()


@router.callback_query(F.data.contains("-changed"))
async def _(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    subject = await get_subject_by_id(int(call.data.replace("-changed", "")))
    await state.update_data(subject=subject.name)
    await call.message.answer(f"Предмет был изменен на <b>{subject.name}</b>.", parse_mode="html")
    data = await state.get_data()

    task = data.get("task")
    subject = data.get("subject")

    if data.get("media_group") is not None:
        media_group = data.get("media_group")
    else:
        media_group = None

    try:
        if subject is not None and task is not None:
            if media_group:
                await call.message.answer_media_group(media_group)
                await call.message.answer(
                    f"<b>{subject}.</b>\n\n{task}\n\n\nВсё верно?",
                    parse_mode="html",
                    reply_markup=kb.check_hw_before_apply_keyboard,
                )
            else:
                await call.message.answer(
                    f"<b>{subject}.</b>\n\n{task}\n\n\nВсё верно?",
                    parse_mode="html",
                    reply_markup=kb.check_hw_before_apply_keyboard,
                )
    except aiogram.exceptions.TelegramBadRequest:
        await call.message.answer("Произошла ошибка. Попробуйте снова.")


@router.message(F.text.lower().contains("посмотреть д/з"))
async def _(message: Message, state: FSMContext):
    await state.set_state(view_homework.day)
    await message.answer("Выбери вариант.", reply_markup=kb.see_hw_keyboard)


@router.message(F.text.lower().contains("по предмету"))
async def _(message: Message):
    user = await get_user_by_id(message.from_user.id)
    group = await get_group_by_id(user.group.uid)
    subjects = group.subjects
    await message.answer(
        "Выбери предмет по которому\nхочешь посмотреть Д/З",
        reply_markup=await kb.allowed_subjects_check_hw_keyboard(subjects),
    )


@router.callback_query(F.data.contains("-check-hw"))
async def _(call: CallbackQuery):
    user = await get_user_by_id(call.from_user.id)
    await call.message.delete()
    subject = await get_subject_by_id(int(call.data.replace("-check-hw", "")))
    homeworks: list = await get_homeworks_by_subject(
        subject.name, limit_last=True, limit_last_count=user.settings["last_homeworks_count"], group_id=user.group.uid
    )
    if homeworks is not None and len(homeworks) > 0:
        homeworks.reverse()
        await call.message.answer(f"Домашнее задание по <b>{subject.name}</b>", parse_mode="html")
        for homework in homeworks:
            text = f"""
Добавлено <b>{homework.from_date.strftime("%d.%m.%Y")}</b> {"<i>(последнее)</i>" if homework == homeworks[-1] else ""} {f'<span class="tg-spoiler">id {homework.uid}</span>' if user.settings["change_ids_visibility"] else ""}

{homework.task}
      """
            media = await get_media_by_id(homework.uid)
            if media is not None and len(media) > 0:
                await send_media(call.message.chat.id, call.message.bot, media, text, parse_mode="html")

            else:
                await call.message.answer(text, parse_mode="html")
    else:
        await call.message.answer(f"Домашнее задание по <b>{subject.name}</b> отсутствует", parse_mode="html")


@router.message(F.text.lower().contains("на сегодня"))
async def _(message: Message, state: FSMContext):
    date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    await send_hw_by_date(message, date, state)


@router.message(F.text.lower().contains("на завтра"))
async def _(message: Message, state: FSMContext):
    date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    await send_hw_by_date(message, date, state)


@router.message(F.text.lower().contains("на послезавтра"))
async def _(message: Message, state: FSMContext):
    date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=2)
    await send_hw_by_date(message, date, state)


@router.message(view_homework.day and F.text.contains("По дате"))
async def show_hw_by_date_handler(message: Message, state: FSMContext):
    await state.set_state(view_homework.with_date)
    current_month = datetime.now().month
    await message.answer(
        f'Введи дату в виде "номер_месяца число" без кавычек. Сейчас <b>{current_month}</b> месяц',
        parse_mode="html",
        reply_markup=kb.back_keyboard,
    )


@router.message(view_homework.with_date)
async def show_hw_by_date(message: Message, state: FSMContext):
    user = await get_user_by_id(message.from_user.id)
    inted_date_from_user: list = []
    try:
        inted_date_from_user = [int(num) for num in message.text.split(" ")]
    except ValueError as e:
        await message.answer('❌ Введите числа в формате "номер_месяца число". Попробуй еще раз.')
        return

    if len(inted_date_from_user) == 2:
        date_time = datetime.strptime(
            f"{inted_date_from_user[1]}/{inted_date_from_user[0]}/{var.cur_year}, 00:00:00", "%d/%m/%Y, %H:%M:%S"
        )
        date_time_timestamp = datetime.timestamp(date_time)
        homeworks = await get_homeworks_by_date(date_time_timestamp, group_id=user.group.uid)
        sent_message = await message.answer(
            f"⏳ Обновляю информацию...", reply_markup=await kb.get_start_keyboard(user)
        )
        await update_homework_dates(user.group.uid)
        if homeworks is None or len(homeworks) == 0:
            await sent_message.edit_text(f"📭 <b>Заданий на этот день нет!</b>", parse_mode="html")
            await state.clear()
        else:
            await sent_message.edit_text(
                f"Домашнее задание на <b>{datetime.fromtimestamp(date_time_timestamp).strftime("%d")} {var.months_words[int(datetime.fromtimestamp(date_time_timestamp).strftime("%m"))]}</b>:",
                parse_mode="html",
            )
            for homework in homeworks:
                text = (
                    f"<b>{homework.subject}</b>"
                    + (
                        f' <span class="tg-spoiler">id {homework.uid}</span>'
                        if user.settings["change_ids_visibility"]
                        else ""
                    )
                    + f"\n\n{homework.task}"
                )
                media = await get_media_by_id(homework.uid)
                if media:
                    await send_media(message.chat.id, message.bot, media, text, parse_mode="html")
                else:
                    await message.answer(text, parse_mode="html")
            await state.clear()
    else:
        await message.answer("❌ Неправильный формат даты. Попробуй еще раз.")
        return


@router.message(F.text.lower().contains("добавить д/з"))
async def add_hw_one(message: Message, state: FSMContext):
    user = await get_user_by_id(message.from_user.id)
    if user.role >= 2:
        await state.set_state(adding_homework.subject)
        subjects = (await get_group_by_id(user.group.uid)).subjects
        await message.answer("Выберите предмет:", reply_markup=await kb.allowed_subjects_keyboard(subjects))
        kb.ReplyKeyboardRemove(remove_keyboard=True)


@router.callback_query(F.data.contains("-add"), adding_homework.subject)
async def add_hw_two(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    subject = await get_subject_by_id(int(call.data.replace("-add", "")))

    await call.message.answer(f"Предмет <b>{subject.name}</b> выбран.", parse_mode="html")
    await state.update_data(subject=subject.name)
    await state.set_state(adding_homework.task)
    await call.message.answer(
        "✍️ Напишите домашнее задание, можно прикрепить медиа.", parse_mode="html", reply_markup=ReplyKeyboardRemove()
    )


@router.message(F.content_type.in_([CT.PHOTO, CT.VIDEO, CT.AUDIO, CT.DOCUMENT]))
@router.message(adding_homework.task)
async def add_hw_three(message: Message, state: FSMContext, album: list = None, album_caption: str = None):

    if message.content_type == "sticker":
        await message.answer("<b>Нельзя прикрепить стикер.</b>", parse_mode="html")
        return

    elif (await state.get_data()).get("task") is None:
        if album and album_caption:
            await state.update_data(task=album_caption)
        elif message.text != None:
            await state.update_data(task=message.text)
        elif message.caption != None:
            await state.update_data(task=message.caption)
        else:
            await state.update_data(task="")

    media_group = []

    data = await state.get_data()

    if album:
        for i in range(len(album)):
            if album[i].photo:
                file_id = album[i].photo[-1].file_id
                media_group.append(InputMediaPhoto(media=file_id))
            elif album[i].video:
                file_id = album[i].video.file_id
                media_group.append(InputMediaVideo(media=file_id))
            elif album[i].audio:
                file_id = album[i].audio.file_id
                media_group.append(InputMediaAudio(media=file_id))
            elif album[i].document:
                file_id = album[i].document.file_id
                media_group.append(InputMediaDocument(media=file_id))
            else:
                obj_dict = album[i].model_dump()
                file_id = obj_dict[album[i].content_type]["file_id"]
                media_group.append(InputMedia(media=file_id))

        # print(media_group)
        # await message.answer("album")
        await state.update_data(media_group=media_group)
        data = await state.get_data()
        # print(data)

    elif message.content_type in [CT.PHOTO, CT.VIDEO, CT.AUDIO, CT.DOCUMENT]:
        if message.photo:
            file_id = message.photo[-1].file_id
            media_group.append(InputMediaPhoto(media=file_id))
        elif message.video:
            file_id = message.video.file_id
            media_group.append(InputMediaVideo(media=file_id))
        elif message.audio:
            file_id = message.audio.file_id
            media_group.append(InputMediaAudio(media=file_id))
        elif message.document:
            file_id = message.document.file_id
            media_group.append(InputMediaDocument(media=file_id))

        # print(media_group)
        # await message.answer("default CT")
        await state.update_data(media_group=media_group)
        data = await state.get_data()
        # print(data)

    print(message.content_type)
    data = await state.get_data()
    subject = data.get("subject")
    task = data.get("task")

    if data.get("media_group") is not None:
        media_group = data.get("media_group")

    try:
        if data.get("subject") is not None and data.get("task") is not None:
            if album:
                await message.reply(
                    f"<b>{subject}.</b>\n\n{task}\n\n\nВсё верно?",
                    parse_mode="html",
                    reply_markup=kb.check_hw_before_apply_keyboard,
                )
            elif message.content_type in [CT.PHOTO, CT.VIDEO, CT.AUDIO, CT.DOCUMENT]:
                await message.reply(
                    f"<b>{subject}.</b>\n\n{task}\n\n\nВсё верно?",
                    parse_mode="html",
                    reply_markup=kb.check_hw_before_apply_keyboard,
                )
            elif media_group:
                await message.answer_media_group(media_group)
                await message.answer(
                    f"<b>{subject}.</b>\n\n{task}\n\n\nВсё верно?",
                    parse_mode="html",
                    reply_markup=kb.check_hw_before_apply_keyboard,
                )
            else:
                await message.answer(
                    f"<b>{subject}.</b>\n\n{task}\n\n\nВсё верно?",
                    parse_mode="html",
                    reply_markup=kb.check_hw_before_apply_keyboard,
                )
    except aiogram.exceptions.TelegramBadRequest:
        await message.answer("Произошла ошибка. Попробуйте снова.")


@router.message(F.text.lower().contains("удалить д/з"))
async def remove_hw_by_id_handler(message: Message, state: FSMContext):
    user = await get_user_by_id(message.from_user.id)
    if user.role >= 2:
        await state.set_state(removing_homework.hw_id)
        await message.answer("Введите id задания:", reply_markup=kb.back_keyboard)


@router.message(removing_homework.hw_id)
async def remove_hw_by_id(message: Message, state: FSMContext):
    user = await get_user_by_id(message.from_user.id)
    await state.update_data(hw_id=message.text)
    data = await state.get_data()

    hw_uid = int(data["hw_id"])
    homework = await get_homework_by_id(hw_uid)

    if homework is None:
        await message.answer("🤷‍♂️ Задание с таким id не найдено.", reply_markup=await kb.get_start_keyboard(user))
        await state.clear()
        return

    media = await get_media_by_id(data["hw_id"])
    if media:
        await send_media(
            message.chat.id, message.bot, media, f"<b>{homework.subject}</b>\n\n{str(homework.task)}", parse_mode="html"
        )
        await message.answer(
            f"Удалить задание с <b>id {data['hw_id']}</b>?", parse_mode="html", reply_markup=kb.remove_hw_by_id_keyboard
        )
    else:
        await message.answer(
            f"Удалить задание с <b>id {data['hw_id']}</b>?\n<b>{homework.subject}</b>\n\n{homework.task}",
            parse_mode="html",
            reply_markup=kb.remove_hw_by_id_keyboard,
        )


@router.callback_query(F.data == "delete_hw")
async def delete_hw_by_id(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    homework = await get_homework_by_id(int(data["hw_id"]))
    await del_homework(int(data["hw_id"]))
    await del_media(int(data["hw_id"]))
    await call.message.edit_text(
        f"🗑️ <b>Задание успешно удалено!</b>\n\n"
        f"▫️ ID: <code>{data['hw_id']}</code>\n"
        f"▫️ Предмет: {homework.subject}\n"
        f"▫️ Текст: <i>{homework.task[:30] + '...' if len(homework.task) > 30 else homework.task}</i>",
        parse_mode="HTML",
    )
    await state.clear()


@router.message(F.text.contains("Сбросить дедлайн"))
async def reset_deadline_handler(message: Message, state: FSMContext):
    user = await get_user_by_id(message.from_user.id)
    if user.role >= 2:
        await state.set_state(resetting_deadline.hw_id)
        await message.answer("Введите id задания:", reply_markup=kb.back_keyboard)


@router.message(resetting_deadline.hw_id)
async def reset_deadline(message: Message, state: FSMContext):
    user = await get_user_by_id(message.from_user.id)
    await state.update_data(hw_id=message.text)
    data = await state.get_data()
    homework = None
    hw_id = (await state.get_data())["hw_id"]

    try:
        hw_id = int(data["hw_id"])
        homework = await get_homework_by_id(int(hw_id))
    except:
        await message.answer(
            "❌ Неверно указано id. Попробуй еще раз.", parse_mode="html", reply_markup=kb.back_keyboard
        )
        return

    if homework:
        await reset_homework_deadline_by_id(hw_id)
        await message.answer("✅ Дата сдачи сброшена.", reply_markup=await kb.get_start_keyboard(user))
        await update_homework_dates(user.group.uid)
        new_homework = await get_homework_by_id(hw_id)
        deadline = new_homework.to_date
        new_deadline_text = (
            f"Новая дата сдачи: <b>{(deadline.strftime('%d.%m.%y') if deadline is not None else 'отсутствует')}</b>"
        )
        await message.answer(new_deadline_text, parse_mode="html", reply_markup=await kb.get_start_keyboard(user))
        await state.clear()
        return
    else:
        await message.answer(
            "🤷‍♂️ Задания с таким id не найдено. Попробуй еще раз.", parse_mode="html", reply_markup=kb.back_keyboard
        )
        return
