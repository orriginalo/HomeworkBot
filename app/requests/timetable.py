from datetime import datetime, timedelta
import aiohttp
import asyncio
import os
from dotenv import load_dotenv
from aiogram.types import Message, FSInputFile

# from utils.log import logger
from rich import print

load_dotenv(override=True)


async def fetch_timetable(group_name: str):
    url = f"{os.getenv("API_URL")}/timetable/{group_name}/"  # Используем имя сервиса FastAPI
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.json()
    except Exception as e:
        print(e)
        return


# async def main():
#   group = "пдо-16"
#   timetable: dict = await fetch_timetable(group)
#   # print(timetable)
#   for group, week in timetable.items():
#     for week_num, day in week.items():
#       for day_timestamp, pairs in day.items():
#         for pair, variants in pairs.items():
#           for variant_num, pair_info in variants.items():
#             print(f"{pair_info["group"]=}")
#             print(f"{pair_info["subject"]=}")
#             print(f"{pair_info["teacher"]=}")
#             print(f"{pair_info["cabinet"]=}")
#             print("---------------")
# asyncio.run(main())
