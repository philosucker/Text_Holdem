from beanie import init_beanie 
from motor.motor_asyncio import AsyncIOMotorClient 
from pydantic_settings import BaseSettings 
from models import UserLog, TableLog, GameLog, ChatLog
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
        await init_beanie(database=database, document_models=[UserLog, TableLog, GameLog, ChatLog])

    async def close_database(self):
        if self.client:
            self.client.close()

settings = Settings(DATABASE_URL=os.getenv("MONGO_GAME_DATABASE_URL"))


