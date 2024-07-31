import aio_pika
import asyncio
from services import floor_service
from database import connection
from messaging import rabbitmq_producer
import json

async def process_update_stack_size(message: aio_pika.IncomingMessage):
    async with message.process():
        data = json.loads(message.body)
        db = await connection.get_db().__anext__()
        try:
            await floor_service.update_stack_size(data, db)
            print("Stack size update successful")
        except Exception as e:
            print(f"Stack size update failed: {e}")

async def process_request_stack_size(message: aio_pika.IncomingMessage):
    async with message.process():
        data = json.loads(message.body)
        db = await connection.get_db().__anext__()
        response = await floor_service.request_stack_size(data, db)
        await rabbitmq_producer.send_stack_size_to_floor("stack_size_queue", response, priority=10)

async def start_consuming():
    connection = await aio_pika.connect_robust("amqp://guest:guest@localhost/")
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)

        # 우선순위 큐 선언
        request_stack_size_queue = await channel.declare_queue(
            "request_stack_size_queue", 
            durable=True,
            arguments={"x-max-priority": 10}  # 우선순위 큐 설정
        )
        update_stack_size_queue = await channel.declare_queue(
            "update_stack_size_queue", 
            durable=True,
            arguments={"x-max-priority": 1}  # 우선순위 큐 설정
        )

        await request_stack_size_queue.consume(process_request_stack_size, no_ack=False)
        await update_stack_size_queue.consume(process_update_stack_size, no_ack=False)

        print(" [*] Waiting for messages. To exit press CTRL+C")
        try:
            await asyncio.Future()
        finally:
            await connection.close()
