import aio_pika
import asyncio
import json
from dotenv import load_dotenv
import os

# .env 파일에서 환경 변수를 로드합니다.
load_dotenv(dotenv_path='./house/.env')

# 환경 변수에서 RabbitMQ URL을 가져옵니다.
RABBITMQ_SERVER_URL = os.getenv("RABBITMQ_SERVER_URL")


class MessageProducer:

    def __init__(self):
        self.producer_channel = {}
        self.producer_queues = {}

    async def start_producing(self):

        connection = await aio_pika.connect_robust(RABBITMQ_SERVER_URL)
        async with connection:
            channel_1 = await connection.channel()
            self.producer_channel["channel_1"] = channel_1

            response_stk_size_query_queue = await channel_1.declare_queue(
                "response_stk_size_query_queue",
                durable=True)
            
            self.producer_queues["response_stk_size_query_queue"] = response_stk_size_query_queue
            try:
                await asyncio.Future()
            finally:
                await connection.close()
    
    async def response_stk_size_query(self, data):
        try:
            # data = {"table_id": str, "nick_stk_dict": dict}
            message = aio_pika.Message(
                body=json.dumps(data).encode(),
                priority=10
            )
            channel : aio_pika.Channel = self.producer_channel["channel_1"]
            queue : aio_pika.Queue = self.producer_queues["response_stk_size_query_queue"]

            await channel.default_exchange.publish(message, routing_key=queue.name)
        except Exception as e:
            print(f"Failed to send message: {e}")