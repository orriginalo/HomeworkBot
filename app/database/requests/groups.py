from app.database.db_setup import session
from app.database.models import Groups
from sqlalchemy import select
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def add_group(name: str, course: int):
  try:
    async with session() as s:
      group = Groups(
        name=name.lower(),
        course=course
      )
      s.add(group)
      await s.commit()
      logger.info(f"Group {name} successfully added!")
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
  
async def get_group_by_name(group_name: str):
  try:
    async with session() as s:
      stmt = select(Groups).where(Groups.name == group_name)
      result = await s.execute(stmt)
      group = result.scalar_one_or_none()
      return vars(group)
  except Exception as e:
    logger.error(f"Error getting group by name {group_name}: {e}")
    return None
  

async def get_all_groups():
  try:
    async with session() as s:
      stmt = select(Groups)
      result = await s.execute(stmt)
      groups = result.scalars().all()
      groups = [vars(group) for group in groups]
      return groups
  except Exception as e:
    logger.error(f"Error getting all groups: {e}")
    return None
  
async def get_group_by_ref(ref: str):
  try:
    async with session() as s:
      stmt = select(Groups).where(Groups.ref_code == ref)
      result = await s.execute(stmt)
      group = result.scalar_one_or_none()
      print(f"ref: {ref}, group: {group}")
      return vars(group) if group else None
  except Exception as e:
    logger.error(f"Error getting group by ref: {e}")
    return None