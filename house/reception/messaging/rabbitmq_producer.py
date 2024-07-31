import aio_pika
import json

async def send_stack_size_to_floor(queue_name: str, data: dict, priority: int):
    connection = await aio_pika.connect_robust("amqp://guest:guest@localhost/")
    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue(queue_name, durable=True)
        message = aio_pika.Message(
            body=json.dumps(data).encode(),
            priority=priority  # 메시지 우선순위 설정
        )
        await channel.default_exchange.publish(message, routing_key=queue.name)
    print(f"Message sent to queue {queue_name}: {data} with priority {priority}")
