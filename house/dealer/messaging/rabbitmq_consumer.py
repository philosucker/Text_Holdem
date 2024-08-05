import aio_pika
import asyncio
import json
from dotenv import load_dotenv
import os
from collections import OrderedDict
# .env 파일에서 환경 변수를 로드합니다.
load_dotenv(dotenv_path='./house/.env')

# 환경 변수에서 RabbitMQ URL을 가져옵니다.
RABBITMQ_SERVER_URL = os.getenv("RABBITMQ_SERVER_URL")

class MessageConsumer:
    def __init__(self):
        '''
        이렇게 서버 메모리에서 처리할 수도 있고 
        redis나 floor mongoDB에 기록후 floor_service에서 DB를 찾게 할 수도 있다.
        그런데 DB에 기록후 조회하게 하는 방법은 disk I/O가 너무 많이 일어날 수 있을 것 같다.
        일단 서버메모리에서 처리하게 하고
        나중에 redis 사용을 고려해 볼 것. 
        '''
        self.table_ready_inbox = asyncio.Queue(maxsize=0)
        
    async def start_consuming(self):
        connection = await aio_pika.connect_robust(RABBITMQ_SERVER_URL)
        async with connection:
            channel_1 = await connection.channel()
            await channel_1.set_qos(prefetch_count=1)

            table_ready_queue = await channel_1.declare_queue(
                "table_ready_queue", 
                durable=True,
                arguments={"x-max-priority": 10}  # 우선순위 큐 설정
            )
            await table_ready_queue.consume(self.process_table_ready, no_ack=False) # from floor MessageProducer
            try:
                await asyncio.Future()
            finally:
                await connection.close()

    async def process_table_ready(self, message: aio_pika.IncomingMessage):
        async with message.process():
            '''
            data = {
            "table_id" : str
            "rings" : int
            "stakes" : str
            new_players : dict[str, int]  # {"nick_4" : 1000, "nick_5": 800, "nick_6" : 1500}
            continuing_players : dict[str, int]  # {"nick_1" : 100, "nick_2": 2000, "nick_3" : 500}
            determined_positions : dict[str, str] # {"nick_1" : "BB", "nick_2": "CO", "nick_3" : D}
            }
            '''
            data = json.loads(message.body)
            self.table_ready_inbox.put(data)


