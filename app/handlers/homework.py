import aiogram
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InputMediaPhoto, InputMediaVideo, InputMediaDocument, InputMedia, InputMediaAudio, ContentType as CT
from aiogram.fsm.context import FSMContext

import app.keyboards as kb
from app.database.queries.group import get_group_by_id
from app.database.queries.homework import add_homework, del_homework, get_homework_by_id, get_homeworks_by_date, get_homeworks_by_subject, reset_homework_deadline_by_id, update_homework_dates
from app.database.queries.media import add_media, del_media, get_media_by_id
from app.database.queries.subjects import get_subject_by_id
from app.database.models import User
from app.database.queries.user import get_user_by_id, get_users

from datetime import datetime

import variables as var


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

@router.callback_query(F.data == "change_subject")
async def change_subject(call: CallbackQuery, state: FSMContext):
  user = await get_user_by_id(call.from_user.id)
  await state.set_state(adding_homework.subject)
  await call.message.delete()
  subjects = (await get_group_by_id(user["group_id"]))["subjects"]
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
  user = await get_user_by_id(call.from_user.id)

  homework = await add_homework(subject, task, user["group_id"], call.from_user.id, var.calculate_today()[1])
  homework_id = homework["uid"]

  if data.get("media_group") is not None:
    for media in data.get("media_group"):
      await add_media(homework_id, media.media, media.type)

  await call.message.answer(f"✅ <b>Домашнее задание добавлено.</b>", parse_mode="html", reply_markup=await kb.get_start_keyboard(user)) # в базу
  await call.message.delete()
  admins = await get_users(User.role == 4, User.group_id == user["group_id"])
  admins += await get_users(User.role == 3, User.group_id == user["group_id"])
  for admin in admins:
    if admin["tg_id"] != call.from_user.id:
      if data.get("media_group") is not None:
        media_group = data.get("media_group")
        
        media_group[0].caption = f"🔔 Добавлено домашнее задание.\n*{subject}*:\n\n{task}\n\nОт [{call.from_user.id}](tg://user?id={call.from_user.id}) *\nid задания - {homework_id}*"
        media_group[0].parse_mode = "Markdown"

        await call.bot.send_media_group(admin["tg_id"], media_group)
      else:
        await call.bot.send_message(admin["tg_id"], f"🔔 Добавлено домашнее задание по\n*{subject}*:\n\n{task}\n\nОт [{call.from_user.id}](tg://user?id={call.from_user.id}) *\nid задания - {homework_id}*", parse_mode="Markdown")

  await state.clear()
  
  
@router.callback_query(F.data.contains("-changed"))
async def add_changed_homework_subject(call: CallbackQuery, state: FSMContext):
  await call.message.delete()
  subject = await get_subject_by_id(int(call.data.replace("-changed", "")))
  subject_name = subject["name"]
  await state.update_data(subject=subject_name)
  await call.message.answer(f"Предмет был изменен на <b>{subject_name}</b>.", parse_mode="html")
  data = await state.get_data()

  subject = data.get("subject")
  task = data.get("task")

  if data.get("media_group") is not None:
    media_group = data.get("media_group")
  else:
    media_group = None

  try:
    if data.get("subject") is not None and data.get("task") is not None:
      if media_group:
        await call.message.answer_media_group(media_group)
        await call.message.answer(f"<b>{subject}.</b>\n\n{task}\n\n\nВсё верно?", parse_mode="html", reply_markup=kb.check_hw_before_apply_keyboard)
      else:
        await call.message.answer(f"<b>{subject}.</b>\n\n{task}\n\n\nВсё верно?", parse_mode="html", reply_markup=kb.check_hw_before_apply_keyboard)
  except aiogram.exceptions.TelegramBadRequest:
    await call.message.answer("Произошла ошибка. Попробуйте снова.")

@router.message(F.text.contains("Посмотреть Д/З"))
async def show_homework_handler(message: Message, state: FSMContext):
  await state.set_state(view_homework.day)
  await message.answer ("Выбери вариант.", reply_markup=kb.see_hw_keyboard)

@router.callback_query(F.data == "by_date")
async def checK_hw_by_date_handler(call: CallbackQuery, state: FSMContext):
  await state.set_state(view_homework.day)
  await call.message.answer("Выберите день", reply_markup=kb.see_hw_keyboard)

# @router.callback_query(F.data == "by_subject")
@router.message(F.text.contains("По предмету"))
async def check_hw_by_subject_handler(message: Message):
  user = await get_user_by_id(message.from_user.id)
  group = await get_group_by_id(user["group_id"])
  subjects = group["subjects"]
  await message.answer("Выбери предмет по которому\nхочешь посмотреть Д/З", reply_markup=await kb.allowed_subjects_check_hw_keyboard(subjects))

@router.callback_query(F.data.contains("-check-hw"))
async def check_hw_by_subject_handler_2(call: CallbackQuery, state: FSMContext):
  user = await get_user_by_id(call.from_user.id)
  await call.message.delete()
  subject = await get_subject_by_id(int(call.data.replace("-check-hw", "")))
  subject_name = subject["name"]
  user_role = (await get_user_by_id(call.from_user.id))["role"]
  homeworks = (await get_homeworks_by_subject(subject_name, limit_last_two=True, group_id=user["group_id"]))
  homeworks.reverse()
  if len(homeworks) > 0:
    await call.message.answer(f"Домашнее задание по <b>{subject_name}</b>", parse_mode="html")
    # print(tasks)
    for homework in homeworks:
      # if await get_all_media_by_id(task[2]) is not None:
      #     media_group_data = await get_all_media_by_id(task[2])
      hw_uid = homework["uid"]
      hw_subject = homework["subject"]
      hw_task = homework["task"]

      hw_media = await get_media_by_id(hw_uid)
      print(f"{hw_media=}")
      if hw_media is not None and len(hw_media) > 0:
          media_group_data = await get_media_by_id(hw_uid)
          media_group = []
          for media_data in media_group_data:
            if media_data["media_type"] == "photo":
              media_group.append(InputMediaPhoto(media=media_data["media_id"]))
            elif media_data["media_type"] == "video":
              media_group.append(InputMediaVideo(media=media_data["media_id"]))
            elif media_data["media_type"] == "audio":
              media_group.append(InputMediaAudio(media=media_data["media_id"]))
            elif media_data["media_type"] == "document":
              media_group.append(InputMediaDocument(media=media_data["media_id"]))

          media_group[0].caption = f"Добавлено <b>{datetime.fromtimestamp(homework["from_date"]).strftime("%d.%m.%Y")}</b> " + ("<i>(последнее)</i>" if homework == homeworks[-1] else "")  + (f' <span class="tg-spoiler">id {hw_uid}</span>' if user_role >= 2 else "") + f"\n\n{hw_task}" 
          media_group[0].parse_mode = "html"

          await call.message.answer_media_group(media_group)
      else:
        await call.message.answer(f"Добавлено <b>{datetime.fromtimestamp(homework["from_date"]).strftime("%d.%m.%Y")}</b> " + ("<i>(последнее)</i>" if homework == homeworks[-1] else "")  + (f' <span class="tg-spoiler">id {hw_uid}</span>' if user_role >= 2 else "") + f"\n\n{hw_task}", parse_mode="html")
  else:
    await call.message.answer(f"Домашнее задание по <b>{subject_name}</b> отсутствует", parse_mode="html")

@router.message(view_homework.day and F.text.contains("На сегодня"))
async def show_hw_today_handler(message: Message, state: FSMContext):
    user = await get_user_by_id(message.from_user.id)
    sent_message = await message.answer(f"⏳ Обновляю информацию...")
    await update_homework_dates()
    # tasks = await get_tasks_by_date(var.calculate_today()[1])
    tasks = await get_homeworks_by_date(var.calculate_today()[1], group_id=user["group_id"])
    user_role = (await get_user_by_id(message.from_user.id))["role"]
    # print(f"TASKS\t {tasks}")
    if tasks is None or len(tasks) == 0:
      await sent_message.edit_text(
        f"📭 <b>Заданий на сегодня нет!</b>",
        parse_mode="HTML"
      )
    else:
      await sent_message.edit_text(f"Домашнее задание на <b>{await var.get_day_month(var.calculate_today()[1])}</b>:", parse_mode="html")
      for homework in tasks:
        subject = homework["subject"]
        task = homework["task"]
        task_id = homework["uid"]
        if await get_media_by_id(task_id) is not None:
          media_group_data = await get_media_by_id(task_id)
          media_group = []
          for media_data in media_group_data:
            if media_data["media_type"] == "photo":
              media_group.append(InputMediaPhoto(media=media_data["media_id"]))
            elif media_data["media_type"] == "video":
              media_group.append(InputMediaVideo(media=media_data["media_id"]))
            elif media_data["media_type"] == "audio":
              media_group.append(InputMediaAudio(media=media_data["media_id"]))
            elif media_data["media_type"] == "document":
              media_group.append(InputMediaDocument(media=media_data["media_id"]))

          media_group[0].caption = f"<b>{subject}</b>" + (f' <span class="tg-spoiler">id {task_id}</span>' if user_role >= 2 else "") + f"\n\n{str(task)}"
          media_group[0].parse_mode = "html"

          await message.answer_media_group(media_group)
        else:
          await message.answer(f"<b>{subject}</b>" + (f' <span class="tg-spoiler">id {task_id}</span>' if user_role >= 2 else "") + f"\n\n{str(task)}", parse_mode="html")
      await state.clear()

@router.message(view_homework.day and F.text.contains("На завтра"))
async def show_hw_tomorrow_handler(message: Message, state: FSMContext):
    user = await get_user_by_id(message.from_user.id)
    sent_message = await message.answer(f"⏳ Обновляю информацию...")
    await update_homework_dates()
    # tasks = await get_tasks_by_date(var.calculate_today()[1])
    tasks = await get_homeworks_by_date(var.calculate_tomorrow()[1], group_id=user["group_id"])
    user_role = (await get_user_by_id(message.from_user.id))["role"]
    # print(f"TASKS\t {tasks}")
    if tasks is None or len(tasks) == 0:
      await sent_message.edit_text(
          f"📭 <b>Заданий на завтра нет!</b>",
          parse_mode="HTML"
      )
    else:
      await sent_message.edit_text(f"Домашнее задание на <b>{await var.get_day_month(var.calculate_tomorrow()[1])}</b>:", parse_mode="html")
      for homework in tasks:
        subject = homework["subject"]
        task = homework["task"]
        task_id = homework["uid"]
        if await get_media_by_id(task_id) is not None:
          media_group_data = await get_media_by_id(task_id)
          media_group = []
          for media_data in media_group_data:
            if media_data["media_type"] == "photo":
              media_group.append(InputMediaPhoto(media=media_data["media_id"]))
            elif media_data["media_type"] == "video":
              media_group.append(InputMediaVideo(media=media_data["media_id"]))
            elif media_data["media_type"] == "audio":
              media_group.append(InputMediaAudio(media=media_data["media_id"]))
            elif media_data["media_type"] == "document":
              media_group.append(InputMediaDocument(media=media_data["media_id"]))

          media_group[0].caption = f"<b>{subject}</b>" + (f' <span class="tg-spoiler">id {task_id}</span>' if user_role >= 2 else "") + f"\n\n{str(task)}"
          media_group[0].parse_mode = "html"

          await message.answer_media_group(media_group)
        else:
          await message.answer(f"<b>{subject}</b>" + (f' <span class="tg-spoiler">id {task_id}</span>' if user_role >= 2 else "") + f"\n\n{str(task)}", parse_mode="html")
      await state.clear()

@router.message(view_homework.day and F.text.contains("На послезавтра"))
async def show_hw_after_tomorrow_handler(message: Message, state: FSMContext):
    user = await get_user_by_id(message.from_user.id)
    sent_message = await message.answer(f"⏳ Обновляю информацию...")
    await update_homework_dates()
    # tasks = await get_tasks_by_date(var.calculate_today()[1])
    tasks = await get_homeworks_by_date(var.calculate_aftertomorrow()[1], group_id=user["group_id"])
    user_role = (await get_user_by_id(message.from_user.id))["role"]
    # print(f"TASKS\t {tasks}")
    if tasks is None or len(tasks) == 0:
      await sent_message.edit_text(
        f"📭 <b>Заданий на послезавтра нет!</b>",
        parse_mode="HTML"
      )
    else:
      await sent_message.edit_text(f"Домашнее задание на <b>{await var.get_day_month(var.calculate_aftertomorrow()[1])}</b>:", parse_mode="html")
      for homework in tasks:
        subject = homework["subject"]
        task = homework["task"]
        task_id = homework["uid"]
        if await get_media_by_id(task_id) is not None:
          media_group_data = await get_media_by_id(task_id)
          media_group = []
          for media_data in media_group_data:
            if media_data["media_type"] == "photo":
              media_group.append(InputMediaPhoto(media=media_data["media_id"]))
            elif media_data["media_type"] == "video":
              media_group.append(InputMediaVideo(media=media_data["media_id"]))
            elif media_data["media_type"] == "audio":
              media_group.append(InputMediaAudio(media=media_data["media_id"]))
            elif media_data["media_type"] == "document":
              media_group.append(InputMediaDocument(media=media_data["media_id"]))

          media_group[0].caption = f"<b>{subject}</b>" + (f' <span class="tg-spoiler">id {task_id}</span>' if user_role >= 2 else "") + f"\n\n{str(task)}"
          media_group[0].parse_mode = "html"

          await message.answer_media_group(media_group)
        else:
          await message.answer(f"<b>{subject}</b>" + (f' <span class="tg-spoiler">id {task_id}</span>' if user_role >= 2 else "") + f"\n\n{str(task)}", parse_mode="html")
      await state.clear()

@router.message(view_homework.day and F.text.contains("По дате"))
async def show_hw_by_date_handler(message: Message, state: FSMContext):
  await state.set_state(view_homework.with_date)
  current_month = datetime.now().month
  await message.answer(f'Введи дату в виде "номер_месяца число" без кавычек. Сейчас <b>{current_month}</b> месяц', parse_mode="html", reply_markup=kb.back_keyboard)
  
@router.message(view_homework.with_date)
async def show_hw_by_date(message: Message, state: FSMContext):
    user = await get_user_by_id(message.from_user.id)
    user_role = user["role"]
    inted_date_from_user: list = []
    try:
      inted_date_from_user = [int(num) for num in message.text.split(" ")]
    except ValueError as e:
      await message.answer('❌ Введите числа в формате "номер_месяца число". Попробуй еще раз.')
      return
    
    print(f"{inted_date_from_user=}")
    if len(inted_date_from_user) == 2:
      date_time = datetime.strptime(f"{inted_date_from_user[1]}/{inted_date_from_user[0]}/2024, 00:00:00", "%d/%m/%Y, %H:%M:%S")
      date_time_timestamp = datetime.timestamp(date_time)
      tasks = await get_homeworks_by_date(date_time_timestamp, group_id=user["group_id"])
      sent_message = await message.answer(f"⏳ Обновляю информацию...", reply_markup=await kb.get_start_keyboard(user))
      await update_homework_dates()
      if tasks is None or len(tasks) == 0:
        await sent_message.edit_text(
          f"📭 <b>Заданий на этот день нет!</b>",
          parse_mode="HTML"
        )
        await state.clear()
      else:
        await sent_message.edit_text(f"Домашнее задание на <b>{datetime.fromtimestamp(date_time_timestamp).strftime("%d")} {var.months_words[int(datetime.fromtimestamp(date_time_timestamp).strftime("%m"))]}</b>:", parse_mode="html")
        for homework in tasks:
          subject = homework["subject"]
          task = homework["task"]
          task_id = homework["uid"]
          if await get_media_by_id(task_id) is not None:
            media_group_data = await get_media_by_id(task_id)
            media_group = []
            for media_data in media_group_data:
              if media_data["media_type"] == "photo":
                media_group.append(InputMediaPhoto(media=media_data["media_id"]))
              elif media_data["media_type"] == "video":
                media_group.append(InputMediaVideo(media=media_data["media_id"]))
              elif media_data["media_type"] == "audio":
                media_group.append(InputMediaAudio(media=media_data["media_id"]))
              elif media_data["media_type"] == "document":
                media_group.append(InputMediaDocument(media=media_data["media_id"]))
            
            media_group[0].caption = f"<b>{subject}</b>" + (f' <span class="tg-spoiler">id {task_id}</span>' if user_role >= 2 else "") + f"\n\n{str(task)}"
            media_group[0].parse_mode = "html"

            await message.answer_media_group(media_group)
          else:
            await message.answer(f"<b>{subject}</b>" + (f' <span class="tg-spoiler">id {task_id}</span>' if user_role >= 2 else "") + f"\n\n{str(task)}", parse_mode="html")
        await state.clear()
    else:
      await message.answer("❌ Неправильный формат даты. Попробуй еще раз.")
      return
    

@router.message(F.text.contains('Добавить Д/З'))
async def add_hw_one(message: Message, state: FSMContext):
  user = await get_user_by_id(message.from_user.id)
  if (await get_user_by_id(message.from_user.id))["role"] >= 2:
    await state.set_state(adding_homework.subject)
    subjects = (await get_group_by_id(user["group_id"]))["subjects"]
    await message.answer("Выберите предмет:", reply_markup=await kb.allowed_subjects_keyboard(subjects))
    kb.ReplyKeyboardRemove(remove_keyboard=True)

@router.callback_query(adding_homework.subject)
@router.callback_query(F.data.contains("-add"))
async def add_hw_two(call: CallbackQuery, state: FSMContext):
  await call.message.delete()
  subject = await get_subject_by_id(int(call.data.replace("-add", "")))
  subject_name = subject["name"]
  
  await call.message.answer(f"Предмет <b>{subject_name}</b> выбран.", parse_mode="html")
  await state.update_data(subject=subject_name)
  await state.set_state(adding_homework.task)
  await call.message.answer("✍️ Напишите домашнее задание, можно прикрепить медиа.", parse_mode="html", reply_markup=ReplyKeyboardRemove())

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
        file_id = obj_dict[album[i].content_type]['file_id']
        media_group.append(InputMedia(media=file_id))

    # print(media_group)
    # await message.answer("album")
    await state.update_data(media_group = media_group)
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
    await state.update_data(media_group = media_group)
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
        await message.reply(f"<b>{subject}.</b>\n\n{task}\n\n\nВсё верно?", parse_mode="html", reply_markup=kb.check_hw_before_apply_keyboard)
      elif message.content_type in [CT.PHOTO, CT.VIDEO, CT.AUDIO, CT.DOCUMENT]:
        await message.reply(f"<b>{subject}.</b>\n\n{task}\n\n\nВсё верно?", parse_mode="html", reply_markup=kb.check_hw_before_apply_keyboard)
      elif media_group:
        await message.answer_media_group(media_group)
        await message.answer(f"<b>{subject}.</b>\n\n{task}\n\n\nВсё верно?", parse_mode="html", reply_markup=kb.check_hw_before_apply_keyboard)
      else:
        await message.answer(f"<b>{subject}.</b>\n\n{task}\n\n\nВсё верно?", parse_mode="html", reply_markup=kb.check_hw_before_apply_keyboard)
  except aiogram.exceptions.TelegramBadRequest:
    await message.answer("Произошла ошибка. Попробуйте снова.")


@router.message(F.text.contains("Удалить Д/З"))
async def remove_hw_by_id_handler(message: Message, state: FSMContext):
  if (await get_user_by_id(message.from_user.id))["role"] >= 2:
    await state.set_state(removing_homework.hw_id)
    await message.answer("Введите id задания:", reply_markup=kb.back_keyboard)

@router.message(removing_homework.hw_id)
async def remove_hw_by_id(message: Message, state: FSMContext):
  user = await get_user_by_id(message.from_user.id)
  await state.update_data(hw_id=message.text)
  data = await state.get_data()
  
  hw_uid = int(data["hw_id"])
  print(f"getting homework by id {hw_uid}")
  homework = await get_homework_by_id(hw_uid)

  if homework is None:
    await message.answer("🤷‍♂️ Задание с таким id не найдено.", reply_markup=await kb.get_start_keyboard(user))
    await state.clear()
    return

  hw_subject = homework["subject"]
  hw_task = homework["task"]

  if await get_media_by_id(data["hw_id"]) is not None:
    media_group_data = await get_media_by_id(data["hw_id"])
    media_group = []
    for media_data in media_group_data:
      if media_data["media_type"] == "photo":
        media_group.append(InputMediaPhoto(media=media_data["media_id"]))
      elif media_data["media_type"] == "video":
        media_group.append(InputMediaVideo(media=media_data["media_id"]))
      elif media_data["media_type"] == "audio":
        media_group.append(InputMediaAudio(media=media_data["media_id"]))
      elif media_data["media_type"] == "document":
        media_group.append(InputMediaDocument(media=media_data["media_id"]))
    
    media_group[0].caption = f"<b>{hw_subject}</b>\n\n{str(hw_task)}"
    media_group[0].parse_mode = "html"

    await message.answer_media_group(media_group)
    await message.answer(f"Удалить задание с <b>id {data['hw_id']}</b>?", parse_mode="html", reply_markup=kb.remove_hw_by_id_keyboard)
  else:
    await message.answer(f"Удалить задание с <b>id {data['hw_id']}</b>?\n<b>{hw_subject}</b>\n\n{hw_task}", parse_mode="html", reply_markup=kb.remove_hw_by_id_keyboard)

@router.callback_query(F.data == "delete_hw")
async def delete_hw_by_id(call: CallbackQuery, state: FSMContext):
  user = await get_user_by_id(call.from_user.id)
  # await call.message.delete()
  data = await state.get_data()

  print(type(data['hw_id']), data['hw_id'])
  print(type(int(data['hw_id'])), int(data['hw_id']))
  
  homework = await get_homework_by_id(int(data['hw_id']))
  await del_homework(int(data['hw_id']))
  await del_media(int(data['hw_id']))
  await call.message.edit_text(
    f"🗑️ <b>Задание успешно удалено!</b>\n\n"
    f"▫️ ID: <code>{data['hw_id']}</code>\n"
    f"▫️ Предмет: {homework['subject']}\n"
    f"▫️ Текст: <i>{homework['task'][:30] + '...' if len(homework['task']) > 30 else homework['task']}</i>",
    parse_mode="HTML"
  )
  await state.clear()
  

@router.message(F.text.contains("Сбросить дедлайн"))
async def reset_deadline_handler(message: Message, state: FSMContext):
  if (await get_user_by_id(message.from_user.id))["role"] >= 2:
    await message.answer("Введите id задания:", reply_markup=kb.back_keyboard)
    await state.set_state(resetting_deadline.hw_id)


@router.message(resetting_deadline.hw_id)
async def reset_deadline(message: Message, state: FSMContext):
    user = await get_user_by_id(message.from_user.id)
    await state.update_data(hw_id=message.text)
    data = await state.get_data()
    homework = None
    hw_id = None
    try:
      hw_id = int(data['hw_id'])
      homework = await get_homework_by_id(hw_id)
    except:
      await message.answer("❌ Неверно указано id. Попробуй еще раз.", parse_mode="html", reply_markup=kb.back_keyboard)
      return
    if homework:
        await reset_homework_deadline_by_id(hw_id)
        await message.answer("✅ Дата сдачи сброшена.", reply_markup=await kb.get_start_keyboard(user))
        await update_homework_dates()
        new_homework = await get_homework_by_id(hw_id)
        print(f"{new_homework=}")
        deadline: datetime = new_homework["to_date"]
        new_deadline_text = f"Новая дата сдачи: <b>{(deadline.strftime('%d.%m.%y') if deadline is not None else 'отсутствует')}</b>"
        await message.answer(new_deadline_text, reply_markup=await kb.get_start_keyboard(user))
        await state.clear()
    else:
        await message.answer("🤷‍♂️ Задания с таким id не найдено. Попробуй еще раз.", parse_mode="html", reply_markup=kb.back_keyboard)
        return