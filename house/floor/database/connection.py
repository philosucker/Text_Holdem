from beanie import init_beanie 
from motor.motor_asyncio import AsyncIOMotorClient 
from pydantic_settings import BaseSettings 
from database.models import UserLog, TableLog, GameLog, ChatLog
import os

class Settings(BaseSettings):
    
    DATABASE_URL: str

    class Config:
        env_file = "./house/.env"
        env_file_encoding = 'utf-8'

    async def initialize_database(self):
        self.client = AsyncIOMotorClient(self.DATABASE_URL)
        database_name = self.DATABASE_URL.split("/")[-1]
        database = self.client[database_name]
        '''
        Beanie를 사용하면 모델 컬렉션을 정의하고 이를 데이터베이스 초기화 시 등록만해두면
        어디서든 컬렉션을 불러와 바로 데이터베이스를 조작할 수 있다.
        SQLAlchemy와 달리 별도의 세션을 만들 필요가 없다. 
        Beanie는 비동기식으로 MongoDB와 직접 상호작용할 수 있도록 도와주며, 
        모델 자체에서 CRUD 작업을 수행할 수 있게 해준다
        '''
        await init_beanie(database=database, document_models=[UserLog, TableLog, GameLog, ChatLog])

    async def close_database(self):
        if self.client:
            self.client.close()

settings = Settings(DATABASE_URL=os.getenv("MONGO_GAME_DATABASE_URL"))


