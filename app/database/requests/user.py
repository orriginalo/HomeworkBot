from sqlalchemy import select, and_
from app.database.db_setup import session
from app.database.models import User
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def add_user(
    tg_id: int,
    role: int = 1,
    username: str = None,
    firstname: str = "",
    lastname: str = "",
    notifications: bool = False,
    group_id: int = None,
    is_leader: bool = False
):
    try:
        async with session() as s:
            # Проверка, существует ли пользователь с таким tg_id
            stmt = select(User).where(User.tg_id == tg_id)
            result = await s.execute(stmt)
            existing_user = result.scalar_one_or_none()

            if existing_user:
                logger.info(f"User with tg_id {tg_id} already exists.")
                return existing_user  # Возвращаем существующего пользователя

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
            await s.refresh(user)
            return vars(user) if user else None
    except Exception as e:
        logger.error(f"Error adding user: {e}")
        return None


async def del_user(tg_id: int):
  try:
    async with session() as s:
      stmt = select(User).where(User.tg_id == tg_id)
      result = await s.execute(stmt)
      user = result.scalar_one_or_none()
      if user:
        await s.delete(user)
        await s.commit()
      else:
        logger.info(f"User with tg_id={tg_id} not found.")
  except Exception as e:
    logger.error(f"Error deleting user {tg_id}: {e}")
    return None

async def get_users_with_notifications():
  users_list = []
  async with session() as s:
    stmt = select(User).where(User.notifications == True)
    result = await s.execute(stmt)
    users = result.scalars().all()
    for user in users:
      users_list.append(vars(user))
    return users_list
  
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
      result = await s.execute(stmt)
      user = result.scalar_one()
      for key, value in kwargs.items():
        if value is not None:
          setattr(user, key, value)
      await s.commit()
      await s.refresh(user)
      return vars(user) if user else None
  except Exception as e:
    logger.error(f"Error updating user {tg_id}: {e}")
    return None

async def get_users(*filters):
  """
  example:
  admins = await get_users(User.role >= 3)
  """
  async with session() as s:
    stmt = select(User)
    if filters:
      stmt = stmt.where(and_(*filters))
    result = await s.execute(stmt)
    users = result.scalars().all()
    users = [vars(user) for user in users]
    return users

async def get_users_with_role(role: int):
  users_list = []
  async with session() as s:
    stmt = select(User).where(User.role == role)
    result = await s.execute(stmt)
    users = result.scalars().all()
    for user in users:
      users_list.append(vars(user))
    return users_list
  