import aio_pika
import asyncio
import json
from dotenv import load_dotenv
import os
from collections import deque
from rabbitmq_producer import MessageProducer
from database.models import Agent, FoodLog
from utils import nick_name_generator, stk_size_generator

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
        self.producer = None 
        self.agents = {}

    def set_producer(self, producer):
        self.producer : MessageProducer = producer

    async def start_consuming(self):
        connection = await aio_pika.connect_robust(RABBITMQ_SERVER_URL)
        async with connection:
            channel_1 = await connection.channel()
            channel_2 = await connection.channel()
            await channel_1.set_qos(prefetch_count=1)
            await channel_2.set_qos(prefetch_count=1)

            request_agent_queue = await channel_1.declare_queue(
                "request_agent_queue", 
                durable=True,
                arguments={"x-max-priority": 10}  # 우선순위 큐 설정
            )

            response_stk_size_update_queue = await channel_1.declare_queue(
                "response_stk_size_update_queue", 
                durable=True,
                arguments={"x-max-priority": 10}  # 우선순위 큐 설정
            )

            training_data_queue = await channel_2.declare_queue(
                "training_data_queue", 
                durable=True,
                arguments={"x-max-priority": 1}  # 우선순위 큐 설정
            )

            await request_agent_queue.consume(self.process_request_agent, no_ack=False)  # from floor
            await response_stk_size_update_queue(self.process_stk_size_update, no_ack=False)  # from floor
            await training_data_queue.consume(self.process_training_data, no_ack=False)  # from floor
            
            try:
                await asyncio.Future()
            finally:
                await connection.close()

    async def process_request_agent(self, message: aio_pika.IncomingMessage):
        async with message.process():
            # data = {"table_id": str,  "nick_stk_dict": {}}
            data = json.loads(message.body)
            '''
            data= {"table_id": str, "agent_info": {"hard" : 2, "easy" : }}
            '''
            self.agents[data["table_id"]] = data["agent_info"]
            self.producer.response_agent()

    async def process_stk_size_update(self, message: aio_pika.IncomingMessage):
        async with message.process():
            try:
                data : dict = json.loads(message.body)

            except Exception as e:
                print(f"Error processing game log: {e}")
                pass

    async def process_training_data(self, message: aio_pika.IncomingMessage):
        async with message.process():
            try:
                '''
                data = {
                    "log_players": log_players,
                    "log_side_pots": log_side_pots,
                    "log_pot_change": log_pot_change,
                    "log_hand_actions": log_hand_actions,
                    "log_community_cards": log_community_cards,
                    "log_best_hands": log_best_hands,
                    "log_nuts": log_nuts,
                    "log_users_ranking": log_users_ranking
                    }
                '''
                data : dict = json.loads(message.body)

                log_players: dict = data.get("log_players")
                log_side_pots: dict = data.get("log_side_pots")
                log_pot_change: list = data.get("log_pot_change")
                log_hand_actions : dict = data.get("log_hand_actions")  # 매 스트릿 일어난 모든 액션들의 내용을 일어난 순서대로 기록
                log_community_cards : dict = data.get("log_community_cards")
                log_best_hands : dict = data.get("log_best_hands")  # 쇼다운 결과 각 유저의 베스트 핸즈
                log_nuts : dict = data.get("log_nuts")  # 쇼다운 결과 넛츠
                log_users_ranking : deque = data.get("log_users_ranking")  # 쇼다운 결과 핸즈 랭킹
                
                # GameLog 생성
                food_log = FoodLog(
                    players=log_players,
                    side_pots=log_side_pots,
                    pot_change=log_pot_change,
                    hand_actions=log_hand_actions,
                    community_cards=log_community_cards,
                    best_hands=log_best_hands,
                    nuts=log_nuts,
                    users_ranking=log_users_ranking
                    )
                await food_log.insert()

            except Exception as e:
                print(f"Error processing game log: {e}")
                pass

