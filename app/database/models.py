from typing import Annotated
from sqlalchemy import ARRAY, BIGINT, TIMESTAMP, String, text
from sqlalchemy.orm import Mapped, mapped_column
from app.database.db_setup import Base

intpk = Annotated[int, mapped_column(primary_key=True, autoincrement=True)]
created_at = Annotated[str, mapped_column(server_default=text("TIMEZONE('UTC-4', CURRENT_TIMESTAMP)"))]
updated_at = Annotated[str, mapped_column(server_default=text("TIMEZONE('UTC-4', CURRENT_TIMESTAMP)"), onupdate=text("TIMEZONE('utc', CURRENT_TIMESTAMP)"))]

class User(Base):
  __tablename__ = "users"
  uid: Mapped[intpk]
  tg_id: Mapped[int] = mapped_column(BIGINT, unique=True)
  role: Mapped[int]
  username: Mapped[str | None]
  firstname: Mapped[str | None]
  lastname: Mapped[str | None]
  notifications: Mapped[bool]
  created_at: Mapped[created_at]
  updated_at: Mapped[updated_at]
  group_id: Mapped[int | None]
  is_leader: Mapped[bool]

class Homework(Base):
  __tablename__ = "homeworks"
  uid: Mapped[intpk]
  from_date: Mapped[int] = mapped_column(TIMESTAMP)
  subject: Mapped[str]
  task: Mapped[str | None]
  to_date: Mapped[int | None] = mapped_column(TIMESTAMP)
  group_id: Mapped[int]
  created_at: Mapped[created_at]
  added_by: Mapped[int | None] = mapped_column(BIGINT)

class Schedule(Base):
  __tablename__ = "schedule"
  uid: Mapped[intpk]
  timestamp: Mapped[int] = mapped_column(TIMESTAMP)
  subject: Mapped[str]
  week_number: Mapped[int]
  group_id: Mapped[int | None]

class Media(Base):
  __tablename__ = "media"
  uid: Mapped[intpk]
  homework_id: Mapped[int]
  media_id: Mapped[str]
  media_type: Mapped[str]
  
class Groups(Base):
  __tablename__ = "groups"
  uid: Mapped[intpk]
  name: Mapped[str]
  course: Mapped[int | None]
  ref_code: Mapped[str | None] = mapped_column(unique=True)
  is_equipped: Mapped[bool] = mapped_column(default=False)
  leader_id: Mapped[int | None] = mapped_column(BIGINT)
  member_count: Mapped[int] = mapped_column(default=0)
  created_at: Mapped[created_at]
  updated_at: Mapped[updated_at]
  subjects: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True, default=None)

class Subjects(Base):
  __tablename__ = "subjects"
  uid: Mapped[intpk]
  name: Mapped[str]