from sqlalchemy import select, and_
from app.database.db_setup import session
from app.database.models import Subjects
from utils.log import logger

from app.database.schemas import SubjectSchema

async def add_subject_to_subjects(subject: str):
  try:
    async with session() as s:
      subject = Subjects(name=subject)
      s.add(subject)
      await s.commit()
      await s.refresh(subject)
      return SubjectSchema.model_validate(subject, from_attributes=True)
  except Exception as e:
    logger.exception(f"Error adding subject {subject}: {e}")
    return None

async def get_subject_by_name(subject: str):
  try:
    async with session() as s:
      stmt = select(Subjects).where(Subjects.name == subject)
      result = await s.execute(stmt)
      subject = result.scalar_one_or_none()
      return SubjectSchema.model_validate(subject, from_attributes=True) if subject else None
  except Exception as e:
    logger.exception(f"Error getting subject by name {subject}: {e}")
    return None
  
async def get_subject_by_id(uid: int):
  try:
    async with session() as s:
      stmt = select(Subjects).where(Subjects.uid == uid)
      result = await s.execute(stmt)
      subject = result.scalar_one_or_none()
      return SubjectSchema.model_validate(subject, from_attributes=True) if subject else None
  except Exception as e:
    logger.exception(f"Error getting subject by id {uid}: {e}")
    return None