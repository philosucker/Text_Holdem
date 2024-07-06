from typing import Optional
from beanie import init_beanie 
from models.events import Event  
from models.users import User  
from motor.motor_asyncio import AsyncIOMotorClient 
from pydantic_settings import BaseSettings 
from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../.env'))

class Settings(BaseSettings):
    DATABASE_URL: Optional[str] = None
    client: Optional[AsyncIOMotorClient] = None
    SECRET_KEY: Optional[str] = None

    async def initialize_database(self):
        self.client = AsyncIOMotorClient(self.DATABASE_URL)
        database_name = self.DATABASE_URL.split("/")[-1]  # URL에서 데이터베이스 이름 추출
        # database = self.client["TempDB"] 위처럼 안하고 이 코드를 쓰면 test_app.py 를 pytest로 실행시 testdb 가 아니라 TempDB 를 사용하게 되어 매 테스트마다 데이터 중복이 발생한다
        database = self.client[database_name]
        await init_beanie(database=database, document_models=[Event, User])

    async def close_database(self):
        if self.client:
            self.client.close()

    class Config:
        env_file = ".env"

settings = Settings()
