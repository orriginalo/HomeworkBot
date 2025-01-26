from app.database.db_setup import session
from app.database.models import Media
from sqlalchemy import select
from utils.logger import logger

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
      return media
  except Exception as e:
    logger.error(f"Error adding media: {e}")
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
        logger.info(f"Media with uid={media_id} not found.")
  except Exception as e:
    logger.error(f"Error deleting media {media_id}: {e}")
    return None

async def get_media_by_id(media_id: int):
  media_list = []
  try:
    async with session() as s:
      stmt = select(Media).where(Media.homework_id == media_id)
      result = await s.execute(stmt)
      media = result.scalars().all()
      for m in media:
        media_list.append(vars(m))
      
      return media_list if len(media_list) > 0 else None
  except Exception as e:
    logger.error(f"Error getting media by ID {media_id}: {e}")
    return None