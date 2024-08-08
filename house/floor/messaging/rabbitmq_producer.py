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
    '''
    채널1
    "request_stk_size_query_queue" 리셉션
    "request_user_stk_size_update_queue" 리셉션

    채널2
    "table_ready_queue" 딜러

    채널3
    "request_agent_queue" 에이전시
    "request_agent_stk_size_update_queue" 에이전시

    채널4
    "training_data_queue" 에이전시
    '''
    async def start_producing(self):
        connection = await aio_pika.connect_robust(RABBITMQ_SERVER_URL)
        async with connection:
            channel_1 = await connection.channel()
            channel_2 = await connection.channel()
            channel_3 = await connection.channel()
            channel_4 = await connection.channel()

            self.producer_channel["channel_1"] = channel_1 # to reception
            self.producer_channel["channel_2"] = channel_2 # to dealer
            self.producer_channel["channel_3"] = channel_3 # to agency
            self.producer_channel["channel_4"] = channel_4 # to agency

            request_stk_size_query_queue = await channel_1.declare_queue(
                "request_stk_size_query_queue", durable=True, 
                arguments={"x-max-priority": 10} 
                )
            request_user_stk_size_update_queue = await channel_1.declare_queue(
                "request_user_stk_size_update_queue", durable=True, 
                arguments={"x-max-priority": 10}
                )
            table_ready_queue = await channel_2.declare_queue(
                "table_ready_queue", durable=True, 
                arguments={"x-max-priority": 10}
                )
            request_agent_queue = await channel_3.declare_queue(
                "request_agent_queue", durable=True, 
                arguments={"x-max-priority": 10}
                )
            request_agent_stk_size_update_queue = await channel_3.declare_queue(
                "request_agent_stk_size_update_queue", durable=True, 
                arguments={"x-max-priority": 10}
                )
            training_data_queue = await channel_4.declare_queue( 
                "training_data_queue", durable=True,
                arguments={"x-max-priority": 1}
                )
            
            self.producer_queues["request_stk_size_query_queue"] = request_stk_size_query_queue # to reception
            self.producer_queues["request_agent_queue"] = request_agent_queue # to agency
            self.producer_queues["table_ready_queue"] = table_ready_queue # to dealer
            self.producer_queues["request_user_stk_size_update_queue"] = request_user_stk_size_update_queue # to reception
            self.producer_queues["request_agent_stk_size_update_queue"] = request_agent_stk_size_update_queue # to agency
            self.producer_queues["training_data_queue"] = training_data_queue # to agenct

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

    async def request_stk_size_query(self, data, priority=10):
        await self._publish_message("request_stk_size_query_queue", "channel_1", data, priority)

    async def request_agent(self, data, priority=5):
        await self._publish_message("request_agent_queue", "channel_1", data, priority)

    async def table_ready(self, data, priority=10):
        await self._publish_message("table_ready_queue", "channel_1", data, priority)

    async def request_user_stk_size_update(self, data, priority=8):
        await self._publish_message("request_user_stk_size_update_queue", "channel_1", data, priority)

    async def request_agent_stk_size_update(self, data, priority=8):
        await self._publish_message("request_user_stk_size_update_queue", "channel_1", data, priority)

    # 추후 사용
    async def training_data(self, data, priority=1):
        await self._publish_message("training_data_queue", "channel_2", data, priority)

