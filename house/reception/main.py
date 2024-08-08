from fastapi import FastAPI
import uvicorn
from contextlib import asynccontextmanager
import asyncio
import logging

from messaging import rabbitmq_consumer, rabbitmq_producer
from utils import key_generator
from routers import user_router
from database import connection

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Starting Reception application lifespan")
    key_generator.generate_secret_key(algorithm="HS256")
    await connection.init_db()  # 데이터베이스 연결 및 테이블 생성
    message_consumer = rabbitmq_consumer.MessageConsumer()
    message_producer = rabbitmq_producer.MessageProducer()
    message_consumer.set_producer(message_producer)
    task1 = asyncio.create_task(message_consumer.start_consuming())
    task2 = asyncio.create_task(message_producer.start_producing())
    logging.info("All Reception tasks started successfully")
    try:
        yield   

    finally:
        print("Closing database connection...")
        await connection.close_db() 
        task1.cancel()
        task2.cancel()
        # try:
        #     await asyncio.gather(task1, task2)
        # except asyncio.CancelledError:
        #     pass
        # except Exception as e:
        #     print(f"Error during shutdown: {e}")
        tasks = [task1, task2]
        for task in tasks:
            try:
                await task
            except asyncio.CancelledError:
                logging.info(f"Task {task.get_name()} cancelled successfully")
                pass
            except Exception as e:
                print(f"Error during shutdown: {e}")

        logging.info("All Reception tasks cancelled and resources released")
        
app = FastAPI(lifespan=lifespan)

app.include_router(user_router.router, prefix="/from_user", tags=["user"])

if __name__ == '__main__':
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)



