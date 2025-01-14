import asyncio
from typing import Any, Dict, Union, Callable, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message

from cachetools import TTLCache

from app.database.requests import log, check_exists_user, add_new_user, get_username_by_id, set_username_by_id

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
        
        
        if await check_exists_user(event.from_user.id) == False:
            await add_new_user(event.from_user.id, 1, event.from_user.username)
        if await get_username_by_id(event.from_user.id) is None:
            await set_username_by_id(event.from_user.id, event.from_user.username)
        msg = event.text
        user_name = event.from_user.first_name
        try:
            if event.content_type == "text":
                await log(f'[{user_name}] - "{msg}"', "MSGLOGGER")
            else:
                await log(f'[{user_name}] - "some <{event.content_type}>"', "MSGLOGGER")
        except Exception as e:
            print(e)
        return await handler(event, data)