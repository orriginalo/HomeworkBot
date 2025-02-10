from sqlalchemy import text, insert, select
from app.database.db_setup import async_engine, sync_engine
from app.database.models import User
from app.database.db_setup import OldBase


async def create_tables(drop_tables: bool = False):
    if drop_tables:
        OldBase.metadata.drop_all(sync_engine)
    OldBase.metadata.create_all(sync_engine)
