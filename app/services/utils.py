from aiogram.types import InputMediaPhoto, InputMediaVideo, InputMediaDocument, InputMediaAudio, InputMediaAnimation
from aiogram import Bot
from app.database.schemas import MediaSchema


async def send_media(chat_id: int, bot: Bot, medias: list[MediaSchema], text: str = None, parse_mode: str = "html"):
    media_list = []
    for media in medias:
        if media.media_type == "photo":
            media_list.append(InputMediaPhoto(media=media.media_id))
        elif media.media_type == "video":
            media_list.append(InputMediaVideo(media=media.media_id))
        elif media.media_type == "audio":
            media_list.append(InputMediaAudio(media=media.media_id))
        elif media.media_type == "document":
            media_list.append(InputMediaDocument(media=media.media_id))
        else:
            media_list.append(media)

    if text:
        media_list[0].caption = text
        media_list[0].parse_mode = parse_mode

    await bot.send_media_group(chat_id, media_list)
