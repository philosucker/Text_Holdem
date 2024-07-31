import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio

from database import connection
from messaging import rabbitmq_consumer
from house.floor.routers import robby_router
from services import floor_service

@asynccontextmanager
async def lifespan():
    await connection.settings.initialize_database()
    task1 = asyncio.create_task(rabbitmq_consumer.start_consuming())
    task2 = asyncio.create_task(floor_service.broadcast_table_list())
    task3 = asyncio.create_task(floor_service.broadcast_table_ready())
    task3 = asyncio.create_task(floor_service.broadcast_chat())
    try:
        yield
    finally:
        print("Closing database connection...")
        await connection.settings.close_database()
        
        # 메시지 브로커 종료
        task1.cancel()
        task2.cancel()
        task3.cancel()
        try:
            await task1
        except asyncio.CancelledError:
            pass
        try:
            await task2
        except asyncio.CancelledError:
            pass
        try:
            await task3
        except asyncio.CancelledError:
            pass

app = FastAPI(lifespan=lifespan)
app.include_router(robby_router.router)

if __name__ == '__main__':
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)