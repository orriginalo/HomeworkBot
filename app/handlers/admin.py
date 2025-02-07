from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, FSInputFile
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

import app.keyboards as kb
from app.database.models import User
from app.database.queries.user import get_user_by_id, get_users, update_user, add_user, del_user
from app.excel_maker.db_to_excel import create_schedule
from app.excel_maker.formatter import format_table

from utils.backuper import create_backups
from utils.log import logger
from utils.timetable.updater import update_timetable

import asyncio 
import os 
import psutil
from datetime import datetime


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

router = Router(name="Admin")

# ADMIN PANEL CALLBACKS
@router.callback_query(F.data == "show_favs")
async def show_favs(call: CallbackQuery):
    user = await get_user_by_id(call.from_user.id)
    adders = [str(f"[{num}](tg://user?id={num})") for num in await get_users(User.role == 2)]
    admins = [str(f"[{num}](tg://user?id={num})") for num in await get_users(User.role == 3)]

    await call.message.answer(f"*Админы:*\n{"\n".join(admins)}\n\n*Добавлятели:*\n{"\n".join(adders)}", parse_mode="Markdown", reply_markup=await kb.get_start_keyboard(user))

@router.callback_query(F.data == "add_admin")
async def adding_admin_handler(call: CallbackQuery, state: FSMContext):
    await state.set_state(adding_admin.user_id)
    await call.message.answer("Перешлите сообщение или введите id пользователя для добавления:", reply_markup=kb.back_keyboard)

@router.message(adding_admin.user_id)
async def add_admin_id(message: Message, state: FSMContext):
    user = await get_user_by_id(message.from_user.id)
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
      await message.answer(f"✅ Пользователь добавлен в администраторы.", parse_mode="html", reply_markup=await kb.get_start_keyboard(user))
    else:
      await message.answer(f"❌ Пользователь уже является администратором.", parse_mode="html", reply_markup=await kb.get_start_keyboard(user))
    
    await state.clear()

@router.callback_query(F.data == "remove_admin")
async def remove_admin_handler(call: CallbackQuery, state: FSMContext):
    await state.set_state(removing_admin.user_id)
    await call.message.answer("Перешлите сообщение или введите id админа для удаления:", reply_markup=kb.back_keyboard)

@router.message(removing_admin.user_id)
async def remove_admin_id(message: Message, state: FSMContext):
    user = await get_user_by_id(message.from_user.id) 
    if message.forward_from:
      await state.update_data(user_id=message.forward_from.id)
      data = await state.get_data()
    else:
      await state.update_data(user_id=message.text)
      data = await state.get_data()

    user_id = data.get("user_id")
    user_to_remove = await get_user_by_id(user_id)

    if user_to_remove.role == None:
      await message.answer(f"❌ Пользователь не существует или скрыл id.", reply_markup=await kb.get_start_keyboard(user))
      await state.clear()
      return

    elif user_to_remove.role == 3:
      await update_user(user_id, role=1)
      await message.answer(f"✅ Пользователь удален из администраторов.", reply_markup=await kb.get_start_keyboard(user))
    else:
      await message.answer(f"❌ Пользователь не является администратором.", reply_markup=await kb.get_start_keyboard(user))
    
    await state.clear()

@router.callback_query(F.data == "add_adder")
async def add_adder_handler(call: CallbackQuery, state: FSMContext):
    await state.set_state(adding_adder.user_id)
    await call.message.answer("Перешлите сообщение или введите id пользователя для добавления:", reply_markup=kb.back_keyboard)

@router.message(adding_adder.user_id)
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
          await message.answer("❌ Вы не можете сделать этого пользователя добавлятелем, поскольку он не входит в вашу группу.", reply_markup=await kb.get_start_keyboard(user))
          await state.clear()
          return

      if adding_user["role"] == None:
        await message.answer(f"❌ Пользователь не существует или скрыл id.", reply_markup=await kb.get_start_keyboard(user))
        await state.clear()
        return
      
      elif adding_user["role"] >= 3:
        await message.answer(f"🚫 Ошибка", parse_mode="html", reply_markup=await kb.get_start_keyboard(user))
      
      elif adding_user["role"] <= 1:
        await update_user(adding_user_id, role=2)
        await message.answer(f"✅ Пользователь добавлен в добавлятелей.", reply_markup=await kb.get_start_keyboard(user))
      else:
        await message.answer(f"❌ Пользователь уже является добавлятелем.", reply_markup=await kb.get_start_keyboard(user))
    else:
      await message.answer(f"❌ Пользователь не существует, или его нет в базе (пусть напишет боту).", reply_markup=await kb.get_start_keyboard(user))

    await state.clear()


@router.callback_query(F.data == "remove_adder")
async def remove_adder_handler(call: CallbackQuery, state: FSMContext):
    user = await get_user_by_id(call.from_user.id)
    await state.set_state(removing_adder.user_id)
    await call.message.answer("Перешлите сообщение или введите id добавлятеля для удаления:", reply_markup=kb.back_keyboard)

@router.message(removing_adder.user_id)
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
      
      elif adding_user["role"] >= 3:
        await message.answer(f"🚫 Ошибка", parse_mode="html", reply_markup=await kb.get_start_keyboard(user))

      elif adding_user["role"] == 2:
        await update_user(adding_user_id, role=1)
        await message.answer(f"✅ Пользователь удален из добавлятелей.", parse_mode="html", reply_markup=await kb.get_start_keyboard(user))

      else:
        await message.answer(f"❌ Пользователь не является добавлятелем.", parse_mode="html", reply_markup=await kb.get_start_keyboard(user))

    else:
      await message.answer(f"🚫 Пользователь не существует, или его нет в базе (пусть напишет боту).", reply_markup=await kb.get_start_keyboard(user))

    await state.clear()

@router.callback_query(F.data == "server_status")
async def get_server_status_handler(call : CallbackQuery):
  system_usage_info = await get_system_usage()
  await call.message.answer(f"Загруженность сервера:\n<b>CPU</b> - {system_usage_info['cpu_usage']:.1f}%\n<b>Memory</b> - {system_usage_info['memory_usage']}\n", parse_mode="html")

@router.callback_query(F.data == "add_user")
async def add_user_handler(call: CallbackQuery, state: FSMContext):
  await state.set_state(adding_user.user_id)
  await call.message.answer("Перешлите сообщение или введите id пользователя для добавления:", reply_markup=kb.back_keyboard)

@router.message(adding_user.user_id)
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


@router.callback_query(F.data == "remove_user")
async def remove_user_id(call: CallbackQuery, state: FSMContext):
  await state.set_state(removing_user.user_id)
  await call.message.answer("Перешлите сообщение или введите id добавлятеля для удаления:", reply_markup=kb.back_keyboard)


@router.message(removing_user.user_id)
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

@router.callback_query(F.data == "get_db_backup")
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

@router.callback_query(F.data == "get_logs_backup")
async def get_logs_backup_handler(call: CallbackQuery):
  logger.info(f"Uploading .log file to user {call.message.from_user.id}")
  logs_backups_path = "data/logs"
  logs_backup_files = os.listdir(logs_backups_path)
  logs_backup_files.sort()
  last_logs_backup_file = logs_backup_files[-1]
  backup_date_str = last_logs_backup_file.replace("backup_logs_", "").replace(".log", "").replace("_", " ")
  backup_date_time = str(datetime.strptime(backup_date_str, "%Y-%m-%d")).replace("00:00:00", "")
  path_to_file = f"{logs_backups_path}/{last_logs_backup_file}"

  logfile = FSInputFile(path_to_file) 

  await call.message.answer_document(logfile, caption=f"Резервная копия логов <b>{backup_date_time}</b>", parse_mode="html")

@router.callback_query(F.data == "get_data_excel")
async def get_data_excel(call: CallbackQuery):
  msg1 = await call.message.answer("⌛ Создание таблицы...")
  create_schedule()
  await msg1.edit_text("⌛ Форматирование...")
  format_table()
  await msg1.edit_text("⌛ Сохранение...")
  await call.message.answer_document(FSInputFile("domashkabot info.xlsx"), caption="✅ Готово!")
  await msg1.delete()
  
@router.callback_query(F.data == "update_timetable")
async def load_new_week_handler(call: CallbackQuery, state: FSMContext):
  msg = await call.message.answer("⏳ Обновление расписания...")
  try:
    await update_timetable()
    await msg.edit_text("✅ Расписание обновлено.")
    await state.clear()
  except Exception as e: 
    await msg.edit_text(
      f"🚨 <b>Ошибка обновления расписания!</b>\n\n"
      f"▫️ Проверьте формат файла\n"
      f"▫️ Убедитесь в корректности данных\n"
      f"▫️ Попробуйте снова через 5 минут",
      parse_mode="HTML"
    )
    logger.exception(f"Error updating schedule: {e}")
    
@router.callback_query(F.data == "tell_all_users_call")
async def tell_all_users_handler(call: CallbackQuery, state: FSMContext):
  await call.message.delete()
  await call.message.answer("Введите сообщение для всех пользователей")
  await state.set_state(tell_all_users.msg)

@router.message(tell_all_users.msg)
async def tell_all_users_state(message: Message, state: FSMContext):
  await message.delete()
  msg = message
  if msg:
    msg1 = await message.answer("Отправляю сообщение всем пользователям...")
    users = await get_users()
    for user in users:
      await message.answer(f"✉️ <a href='tg://user?id={user['tg_id']}'>{user['tg_id']}</a>...")
      await message.bot.send_message(user["tg_id"], msg)
    await msg1.delete()
    await message.answer("✅ Сообщение отправлено всем пользователям.")
  await state.clear()
  await message.answer("Выберите опцию:", reply_markup=await kb.get_start_keyboard(user))

@router.message(F.text == "secret ❔🔧")
async def secret(message: Message):
  user = await get_user_by_id(message.from_user.id)
  
  msg = """
🎉 <b>DomashkaBot</b> обновился!

▫️ Если у вас не работает какая то команда, попробуйте написать <b>/start</b> или <b>/repair</b> 
▫️ <b>/settings</b> (настройки рассылки) были перенесены в <b>@t1met4ble_bot</b>
▫️ Теперь бот поддерживает все группы КЭИ | УлГТУ.

🔗 Пригласительная ссылка для <code>Пдо-16</code>
👉 https://t.me/homew0rk_bot?start=invite_svmeP8pb_pdo-16
  """
  
  msg_for_adders = """
У тебя, как у <i>добавлятеля</i> появились новые возможности:

▫️ 🔄 Сбросить дедлайн - Перенести Д/З на следующую пару 
▫️ 🗑️ Удалить Д/З - Удалить Д/З 😱
"""

  if user["role"] >= 4:
    message
    users = await get_users()
    for user in users:
      if user["tg_id"] != 1579774985:
        await message.answer(f"✉️ <a href='tg://user?id={user['tg_id']}'>{user['tg_id']}</a>...", parse_mode="html")
        await message.bot.send_message(user["tg_id"], msg, parse_mode="html")
        if user["role"] == 2:
          await message.bot.send_message(user["tg_id"], msg_for_adders, parse_mode="html")
    await message.answer("✅ Сообщение отправлено всем пользователям.")
    await message.answer("Выберите опцию:", reply_markup=await kb.get_start_keyboard(user))