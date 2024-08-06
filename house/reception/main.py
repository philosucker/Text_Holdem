from fastapi import FastAPI
import uvicorn
from contextlib import asynccontextmanager
import asyncio

from .messaging import rabbitmq_consumer, rabbitmq_producer
from .utils import key_generator
from .routers import user_router
from .database import connection

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 애플리케이션이 시작될 때 실행
    key_generator.generate_secret_key(algorithm="HS256")
    await connection.init_db()  # 데이터베이스 연결 및 테이블 생성
    message_consumer = rabbitmq_consumer.MessageConsumer()
    message_producer = rabbitmq_producer.MessageProducer()
    message_consumer.set_producer(message_producer)
    task1 = asyncio.create_task(message_consumer.start_consuming())
    task2 = asyncio.create_task(message_producer.start_producing())
    try:
        yield   

    finally:
        print("Closing database connection...")
        await connection.close_db() 
        task1.cancel()
        task2.cancel()
        try:
            await asyncio.gather(task1, task2)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Error during shutdown: {e}")

app = FastAPI(lifespan=lifespan)

app.include_router(user_router.router, prefix="/from_user", tags=["user"])

if __name__ == '__main__':
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)



