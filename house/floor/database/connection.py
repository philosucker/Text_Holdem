from beanie import init_beanie 
from motor.motor_asyncio import AsyncIOMotorClient 
import os
import logging
from dotenv import load_dotenv

from database.models import UserLog, TableLog, GameLog, ChatLog

# .env 파일에서 환경 변수를 불러옴
load_dotenv(dotenv_path="./house/.env", encoding='utf-8')

logging.basicConfig(level=logging.INFO)
# logging.getLogger('motor').setLevel(logging.DEBUG)
# logging.getLogger('pymongo').setLevel(logging.DEBUG)
logging.getLogger('motor').setLevel(logging.INFO)
logging.getLogger('pymongo').setLevel(logging.INFO)


# 환경 변수에서 데이터베이스 URL을 가져옴
DATABASE_URL = os.getenv("FLOOR_DATABASE_URL")


async def init_db():
    client = AsyncIOMotorClient(DATABASE_URL)
    database_name = DATABASE_URL.split("/")[-1]
    database = client[database_name]

    await init_beanie(database=database, document_models=[UserLog, TableLog, GameLog, ChatLog])

    # 컬렉션 존재 여부 확인 및 생성
    collections = ["UserLog", "TableLog", "GameLog", "ChatLog"]
    for collection in collections:
        if collection not in await database.list_collection_names():
            await database.create_collection(collection)
            
    return client

async def close_db(client : AsyncIOMotorClient):
    client.close()
