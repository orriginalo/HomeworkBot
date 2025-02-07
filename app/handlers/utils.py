from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from app.database.schemas import UserSchema
import app.keyboards as kb
from app.database.queries.user import get_user_by_id, update_user

router = Router(name="Utils")


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
  
@router.callback_query(F.data.contains("setting"))
async def settings_handler(call: CallbackQuery):
  setting_name = call.data.replace("_setting", "").replace("disable_", "").replace("enable_", "")
  setting_condition = False if call.data.split("_")[0] == "disable" else True
  print(setting_name, setting_condition)
  user = await get_user_by_id(call.from_user.id)
  user_settings = user["settings"]
  user_settings_copy = user_settings.copy()
  match (setting_name):
    case "send_timetable_new_week":
      user_settings_copy["send_timetable_new_week"] = not setting_condition
    case "send_timetable_updated":
      user_settings_copy["send_timetable_updated"] = not setting_condition
    case "send_changes_updated":
      user_settings_copy["send_changes_updated"] = not setting_condition
    case _:
      pass
  user = await update_user(call.from_user.id, settings=user_settings_copy)
  updated_kb = await kb.get_settings_keyboard(user)
  await call.message.edit_reply_markup(reply_markup=updated_kb)
  
  
def check_time_moved(user: UserSchema):
  current_time = datetime.now()
  if user.moved_at is not None and current_time - user.moved_at > timedelta(days=2):
    return True
  else:
    return False