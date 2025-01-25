import aiogram.exceptions
from app.database.requests.homework import *
from app.database.requests.subjects import get_subject_by_id
from app.database.requests.user import *
from app.database.requests.other import *
from app.database.requests.media import *
from app.database.requests.groups import *
import variables as var
import app.keyboards as kb
from app.backuper import create_backups, update_timetable_job
from app.middlewares import AlbumMiddleware, AntiFloodMiddleware, TestMiddleware, MsgLoggerMiddleware
import os
import sys
import time

import aiogram
from aiogram import F, types, Router
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import Message, CallbackQuery, FSInputFile, LabeledPrice, InputMediaPhoto, InputMediaVideo, InputMediaDocument, InputMedia, InputMediaAudio, ContentType as CT
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from app.excel_maker.db_to_excel import create_schedule
from app.excel_maker.formatter import format_table

from utils.referal import generate_unique_code, get_referal_link
from utils.db_subject_populator import populate_schedule
from utils.timetable_downloader import download_timetable
from utils.timetable_parser import parse_timetable
from utils.db_subject_populator import populate_schedule
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

import psutil


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

class tell_all_users(StatesGroup):
  msg = State()

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


class setting_group(StatesGroup):
  group_name = State()

class transferring_leadership(StatesGroup):
  user_id = State()

dp = Router()

dp.message.middleware(AlbumMiddleware())
dp.message.middleware(MsgLoggerMiddleware())
# dp.message.middleware(AntiFloodMiddleware(0.3))
# dp.message.middleware(TestMiddleware())
notifications_scheduler = AsyncIOScheduler()

@dp.message(CommandStart())
async def start(message: Message, state: FSMContext, user):
  print(user)
  await state.clear()
  if (await get_user_by_id(message.from_user.id))["role"] != 0:

    # If referal
    args = message.text.split()
    if len(args) > 1 and args[0] == "/start":
      ref_code = args[1]
      ref_code = ref_code[4:]
      group = await get_group_by_ref(ref_code)

      if group:
        if user["group_id"]:
          if group["uid"] == user["group_id"]:
            await message.answer("Вы уже присоеденены к этой группе!")
          else:
            await message.answer("Вы хотите присоединиться к другой группе? Менять группу можно раз в 48 часов.")
        else:
          await message.answer(f"Вы хотите присоединиться к группе <b>{group['name']}</b>?\n<i>В случае присоединения, вы не сможете сменить группу в следующие 48 часов.</i>", parse_mode="html", reply_markup=kb.do_join_to_group_keyboard)
          
          await update_user(user["tg_id"], group_id=group["uid"])
          await state.clear()
      else:
        await message.answer("Недействительная ссылка на вступление в группу.")


    else:
      if (await get_user_by_id(message.from_user.id))["group_id"] is None:
        await message.answer("Привет! Напиши название своей группы (например пдо-16, рэсдо-12, исдо-22)")
        await state.set_state(setting_group.group_name)
      else:
        await message.answer("Тут можно посмотреть домашнее задание. Выбери опцию.", reply_markup=await kb.get_start_keyboard(user))

@dp.callback_query(F.data == "join_group")
async def join_group_handler(call: CallbackQuery):
  user = await get_user_by_id(call.from_user.id)
  group = await get_group_by_id(user["group_id"])
  await call.message.delete()
  await call.message.answer(f"🎉 Вы присоединились к группе <b>{group['name']}</b>", parse_mode="html", reply_markup=await kb.get_start_keyboard(user))

@dp.callback_query(F.data == "transfer_leadership")
async def transfer_leadership_handler(call: CallbackQuery, state: FSMContext):
  user = await get_user_by_id(call.from_user.id)
  group = await get_group_by_id(user["group_id"])
  await call.message.delete()
  await call.message.answer(f"Отправьте телеграм id человека или перешлите его сообщение для передачи прав лидерства.", parse_mode="html", reply_markup=await kb.get_start_keyboard(user))
  await state.set_state(transferring_leadership.user_id)

@dp.message(transferring_leadership.user_id)
async def transfer_leadership(message: Message, state: FSMContext):
  user = await get_user_by_id(message.from_user.id)
  group = await get_group_by_id(user["group_id"])
  
  future_leader_id = None
  if message.forward_from:
    future_leader_id = message.forward_from.id
  else:
    future_leader_id = message.text

  try:
    future_leader = await get_user_by_id(int(future_leader_id))
  except:
    await message.answer("❌ Неверный id пользователя.")
  if future_leader is None:
    await message.answer("❌ Пользователь не существует, или его нет в базе.")
    await state.clear()
    return
  elif future_leader["group_id"] != user["group_id"]:
    await message.answer("❌ Вы не можете передать права лидерства человеку который находится в другой группе.")
    await state.clear()
    return
  
  await state.update_data(user_id=future_leader["tg_id"])
  await message.answer(f"❗Вы уверены что хотите передать права лидерства <a href='tg://user?id={future_leader['tg_id']}'>{future_leader['firstname'] if future_leader['firstname'] else ''} {future_leader['lastname'] if future_leader['lastname'] else ''}</a>❓", parse_mode="html", reply_markup=kb.transfer_leadership_confirm_keyboard)

@dp.callback_query(F.data == "transfer_leadership_confirm")
async def transfer_leadership_confirm_handler(call: CallbackQuery, state: FSMContext):
  user = await get_user_by_id(call.from_user.id)
  group = await get_group_by_id(user["group_id"])
  data = await state.get_data()
  future_leader_id = data["user_id"]

  future_leader = await get_user_by_id(future_leader_id)

  await call.message.delete()
  await update_user(user["tg_id"], is_leader=False)
  await update_user(future_leader_id, is_leader=True, role=2)
  await update_group(group["uid"], leader_id=future_leader_id)
  await call.message.answer("✅ Права лидерства переданы.", reply_markup=await kb.get_start_keyboard(user))
  await state.clear()

@dp.message(setting_group.group_name)
async def set_group_name(message: Message, state: FSMContext):
  if (await state.get_data()).get("group_name") is not None:
    return
  all_groups = await get_all_groups()
  all_groups_names = [group["name"].lower() for group in all_groups]
  if message.text.strip().lower() in all_groups_names:
    await state.update_data(group_name=message.text.strip().lower())
    group = await get_group_by_name(message.text.strip().lower())
    if group:
      if group["is_equipped"]:
        await message.answer("Эта группа уже зарегистрирована в системе. Запросите ссылку на вступление у <i>лидера</i> группы.", parse_mode="html")
        await state.clear()
      else:
        await message.answer("Эта группа еще не зарегистрирована в системе, при подтверждении вы станете <b>лидером</b> группы \n\n(о том что может лидер группы вы можете узнать в /info)", parse_mode="html", reply_markup=kb.create_group_keyboard)
  else:
    await message.answer("❌ Такая группа не найдена, попробуй еще раз.")

@dp.callback_query(F.data == "create_group")
async def create_group_handler(callback: CallbackQuery, state: FSMContext):
  user = await get_user_by_id(callback.from_user.id)
  await callback.message.delete()
  msg = await callback.message.answer(f"⌛ Создание группы...")
  try:
    data = await state.get_data()
    group = await get_group_by_name(data["group_name"])

    referal_code = await generate_unique_code()
    referal_link = await get_referal_link(referal_code)
    
    await update_group(group["uid"], ref_code=referal_code, is_equipped=True, member_count=group["member_count"] + 1, leader_id=callback.from_user.id)
    user = await update_user(callback.from_user.id, role=2, group_id=group["uid"], is_leader=True)

    await update_timetable_job()

    await msg.edit_text("✅ Группа создана!")
    
    await callback.message.answer(f"🔗 <b>Ссылка для вступления:</b>\n👉{referal_link}", parse_mode="html", reply_markup=await kb.get_start_keyboard(user))
  except Exception as e:
    await msg.edit_text(f"❌ Ошибка создания группы")
    logging.ERROR("Error creating group: ", e)

  await state.clear()

@dp.callback_query(F.data == "back_to_start")
async def back_to_start(callback: CallbackQuery, state: FSMContext):
  await callback.message.answer("❌ Действие отменено")

  await state.clear()

@dp.message(F.text == "Админ-панель 😈")
async def show_admin_panel(message: Message):
  if (await get_user_by_id(message.from_user.id))["role"] == 3:
    await message.answer("Админ-панель:", reply_markup=kb.adminka_keyboard)
  if (await get_user_by_id(message.from_user.id))["role"] == 4:
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
    await asyncio.sleep(1)
    await n1_msg.edit_text("⏳ Обновление расписания...")
    await populate_schedule(file_name)
    await n1_msg.edit_text("✅ Расписание обновлено.")
    await state.clear()
  except Exception as e:
    print(e)
    await message.answer("❌ Не удалось обновить расписание.")

@dp.callback_query(F.data == "back")
async def back(call: CallbackQuery, state: FSMContext):
  user = await get_user_by_id(call.from_user.id)
  await call.message.delete()
  await call.message.answer("❌ Действие отменено.", reply_markup=await kb.get_start_keyboard(user))
  await state.clear()

@dp.callback_query(F.data == "change_subject")
async def change_subject(call: CallbackQuery, state: FSMContext):
  user = await get_user_by_id(call.from_user.id)
  await state.set_state(adding_homework.subject)
  await call.message.delete()
  subjects = (await get_group_by_id(user["group_id"]))["subjects"]
  await call.message.answer("🔄 Выберите предмет:", reply_markup=await kb.allowed_subjects_change_keyboard(subjects))

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
  user = await get_user_by_id(call.from_user.id)

  homework = await add_homework(subject, task, user["group_id"], call.from_user.id, var.calculate_today()[1])
  homework_id = homework["uid"]

  if data.get("media_group") is not None:
    for media in data.get("media_group"):
      await add_media(homework_id, media.media, media.type)

  await call.message.answer(f"✅ <b>Домашнее задание добавлено.</b>", parse_mode="html") # в базу
  await call.message.answer(f"Выбери опцию.", reply_markup=await kb.get_start_keyboard(user))
  await call.message.delete()
  admins = await get_users_with_role(3)
  admins += await get_users_with_role(4)
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
    adders = [str(f"[{num}](tg://user?id={num})") for num in await get_users_with_role(2)]
    admins = [str(f"[{num}](tg://user?id={num})") for num in await get_users_with_role(3)]

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

    user_role = (await get_user_by_id(user_id))["role"]
    if user_role == None:
      await message.answer(f"❌ Пользователь не существует или скрыл id.")
      await state.clear()
      return

    elif user_role <= 2:
      await update_user(user_id, role=3)
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

    user_role = (await get_user_by_id(user_id))["role"]
    if user_role == None:
      await message.answer(f"❌ Пользователь не существует или скрыл id.")
      await state.clear()
      return

    elif user_role == 3:
      await update_user(user_id, role=1)
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
    user = await get_user_by_id(message.from_user.id)
    if message.forward_from:
      await state.update_data(user_id=message.forward_from.id)
      data = await state.get_data()
    else:
      await state.update_data(user_id=message.text)
      data = await state.get_data()
    
    adding_user_id = data.get("user_id")

    adding_user = (await get_user_by_id(adding_user_id))

    if adding_user:
      if user["role"] <= 3:
        if adding_user["group_id"] != user["group_id"]:
          await message.answer("❌ Вы не можете сделать этого пользователя добавлятелем, поскольку он не входит в вашу группу.")
          await state.clear()
          return

      if adding_user["role"] == None:
        await message.answer(f"❌ Пользователь не существует или скрыл id.")
        await state.clear()
        return
      
      elif adding_user["role"] <= 1:
        await update_user(adding_user_id, role=2)
        await message.answer(f"✅ Пользователь добавлен в добавлятелей.")
      else:
        await message.answer(f"❌ Пользователь уже является добавлятелем.")
    else:
      await message.answer(f"❌ Пользователь не существует, или его нет в базе (пусть напишет боту).")

    await state.clear()


@dp.callback_query(F.data == "remove_adder")
async def remove_adder_handler(call: CallbackQuery, state: FSMContext):
    await state.set_state(removing_adder.user_id)
    await call.message.answer("Перешлите сообщение или введите id добавлятеля для удаления:", reply_markup=types.ReplyKeyboardRemove())

@dp.message(removing_adder.user_id)
async def remove_adder_id(message: Message, state: FSMContext):
    user = await get_user_by_id(message.from_user.id)
    if message.forward_from:
      await state.update_data(user_id=message.forward_from.id)
      data = await state.get_data()
    else:
      await state.update_data(user_id=message.text)
      data = await state.get_data()
    
    adding_user_id = data.get("user_id")

    adding_user = (await get_user_by_id(adding_user_id))

    if adding_user:
      if user["role"] <= 3:
        if adding_user["group_id"] != user["group_id"]:
          await message.answer("❌ Вы не можете удалить роль добавлятеля у этого пользователя, поскольку он не входит в вашу группу.")
          await state.clear()
          return

      if adding_user["role"] == None:
        await message.answer(f"❌ Пользователь скрыл id.")
        await state.clear()
        return
 
      elif adding_user["role"] == 2:
        await update_user(adding_user_id, role=1)
        await message.answer(f"✅ Пользователь удален из добавлятелей.", parse_mode="html")
      else:
        await message.answer(f"❌ Пользователь не является добавлятелем.", parse_mode="html")
    else:
      await message.answer(f"❌ Пользователь не существует, или его нет в базе (пусть напишет боту).")

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

  if await get_user_by_id(user_id):
    await message.answer(f"❌ Пользователь уже существует.")
  else:
    await add_user(user_id, 1)
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

  if await get_user_by_id(user_id):
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
  backup_date_time = str(datetime.strptime(backup_date_str, "%Y-%m-%d")).replace("00:00:00", "")
  path_to_file = f"{logs_backups_path}/{last_logs_backup_file}"

  logfile = FSInputFile(path_to_file) 

  await call.message.answer_document(logfile, caption=f"Резервная копия логов <b>{backup_date_time}</b>", parse_mode="html")

@dp.callback_query(F.data == "get_data_excel")
async def get_data_excel(call: CallbackQuery):
  msg1 = await call.message.answer("⌛ Создание таблицы...")
  create_schedule()
  await msg1.edit_text("⌛ Форматирование...")
  format_table()
  await msg1.edit_text("⌛ Сохранение...")
  await call.message.answer_document(FSInputFile("domashkabot info.xlsx"), caption="✅ Готово!")
  await msg1.delete()

@dp.callback_query(F.data.contains("-changed"))
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

@dp.message(F.text == '👀 Посмотреть Д/З')
async def show_homework_handler(message: Message, state: FSMContext):
  await state.set_state(view_homework.day)
  await message.answer ("Выбери вариант.", reply_markup=kb.see_hw_keyboard)

@dp.callback_query(F.data == "by_date")
async def checK_hw_by_date_handler(call: CallbackQuery, state: FSMContext):
  await state.set_state(view_homework.day)
  await call.message.answer("Выберите день", reply_markup=kb.see_hw_keyboard)

# @dp.callback_query(F.data == "by_subject")
@dp.message(F.text == "Посмотреть по предмету")
async def check_hw_by_subject_handler(message: Message):
  user = await get_user_by_id(message.from_user.id)
  group = await get_group_by_id(user["group_id"])
  print(group)
  subjects = group["subjects"]
  print(subjects) 
  await message.answer("Выбери предмет по которому\nхочешь посмотреть Д/З", reply_markup=await kb.allowed_subjects_check_hw_keyboard(subjects))

@dp.callback_query(F.data.contains("-check-hw"))
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

          media_group[0].caption = f"Добавлено <b>{datetime.fromtimestamp(homework["from_date"]).strftime("%d.%m.%Y")}</b> " + ("<i>(последнее)</i>" if homework == homeworks[-1] else "")  + (f" <i>id {hw_uid}</i>" if user_role >= 3 else "") + f"\n\n{hw_task}"
          media_group[0].parse_mode = "html"

          await call.message.answer_media_group(media_group)
      else:
        await call.message.answer(f"Добавлено <b>{datetime.fromtimestamp(homework["from_date"]).strftime("%d.%m.%Y")}</b> " + ("<i>(последнее)</i>" if homework == homeworks[-1] else "")  + (f" <i>id {hw_uid}</i>" if user_role >= 3 else "") + f"\n\n{hw_task}", parse_mode="html")
  else:
    await call.message.answer(f"Домашнее задание по <b>{subject_name}</b> отсутствует", parse_mode="html")

@dp.message(view_homework.day and F.text == "На сегодня")
async def show_hw_today_handler(message: Message, state: FSMContext):
    user = await get_user_by_id(message.from_user.id)
    sent_message = await message.answer(f"⏳ Обновляю информацию...")
    await update_homework_dates()
    # tasks = await get_tasks_by_date(var.calculate_today()[1])
    tasks = await get_homeworks_by_date(var.calculate_today()[1], group_id=user["group_id"])
    user_role = (await get_user_by_id(message.from_user.id))["role"]
    # print(f"TASKS\t {tasks}")
    if tasks is None or len(tasks) == 0:
      await sent_message.edit_text(f"Домашние задания на этот день отсутствуют")
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

          media_group[0].caption = f"<b>{subject}</b>" + (f" <i>id {task_id}</i>" if user_role >= 3 else "") + f"\n\n{str(task)}"
          media_group[0].parse_mode = "html"

          await message.answer_media_group(media_group)
        else:
          await message.answer(f"<b>{subject}</b>" + (f" <i>id {task_id}</i>" if user_role >= 3 else "") + f"\n\n{str(task)}", parse_mode="html")
      await state.clear()

@dp.message(view_homework.day and F.text == "На завтра")
async def show_hw_tomorrow_handler(message: Message, state: FSMContext):
    user = await get_user_by_id(message.from_user.id)
    sent_message = await message.answer(f"⏳ Обновляю информацию...")
    await update_homework_dates()
    # tasks = await get_tasks_by_date(var.calculate_today()[1])
    tasks = await get_homeworks_by_date(var.calculate_tomorrow()[1], group_id=user["group_id"])
    user_role = (await get_user_by_id(message.from_user.id))["role"]
    # print(f"TASKS\t {tasks}")
    if tasks is None or len(tasks) == 0:
      await sent_message.edit_text(f"Домашние задания на этот день отсутствуют")
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

          media_group[0].caption = f"<b>{subject}</b>" + (f" <i>id {task_id}</i>" if user_role >= 3 else "") + f"\n\n{str(task)}"
          media_group[0].parse_mode = "html"

          await message.answer_media_group(media_group)
        else:
          await message.answer(f"<b>{subject}</b>" + (f" <i>id {task_id}</i>" if user_role >= 3 else "") + f"\n\n{str(task)}", parse_mode="html")
      await state.clear()

@dp.message(view_homework.day and F.text == "На послезавтра")
async def show_hw_after_tomorrow_handler(message: Message, state: FSMContext):
    user = await get_user_by_id(message.from_user.id)
    sent_message = await message.answer(f"⏳ Обновляю информацию...")
    await update_homework_dates()
    # tasks = await get_tasks_by_date(var.calculate_today()[1])
    tasks = await get_homeworks_by_date(var.calculate_aftertomorrow()[1], group_id=user["group_id"])
    user_role = (await get_user_by_id(message.from_user.id))["role"]
    # print(f"TASKS\t {tasks}")
    if tasks is None or len(tasks) == 0:
      await sent_message.edit_text(f"Домашние задания на этот день отсутствуют")
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

          media_group[0].caption = f"<b>{subject}</b>" + (f" <i>id {task_id}</i>" if user_role >= 3 else "") + f"\n\n{str(task)}"
          media_group[0].parse_mode = "html"

          await message.answer_media_group(media_group)
        else:
          await message.answer(f"<b>{subject}</b>" + (f" <i>id {task_id}</i>" if user_role >= 3 else "") + f"\n\n{str(task)}", parse_mode="html")
      await state.clear()

@dp.message(view_homework.day and F.text == "🗓 По дате")
async def show_hw_by_date_handler(message: Message, state: FSMContext):
  await state.set_state(view_homework.with_date)
  await message.answer(f'Введи дату в виде "номер_месяца число" без кавычек. Сейчас <b>{datetime.fromtimestamp(var.calculate_today()[1]).strftime("%m")}</b> месяц', parse_mode="html")


@dp.message(F.text == "Назад ↩️")
async def back_handler(message: Message, state: FSMContext):
  user = await get_user_by_id(message.from_user.id)
  await state.clear()
  await message.answer("Выбери опцию.", reply_markup=await kb.get_start_keyboard(user))

@dp.message(view_homework.with_date)
async def show_hw_by_date(message: Message, state: FSMContext):
    user = await get_user_by_id(message.from_user.id)
    user_role = user["role"]
    try:
      inted_date_from_user = [int(num) for num in message.text.split(" ")]
    except:
      await message.answer("Попробуй еще раз.")

    while len(inted_date_from_user) > 2:
      await message.answer("Попробуй еще раз.")
    date_time = datetime.strptime(f"{inted_date_from_user[1]}/{inted_date_from_user[0]}/2024, 00:00:00", "%d/%m/%Y, %H:%M:%S")
    date_time_timestamp = datetime.timestamp(date_time)
    tasks = await get_homeworks_by_date(date_time_timestamp, group_id=user["group_id"])
    sent_message = await message.answer(f"⏳ Обновляю информацию...")
    await update_homework_dates()
    if tasks is None or len(tasks) == 0:
      await sent_message.edit_text(f"Домашние задания на этот день отсутствуют")
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
          
          media_group[0].caption = f"<b>{subject}</b>" + (f" <i>id {task_id}</i>" if user_role >= 3 else "") + f"\n\n{str(task)}"
          media_group[0].parse_mode = "html"

          await message.answer_media_group(media_group)
        else:
          await message.answer(f"<b>{subject}</b>" + (f" <i>id {task_id}</i>" if user_role >= 3 else "") + f"\n\n{str(task)}", parse_mode="html")
    await state.clear()

@dp.message(F.text == 'Добавить Д/З ➕')
async def add_hw_one(message: Message, state: FSMContext):
  user = await get_user_by_id(message.from_user.id)
  if (await get_user_by_id(message.from_user.id))["role"] >= 2:
    await state.set_state(adding_homework.subject)
    subjects = (await get_group_by_id(user["group_id"]))["subjects"]
    await message.answer("Выберите предмет:", reply_markup=await kb.allowed_subjects_keyboard(subjects))
    kb.ReplyKeyboardRemove(remove_keyboard=True)

@dp.callback_query(adding_homework.subject)
@dp.callback_query(F.data.contains("-add"))
async def add_hw_two(call: CallbackQuery, state: FSMContext):
  await call.message.delete()
  subject = await get_subject_by_id(int(call.data.replace("-add", "")))
  subject_name = subject["name"]
  
  await call.message.answer(f"Предмет <b>{subject_name}</b> выбран.", parse_mode="html")
  await state.update_data(subject=subject_name)
  await state.set_state(adding_homework.task)
  await call.message.answer("Напишите домашнее задание <b>(текст обязателен, можно прикрепить медиа)</b>:", parse_mode="html", reply_markup=types.ReplyKeyboardRemove())

@dp.message(F.content_type.in_([CT.PHOTO, CT.VIDEO, CT.AUDIO, CT.DOCUMENT]))
@dp.message(adding_homework.task)
async def add_hw_three(message: Message, state: FSMContext, album: list = None, album_caption: str = None):

  if message.content_type == "sticker":
    await message.answer("Нельзя прикрепить стикер.")


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


@dp.message(F.text == "❌ Удалить Д/З")
async def remove_hw_by_id_handler(message: Message, state: FSMContext):
  if (await get_user_by_id(message.from_user.id))["role"] >= 3:
    await state.set_state(removing_homework.hw_id)
    await message.answer("Введите id задания:", reply_markup=kb.back_keyboard)

@dp.message(removing_homework.hw_id)
async def remove_hw_by_id(message: Message, state: FSMContext):
  await state.update_data(hw_id=message.text)
  data = await state.get_data()

  hw_uid = int(data["hw_id"])
  print(f"getting homework by id {hw_uid}")
  homework = await get_homework_by_id(hw_uid)

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

@dp.callback_query(F.data == "delete_hw")
async def delete_hw_by_id(call: CallbackQuery, state: FSMContext):
  user = await get_user_by_id(call.from_user.id)
  # await call.message.delete()
  data = await state.get_data()

  print(type(data['hw_id']), data['hw_id'])
  print(type(int(data['hw_id'])), int(data['hw_id']))
  
  await del_homework(int(data['hw_id']))
  await del_media(int(data['hw_id']))
  await call.message.edit_text("Задание удалено.")
  await state.clear()
  await call.message.answer("Выберите опцию:", reply_markup=await kb.get_start_keyboard(user))

@dp.callback_query(F.data == "update_timetable")
async def load_new_week_handler(call: CallbackQuery, state: FSMContext):
  msg = await call.message.answer("⏳ Обновление расписания...")
  try:
    await update_timetable_job()
    await msg.edit_text("✅ Расписание обновлено.")
    await state.clear()
  except Exception as e: 
    await msg.edit_text("❌ Ошибка при обновлении расписания.")

@dp.message(F.text == "👑 Управление группой 👑")
async def show_group_controller_handler(message: CallbackQuery):
  user = await get_user_by_id(message.from_user.id)
  group = await get_group_by_id(user["group_id"])
  all_users_in_group = await get_users(User.group_id == user["group_id"])

  all_users_in_group_id = [user["tg_id"] for user in all_users_in_group]

  def get_link(user_id, firstname, lastname):
    if firstname == None:
      return f"<a href='tg://user?id={user_id}'>{lastname}</a>"
    elif lastname == None:
      return f"<a href='tg://user?id={user_id}'>{firstname}</a>"
    elif firstname == None and lastname == None:
      return f"<a href='tg://user?id={user_id}'>{user_id}</a>"
    else:
      # return f"[{firstname} {lastname}](tg://user?id={user_id})\n"
      return f"<a href='tg://user?id={user_id}'>{firstname} {lastname}</a>"

  users_links = [get_link(user_id, user["firstname"], user["lastname"]) for user_id in all_users_in_group_id]
  users_links = "\n".join(users_links)

  await message.answer(f"<b>👑 Управление группой</b>\n\nГруппа:  <b>{group['name']}</b>\nУчастники:\n{users_links}", parse_mode="html", reply_markup=kb.group_controller_keyboard)

@dp.callback_query(F.data == "get_group_link")
async def get_group_link_handler(call: CallbackQuery):
  user = await get_user_by_id(call.from_user.id)
  group = await get_group_by_id(user["group_id"])
  referal_link = await get_referal_link(group["ref_code"])
  await call.message.answer(f"🔗 <b>Ссылка для вступления:</b>\n👉{referal_link}", parse_mode="html", reply_markup=await kb.get_start_keyboard(user))

@dp.message(F.text == "🔄 Сбросить дедлайн Д/З 🔄")
async def reset_deadline_handler(message: Message, state: FSMContext):
  await message.answer("Введите id задания:", reply_markup=kb.back_keyboard)
  await state.set_state(resetting_deadline.hw_id)


@dp.message(resetting_deadline.hw_id)
async def reset_deadline(message: Message, state: FSMContext):
    user = await get_user_by_id(message.from_user.id)
    await state.update_data(hw_id=message.text)
    data = await state.get_data()
    await reset_homework_deadline_by_id(data['hw_id'])
    await message.answer("✅ Дата сдачи сброшена.")
    # await update_homework_dates()
    deadline = (await get_homework_by_id(data['hw_id']))["to_date"]
    new_deadline_text = f"Новая дата сдачи: {(str(datetime.fromtimestamp(deadline)) if deadline is not None else 'отсутствует').replace("00:00:00", "")}"
    await message.answer(new_deadline_text)
    await state.clear()
    await message.answer("Выберите опцию:", reply_markup=await kb.get_start_keyboard(user))

@dp.message(Command("repair"))
async def repair_bot(message: Message, command: CommandObject, state: FSMContext):
  await state.clear()
  await message.answer("🔧 Бот починен.")

@dp.message(Command("settings"))
async def show_settings(message: Message, command: CommandObject, state: FSMContext):
  await state.clear()
  await message.answer("🔧 Настройки:", reply_markup=await kb.get_settings_keyboard((await get_user_by_id(message.from_user.id))["notifications"]))

@dp.callback_query(F.data == "enable_notifications")
async def enable_notifications(call: CallbackQuery):
    # Включаем рассылку
    await update_user(call.from_user.id, notifications=True)

    updated_keyboard = await kb.get_settings_keyboard(True)
    await call.message.edit_reply_markup(reply_markup=updated_keyboard)
    await call.message.answer("✅ Рассылка расписания включена.")

@dp.callback_query(F.data == "disable_notifications")
async def disable_notifications(call: CallbackQuery):
    # Отключаем рассылку
    await update_user(call.from_user.id, notifications=True)

    updated_keyboard = await kb.get_settings_keyboard(False)
    await call.message.edit_reply_markup(reply_markup=updated_keyboard)
    await call.message.answer("✅ Рассылка расписания отключена.")


@dp.callback_query(F.data == "tell_all_users_call")
async def tell_all_users_handler(call: CallbackQuery, state: StatesGroup):
  await call.message.delete()
  await call.message.answer("Введите сообщение для всех пользователей")
  await state.set_state(tell_all_users.msg)

@dp.message(tell_all_users.msg)
async def tell_all_users_state(message: Message, state: FSMContext):
  await message.delete()
  msg = message.text
  if msg:
    await message.answer("Отправляю сообщение всем пользователям...")
    users = await get_users()
    for user in users:
      await message.answer(f"✉️ {user}...")
      await message.bot.send_message(user["tg_id"], msg)
    await message.answer("✅ Сообщение отправлено всем пользователям.")
  await state.clear()
  await message.answer("Выберите опцию:", reply_markup=await kb.get_start_keyboard(user))


# @dp.callback_query(F.data == "donate_cancel")
# async def donate_cancel_handler(call: CallbackQuery):
#   await call.message.delete()
#   await call.message.answer("❌ Действие отменено.")
#   await call.message.answer("Выберите опцию:", reply_markup=await kb.get_start_keyboard(user))


# @dp.message(Command("donate", "donat", "донат"))
# async def donate(message: Message, command: CommandObject):
#   if command.args is None or not command.args.isdigit() or not 1 <= int(command.args) <= 2500:
#     await message.answer("Ошибка")
#     return
#   amount = int(command.args)

#   prices = [LabeledPrice(label="XTR", amount=amount)]
#   await message.answer_invoice(
#     title="Поддержать донатиком",
#     description="",
#     prices=prices,
#     provider_token="",
#     payload=f"{amount} stars",
#     currency="XTR",
#     reply_markup=kb.donate_keyboard)