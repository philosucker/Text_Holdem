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
            channel_2 = await connection.channel()
            self.producer_channel["channel_1"] = channel_1
            self.producer_channel["channel_2"] = channel_2

            game_log_queue = await channel_1.declare_queue("table_failed", durable=True)  # to floor
            table_failed = await channel_2.declare_queue("game_log_queue", durable=True)  # to floor
            self.producer_queues["table_failed"] = table_failed
            self.producer_queues["game_log_queue"] = game_log_queue 
            try:
                await asyncio.Future()
            finally:
                await connection.close()

    async def _publish_message(self, queue_name, channel_name, data, priority):
        try:
            message = aio_pika.Message(
                body=json.dumps(data).encode(),
                priority=priority  # 우선순위 설정
            )
            channel: aio_pika.Channel = self.producer_channel[channel_name]
            queue: aio_pika.Queue = self.producer_queues[queue_name]
            await channel.default_exchange.publish(message, routing_key=queue.name)
        except Exception as e:
            print(f"Failed to send message to {queue_name}: {e}")
            
    async def table_failed(self, data, priority):
        await self._publish_message("table_failed", "channel_1", data, priority)

    async def game_log(self, data, priority=10):
        await self._publish_message("game_log_queue", "channel_2", data, priority)

