import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio
import logging

from agency.messaging import rabbitmq_consumer, rabbitmq_producer
from agency.services import agency_service
from agency.routers import agency_router
from agency.database import connection

# 로깅 설정
logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Starting Agency application lifespan")
    db_client = await connection.init_db()

    agent_manager = agency_service.AgentManager()
    message_consumer = rabbitmq_consumer.MessageConsumer()
    message_producer = rabbitmq_producer.MessageProducer()

    agent_manager.set_producer(message_producer)
    agent_manager.set_consumer(message_consumer)

    task1 = asyncio.create_task(message_consumer.start_consuming())
    task2 = asyncio.create_task(message_producer.start_producing())
    logging.info("All Agency tasks started successfully")
    try:
        app.state.agent_manager = agent_manager
        yield
    finally:
        await connection.close_db(db_client)
        task1.cancel()
        task2.cancel()
        # try:
        #     await asyncio.gather(task1, task2)
        # except asyncio.CancelledError:
        #     pass
        # except Exception as e:
        #     print(f"Error during shutdown: {e}")
        tasks : list[asyncio.Task] = [task1, task2]
        for task in tasks:
            try:
                await task 
            except asyncio.CancelledError:
                logging.info(f"Task {task.get_name()} cancelled successfully")
                pass
            except Exception as e:
                print(f"Error during shutdown: {e}")

        logging.info("All Agency tasks cancelled and resources released")

app = FastAPI(lifespan=lifespan)
app.include_router(agency_router.router)

if __name__ == '__main__':
    uvicorn.run("main:app", host="127.0.0.1", port=8003, reload=True)