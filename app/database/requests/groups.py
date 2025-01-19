from app.database.db_setup import session
from app.database.models import Groups
from sqlalchemy import select
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def add_group(course: int):
  try:
    async with session() as s:
      group = Groups(
        course=course
      )
      s.add(group)
      await s.commit()
      return group
  except Exception as e:
    logger.error(f"Error adding group: {e}")
    return None

async def del_group(group_id: int):
  try:
    async with session() as s:
      stmt = select(Groups).where(Groups.uid == group_id)
      group = s.execute(stmt).scalar_one_or_none()
      if group:
        s.delete(group)
        await s.commit()
      else:
        logger.info(f"Group with uid={group_id} not found.")
  except Exception as e:
    logger.error(f"Error deleting group {group_id}: {e}")
    return None

async def get_group_by_id(group_id: int):
  try:
    async with session() as s:
      stmt = select(Groups).where(Groups.uid == group_id)
      result = await s.execute(stmt).scalar_one_or_none()
      return result
  except Exception as e:
    logger.error(f"Error getting group by ID {group_id}: {e}")
    return None