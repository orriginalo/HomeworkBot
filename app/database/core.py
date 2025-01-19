from sqlalchemy import text, insert, select
from app.database.db_setup import async_engine, sync_engine
from app.database.models import User
from app.database.db_setup import Base

async def create_tables():
  Base.metadata.drop_all(sync_engine)
  Base.metadata.create_all(sync_engine)