from typing import Optional
from beanie import init_beanie 
from models.events import Event  
from models.users import User  
from motor.motor_asyncio import AsyncIOMotorClient 
from pydantic_settings import BaseSettings 


class Settings(BaseSettings):

    DATABASE_URL: Optional[str] = None 
    client: Optional[AsyncIOMotorClient] = None
    SECRET_KEY: Optional[str] = None 
 
    async def initialize_database(self):
        self.client = AsyncIOMotorClient(self.DATABASE_URL)  
        database = self.client["TempDB"] 
        
        await init_beanie(database=database, document_models=[Event, User])  

    async def close_database(self):
        if self.client:
            self.client.close()  

    class Config:
        env_file = ".env"

settings = Settings()