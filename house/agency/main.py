import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio

from messaging import rabbitmq_consumer, rabbitmq_producer
from services import agency_service
from routers import agency_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    agent_manager = agency_service.AgentManager()
    message_consumer = rabbitmq_consumer.MessageConsumer()
    message_producer = rabbitmq_producer.MessageProducer()

    agent_manager.set_producer(message_producer)
    agent_manager.set_consumer(message_consumer)

    task1 = asyncio.create_task(message_consumer.start_consuming())
    task2 = asyncio.create_task(message_producer.start_producing())

    try:
        app.state.agent_manager = agent_manager
        yield
    finally:
        task1.cancel()
        task2.cancel()
        try:
            await asyncio.gather(task1, task2)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Error during shutdown: {e}")

app = FastAPI(lifespan=lifespan)
app.include_router(agency_router.router)

if __name__ == '__main__':
    uvicorn.run("main:app", host="127.0.0.1", port=8003, reload=True)