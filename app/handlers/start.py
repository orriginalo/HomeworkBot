from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart

from app.database.queries.group import get_all_groups, get_group_by_name, get_group_by_ref
from app.handlers.utils import check_time_moved
import app.keyboards as kb
from app.database.queries.user import get_user_by_id

import re

class joiningToGroup(StatesGroup):
  group_name = State()

class setting_group(StatesGroup):
  group_name = State()

router = Router(name="Start")

@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
  user = await get_user_by_id(message.from_user.id)

  await state.clear()
  if user.role != 0:

    # If referal
    args = message.text.split()
    if len(args) > 1 and args[0] == "/start":
      ref_code = args[1]
      match = re.search(r'invite_([a-zA-Z0-9]+)_', ref_code)
      ref_code = match.group(1) if match else ""
      group = await get_group_by_ref(ref_code)

      if group:
        if user.group_id:
          if group.uid == user.group_id:
            await message.answer("Вы уже присоеденены к этой группе!")
          else:
            if user.is_leader:
              await message.answer("Вы сможете присоединиться к другой группе как только передадите права лидерства другому человеку.") 
            else:
              if check_time_moved(user):
                await message.answer(f"Вы хотите присоединиться к другой группе (<b>{group.name}</b>)?\n<i>В случае присоединения, вы не сможете сменить группу в следующие 48 часов.</i>", parse_mode="html", reply_markup=kb.do_join_to_group_keyboard)
                await state.set_state(joiningToGroup.group_name)
                await state.update_data(group_name=group.name)
              else:
                await message.answer(f"Вы временно не можете изменять группу\n<i>Ограничение на 48 часов</i>", parse_mode="html", reply_markup=await kb.get_start_keyboard(user))
        else:
          await message.answer(f"Вы хотите присоединиться к группе <b>{group.name}</b>?\n<i>В случае присоединения, вы не сможете сменить группу в следующие 48 часов.</i>", parse_mode="html", reply_markup=kb.do_join_to_group_keyboard)
          await state.set_state(joiningToGroup.group_name)
          await state.update_data(group_name=group.name)
      else:
        await message.answer("Недействительная ссылка на вступление в группу.")


    else:
      if user.group_id is None:
        await message.answer(
            f"👋 <b>Добро пожаловать в DomashkaBot!</b>\n\n"
            f"📝 Для начала работы укажи <i>название своей группы</i> (например: <code>пдо-16</code>, <code>рэсдо-12</code>):",
            parse_mode="HTML"
        )
        await state.set_state(setting_group.group_name)
      else:
        await message.answer("Тут можно посмотреть домашнее задание. Выбери опцию.", reply_markup=await kb.get_start_keyboard(user))
        
@router.message(setting_group.group_name)
async def set_group_name(message: Message, state: FSMContext):
  if (await state.get_data()).get("group_name") is not None:
    return
  all_groups = await get_all_groups()
  all_groups_names = [group.name.lower() for group in all_groups]
  if message.text.strip().lower() in all_groups_names:
    await state.update_data(group_name=message.text.strip().lower())
    group = await get_group_by_name(message.text.strip().lower())
    if group:
      if group.is_equipped:
        await message.answer("Эта группа уже зарегистрирована в системе. Запросите ссылку на вступление у <i>лидера</i> группы.", parse_mode="html")
        await state.clear()
      else:
        await message.answer("Эта группа еще не зарегистрирована в системе, при подтверждении вы станете <b>лидером</b> группы \n\n(о том что может лидер группы вы можете узнать в /about)", parse_mode="html", reply_markup=kb.create_group_keyboard)
  else:
    await message.answer("❌ Такая группа не найдена, попробуй еще раз.")