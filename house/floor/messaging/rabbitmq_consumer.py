import aio_pika
import asyncio
import json
from dotenv import load_dotenv
import os
from collections import deque, OrderedDict
from rabbitmq_producer import MessageProducer
from database.models import TableLog, GameLog 

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
        self.user_nick_stk_inbox = OrderedDict()
        self.agent_nick_stk_inbox = OrderedDict()
        self.producer = None 

    def set_producer(self, producer):

        self.producer : MessageProducer = producer

    '''
    채널1
    "response_stk_size_query_queue" 리셉션
    "response_agent_queue" 에이전시

    채널2
    "game_log_queue" 딜러
    '''
    async def start_consuming(self):
        connection = await aio_pika.connect_robust(RABBITMQ_SERVER_URL)
        async with connection:
            channel_1 = await connection.channel()
            channel_2 = await connection.channel()
            await channel_1.set_qos(prefetch_count=1)
            await channel_2.set_qos(prefetch_count=1)

            response_stk_size_query_queue = await channel_1.declare_queue(
                "response_stk_size_query_queue", 
                durable=True,
                arguments={"x-max-priority": 10}  # 우선순위 큐 설정
            )
            response_agent_queue = await channel_1.declare_queue(
                "response_agent_queue", 
                durable=True,
                arguments={"x-max-priority": 1}  # 우선순위 큐 설정
            )
            
            table_failed_queue = await channel_1.declare_queue(
                "table_failed", 
                durable=True,
                arguments={"x-max-priority": 1}  # 우선순위 큐 설정
            )
                        
            game_log_queue = await channel_2.declare_queue(
                "game_log_queue", 
                durable=True,
                arguments={"x-max-priority": 1}  # 우선순위 큐 설정
            )
            await response_stk_size_query_queue.consume(self.process_stk_size_query, no_ack=False) # from reception MessageProducer
            await response_agent_queue(self.process_agent_info, no_ack=False) # from agency
            await table_failed_queue.consume(self.process_table_update, no_ack=False)  # from dealer
            await game_log_queue.consume(self.process_game_log, no_ack=False)  # from dealer
            

            try:
                await asyncio.Future()
            finally:
                await connection.close()

    async def process_stk_size_query(self, message: aio_pika.IncomingMessage):
        async with message.process():
            # data = {"table_id": str,  "nick_stk_dict": {}}
            data = json.loads(message.body)
            self.user_nick_stk_inbox[data["table_id"]] = data["nick_stk_dict"]

    async def process_agent_info(self, message: aio_pika.IncomingMessage):
        async with message.process():
            # data = {"table_id": str,  "nick_stk_dict": {}}
            data = json.loads(message.body)
            self.agent_nick_stk_inbox[data["table_id"]] = data["nick_stk_dict"]

    async def process_table_update(self, message: aio_pika.IncomingMessage):
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
            try:            
                data : dict = json.loads(message.body)
                table_id: str = data.get("table_id")
                table_log = await TableLog.find_one(TableLog.table_id == table_id)
                table_log.status = "waiting"
                table_log.now = len(data["new_players"]) + len(data["continuing_players"])
                table_log.new_players = data["new_players"]
                table_log.continuing_players = data["continuing_players"]
                table_log.determined_positions = data["determined_positions"]
                
                await table_log.save()
                
            except Exception as e:
                print(f"Error updating table log: {e}")
                pass
            
    async def process_game_log(self, message: aio_pika.IncomingMessage):
        async with message.process():
            data: dict = json.loads(message.body)
            try:
                # 데이터 파싱
                table_id: str = data.get("table_id")
                continuing_players: dict = data.get("continuing_players")
                determined_positions: dict = data.get("determined_positions")

                log_start_time: str = data.get("start_time")
                log_end_time: str = data.get("end_time")
                log_players: dict = data.get("log_players")
                log_side_pots: dict = data.get("log_side_pots")
                log_pot_change: list = data.get("log_pot_change")
                log_hand_actions : dict = data.get("log_hand_actions")  # 매 스트릿 일어난 모든 액션들의 내용을 일어난 순서대로 기록
                log_community_cards : dict = data.get("log_community_cards")
                log_best_hands : dict = data.get("log_best_hands")  # 쇼다운 결과 각 유저의 베스트 핸즈
                log_nuts : dict = data.get("log_nuts")  # 쇼다운 결과 넛츠
                log_users_ranking : deque = data.get("log_users_ranking")  # 쇼다운 결과 핸즈 랭킹


                query = {log_players[position]["user_nick"] : log_players[position]["stk_size"] for position in log_players}
                # 유저 스택사이즈 업데이트 요청
                await self.producer.request_stk_size_update(query)

                # TableLog 업데이트
                table_log = await TableLog.find_one(TableLog.table_id == table_id)
                if table_log:
                    if not continuing_players:
                        table_log.status = "dismissed"
                        table_log.dismissed_time = log_end_time
                        # 끝난 테이블은 아예 지워버릴까?
                    else:
                        table_log.status = "waiting"
                        table_log.now = len(continuing_players)
                        table_log.continuing_players = continuing_players
                        table_log.determined_positions = determined_positions
                    await table_log.save()

                # GameLog 생성
                game_log = GameLog(
                    start_time=log_start_time,
                    end_time=log_end_time,
                    players=log_players,
                    side_pots=log_side_pots,
                    pot_change=log_pot_change,
                    hand_actions=log_hand_actions,
                    community_cards=log_community_cards,
                    best_hands=log_best_hands,
                    nuts=log_nuts,
                    users_ranking=log_users_ranking
                )
                await game_log.insert()

            except Exception as e:
                print(f"Error processing game log: {e}")
                pass

