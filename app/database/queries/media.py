from app.database.db_setup import session
from app.database.models import Media
from sqlalchemy import select
from utils.log import logger

from app.database.schemas import MediaSchema

async def add_media(homework_id: int, media_id: str, media_type: str):
  try:
    async with session() as s:
      media = Media(
        homework_id=homework_id, 
        media_id=media_id, 
        media_type=media_type
      )
      s.add(media)
      await s.commit()
      return MediaSchema.model_validate(media, from_attributes=True)
  except Exception as e:
    logger.exception(f"Error adding media: {e}")
    return None
  
async def del_media(media_id: int):
  try:
    async with session() as s:
      stmt = select(Media).where(Media.uid == media_id)
      media = await s.execute(stmt)
      media = media.scalar_one_or_none()
      if media:
        await s.delete(media)
        await s.commit()
      else:
        logger.debug(f"Media with uid={media_id} not found.")
  except Exception as e:
    logger.exception(f"Error deleting media {media_id}: {e}")
    return None

async def get_media_by_id(media_id: int):
  try:
    async with session() as s:
      stmt = select(Media).where(Media.homework_id == media_id)
      result = await s.execute(stmt)
      media = result.scalars().all()
      medias = [MediaSchema.model_validate(media, from_attributes=True) for media in media]
      return medias if len(medias) > 0 else None
  except Exception as e:
    logger.exception(f"Error getting media by ID {media_id}: {e}")
    return None