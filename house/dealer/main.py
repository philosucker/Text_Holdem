import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio

from messaging import rabbitmq_consumer, rabbitmq_producer
from services import dealer_service
from routers import dealer_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    dealer_manager = dealer_service.DealerManager()
    message_consumer = rabbitmq_consumer.MessageConsumer()
    message_producer = rabbitmq_producer.MessageProducer()

    dealer_manager.set_producer(message_producer)
    dealer_manager.set_consumer(message_consumer)

    task1 = asyncio.create_task(message_consumer.start_consuming())
    task2 = asyncio.create_task(message_producer.start_producing())
    task3 = asyncio.create_task(dealer_manager.table_loop())
    task4 = asyncio.create_task(dealer_manager.result_processor())
    try:
        app.state.dealer_manager = dealer_manager
        # await asyncio.gather(task1, task2, task3, task4) # 필요한거 맞나?
        yield
    finally:
        task1.cancel()
        task2.cancel()
        task3.cancel()
        task4.cancel()
        try:
            await task1
            await task2
            await task3
            await task4
        except asyncio.CancelledError:
            pass

app = FastAPI(lifespan=lifespan)
app.include_router(dealer_router.router)

if __name__ == '__main__':
    uvicorn.run("main:app", host="127.0.0.1", port=8002, reload=True)