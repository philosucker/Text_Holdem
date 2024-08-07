import aio_pika
import asyncio
import json
from dotenv import load_dotenv
import os

from services import server_service
from database import connection
from messaging import rabbitmq_producer

# .env 파일에서 환경 변수를 로드합니다.
load_dotenv(dotenv_path='./house/.env')

# 환경 변수에서 RabbitMQ URL을 가져옵니다.
RABBITMQ_SERVER_URL = os.getenv("RABBITMQ_SERVER_URL")


class MessageConsumer:

    def __init__(self):
        self.producer = None 

    def set_producer(self, producer):

        self.producer : rabbitmq_producer.MessageProducer = producer

    async def start_consuming(self):

        connection = await aio_pika.connect_robust(RABBITMQ_SERVER_URL)
        async with connection:
            channel_1 = await connection.channel()
            await channel_1.set_qos(prefetch_count=1)
            
            request_stk_size_query_queue = await channel_1.declare_queue(
                "request_stk_size_query_queue", 
                durable=True,
                arguments={"x-max-priority": 10}  
            )
            request_stk_size_update_queue = await channel_1.declare_queue(
                "request_user_stk_size_update_queue",
                durable=True,
                arguments={"x-max-priority": 1} 
            )

            await request_stk_size_query_queue.consume(self.process_stk_size_query, no_ack=False)
            await request_stk_size_update_queue.consume(self.process_stk_size_update, no_ack=False)

            print(" [*] Waiting for messages. To exit press CTRL+C")
            try:
                await asyncio.Future()
            finally:
                await connection.close()

    async def process_stk_size_query(self, message: aio_pika.IncomingMessage):

        async with message.process():
            query = json.loads(message.body)
            # query = {"table_id" : str, "user_nick_list" : list}
            db = await connection.get_db().__anext__()
            try:
                nick_stk_dict = await server_service.stk_size_query(query, db)
                response = {
                    "table_id": query["table_id"],
                    "nick_stk_dict": nick_stk_dict
                }
                await self.producer.response_stk_size_query(response)

            except Exception as e:
                print(f"Stack size query failed: {e}")

    async def process_stk_size_update(self, message: aio_pika.IncomingMessage):
        
        async with message.process():
            data = json.loads(message.body)
            # data = {"user_nick" : str, "stk_size" : int}
            db = await connection.get_db().__anext__()
            try:
                await server_service.stk_size_update(data, db)
                print("Stack size update successful")
            except Exception as e:
                print(f"Stack size update failed: {e}")