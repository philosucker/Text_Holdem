import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio
import logging

from database import connection
from messaging import rabbitmq_consumer, rabbitmq_producer
from services import floor_service
from routers import robby_router

# 로깅 설정
logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app : FastAPI):
    logging.info("Starting Floor application lifespan")
    db_client = await connection.init_db()
    app.state.db_client = db_client  # 데이터베이스 클라이언트를 애플리케이션 상태에 저장
    
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
    logging.info("All Floor tasks started successfully")
    try:
        yield
    finally:
        print("Closing database connection...")
        await connection.close_db(db_client)
        
        # 메시지 브로커 종료
        task1.cancel()
        task2.cancel()
        task3.cancel()
        task4.cancel()
        task5.cancel()
        # try:
        #     await asyncio.gather(task1, task2, task3, task4, task5)
        # except asyncio.CancelledError:
        #     pass
        # except Exception as e:
        #     print(f"Error during shutdown: {e}")

        tasks : list[asyncio.Task] = [task1, task2, task3, task4, task5]
        for task in tasks:
            try:
                await task 
            except asyncio.CancelledError:
                logging.info(f"Task {task.get_name()} cancelled successfully")
                pass
            except Exception as e:
                print(f"Error during shutdown: {e}")

        logging.info("All Floor tasks cancelled and resources released")

app = FastAPI(lifespan=lifespan)
app.include_router(robby_router.router)

if __name__ == '__main__':
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)

