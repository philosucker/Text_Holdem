import aio_pika
import json

async def send_update_stack_size_to_reception(data):
    connection = await aio_pika.connect_robust("amqp://guest:guest@localhost/")
    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue("update_stack_size_queue", durable=True)
        message = aio_pika.Message(
            body=json.dumps(data).encode(),
            priority=1  # 낮은 우선순위
        )
        await channel.default_exchange.publish(message, routing_key=queue.name)
    print(f"Message sent to update_stack_size queue: {data}")

async def send_stack_size_response_to_reception(data):
    connection = await aio_pika.connect_robust("amqp://guest:guest@localhost/")
    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue("stack_size_response_queue", durable=True)
        message = aio_pika.Message(
            body=json.dumps(data).encode(),
            priority=10  # 높은 우선순위
        )
        await channel.default_exchange.publish(message, routing_key=queue.name)
    print(f"Message sent to stack_size_response_queue: {data}")
