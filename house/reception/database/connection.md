
```python
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from database import manipulation
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
'''
SQLAlchemy의 선언적 베이스 클래스를 생성합니다.
이 클래스는 모든 모델 클래스가 상속받을 기본 클래스가 됩니다.
'''
Base = declarative_base()

'''
비동기 엔진을 사용하더라도, 
SQLAlchemy의 Base.metadata.create_all 같은 메서드는 동기적으로 설계되어 있습니다. 
이를 비동기 컨텍스트에서 실행하려면 run_sync를 사용해야 합니다. 
run_sync는 동기 함수를 비동기 컨텍스트에서 실행할 수 있게 해줍니다.

Base.metadata.create_all을 비동기 컨텍스트에서 실행하여 데이터베이스에 테이블을 생성합니다.

Base.metadata.create_all은 SQLAlchemy에서 선언된 모든 테이블을 포함합니다. 
테이블은 Base 클래스를 상속받아 정의된 모든 ORM 모델 클래스의 메타데이터에 포함됩니다.
'''
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


'''
get_db: 데이터베이스 세션을 제공하는 제너레이터 함수입니다.
with db_session() as session: 컨텍스트 매니저를 사용하여 세션을 생성하고, 블록이 종료되면 자동으로 세션을 종료합니다.
yield session: 세션을 호출자에게 반환합니다. 
이 함수는 주로 FastAPI의 종속성 주입 시스템과 함께 사용됩니다. 
FastAPI 엔드포인트 함수는 이 제너레이터를 호출하여 세션을 사용하고, 요청 처리가 끝나면 세션이 자동으로 종료됩니다.
'''
async def get_db():
    async with AsyncSessionLocal() as session:
        yield manipulation.Database(session)

async def close_db():
    await engine.dispose()


```