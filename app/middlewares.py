import asyncio
from utils.log import logger
from typing import Any, Dict, Union, Callable, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

from cachetools import TTLCache

from app.database.requests.user import add_user, get_user_by_id, update_user

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
    


class MsgLoggerMiddleware(BaseException):

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        
        
        user = await get_user_by_id(event.from_user.id)
        print("User is none?")
        if user is None:
            print("User is none!")
            user = await add_user(
                tg_id=event.from_user.id,
                role=1,
                username=event.from_user.username,
                firstname=event.from_user.first_name,
                lastname=event.from_user.last_name,
                notifications=False,
                group_id=None,
                is_leader=False
            )
                
        else:
            if user["role"] == 0:
                return
        await update_user(event.from_user.id, username=event.from_user.username, firstname=event.from_user.first_name, lastname=event.from_user.last_name)
        
        data["user"] = user
        msg = event.text
        user_name = f"{event.from_user.first_name if event.from_user.first_name else ''}{(" " + event.from_user.last_name) if event.from_user.last_name else ''}"
        try:
            if event.content_type == "text":
                logger.info(f'[{user_name}] - "{msg}"')
            else:
                logger.info(f'[{user_name}] - "some <{event.content_type}>"')
        except Exception as e:
            print(e)
        return await handler(event, data)