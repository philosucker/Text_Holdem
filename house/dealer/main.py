import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio
import logging

from messaging import rabbitmq_consumer, rabbitmq_producer
from services import dealer_service
from routers import dealer_router

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Starting Dealer application lifespan")
    dealer_manager = dealer_service.DealerManager()
    message_consumer = rabbitmq_consumer.MessageConsumer()
    message_producer = rabbitmq_producer.MessageProducer()

    dealer_manager.set_producer(message_producer)
    dealer_manager.set_consumer(message_consumer)

    task1 = asyncio.create_task(message_consumer.start_consuming())
    task2 = asyncio.create_task(message_producer.start_producing())
    task3 = asyncio.create_task(dealer_manager.table_loop())
    task4 = asyncio.create_task(dealer_manager.result_processor())
    logging.info("All Dealer tasks started successfully")
    try:
        app.state.dealer_manager = dealer_manager
        yield
    finally:
        task1.cancel()
        task2.cancel()
        task3.cancel()
        task4.cancel()
        # try:
        #     await asyncio.gather(task1, task2, task3, task4)
        # except asyncio.CancelledError:
        #     pass
        # except Exception as e:
        #     print(f"Error during shutdown: {e}")
        tasks : list[asyncio.Task] = [task1, task2, task3, task4]
        for task in tasks:
            try:
                await task 
            except asyncio.CancelledError:
                logging.info(f"Task {task.get_name()} cancelled successfully")
                pass
            except Exception as e:
                print(f"Error during shutdown: {e}")

        logging.info("All Dealer tasks cancelled and resources released")

app = FastAPI(lifespan=lifespan)
app.include_router(dealer_router.router)

if __name__ == '__main__':
    uvicorn.run("main:app", host="127.0.0.1", port=8002, reload=True)