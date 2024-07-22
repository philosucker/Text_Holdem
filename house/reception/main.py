from fastapi import FastAPI
import uvicorn
from contextlib import asynccontextmanager
from routers import user_router, floor_router, dealer_router
from database import connection

# app = FastAPI()
'''
@asynccontextmanager 데코레이터를 사용한 lifespan 함수는 
FastAPI 애플리케이션의 수명 주기 동안 특정 작업을 수행하기 위해 사용됩니다.
@asynccontextmanager를 사용하여 lifespan 함수를 정의할 때, 
yield를 사용하면 함수의 앞부분은 애플리케이션이 시작될 때 실행되고,
yield 다음에 오는 코드는 애플리케이션이 종료될 때 실행됩니다.
@asynccontextmanager는 비동기 컨텍스트 관리자 생성기 함수입니다.
비동기 컨텍스트 관리자 함수는 yield를 사용하여 진입 및 종료 지점을 정의합니다.
'''
@asynccontextmanager
async def lifespan():
    # 애플리케이션이 시작될 때 실행
    await connection.init_db()  # 데이터베이스 연결 및 테이블 생성
    try:
        yield   # 함수가 여기서 일시 중단되고, 이 지점에서 애플리케이션이 실행됨
                # 애플리케이션이 클라이언트 요청을 처리하기 시작
    finally:
        # 애플리케이션이 종료될 때 실행
        print("Closing database connection...")
        await connection.close_db() # SQLAlchemy 엔진에서 연결 풀을 안전하게 닫고, 모든 연결을 정리
        # 이 방법은 데이터베이스 리소스를 안전하게 관리하고, 애플리케이션이 종료될 때 리소스 누수를 방지합니다.


# app.router.lifespan = lifespan
app = FastAPI(lifespan=lifespan)

app.include_router(user_router.router, prefix="/from_user", tags=["user"])
app.include_router(floor_router.router, prefix="/from_floor", tags=["floor"])
app.include_router(dealer_router.router, prefix="/from_dealer", tags=["dealer"])

if __name__ == '__main__':
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)