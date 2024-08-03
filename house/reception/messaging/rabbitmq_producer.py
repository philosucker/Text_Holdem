import aio_pika
import asyncio
import json
from dotenv import load_dotenv
import os

# .env 파일에서 환경 변수를 로드합니다.
load_dotenv(dotenv_path='house/.env')

# 환경 변수에서 RabbitMQ URL을 가져옵니다.
RABBITMQ_SERVER_URL = os.getenv("RABBITMQ_SERVER_URL")


class MessageProducer:

    def __init__(self):
        self.producer_channel = None
        self.producer_queues = {}

    async def start_producing(self):

        connection = await aio_pika.connect_robust(RABBITMQ_SERVER_URL)
        async with connection:
            self.producer_channel = await connection.channel()
            response_stk_size_query_queue = await self.producer_channel.declare_queue(
                "response_stk_size_query_queue",
                durable=True)
            self.producer_queues["response_stk_size_query_queue"] = response_stk_size_query_queue
            try:
                await asyncio.Future()
            finally:
                await connection.close()

    async def response_stk_size_query(self, data):

        # data = {"table_id": str,  "nick_stk_dict": {}}
        message = aio_pika.Message(
            body=json.dumps(data).encode(),
            priority=10  
        )
        queue_name = self.producer_queues["response_stk_size_query_queue"]

        await self.producer_channel.default_exchange.publish(message, routing_key=queue_name)


    