from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from app.database.queries.group import get_all_groups, get_group_by_id, get_group_by_name, update_group
from app.database.schemas import UserRelSchema
import app.keyboards as kb
from app.database.models import User
from app.database.queries.user import get_user_by_id, get_users, update_user
from app.middlewares import AlbumMiddleware, GroupChecker, MsgLoggerMiddleware

from utils.log import logger
from utils.referal import generate_unique_code, get_referal_link
from utils.timetable.updater import update_timetable

from datetime import datetime


class transferring_leadership(StatesGroup):
    user_id = State()


router = Router(name="Groups")

router.message.middleware(MsgLoggerMiddleware())
router.callback_query.middleware(MsgLoggerMiddleware())
router.message.middleware(AlbumMiddleware())
router.message.filter(GroupChecker())


@router.callback_query(F.data == "join_group")
async def join_group_handler(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    user = await get_user_by_id(call.from_user.id)
    group_name = (await state.get_data())["group_name"]
    group = await get_group_by_name(group_name)
    user = await update_user(user.tg_id, role=1, moved_at=datetime.now(), group_uid=group.uid, group_name=group.name)
    await call.message.answer(
        f"🎉 Вы присоединились к группе <b>{group.name}</b>",
        parse_mode="html",
        reply_markup=await kb.get_start_keyboard(user),
    )


@router.callback_query(F.data == "transfer_leadership")
async def transfer_leadership_handler(call: CallbackQuery, state: FSMContext):
    user = await get_user_by_id(call.from_user.id)
    await call.message.delete()
    await call.message.answer(
        f"Отправьте телеграм id человека или перешлите его сообщение для передачи прав лидерства.",
        parse_mode="html",
        reply_markup=await kb.get_start_keyboard(user),
    )
    await state.set_state(transferring_leadership.user_id)


@router.message(transferring_leadership.user_id)
async def transfer_leadership(message: Message, state: FSMContext):
    user = await get_user_by_id(message.from_user.id)

    future_leader_id: int = None
    if message.forward_from:
        future_leader_id = int(message.forward_from.id)
    else:
        future_leader_id = int(message.text)

    try:
        future_leader = await get_user_by_id(future_leader_id)
    except:
        await message.answer("❌ Неверный id пользователя.", reply_markup=await kb.get_start_keyboard(user))
        await state.clear()
        return

    if future_leader is None:
        await message.answer(
            "❌ Пользователь не существует, или его нет в базе (пусть напишет боту).",
            reply_markup=await kb.get_start_keyboard(user),
        )
        await state.clear()
        return
    elif future_leader.group.uid != user.group.uid:
        await message.answer(
            "❌ Вы не можете передать права лидерства человеку который находится в другой группе.",
            reply_markup=await kb.get_start_keyboard(user),
        )
        await state.clear()
        return

    await state.update_data(user_id=future_leader.tg_id)
    await message.answer(
        f"❗Вы уверены что хотите передать права лидерства <a href='tg://user?id={future_leader.tg_id}'>{future_leader.firstname if future_leader.firstname else ''} {future_leader.lastname if future_leader.lastname else ''}</a>❓",
        parse_mode="html",
        reply_markup=kb.transfer_leadership_confirm_keyboard,
    )


@router.callback_query(F.data == "transfer_leadership_confirm")
async def transfer_leadership_confirm_handler(call: CallbackQuery, state: FSMContext):
    user = await get_user_by_id(call.from_user.id)
    group = await get_group_by_id(user.group.uid)
    data = await state.get_data()
    future_leader_id = data["user_id"]

    future_leader = await get_user_by_id(future_leader_id)

    await call.message.delete()
    await update_user(user.tg_id, is_leader=False)
    await update_user(future_leader_id, is_leader=True, role=2)
    await update_group(group.uid, leader_id=future_leader_id)
    username = (
        (future_leader.firstname if future_leader.firstname else "")
        + " "
        + (future_leader.lastname if future_leader.lastname else "")
    )
    username = username.strip()
    await call.message.answer(
        f"🔄 <b>Права лидера переданы!</b>\n\n"
        f"👤 Новый лидер: <a href='tg://user?id={future_leader_id}'>{username}</a>\n"
        f"⚠️ Теперь вы <i>обычный участник</i> группы",
        parse_mode="HTML",
    )
    await state.clear()


@router.callback_query(F.data == "create_group")
async def create_group_handler(callback: CallbackQuery, state: FSMContext):
    start_user = await get_user_by_id(callback.from_user.id)
    await callback.message.delete()
    msg = await callback.message.answer(f"⌛ Создание группы...")
    data = await state.get_data()
    group = await get_group_by_name(data["group_name"])
    try:

        referal_code = None
        while referal_code == None:
            referal_code = await generate_unique_code()

        referal_link = await get_referal_link(referal_code, group.name)

        settings_copy = start_user.settings.copy()
        settings_copy["change_ids_visibility"] = True
        await update_group(
            group.uid,
            ref_code=referal_code,
            is_equipped=True,
            member_count=group.member_count + 1,
            leader_id=callback.from_user.id,
        )
        user = await update_user(
            callback.from_user.id,
            role=2,
            settings=settings_copy,
            group_uid=group.uid,
            group_name=group.name,
            is_leader=True,
            moved_at=datetime.now(),
        )

        await update_timetable(for_all=False, group_name=group.name)

        await msg.edit_text(
            f"🎉 <b>Группа успешно создана!</b>\n\n"
            f"▫️ Вы стали <i>лидером группы</i>\n"
            f"▫️ Теперь вы можете:\n"
            f"   ➕ Добавлять задания\n"
            f"   👥 Приглашать участников\n"
            f"   👑 Управлять группой",
            parse_mode="HTML",
        )

        await callback.message.answer(
            f"🔗 <b>Пригласительная ссылка для вступления:</b>\n\n👉 {referal_link}",
            parse_mode="html",
            reply_markup=await kb.get_start_keyboard(user),
        )
    except Exception as e:
        await update_group(group.uid, ref_code=None, is_equipped=False, member_count=0, leader_id=None)
        await update_user(
            start_user.tg_id, role=start_user.role, group_uid=None, group_name=None, is_leader=False, moved_at=None
        )
        await msg.edit_text(f"❌ Ошибка создания группы. Попробуйте еще раз (/start).")
        logger.exception(f"Error creating group: {e}")

    await state.clear()


@router.message(F.text.contains("Управление группой"))
async def show_group_controller_handler(message: CallbackQuery):
    user = await get_user_by_id(message.from_user.id)
    if user.is_leader:
        all_users_in_group = await get_users(User.group_uid == user.group.uid)
        all_users_in_group.sort(key=lambda user: user.role, reverse=True)

        def get_emoji(user: UserRelSchema):
            if user.is_leader:
                return "👑"
            elif user.role <= 1:
                return "👤"
            elif user.role >= 2:
                return "➕"

        # Определяем максимальную длину имени для выравнивания
        max_name_length = max(len(f"{u.firstname or ''} {u.lastname or ''}".strip()) for u in all_users_in_group)

        def get_link(user):
            emoji = get_emoji(user)
            full_name = f"{user.firstname or ''} {user.lastname or ''}".strip()
            full_name = full_name if full_name else str(user.tg_id)  # Если нет имени, показываем ID

            return f"{emoji} <a href='tg://user?id={user.tg_id}'>{full_name}</a> (<code>{user.tg_id}</code>)"

        users_links = [get_link(user) for user in all_users_in_group]
        users_links = "\n".join(users_links)

        await message.answer(
            (
                f"👑 <b>Панель управления группой</b>\n\n"
                f"▫️ Название: <code>{user.group.name}</code>\n"
                f"▫️ Лидер: <a href='tg://user?id={user.group.leader_id}'>{user.firstname if user.firstname else ''} {user.lastname if user.lastname else ''}</a>\n\n"
                f"▫️ Всего участников: {len(all_users_in_group)}"
                f"\n📃 Список участников:\n{users_links}"
                if users_links
                else "" f"🛠 <i>Доступные действия:</i>"
            ),
            parse_mode="html",
            reply_markup=kb.group_controller_keyboard,
        )


@router.callback_query(F.data == "get_group_link")
async def get_group_link_handler(call: CallbackQuery):
    user = await get_user_by_id(call.from_user.id)
    group = await get_group_by_id(user.group.uid)
    referal_link = await get_referal_link(group.ref_code, group.name)
    await call.message.answer(
        f"🔗 <b>Ссылка для вступления:</b>\n👉{referal_link}",
        parse_mode="html",
        reply_markup=await kb.get_start_keyboard(user),
    )
