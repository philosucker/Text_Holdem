import aio_pika
import asyncio
import json
from messaging import rabbitmq_producer
from house.floor.services import robby_service

async def process_update_stack_size_message(message: aio_pika.IncomingMessage):
    async with message.process():
        data = json.loads(message.body)
        await rabbitmq_producer.send_update_stack_size_to_reception(data)

async def process_stack_size_request(message: aio_pika.IncomingMessage):
    async with message.process():
        data = json.loads(message.body)
        response = await robby_service.process_stack_size_request(data)
        await rabbitmq_producer.send_stack_size_response_to_reception(response)

async def process_stack_size_response(message: aio_pika.IncomingMessage):
    async with message.process():
        data = json.loads(message.body)
        await robby_service.handle_stack_size_response(data)

async def start_consuming():
    connection = await aio_pika.connect_robust("amqp://guest:guest@localhost/")
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)

        dealer_queue = await channel.declare_queue(
            "dealer_queue", 
            durable=True,
            arguments={"x-max-priority": 1}  # 우선순위 큐 설정
        )
        stack_size_request_queue = await channel.declare_queue(
            "stack_size_request_queue", 
            durable=True,
            arguments={"x-max-priority": 10}  # 우선순위 큐 설정
        )
        stack_size_response_queue = await channel.declare_queue(
            "stack_size_response_queue", 
            durable=True,
            arguments={"x-max-priority": 10}  # 우선순위 큐 설정
        )

        await stack_size_request_queue.consume(process_stack_size_request, no_ack=False)
        await dealer_queue.consume(process_update_stack_size_message, no_ack=False)
        await stack_size_response_queue.consume(process_stack_size_response, no_ack=False)

        print(" [*] Waiting for messages from dealer. To exit press CTRL+C")
        try:
            await asyncio.Future()
        finally:
            await connection.close()
