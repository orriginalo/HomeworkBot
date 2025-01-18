from sqlalchemy import select
from app.database.db_setup import session
from app.database.models import User
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def add_user(tg_id: int, role: int = 1, username: str = None, firstname: str = "", lastname: str = "", notifications: bool = False, group_id: int = None, is_leader: bool = False):
    try:
      async with session() as s:
        user = User(
            tg_id=tg_id, 
            role=role, 
            username=username, 
            firstname=firstname, 
            lastname=lastname, 
            notifications=notifications, 
            group_id=group_id, 
            is_leader=is_leader
        )
        s.add(user)
        await s.commit()
        return user
    except Exception as e:
      logger.error(f"Error adding user: {e}")
      return None

async def del_user(tg_id: int):
  try:
    async with session() as s:
      stmt = select(User).where(User.tg_id == tg_id)
      user = await s.execute(stmt).scalar_one_or_none()
      if user:
        await s.delete(user)
        await s.commit()
      else:
        logger.info(f"User with tg_id={tg_id} not found.")
  except Exception as e:
    logger.error(f"Error deleting user {tg_id}: {e}")
    return None

async def get_users_with_notifications():
  async with session() as s:
    stmt = select(User).where(User.notifications == True)
    users = await s.execute(stmt).scalars().all()
    return users
  
async def get_user_by_id(tg_id: int):
  try:
    async with session() as s:
      stmt = select(User).where(User.tg_id == tg_id)
      result = await s.execute(stmt)
      user = result.scalar_one_or_none()
      if user:
        return vars(user)
      else:
        return None
  except Exception as e:
    logger.error(f"Error getting user by ID {tg_id}: {e}")
    return None

async def update_user(tg_id: int, **kwargs):
  try:
    async with session() as s:
      stmt = select(User).where(User.tg_id == tg_id)
      user = await s.execute(stmt).scalar_one()
      for key, value in kwargs.items():
        if value is not None:
          setattr(user, key, value)
      await s.commit()
      return user
  except Exception as e:
    logger.error(f"Error updating user {tg_id}: {e}")
    return None

async def get_users():
  async with session() as s:
    stmt = select(User)
    users = await s.execute(stmt).scalars().all()
    return users

async def get_users_with_role(role: int):
  async with session() as s:
    stmt = select(User).where(User.role == role)
    users = await s.execute(stmt).scalars().all()
    return users