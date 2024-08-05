import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio

from database import connection
from messaging import rabbitmq_consumer, rabbitmq_producer
from services import floor_service
from routers import robby_router



@asynccontextmanager
async def lifespan():
    await connection.settings.initialize_database()
    message_consumer = rabbitmq_consumer.MessageConsumer()
    message_producer = rabbitmq_producer.MessageProducer()
    message_consumer.set_producer(message_producer)
    core_service = floor_service.CoreService()
    core_service.set_producer(message_producer)
    core_service.set_consumer(message_consumer)
    task1 = asyncio.create_task(message_consumer.start_consuming())
    task2 = asyncio.create_task(message_producer.start_producing())
    task3 = asyncio.create_task(floor_service.broadcast_table_list())
    task4 = asyncio.create_task(core_service.setting_table())
    task5 = asyncio.create_task(floor_service.broadcast_chat())
    try:
        yield
    finally:
        print("Closing database connection...")
        await connection.settings.close_database()
        
        # 메시지 브로커 종료
        task1.cancel()
        task2.cancel()
        task3.cancel()
        task4.cancel()
        task5.cancel()
        try:
            await task1
            await task2
            await task3
            await task4
            await task5
        except asyncio.CancelledError:
            pass

app = FastAPI(lifespan=lifespan)
app.include_router(robby_router.router)

if __name__ == '__main__':
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)