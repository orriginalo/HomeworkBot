from app.database.db_setup import Base
from datetime import datetime
from typing import Annotated
from sqlalchemy import ARRAY, BIGINT, TIMESTAMP, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from variables import default_user_settings

intpk = Annotated[int, mapped_column(primary_key=True, autoincrement=True)]
created_at = Annotated[datetime, mapped_column(server_default=text("TIMEZONE('UTC-4', CURRENT_TIMESTAMP)"))]
updated_at = Annotated[
    datetime,
    mapped_column(
        server_default=text("TIMEZONE('UTC-4', CURRENT_TIMESTAMP)"),
        onupdate=text("TIMEZONE('UTC-4', CURRENT_TIMESTAMP)"),
    ),
]


class User(Base):
    __tablename__ = "users"
    uid: Mapped[intpk]
    tg_id: Mapped[int] = mapped_column(BIGINT, unique=True)
    role: Mapped[int]
    username: Mapped[str | None]
    firstname: Mapped[str | None]
    lastname: Mapped[str | None]
    settings: Mapped[dict] = mapped_column(JSONB, nullable=False, default=default_user_settings)
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]
    moved_at: Mapped[datetime | None]
    group_uid: Mapped[int | None] = mapped_column(ForeignKey("groups.uid"))
    group: Mapped["Groups"] = relationship()
    is_leader: Mapped[bool]
    homeworks: Mapped[list["Homework"] | None] = relationship(back_populates="user")


class Homework(Base):
    __tablename__ = "homeworks"
    uid: Mapped[intpk]
    from_date: Mapped[datetime] = mapped_column(TIMESTAMP)
    subject: Mapped[str]
    task: Mapped[str | None]
    to_date: Mapped[datetime | None] = mapped_column(TIMESTAMP)
    group_uid: Mapped[int | None] = mapped_column(ForeignKey("groups.uid"))
    group: Mapped["Groups"] = relationship()
    created_at: Mapped[created_at]
    user_uid: Mapped[int | None] = mapped_column(BIGINT, ForeignKey("users.uid"))
    user: Mapped["User"] = relationship(back_populates="homeworks")


class Schedule(Base):
    __tablename__ = "schedule"
    uid: Mapped[intpk]
    timestamp: Mapped[datetime] = mapped_column(TIMESTAMP)
    subject: Mapped[str]
    teacher: Mapped[str]
    cabinet: Mapped[str]
    group_name: Mapped[str]
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
    name: Mapped[str] = mapped_column(unique=True)


class Settings(Base):
    __tablename__ = "settings"
    uid: Mapped[intpk]
    key: Mapped[str]
    value: Mapped[str]
