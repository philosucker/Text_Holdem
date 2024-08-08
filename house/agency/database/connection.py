from beanie import init_beanie 
from motor.motor_asyncio import AsyncIOMotorClient 
import logging
from agency.database.models import AgentLog, FoodLog
import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수를 불러옴
dotenv_path = "./house/.env"
load_dotenv(dotenv_path=dotenv_path, encoding='utf-8')

logging.basicConfig(level=logging.INFO)
logging.getLogger('motor').setLevel(logging.INFO)
logging.getLogger('pymongo').setLevel(logging.WARNING)

# 환경 변수에서 데이터베이스 URL을 가져옴
DATABASE_URL = os.getenv("AGENCY_DATABASE_URL")

# 환경 변수가 제대로 로드되었는지 확인
if not DATABASE_URL:
    raise ValueError(f"AGENCY_DATABASE_URL not set in {dotenv_path}")

logging.info(f"AGENCY_DATABASE_URL loaded from {dotenv_path}")

async def init_db():
    client = AsyncIOMotorClient(DATABASE_URL)
    database_name = DATABASE_URL.split("/")[-1]
    database = client[database_name]

    await init_beanie(database=database, document_models=[AgentLog, FoodLog])
    collections = ["AgentLog", "FoodLog"]
    for collection in collections:
        if collection not in await database.list_collection_names():
            await database.create_collection(collection)

    return client

async def close_db(client : AsyncIOMotorClient):
    client.close()
