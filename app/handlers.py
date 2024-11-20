import aiogram.exceptions
from app.database.requests import *
import app.variables as var
import app.keyboards as kb
from app.backuper import create_backups
from app.middlewares import AlbumMiddleware, AntiFloodMiddleware, TestMiddleware, MsgLoggerMiddleware
import os
import sys
import time

import aiogram
from aiogram import F ,types, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, FSInputFile, InputMediaPhoto, InputMediaVideo, InputMediaDocument, InputMedia, InputMediaAudio, ContentType as CT
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from other_scripts.db_subject_populator import populate_schedule

import psutil

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

class adding_admin(StatesGroup):
  user_id = State()

class adding_adder(StatesGroup):
  user_id = State()

class removing_admin(StatesGroup):
  user_id = State()

class removing_adder(StatesGroup):
  user_id = State()

class adding_user(StatesGroup): # Temporary
  user_id = State()

class removing_user(StatesGroup):
  user_id = State()

class adding_new_week(StatesGroup):
  file = State()


dp = Router()

dp.message.middleware(AlbumMiddleware())
dp.message.middleware(MsgLoggerMiddleware())
# dp.message.middleware(AntiFloodMiddleware(0.3))
# dp.message.middleware(TestMiddleware())

@dp.message(CommandStart())
async def start(message: Message):
      await add_new_user(message.from_user.id, 1)
      if await get_user_role(message.from_user.id) != 0:
        if await get_user_role(message.from_user.id) >= 2:
          await message.answer("Тут можно посмотреть домашнее задание. Выбери опцию.", reply_markup=await kb.get_start_keyboard(await get_user_role(message.from_user.id)))
        else: 
          await message.answer("Тут можно посмотреть домашнее задание. Выбери опцию.", reply_markup=await kb.get_start_keyboard(await get_user_role(message.from_user.id)))
    # else:
    #   await add_new_user(message.from_user.id, 0)

@dp.message(F.text == "Админ-панель 😈")
async def show_admin_panel(message: Message):
  if await get_user_role(message.from_user.id) == 3:
    await message.answer("Админ-панель:", reply_markup=kb.adminka_keyboard)
  if await get_user_role(message.from_user.id) == 4:
    await message.answer("Админ-панель:", reply_markup=kb.superuser_keyboard)

@dp.message(adding_new_week.file, F.content_type == CT.DOCUMENT)
async def load_new_week(message: Message, state: FSMContext):
  try:
    await state.update_data(file=message.document.file_id)
    await state.clear()
    file_id = message.document.file_id
    schedule_file = await message.bot.get_file(file_id)
    file_path = schedule_file.file_path
    file_name = message.document.file_name
    file_info = await message.bot.download_file(file_path)
    with open(f"{file_name}", "wb") as new_file:
      new_file.write(file_info.getvalue())
    n1_msg = await message.answer("✅ Файл загружен.")
    time.sleep(0.5)
    await n1_msg.edit_text("⏳ Обновление расписания...")
    populate_schedule(file_name)
    await n1_msg.edit_text("✅ Расписание обновлено.")
    await state.clear()
  except Exception as e:
    print(e)
    await message.answer("❌ Не удалось обновить расписание.")

@dp.callback_query(F.data == "back")
async def back(call: CallbackQuery, state: FSMContext):
  await call.message.delete()
  await call.message.answer("❌ Действие отменено.")
  await call.message.answer("Выбери опцию.", reply_markup=await kb.get_start_keyboard(await get_user_role(call.from_user.id)))
  await state.clear()

@dp.callback_query(F.data == "change_subject")
async def change_subject(call: CallbackQuery, state: FSMContext):
  await state.set_state(adding_homework.subject)
  await call.message.delete()
  await call.message.answer("🔄 Выберите предмет:", reply_markup=await kb.allowed_subjects_change_keyboard(var.allowed_subjects))

@dp.callback_query(F.data == "change_task")
async def change_task(call: CallbackQuery, state: FSMContext):
  await state.set_state(adding_homework.task)
  await state.update_data(task=None)
  await call.message.delete()
  await call.message.answer("🔄 Введите домашнее задание:", reply_markup=types.ReplyKeyboardRemove())

@dp.callback_query(F.data == "all_right")
async def add_homework_to_db(call: CallbackQuery, state: FSMContext):
  data = await state.get_data()

  subject = data.get("subject")
  task = data.get("task")

  homework_id = await add_homework(subject, task)

  if data.get("media_group") is not None:
    for media in data.get("media_group"):
      await add_media_to_db(homework_id, media.media, media.type)

  await call.message.delete()
  await call.message.answer(f"✅ Домашнее задание добавлено.") # в базу
  await call.message.answer(f"Выбери опцию.", reply_markup=await kb.get_start_keyboard(await get_user_role(call.from_user.id)))
  admins = await get_admins_chatid()
  for admin_id in admins:
    if admin_id[0] != call.from_user.id:
      if data.get("media_group") is not None:
        media_group = data.get("media_group")
        
        media_group[0].caption = f"🔔 Добавлено домашнее задание.\n*{subject}*:\n\n{task}\n\nОт [{call.from_user.id}](tg://user?id={call.from_user.id}) *\nid задания - {homework_id}*"
        media_group[0].parse_mode = "Markdown"

        await call.bot.send_media_group(admin_id[0], media_group)
      else:
        await call.bot.send_message(admin_id[0], f"🔔 Добавлено домашнее задание по\n*{subject}*:\n\n{task}\n\nОт [{call.from_user.id}](tg://user?id={call.from_user.id}) *\nid задания - {homework_id}*", parse_mode="Markdown")

  await state.clear()
  

# ADMIN PANEL CALLBACKS
@dp.callback_query(F.data == "show_favs")
async def show_favs(call: CallbackQuery):
    adders = [str(f"[{num}](tg://user?id={num})") for num in await get_all_users_with_role(2)]
    admins = [str(f"[{num}](tg://user?id={num})") for num in await get_all_users_with_role(3)]

    await call.message.answer(f"*Админы:*\n{"\n".join(admins)}\n\n*Добавлятели:*\n{"\n".join(adders)}", parse_mode="Markdown")

@dp.callback_query(F.data == "add_admin")
async def adding_admin_handler(call: CallbackQuery, state: FSMContext):
    await state.set_state(adding_admin.user_id)
    await call.message.answer("Перешлите сообщение или введите id пользователя для добавления:", reply_markup=types.ReplyKeyboardRemove())

@dp.message(adding_admin.user_id)
async def add_admin_id(message: Message, state: FSMContext):
    if message.forward_from:
      await state.update_data(user_id=message.forward_from.id)
      data = await state.get_data()
    else:
      await state.update_data(user_id=message.text)
      data = await state.get_data()

    user_id = data.get("user_id")

    user_role = await get_user_role(user_id)
    if user_role == None:
      await message.answer(f"❌ Пользователь не существует или скрыл id.")
      await state.clear()
      return

    elif user_role <= 2:
      await change_user_role(user_id, 3)
      await message.answer(f"✅ Пользователь добавлен в администраторы.", parse_mode="html")
    else:
      await message.answer(f"❌ Пользователь уже является администратором.", parse_mode="html")
    
    await state.clear()

@dp.callback_query(F.data == "remove_admin")
async def remove_admin_handler(call: CallbackQuery, state: FSMContext):
    await state.set_state(removing_admin.user_id)
    await call.message.answer("Перешлите сообщение или введите id админа для удаления:", reply_markup=types.ReplyKeyboardRemove())

@dp.message(removing_admin.user_id)
async def remove_admin_id(message: Message, state: FSMContext):
    if message.forward_from:
      await state.update_data(user_id=message.forward_from.id)
      data = await state.get_data()
    else:
      await state.update_data(user_id=message.text)
      data = await state.get_data()

    user_id = data.get("user_id")

    user_role = await get_user_role(user_id)
    if user_role == None:
      await message.answer(f"❌ Пользователь не существует или скрыл id.")
      await state.clear()
      return

    elif user_role == 3:
      await change_user_role(user_id, 1)
      await message.answer(f"✅ Пользователь удален из администраторов.")
    else:
      await message.answer(f"❌ Пользователь не является администратором.")
    
    await state.clear()

@dp.callback_query(F.data == "add_adder")
async def add_adder_handler(call: CallbackQuery, state: FSMContext):
    await state.set_state(adding_adder.user_id)
    await call.message.answer("Перешлите сообщение или введите id пользователя для добавления:", reply_markup=types.ReplyKeyboardRemove())

@dp.message(adding_adder.user_id)
async def add_adder_id(message: Message, state: FSMContext):
    if message.forward_from:
      await state.update_data(user_id=message.forward_from.id)
      data = await state.get_data()
    else:
      await state.update_data(user_id=message.text)
      data = await state.get_data()
    
    user_id = data.get("user_id")

    user_role = await get_user_role(user_id)
    if user_role == None:
      await message.answer(f"❌ Пользователь не существует или скрыл id.")
      await state.clear()
      return
    
    elif user_role <= 1:
      await change_user_role(user_id, 2)
      await message.answer(f"✅ Пользователь добавлен в добавлятелей.")
    else:
      await message.answer(f"❌ Пользователь уже является добавлятелем.")

    await state.clear()

@dp.callback_query(F.data == "remove_adder")
async def remove_adder_handler(call: CallbackQuery, state: FSMContext):
    await state.set_state(removing_adder.user_id)
    await call.message.answer("Перешлите сообщение или введите id добавлятеля для удаления:", reply_markup=types.ReplyKeyboardRemove())

@dp.message(removing_adder.user_id)
async def remove_adder_id(message: Message, state: FSMContext):
    if message.forward_from:
      await state.update_data(user_id=message.forward_from.id)
      data = await state.get_data()
    else:
      await state.update_data(user_id=message.text)
      data = await state.get_data()
    
    user_id = data.get("user_id")

    user_role = await get_user_role(user_id)
    if user_role == None:
      await message.answer(f"❌ Пользователь не существует или скрыл id.")
      await state.clear()
      return

    elif user_role == 2:
      await change_user_role(user_id, 1)
      await message.answer(f"✅ Пользователь удален из добавлятелей.", parse_mode="html")
    else:
      await message.answer(f"❌ Пользователь не является добавлятелем.", parse_mode="html")

    await state.clear()

@dp.callback_query(F.data == "server_status")
async def get_server_status_handler(call : CallbackQuery):
  system_usage_info = await get_system_usage()
  await call.message.answer(f"Загруженность сервера:\n<b>CPU</b> - {system_usage_info['cpu_usage']:.1f}%\n<b>Memory</b> - {system_usage_info['memory_usage']}\n", parse_mode="html")

@dp.callback_query(F.data == "add_user")
async def add_user_handler(call: CallbackQuery, state: FSMContext):
  await state.set_state(adding_user.user_id)
  await call.message.answer("Перешлите сообщение или введите id добавлятеля для добавления:", reply_markup=types.ReplyKeyboardRemove())

@dp.message(adding_user.user_id)
async def add_user_id(message: Message, state: FSMContext):
  if message.forward_from:
    await state.update_data(user_id=message.forward_from.id)
    data = await state.get_data()
  else:
    await state.update_data(user_id=message.text)
    data = await state.get_data()
  
  user_id = data.get("user_id")

  if await check_exists_user(user_id):
    await message.answer(f"❌ Пользователь уже существует.")
  else:
    await add_new_user(user_id, 1)
    await message.answer(f"✅ Пользователь добавлен.")

  await state.clear()


@dp.callback_query(F.data == "remove_user")
async def remove_user_id(call: CallbackQuery, state: FSMContext):
  await state.set_state(removing_user.user_id)
  await call.message.answer("Перешлите сообщение или введите id добавлятеля для удаления:", reply_markup=types.ReplyKeyboardRemove())


@dp.message(removing_user.user_id)
async def remove_user_id(message: Message, state: FSMContext):
  if message.forward_from:
    await state.update_data(user_id=message.forward_from.id)
    data = await state.get_data()
  else:
    await state.update_data(user_id=message.text)
    data = await state.get_data()
  
  user_id = data.get("user_id")

  if await check_exists_user(user_id):
    await del_user(user_id)
    await message.answer(f"✅ Пользователь удален.")
  else:
    await message.answer(f"❌ Пользователь не существует.")

  await state.clear()

async def get_system_usage():
  # Используем asyncio.to_thread для выполнения синхронных функций в асинхронном контексте
  cpu_usage = await asyncio.to_thread(psutil.cpu_percent, interval=1)

  memory_info = await asyncio.to_thread(psutil.virtual_memory)
  used_memory_mb = memory_info.used / (1024 ** 2)  # Перевод в мегабайты
  total_memory_mb = memory_info.total / (1024 ** 2)  # Перевод в мегабайты

  # gpus = await asyncio.to_thread(GPUtil.getGPUs)
  # gpu_usage = [gpu.load * 100 for gpu in gpus]  # Нагрузка в процентах

  return {
      'cpu_usage': cpu_usage,
      'memory_usage': f"{used_memory_mb:.2f}mb/{total_memory_mb:.0f}mb"
      # 'gpu_usage': gpu_usage
  }

@dp.callback_query(F.data == "get_db_backup")
async def get_db_backup_handler(call: CallbackQuery):
  db_backups_path = "data/backups/databases"
  await create_backups()
  db_backup_files = os.listdir(db_backups_path)
  db_backup_files.sort()
  last_db_backup_file = db_backup_files[-1]
  backup_date_str = last_db_backup_file.replace("backup_Database_", "").replace(".db", "").replace("_", " ")
  backup_date_time = datetime.strptime(backup_date_str, "%Y%m%d %H%M%S")
  path_to_file = f"{db_backups_path}/{last_db_backup_file}"

  dbfile = FSInputFile(path_to_file) 

  await call.message.answer_document(dbfile, caption=f"Резервная копия базы данных <b>{backup_date_time}</b>", parse_mode="html")

@dp.callback_query(F.data == "get_logs_backup")
async def get_logs_backup_handler(call: CallbackQuery):
  await log("Uploading .log file", "FILEMANAGER")
  logs_backups_path = "data/logs"
  logs_backup_files = os.listdir(logs_backups_path)
  logs_backup_files.sort()
  last_logs_backup_file = logs_backup_files[-1]
  backup_date_str = last_logs_backup_file.replace("backup_logs_", "").replace(".log", "").replace("_", " ")
  backup_date_time = datetime.strptime(backup_date_str, "%Y-%m-%d")
  path_to_file = f"{logs_backups_path}/{last_logs_backup_file}"

  logfile = FSInputFile(path_to_file) 

  await call.message.answer_document(logfile, caption=f"Резервная копия логов <b>{backup_date_time}</b>", parse_mode="html")


@dp.callback_query(F.data.contains("-changed"))
async def add_changed_homework_subject(call: CallbackQuery, state: FSMContext):
  await call.message.delete()
  await state.update_data(subject=call.data.replace("-changed", ""))
  await call.message.answer(f"Предмет был изменен на <b>{call.data.replace('-changed', '')}</b>.", parse_mode="html")
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

@dp.message(F.text == '👀 Посмотреть Д/З')
async def show_homework_handler(message: Message, state: FSMContext):
  await state.set_state(view_homework.day)
  await message.answer("В каком форматике?", reply_markup=kb.v_kakom_formatike_keyboard)

@dp.callback_query(F.data == "by_date")
async def checK_hw_by_date_handler(call: CallbackQuery, state: FSMContext):
  await state.set_state(view_homework.day)
  await call.message.answer("Выберите день", reply_markup=kb.see_hw_keyboard)

@dp.callback_query(F.data == "by_subject")
async def check_hw_by_subject_handler(call: CallbackQuery):
  await call.message.answer("Выбери предмет по которому\nхочешь посмотреть Д/З", reply_markup=await kb.allowed_subjects_check_hw_keyboard(var.allowed_subjects))

@dp.callback_query(F.data.contains("-check-hw"))
async def check_hw_by_subject_handler(call: CallbackQuery, state: FSMContext):
  await call.message.delete()
  tasks = await get_task_by_subject(call.data.replace("-check-hw", ""))
  if len(tasks) > 0:
    await call.message.answer(f"Домашнее задание по <b>{call.data.replace('-check-hw', '')}</b>", parse_mode="html")
    # print(tasks)
    for task in tasks:
      if await get_all_media_by_id(task[2]) is not None:
          media_group_data = await get_all_media_by_id(task[2])
          media_group = []
          for media_data in media_group_data:
            if media_data[1] == "photo":
              media_group.append(InputMediaPhoto(media=media_data[0]))
            elif media_data[1] == "video":
              media_group.append(InputMediaVideo(media=media_data[0]))
            elif media_data[1] == "audio":
              media_group.append(InputMediaAudio(media=media_data[0]))
            elif media_data[1] == "document":
              media_group.append(InputMediaDocument(media=media_data[0]))

          media_group[0].caption = f"Добавлено <b>{datetime.fromtimestamp(task[0]).strftime('%d.%m.%Y')}</b>\n\n{str(task[1]).capitalize()}"
          media_group[0].parse_mode = "html"

          await call.message.answer_media_group(media_group)
      else:
        await call.message.answer(f"Добавлено <b>{datetime.fromtimestamp(task[0]).strftime("%d.%m.%Y")}</b>\n\n{str(task[1]).capitalize()}", parse_mode="html")
  else:
    await call.message.answer(f"Домашнее задание по <b>{call.data.replace('-check-hw', '')}</b> отсутствует", parse_mode="html")

@dp.message(view_homework.day, F.text == "На вчера")
async def show_hw_yesterday_handler(message: Message, state: FSMContext):
    sent_message = await message.answer(f"⏳ Обновляю информацию...")
    await update_homework_dates()
    tasks = await get_tasks_by_date(var.yesterday_ts)
    # print(f"TASKS\t {tasks}")
    if tasks is None:
      await sent_message.edit_text(f"Домашние задания на этот день отсутствуют")
    else:
      await sent_message.edit_text(f"Домашнее задание на <b>{await var.get_day_month(var.yesterday_ts)}</b>:", parse_mode="html")
      for homework in tasks:
        subject = homework[0]
        task = homework[1]
        await message.answer(f"<b>{subject}</b>\n\n{str(task).capitalize()}",parse_mode="html")
        if await get_all_media_by_id(homework[2]) is not None:
          media_group_data = await get_all_media_by_id(homework[2])
          media_group = []
          for media_data in media_group_data:
            if media_data[1] == "photo":
              media_group.append(InputMediaPhoto(media=media_data[0]))
            elif media_data[1] == "video":
              media_group.append(InputMediaVideo(media=media_data[0]))
            elif media_data[1] == "audio":
              media_group.append(InputMediaAudio(media=media_data[0]))
            elif media_data[1] == "document":
              media_group.append(InputMediaDocument(media=media_data[0]))
          await message.answer_media_group(media_group)
      await state.clear()

@dp.message(view_homework.day and F.text == "На сегодня")
async def show_hw_today_handler(message: Message, state: FSMContext):
    sent_message = await message.answer(f"⏳ Обновляю информацию...")
    await update_homework_dates()
    tasks = await get_tasks_by_date(var.calculate_today()[1])
    # print(f"TASKS\t {tasks}")
    if tasks is None:
      await sent_message.edit_text(f"Домашние задания на этот день отсутствуют")
    else:
      await sent_message.edit_text(f"Домашнее задание на <b>{await var.get_day_month(var.calculate_today()[1])}</b>:", parse_mode="html")
      for homework in tasks:
        subject = homework[0]
        task = homework[1]
        if await get_all_media_by_id(homework[2]) is not None:
          media_group_data = await get_all_media_by_id(homework[2])
          media_group = []
          for media_data in media_group_data:
            if media_data[1] == "photo":
              media_group.append(InputMediaPhoto(media=media_data[0]))
            elif media_data[1] == "video":
              media_group.append(InputMediaVideo(media=media_data[0]))
            elif media_data[1] == "audio":
              media_group.append(InputMediaAudio(media=media_data[0]))
            elif media_data[1] == "document":
              media_group.append(InputMediaDocument(media=media_data[0]))

          media_group[0].caption = f"<b>{subject}</b>\n\n{str(task).capitalize()}"
          media_group[0].parse_mode = "html"

          await message.answer_media_group(media_group)
        else:
          await message.answer(f"<b>{subject}</b>\n\n{str(task).capitalize()}", parse_mode="html")
      await state.clear()

@dp.message(view_homework.day and F.text == "На завтра")
async def show_hw_tomorrow_handler(message: Message, state: FSMContext):
    sent_message = await message.answer(f"⏳ Обновляю информацию...")
    await update_homework_dates()
    tasks = await get_tasks_by_date(var.calculate_tomorrow()[1])
    # print(f"TASKS\t {tasks}")
    if tasks is None:
      await sent_message.edit_text(f"Домашние задания на этот день отсутствуют")
    else:
      await sent_message.edit_text(f"Домашнее задание на <b>{await var.get_day_month(var.calculate_tomorrow()[1])}</b>:", parse_mode="html")
      for homework in tasks:
        subject = homework[0]
        task = homework[1]
        if await get_all_media_by_id(homework[2]) is not None:
          media_group_data = await get_all_media_by_id(homework[2])
          media_group = []
          for media_data in media_group_data:
            if media_data[1] == "photo":
              media_group.append(InputMediaPhoto(media=media_data[0]))
            elif media_data[1] == "video":
              media_group.append(InputMediaVideo(media=media_data[0]))
            elif media_data[1] == "audio":
              media_group.append(InputMediaAudio(media=media_data[0]))
            elif media_data[1] == "document":
              media_group.append(InputMediaDocument(media=media_data[0]))

          media_group[0].caption = f"<b>{subject}</b>\n\n{str(task).capitalize()}"
          media_group[0].parse_mode = "html"

          await message.answer_media_group(media_group)
        else:
          await message.answer(f"<b>{subject}</b>\n\n{str(task).capitalize()}", parse_mode="html")
      await state.clear()

@dp.message(view_homework.day and F.text == "На послезавтра")
async def show_hw_after_tomorrow_handler(message: Message, state: FSMContext):
    sent_message = await message.answer(f"⏳ Обновляю информацию...")
    await update_homework_dates()
    tasks = await get_tasks_by_date(var.calculate_aftertomorrow()[1])
    # print(f"TASKS\t {tasks}")
    if tasks is None:
      await sent_message.edit_text(f"Домашние задания на этот день отсутствуют")
    else:
      await sent_message.edit_text(f"Домашнее задание на <b>{await var.get_day_month(var.calculate_aftertomorrow()[1])}</b>:", parse_mode="html")
      for homework in tasks:
        subject = homework[0]
        task = homework[1]
        # await message.answer(f"<b>{subject}</b>\n\n{str(task).capitalize()}", parse_mode="html")
        if await get_all_media_by_id(homework[2]) is not None:
          media_group_data = await get_all_media_by_id(homework[2])
          media_group = []
          for media_data in media_group_data:
            if media_data[1] == "photo":
              media_group.append(InputMediaPhoto(media=media_data[0]))
            elif media_data[1] == "video":
              media_group.append(InputMediaVideo(media=media_data[0]))
            elif media_data[1] == "audio":
              media_group.append(InputMediaAudio(media=media_data[0]))
            elif media_data[1] == "document":
              media_group.append(InputMediaDocument(media=media_data[0]))

          media_group[0].caption = f"<b>{subject}</b>\n\n{str(task).capitalize()}"
          media_group[0].parse_mode = "html"

          await message.answer_media_group(media_group)
        else:
          await message.answer(f"<b>{subject}</b>\n\n{str(task).capitalize()}", parse_mode="html")
      await state.clear()

@dp.message(view_homework.day and F.text == "🗓 По дате")
async def show_hw_by_date_handler(message: Message, state: FSMContext):
  await state.set_state(view_homework.with_date)
  await message.answer(f'Введи дату в виде "номер_месяца число" без кавычек. Сейчас <b>{datetime.fromtimestamp(var.calculate_today()[1]).strftime("%m")}</b> месяц', parse_mode="html")


@dp.message(F.text == "Назад ↩️")
async def back_handler(message: Message):
  await message.answer("Выбери опцию.", reply_markup=await kb.get_start_keyboard(await get_user_role(message.from_user.id)))

@dp.message(view_homework.with_date)
async def show_hw_by_date(message: Message, state: FSMContext):
    try:
      inted_date_from_user = [int(num) for num in message.text.split(" ")]
    except:
      await message.answer("Попробуй еще раз.")

    while len(inted_date_from_user) > 2:
      await message.answer("Попробуй еще раз.")
    date_time = datetime.strptime(f"{inted_date_from_user[1]}/{inted_date_from_user[0]}/2024, 00:00:00", "%d/%m/%Y, %H:%M:%S")
    # print(inted_date_from_user)
    # print(date_time)
    # print(datetime.timestamp(date_time))
    date_time_timestamp = datetime.timestamp(date_time)
    tasks = await get_tasks_by_date(date_time_timestamp)
    # print(f"TASKS\t {tasks}")
    sent_message = await message.answer(f"⏳ Обновляю информацию...")
    await update_homework_dates()
    if tasks is None:
      await sent_message.edit_text(f"Домашние задания на этот день отсутствуют")
    else:
      await sent_message.edit_text(f"Домашнее задание на <b>{datetime.fromtimestamp(date_time_timestamp).strftime("%d")} {var.months_words[int(datetime.fromtimestamp(date_time_timestamp).strftime("%m"))]}</b>:", parse_mode="html")
      for homework in tasks:
        subject = homework[0]
        task = homework[1]
        if await get_all_media_by_id(homework[2]) is not None:
          media_group_data = await get_all_media_by_id(homework[2])
          media_group = []
          for media_data in media_group_data:
            if media_data[1] == "photo":
              media_group.append(InputMediaPhoto(media=media_data[0]))
            elif media_data[1] == "video":
              media_group.append(InputMediaVideo(media=media_data[0]))
            elif media_data[1] == "audio":
              media_group.append(InputMediaAudio(media=media_data[0]))
            elif media_data[1] == "document":
              media_group.append(InputMediaDocument(media=media_data[0]))
          
          media_group[0].caption = f"<b>{subject}</b>\n\n{str(task).capitalize()}"
          media_group[0].parse_mode = "html"

          await message.answer_media_group(media_group)
        else:
          await message.answer(f"<b>{subject}</b>\n\n{str(task).capitalize()}", parse_mode="html")
    await state.clear()

@dp.message(F.text == 'Добавить Д/З ➕')
async def add_hw_one(message: Message, state: FSMContext):
  if await get_user_role(message.from_user.id) >= 2:
    await state.set_state(adding_homework.subject)
    await message.answer("Выберите предмет:", reply_markup=await kb.allowed_subjects_keyboard(var.allowed_subjects))
    kb.ReplyKeyboardRemove(remove_keyboard=True)

@dp.message(adding_homework.subject)
@dp.callback_query(F.data.in_(var.allowed_subjects))
async def add_hw_two(call: CallbackQuery, state: FSMContext):
  await call.message.delete()
  await call.message.answer(f"Предмет <b>{call.data}</b> выбран.", parse_mode="html")
  await state.update_data(subject=call.data)
  await state.set_state(adding_homework.task)
  await call.message.answer("Напишите домашнее задание <b>(текст обязателен, можно прикрепить медиа)</b>:", parse_mode="html", reply_markup=types.ReplyKeyboardRemove())

@dp.message(F.content_type.in_([CT.PHOTO, CT.VIDEO, CT.AUDIO, CT.DOCUMENT]))
@dp.message(adding_homework.task)
async def add_hw_three(message: Message, state: FSMContext, album: list = None, album_caption: str = None):

  if (await state.get_data()).get("task") is None:
    if album and album_caption:
      await state.update_data(task=album_caption)
    elif message.text != None:
      await state.update_data(task=message.text)
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


@dp.message(F.text == "❌ Удалить Д/З")
async def remove_hw_by_id_handler(message: Message, state: FSMContext):
  if await get_user_role(message.from_user.id) >= 3:
    await state.set_state(removing_homework.hw_id)
    await message.answer("Введите id задания:", reply_markup=kb.back_keyboard)

@dp.message(removing_homework.hw_id)
async def remove_hw_by_id(message: Message, state: FSMContext):
  await state.update_data(hw_id=message.text)
  data = await state.get_data()
  task = await get_homework_by_id(data['hw_id'])

  if await get_all_media_by_id(data["hw_id"]) is not None:
    media_group_data = await get_all_media_by_id(data["hw_id"])
    media_group = []
    for media_data in media_group_data:
      if media_data[1] == "photo":
        media_group.append(InputMediaPhoto(media=media_data[0]))
      elif media_data[1] == "video":
        media_group.append(InputMediaVideo(media=media_data[0]))
      elif media_data[1] == "audio":
        media_group.append(InputMediaAudio(media=media_data[0]))
      elif media_data[1] == "document":
        media_group.append(InputMediaDocument(media=media_data[0]))
    
    media_group[0].caption = f"<b>{task[0]}</b>\n\n{str(task[1]).capitalize()}"
    media_group[0].parse_mode = "html"

    await message.answer_media_group(media_group)
    await message.answer(f"Удалить задание с <b>id {data['hw_id']}</b>?", parse_mode="html", reply_markup=kb.remove_hw_by_id_keyboard)
  else:
    await message.answer(f"Удалить задание с <b>id {data['hw_id']}</b>?\n<b>{task[0]}</b>\n\n{task[1]}", parse_mode="html", reply_markup=kb.remove_hw_by_id_keyboard)

@dp.callback_query(F.data == "delete_hw")
async def delete_hw_by_id(call: CallbackQuery, state: FSMContext):
  # await call.message.delete()
  data = await state.get_data()
  await delete_homework_by_id(data['hw_id'])
  await delete_media_by_id(data['hw_id'])
  await call.message.edit_text("Задание удалено.")
  await state.clear()
  await call.message.answer("Выберите опцию:", reply_markup=await kb.get_start_keyboard(await get_user_role(call.from_user.id)))


# @dp.callback_query(F.data == "add_photo")
# async def add_hw_photo_handler(call: CallbackQuery, state: FSMContext):
#   await call.message.delete()
#   await state.set_state(adding_homework.media_group)
#   await call.message.answer("Отправьте медиа (сгруппированно, одним сообщением)", reply_markup=types.ReplyKeyboardRemove())


@dp.callback_query(F.data == "load_new_week")
async def load_new_week_handler(call: CallbackQuery, state: FSMContext):
  await state.set_state(adding_new_week.file)
  await call.message.answer("Отправьте файл с новой неделей", reply_markup=types.ReplyKeyboardRemove())


  

# @dp.message(adding_homework.media_group and F.content_type.in_([CT.PHOTO, CT.VIDEO, CT.AUDIO, CT.DOCUMENT]))
# async def handle_albums(message: Message, album: list[Message], state: FSMContext):
#     media_group = []
#     for msg in album:
#         if msg.photo:
#             file_id = msg.photo[-1].file_id
#             media_group.append(InputMediaPhoto(media=file_id))
#         else:
#             obj_dict = msg.model_dump()
#             file_id = obj_dict[msg.content_type]['file_id']
#             media_group.append(InputMedia(media=file_id))

#     print("MEDIA GROUP: ", media_group)
#     await message.answer_media_group(media_group)
#     await state.update_data(media_group=media_group)