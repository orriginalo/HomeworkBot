from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from app.database.schemas import UserSchema
import app.keyboards as kb
from app.database.queries.user import get_user_by_id, update_user
from app.middlewares import AlbumMiddleware, GroupChecker, MsgLoggerMiddleware
from utils.log import logger


router = Router(name="Utils")

router.message.middleware(MsgLoggerMiddleware())
router.callback_query.middleware(MsgLoggerMiddleware())
router.message.middleware(AlbumMiddleware())
router.message.filter(GroupChecker())

class ChangingLastHomeworksCount(StatesGroup):
  count = State()

@router.callback_query(F.data == "back_to_start")
async def back_to_start(callback: CallbackQuery, state: FSMContext):
  await callback.message.answer("❌ Действие отменено")
  await callback.message.delete()
  await state.clear()
  
  
@router.callback_query(F.data == "back")
async def back(call: CallbackQuery, state: FSMContext):
  user = await get_user_by_id(call.from_user.id)
  await call.message.delete()
  await call.message.answer("❌ Действие отменено.", reply_markup=await kb.get_start_keyboard(user))
  await state.clear()
  
  
@router.message(F.text.contains("Назад"))
async def back_handler(message: Message, state: FSMContext):
  user = await get_user_by_id(message.from_user.id)
  await state.clear()
  await message.answer("Выбери опцию.", reply_markup=await kb.get_start_keyboard(user))
  
@router.message(Command("repair"))
async def repair_bot(message: Message, state: FSMContext):
  await state.clear()
  await message.answer("🔧 Бот починен.")

@router.message(Command("settings"))
async def show_settings(message: Message, state: FSMContext):
  await state.clear()
  user = await get_user_by_id(message.from_user.id)
  await message.answer("🔧 Настройки:", reply_markup=await kb.get_settings_keyboard(user))
# User settings: {"send_timetable_new_week": false, "send_timetable_updated": false, "send_changes_updated": false}

@router.callback_query(F.data.contains("setting"))
async def settings_handler(call: CallbackQuery):
  setting_name = call.data.replace("_setting", "").replace("disable_", "").replace("enable_", "")
  setting_condition = False if call.data.split("_")[0] == "disable" else True
  user = await get_user_by_id(call.from_user.id)
  logger.debug(f"User {user.username} (id {user.tg_id}) changing setting {setting_name} to {not setting_condition}")
  user_settings = user.settings
  user_settings_copy = user_settings.copy()
  match (setting_name):
    case "send_timetable_new_week":
      user_settings_copy["send_timetable_new_week"] = not setting_condition
    case "send_timetable_updated":
      user_settings_copy["send_timetable_updated"] = not setting_condition
    case "send_changes_updated":
      user_settings_copy["send_changes_updated"] = not setting_condition
    case "change_ids_visibility":
      user_settings_copy["change_ids_visibility"] = not setting_condition
    case _:
      pass
  user = await update_user(call.from_user.id, settings=user_settings_copy)
  updated_kb = await kb.get_settings_keyboard(user)
  await call.message.edit_reply_markup(reply_markup=updated_kb)
  
@router.callback_query(F.data == "change_last_homeworks_count")
async def _(call: CallbackQuery, state: FSMContext):
  user = await get_user_by_id(call.from_user.id)
  await state.set_state(ChangingLastHomeworksCount.count)
  await call.message.answer(f"Введите кол-во отображаемых последних Д/З\n<i>Текущее значение: {user.settings['last_homeworks_count']}</i>", parse_mode="html")
  
@router.message(ChangingLastHomeworksCount.count)
async def _(message: Message, state: FSMContext):
  user = await get_user_by_id(message.from_user.id)
  num: int = None
  try:
    num = int(message.text.strip())
  except:
    await message.answer("❌ Неверный ввод. Попробуй еще раз.")
    return
  
  await state.update_data(count=message.text)
  settings_copy = user.settings.copy()
  settings_copy["last_homeworks_count"] = num
  user = await update_user(user.tg_id, settings=settings_copy)
  await message.answer(f"✅ Кол-во последних Д/З изменено на <b>{num}</b>.", parse_mode="html", reply_markup=await kb.get_start_keyboard(user))
  
def check_time_moved(user: UserSchema):
  current_time = datetime.now()
  if user.moved_at is not None and current_time - user.moved_at > timedelta(days=2):
    return True
  else:
    return False