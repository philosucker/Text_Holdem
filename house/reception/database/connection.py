import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from . import manipulation
from dotenv import load_dotenv

load_dotenv(dotenv_path="./house/.env")

DATABASE_URL = os.getenv("SQL_USER_DATABASE_URL")

connect_args = {"check_same_thread": False}

engine = create_async_engine(DATABASE_URL, echo=True)

AsyncSessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)
Base = declarative_base()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield manipulation.Database(session)

async def close_db():
    await engine.dispose()

