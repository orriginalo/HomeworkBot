from sqlalchemy import select, and_
from app.database.db_setup import session
from app.database.models import User
from utils.log import logger
from variables import default_user_settings
from app.database.schemas import UserSchema

async def add_user(
    tg_id: int,
    role: int = 1,
    username: str = None,
    firstname: str = "",
    lastname: str = "",
    settings: dict = default_user_settings,
    group_id: int = None,
    group_name: str = None,
    is_leader: bool = False
):
    try:
        async with session() as s:
            # Проверка, существует ли пользователь с таким tg_id
            stmt = select(User).where(User.tg_id == tg_id)
            result = await s.execute(stmt)
            existing_user = result.scalar_one_or_none()

            if existing_user:
                logger.warning(f"User with tg_id {tg_id} already exists.")
                return UserSchema(**existing_user.__dict__)

            user = User(
                tg_id=tg_id,
                role=role,
                username=username,
                firstname=firstname,
                lastname=lastname,
                settings=settings,
                group_id=group_id,
                group_name=group_name,
                is_leader=is_leader
            )
            s.add(user)
            await s.commit()
            await s.refresh(user)
            return UserSchema.model_validate(user, from_attributes=True) if user else None
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
        logger.debug(f"User with tg_id={tg_id} not found.")
  except Exception as e:
    logger.exception(f"Error deleting user {tg_id}: {e}")
    return None

async def get_user_by_id(tg_id: int):
  try:
    async with session() as s:
      stmt = select(User).where(User.tg_id == tg_id)
      result = await s.execute(stmt)
      user = result.scalar_one_or_none()
      if user:
        return UserSchema.model_validate(user, from_attributes=True) if user else None
      else:
        return None
  except Exception as e:
    logger.exception(f"Error getting user by ID {tg_id}: {e}")
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
      return UserSchema.model_validate(user, from_attributes=True) if user else None
  except Exception as e:
    logger.exception(f"Error updating user {tg_id}: {e}")
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
    users = [UserSchema.model_validate(user, from_attributes=True) for user in users]
    return users

async def get_users_with_role(role: int):
  async with session() as s:
    stmt = select(User).where(User.role == role)
    result = await s.execute(stmt)
    users = result.scalars().all()
    users = [UserSchema.model_validate(user, from_attributes=True) for user in users]
    return users
  