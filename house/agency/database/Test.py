from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수를 불러옴
dotenv_path = "./house/.env"
load_dotenv(dotenv_path=dotenv_path, encoding='utf-8')

DATABASE_URL = os.getenv("AGENCY_DATABASE_URL")
if not DATABASE_URL:
    raise ValueError(f"AGENCY_DATABASE_URL not set in {dotenv_path}")

async def test_connection():
    client = AsyncIOMotorClient(DATABASE_URL)
    try:
        # 서버 정보를 가져와서 연결이 성공적인지 테스트
        server_info = await client.server_info()
        print("MongoDB 연결 성공:", server_info)
    except Exception as e:
        print("MongoDB 연결 실패:", e)
    finally:
        client.close()

import asyncio
asyncio.run(test_connection())
