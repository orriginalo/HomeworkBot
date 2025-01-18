from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine

from dotenv import load_dotenv
import os
load_dotenv()


engine = create_async_engine(
  url=os.getenv("SQLALCHEMY_URL"),
  echo=True
  )

async_session = async_sessionmaker(engine)

class Base(AsyncAttrs, DeclarativeBase):
  pass


class User(Base):
  __tablename__ = "users"
  id: Mapped[int] = mapped_column(primary_key=True)
  role: Mapped[int]
  username: Mapped[str]
  firstname: Mapped[str]
  lastname: Mapped[str]
  created_at: Mapped[int]
  notifications: Mapped[int]


class Homeworks(Base):
  __tablename__ = "homeworks"
  id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
  from_date: Mapped[int] = mapped_column(nullable=True)
  subject: Mapped[str] = mapped_column(nullable=True)
  task: Mapped[str] = mapped_column(nullable=True)
  to_date: Mapped[int] = mapped_column(nullable=True)



class Schedule(Base):
  __tablename__ = "schedule"
  id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
  timestamp: Mapped[int] = mapped_column(nullable=True)
  subject: Mapped[str] = mapped_column(nullable=True)
  weeknumber: Mapped[int] = mapped_column(nullable=True)



class Media(Base):
  __tablename__ = "media"
  homework_id: Mapped[int] = mapped_column(primary_key=True)
  media_id: Mapped[int] = mapped_column(nullable=True)
  media_type: Mapped[str] = mapped_column(nullable=True)


async def async_main():
  async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)