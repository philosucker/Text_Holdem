from beanie import init_beanie 
from motor.motor_asyncio import AsyncIOMotorClient 
import os
import logging
from dotenv import load_dotenv

from database.models import UserLog, TableLog, GameLog, ChatLog

# .env 파일에서 환경 변수를 불러옴
dotenv_path = "./house/.env"
load_dotenv(dotenv_path=dotenv_path, encoding='utf-8')

logging.basicConfig(level=logging.INFO)
logging.getLogger('motor').setLevel(logging.INFO)
logging.getLogger('pymongo').setLevel(logging.WARNING)

# 환경 변수에서 데이터베이스 URL을 가져옴
DATABASE_URL = os.getenv("FLOOR_DATABASE_URL")

# 환경 변수가 제대로 로드되었는지 확인
if not DATABASE_URL:
    raise ValueError(f"FLOOR_DATABASE_URL not set in {dotenv_path}")

logging.info(f"FLOOR_DATABASE_URL loaded from {dotenv_path}")

async def init_db():
    client = AsyncIOMotorClient(DATABASE_URL)
    database_name = DATABASE_URL.split("/")[-1]
    database = client[database_name]
    '''
    Beanie를 사용하면 모델 컬렉션을 정의하고 이를 데이터베이스 초기화 시 등록만해두면
    어디서든 컬렉션을 불러와 바로 데이터베이스를 조작할 수 있다.
    SQLAlchemy와 달리 별도의 세션을 만들 필요가 없다. 
    Beanie는 비동기식으로 MongoDB와 직접 상호작용할 수 있도록 도와주며, 
    모델 자체에서 CRUD 작업을 수행할 수 있게 해준다
    '''
    await init_beanie(database=database, document_models=[UserLog, TableLog, GameLog, ChatLog])

    # 컬렉션 존재 여부 확인 및 생성
    collections = ["UserLog", "TableLog", "GameLog", "ChatLog"]
    for collection in collections:
        if collection not in await database.list_collection_names():
            await database.create_collection(collection)
            
    return client

async def close_db(client : AsyncIOMotorClient):
    client.close()
