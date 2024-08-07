import asyncio
from fastapi import WebSocket, HTTPException, WebSocketDisconnect
from concurrent.futures import ProcessPoolExecutor

from schemas import user
from messaging import rabbitmq_consumer, rabbitmq_producer
from core import dealer

def run_async(func, *args):
    return asyncio.run(func(*args))

class DealerManager:
    '''
    redis 사용 고려
    '''
    def __init__(self):

        self.active_connections: dict[str, dict[str, WebSocket]] = {}
        self.dealer_instances : dict[str, dealer.Dealer] = {}
        self.tables_info :dict[str, dict]= {}

        self.producer = None 
        self.consumer = None
        self.table_queue = asyncio.Queue()

        self.executor = ProcessPoolExecutor()  # 프로세스 풀 생성

    def set_producer(self, producer):
        self.producer: rabbitmq_producer.MessageProducer = producer
    
    def set_consumer(self, consumer):
        self.consumer: rabbitmq_consumer.MessageConsumer = consumer

    async def handle_user_connection(self, current_user: dict, message : user.TableID, websocket: WebSocket) -> tuple[str, str]:

        user_nick = current_user.get("user_nick")
        user_email = current_user.get("user_email")
        table_id = message.table_id

        if not user_nick or not user_email:
            raise HTTPException(status_code=400, detail="Invalid token")
        
        if not table_id:
            raise HTTPException(status_code=400, detail="Missing table_id")

        # 게임 진행 중 재접속한 경우
        if table_id in self.dealer_instances:
            dealer_instance = self.dealer_instances[table_id]
            await dealer_instance.reconnection_handler({user_nick : websocket})   

        # 최초 연결 유저는 테이블 정보 생성
        if table_id not in self.active_connections:
            self.active_connections[table_id] = {}

        # 중복 연결 방지: 동일 닉네임으로 다른 연결이 이미 존재하는 경우, 기존 연결 종료
        if user_nick in self.active_connections[table_id]:
            old_websocket: WebSocket = self.active_connections[table_id][user_nick]
            try:
                await old_websocket.close()
            except WebSocketDisconnect:
                # 클라이언트가 이미 연결을 끊은 경우, 특별히 할 작업이 없음
                pass
            except ConnectionError:
                # 네트워크 오류 처리
                print(f"Network error occurred while closing websocket for {user_nick}")
            except Exception as e:
                # 기타 모든 예외 처리
                print(f"Unexpected error during disconnection handling for {user_nick}: {str(e)}")
            finally:
                # 연결 정보 정리
                await self.handle_user_disconnection(user_nick, table_id)

        self.active_connections[table_id][user_nick] = websocket 

        return user_nick, table_id

    async def handle_user_disconnection(self, user_nick: str, table_id: str) -> None:
        del self.active_connections[table_id][user_nick]

    async def table_loop(self):
        while True:
            
            # 큐가 비어 있으면, inbox에 메시지가 들어올 때까지 대기 
            data : dict = await self.consumer.table_ready_inbox.get()
            '''
            data = {
            "table_id" : str
            "rings" : int
            "stakes" : str
            "new_players" : dict[str, int]  # {"nick_4" : 1000, "nick_5": 800, "nick_6" : 1500}
            "continuing_players" : dict[str, int]  # {"nick_1" : 100, "nick_2": 2000, "nick_3" : 500}
            "determined_positions" : dict[str, str] # {"nick_1" : "BB", "nick_2": "CO", "nick_3" : D}
            }
            '''
            table_id = data.get("table_id")
            connections :dict = self.active_connections.get(table_id, {})
            all_user = list(data["new_players"]) + list(data["continuing_players"])
            '''
            table_ready 메시지는 왔으나 웹소켓 연결이 불완전한 경우 floor로 돌려보낸다.
            아니면 await self.consumer.table_ready_inbox.put(data)를 해야할까..
            '''
            if not connections:
                await self.producer.table_failed(data)
                continue

            elif len(connections) != len(all_user):
                valid_keys = connections.keys()
                data["new_players"] = {k: v for k, v in data["new_players"].items() if k in valid_keys}
                data["continuing_players"] = {k: v for k, v in data["continuing_players"].items() if k in valid_keys}
                data["determined_positions"] = {k: v for k, v in data["determined_positions"].items() if k in valid_keys}
                await self.producer.table_failed(data)
                continue

            elif not all(user_nick in connections for user_nick in all_user):
                mismatched_nicks_in_data = [user_nick for user_nick in all_user if user_nick not in connections]
                mismatched_nicks_in_connections = [user_nick for user_nick in connections if user_nick not in all_user]

                invalid_keys = mismatched_nicks_in_data + mismatched_nicks_in_connections

                for user_nick in invalid_keys:
                    if user_nick in data["new_players"]:
                        del data["new_players"][user_nick]
                    if user_nick in data["continuing_players"]:
                        del data["continuing_players"][user_nick]
                    if user_nick in data[["determined_positions"]]:
                        del data["determined_positions"][user_nick]
                await self.producer.table_failed(data)
                continue
            
            self.tables_info[table_id] = data
            table_info = self.tables_info[table_id]
            dealer_instance = dealer.Dealer(table_info, connections)
            self.dealer_instances[table_id] = dealer_instance

            # loop = asyncio.get_running_loop()
            # task = loop.run_in_executor(self.executor, dealer_instance.go_street)
            # task = loop.run_in_executor(self.executor, run_async, dealer_instance.go_street)

            task = asyncio.create_task(dealer_instance.go_street())
            await self.table_queue.put(task)
            await asyncio.sleep(0.5)
            
    async def result_processor(self):
        while True:
            # 큐에서 완료된 작업을 가져와 결과를 처리
            task = await self.table_queue.get()
            result = await task 
            await self.producer.game_log(result) 
            table_id = result["table_id"]
            dealer_instance = self.dealer_instances.pop(table_id, None)
            if dealer_instance:
                for websocket in self.active_connections[table_id].values():
                    await websocket.close()
                del self.tables_info[table_id]
                del self.active_connections[table_id]
            await asyncio.sleep(0.5)
