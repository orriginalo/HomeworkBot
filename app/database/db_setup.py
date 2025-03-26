import asyncio
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import os
from dotenv import load_dotenv
from config import settings

async_engine = create_async_engine(
    url=settings.SQLALCHEMY_URL,
    echo=True,
    pool_size=5,
)

sync_engine = create_engine(
    url=settings.SQLALCHEMY_URL_SYNC,
    # echo=True,
    pool_size=5,
)


session = async_sessionmaker(async_engine)

class Base(DeclarativeBase):
    pass
