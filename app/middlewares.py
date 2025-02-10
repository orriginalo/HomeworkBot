import asyncio
from utils.log import logger
from typing import Any, Dict, Union, Callable, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Filter

from cachetools import TTLCache

from app.database.queries.user import add_user, get_user_by_id, update_user

from rich import print

class AlbumMiddleware(BaseMiddleware):
    def __init__(self, latency: Union[int, float] = 0.1):
        self.latency = latency
        self.album_data = {}

    def collect_album_messages(self, event: Message):
        if event.media_group_id not in self.album_data:
            self.album_data[event.media_group_id] = {"messages": []}
        self.album_data[event.media_group_id]["messages"].append(event)
        return len(self.album_data[event.media_group_id]["messages"])

    async def __call__(self, handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]], event: Message, data: Dict[str, Any]) -> Any:
        if not event.media_group_id:
            return await handler(event, data)

        total_before = self.collect_album_messages(event)
        await asyncio.sleep(self.latency)
        total_after = len(self.album_data[event.media_group_id]["messages"])

        if total_before != total_after:
            return

        album_messages = self.album_data[event.media_group_id]["messages"]
        album_messages.sort(key=lambda x: x.message_id)
        data["album"] = album_messages
        for msg in album_messages:
            if msg.caption:
                data["album_caption"] = msg.caption
                break
        del self.album_data[event.media_group_id]
        return await handler(event, data)

class AntiFloodMiddleware(BaseMiddleware):

    def __init__(self, time_limit: int=2) -> None:
        self.limit = TTLCache(maxsize=10_000, ttl=time_limit)

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        if event.chat.id in self.limit:
            return
        else:
            self.limit[event.chat.id] = None
        return await handler(event, data)
    

class TestMiddleware(BaseMiddleware):

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        print("------------test middleware---------")
        print("--------------handler---------------")
        print(await handler(event, data))
        print("---------------event----------------")
        print(event)
        print("---------------data-----------------")
        print(data)
        data["aboba"] = "abobus mobobus"
        return await handler(event, data)
    
class GroupChecker(Filter):
    
    async def __call__(
    self, 
    message: Message, 
    state: FSMContext
    ) -> bool:
        
        user = await get_user_by_id(message.from_user.id)
        if user is not None and user.group is None:
            stmt = "/start" not in message.text and message.text.strip() != "/repair" and (await state.get_state() != "setting_group:group_name")
            if stmt:
                await message.answer("➡️ Для продолжения использования бота присоединитесь к группе\n\nИз <b>Пдо-16</b>?\n👉 https://t.me/homew0rk_bot?start=invite_svmeP8pb_pdo-16", parse_mode="html")
                return False
        return True
        

class MsgLoggerMiddleware(BaseException):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        
        user = await get_user_by_id(event.from_user.id)
        if user is None:
            user = await add_user(
                tg_id=event.from_user.id,
                role=1,
                username=event.from_user.username,
                firstname=event.from_user.first_name,
                lastname=event.from_user.last_name,
                group_uid=None,
                is_leader=False
            )
        else:
            if user.role == 0:
                return  # Прерываем выполнение, если роль 0
        
        # Обновляем данные пользователя в БД
        await update_user(
            event.from_user.id,
            username=event.from_user.username,
            firstname=event.from_user.first_name,
            lastname=event.from_user.last_name
        )
        
        # Добавляем пользователя в data
        data["user"] = user
        msg = ""

        # Определяем имя пользователя
        user_name = f"{event.from_user.first_name or ''}{' ' + event.from_user.last_name if event.from_user.last_name else ''}"

        try:
            if isinstance(event, Message):
                msg = event.text if event.content_type == "text" else f"some <{event.content_type}>"
                logger.info(f'Message  - [{user_name}] - "{msg}"')

            elif isinstance(event, CallbackQuery):
                data["callback_data"] = event.data  # Не перезаписываем весь `data`
                msg = ""
                
                if event.message.reply_markup and event.message.reply_markup.inline_keyboard:
                    for line in event.message.reply_markup.inline_keyboard:
                        for button in line:
                            if button.callback_data == event.data:
                                msg = button.text
                                break
                
                logger.info(f'Callback - [{user_name}] - "{msg}" : {event.data}')

        except Exception as e:
            print(f"Ошибка в логировании: {e}")

        return await handler(event, data)  # `data` остаётся словарём!
