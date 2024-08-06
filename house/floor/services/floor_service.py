import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from database.models import TableLog, ChatLog
import json
import zlib

from routers import robby_router
from services import robby_service
from messaging import rabbitmq_consumer, rabbitmq_producer

async def broadcast_table_list():
    while True:
        try:
            # 필터 조건 정의: now < max 이고, status가 "waiting"인 테이블만 선택
            filters = {"now": {"$lt": "max"}, "status": "waiting"}
            projection = {"table_id": 1, 
                          "creation_time": 1, 
                          "rings": 1, 
                          "stakes": 1, 
                          "agent": 1, 
                          "now": 1, 
                          "max": 1, 
                          "status": 1}

            # 필터 조건을 사용하여 테이블 로그 검색 (필드 선택 포함)
            table_logs :list[TableLog] = await TableLog.find(filters, projection=projection).to_list()
 
            table_list = []

            for log in table_logs:
                table_info = {
                    "table_id": log.table_id,
                    "creation_time": log.creation_time,
                    "rings": log.rings,
                    "stakes": log.stakes,
                    "agent": log.agent,
                    "now": log.now,
                    "max": log.max,
                    "status": log.status,
                }
                table_list.append(table_info)
            
            # 남은 자리 수가 적은 순서대로, 같은 경우 생성 시간 기준으로 정렬
            table_list = sorted(
                table_list, 
                key=lambda table_info: (table_info['max'] - table_info['now'], table_info.get('creation_time'))
            )

            # JSON 데이터 압축
            compressed_data = zlib.compress(json.dumps({"Table list": table_list}).encode('utf-8'))

            # 모든 연결된 클라이언트에게 메시지 전송
            disconnected_clients = []
            for user_nick, websocket in robby_router.connected_clients.items():
                try:
                    await websocket.send_bytes(compressed_data)
                except WebSocketDisconnect:
                    disconnected_clients.append(user_nick)
                except Exception as e:
                    disconnected_clients.append(user_nick)
                    print(f"Error sending message: {e}")

            # 연결이 끊어진 클라이언트 처리
            for user_nick in disconnected_clients:
                await robby_service.handle_user_disconnection(user_nick)

            await asyncio.sleep(1)  # 주기 조정

        except Exception as e:
            print(f"Unexpected error in broadcast_table_list: {e}")
            await asyncio.sleep(1)

class CoreService:
    
    def __init__(self):
        self.producer = None 
        self.consumer = None

    def set_producer(self, producer):
        self.producer: rabbitmq_producer.MessageProducer = producer
    
    def set_consumer(self, consumer):
        self.consumer: rabbitmq_consumer.MessageConsumer = consumer

    async def setting_table(self):
        '''
        TableLog에서 게임 시작 가능한 테이블을 찾은뒤
        해당 테이블의 유저들 스택사이즈를 reception에 요청하고, 
        유저들에게 dealer 서버에 웹소켓 연결 신청 메시지를 보낸다.
        모든 유저에게 메시징 완료하면
        리셉션 서버에서 전달한 해당 테이블의 유저들 스택사이즈를 받아서
        테이블 정보를 딜러 서버에 보낸다.
        
        여기서는 해당 테이블의 유저들이 웹소켓 연결에 모두 성공했는지 확인하지 않는다.
        '''
        while True:
            try:
                # 필터 조건 정의: now == max 이고, status가 "waiting"인 테이블만 선택
                filters = {"now": {"$eq": "max"}, "status": "waiting"}
                projection = {
                    "table_id": 1,
                    "rings": 1,
                    "stakes": 1,
                    "agent": 1, # {"hard" : 2, "easy" : 1}
                    "new_players": 1, # {"nick_4" : 0, "nick_5": 0, "nick_6" : 0}
                    "continuing_players": 1, # {"nick_1" : 100, "nick_2": 2000, "nick_3" : 500}
                    "determined_positions": 1, # {"nick_1" : "BB", "nick_2": "CO", "nick_3" : D}
                }
                # 필터 조건을 사용하여 테이블 로그 검색 (필드 선택 포함)
                full_tables: list[TableLog] = await TableLog.find(filters, projection=projection).to_list()
                # 앱에서 유저들이 테이블 생성, 조회, 선택 취소 등으로 TableLog의 상태가 계속 변하고 있는데
                # 그 과정 중에 특정 시점에서 끊고 검색을 하게 되는 건가? 이럴 때 문제는 없나?
            
                # 각 테이블에 대한 작업
                for log in full_tables:
                    table_info = {
                        "table_id": log.table_id,
                        "rings": log.rings,
                        "stakes": log.stakes,
                        "agent": log.agent,
                        "new_players": log.new_players,
                        "continuing_players": log.continuing_players,
                        "determined_positions": log.determined_positions
                    }
                    query = {"table_id": table_info["table_id"], "user_nick_list": table_info["new_players"]}
                    # 1. query를 메시지 브로커의 "request_stk_size_query_queue" 큐로 리셉션 서버에 보내는 함수
                    await self.producer.request_stk_size_query(query)

                    if table_info.get("agent", None):
                        agent_info = {"table_id": table_info["table_id"], "agent_info": table_info["agent"]}
                        # 2. agent_info를 메시지 브로커의 "request_agent_queue" 큐로 에이전시 서버에 보내는 함수
                        await self.producer.request_agent(agent_info)

                    message = {"Message": "Table Full", "Table id": str(table_info["table_id"])}
                    compressed_data = zlib.compress(json.dumps(message).encode('utf-8'))
                    count = 0
                    user_nick_list = list(table_info["new_players"]) + list(table_info["determined_positions"])
                    
                    # 3. 일치하는 웹소켓 클라이언트를 찾아 메시지 전송
                    for user_nick in user_nick_list:
                        websocket: WebSocket = robby_router.connected_clients.get(user_nick)
                        if websocket:
                            try:
                                await websocket.send_bytes(compressed_data)
                                count += 1
                            except WebSocketDisconnect:
                                await robby_service.handle_user_disconnection(user_nick)
                            except Exception as e:
                                print(f"Error sending message to {user_nick}: {e}")
                        else:
                            # 웹소켓이 없는 경우 table_info["new_players"]와 table_info["determined_positions"]에서 
                            # user_nick을 키로 갖는 딕셔너리를 제거
                            if user_nick in table_info["new_players"]:
                                del log.new_players[user_nick]
                            elif user_nick in table_info["determined_positions"]:
                                del log.determined_positions[user_nick]
                    
                    if count != len(user_nick_list):
                        log.now = count
                        await log.save()
                        continue
                    else:
                        # 3. 리셉션 서버가 1.에서 보낸 메시지를 받아 처리한 후 회신한 메시지를 수신
                        # 메시지의 테이블 아이디를 확인해서 현재 테이블 번호와 맞는 메시지를 찾을 때까지 대기
                        while table_info["table_id"] not in self.consumer.user_nick_stk_inbox:
                            await asyncio.sleep(0.5)
                        user_nick_stk_dict = self.consumer.user_nick_stk_inbox.pop(table_info["table_id"])
                        table_info["new_players"] = user_nick_stk_dict

                        if table_info.get("agent", None):
                            # 4. 리셉션 서버가 2.에서 보낸 메시지를 받아 처리한 후 회신한 메시지를 수신
                            # 메시지의 테이블 아이디를 확인해서 현재 테이블 번호와 맞는 메시지를 찾을 때까지 대기
                            while table_info["table_id"] not in self.consumer.agent_nick_stk_inbox:
                                await asyncio.sleep(0.5)
                            agent_nick_stk_dict = self.consumer.agent_nick_stk_inbox.pop(table_info["table_id"])
                            table_info["new_players"] = agent_nick_stk_dict
                        
                        # 5. table_info를 메시지 브로커의 "table_ready_queue" 큐로 딜러 서버에 보내는 함수
                        await self.producer.table_ready(table_info)
 
                        # 문제 없이 테이블이 준비되면 테이블 상태를 "playing"으로 업데이트
                        log.status = "playing"
                        await log.save()
                await asyncio.sleep(1)  # 주기 조정

            except Exception as e:
                print(f"Unexpected error in broadcast_table_ready: {e}")
                await asyncio.sleep(1)


async def broadcast_chat():
    while True:
        try:
            # 최신 8개의 채팅 로그를 timestamp 기준으로 가져오기
            chat_logs = await ChatLog.find({}, sort=[("timestamp", -1)], limit=8).to_list()

            # 필요한 필드만 추출하여 리스트 생성
            chat_messages = [{"user_nick": log.user_nick, "content": log.content} for log in chat_logs]

            # JSON 데이터 압축
            compressed_data = zlib.compress(json.dumps({"Chat logs": chat_messages}).encode('utf-8'))

            # 모든 연결된 클라이언트에게 메시지 전송
            disconnected_clients = []
            for user_nick, websocket in robby_router.connected_clients.items():
                if isinstance(websocket, WebSocket):
                    try:
                        await websocket.send_bytes(compressed_data)
                    except WebSocketDisconnect:
                        disconnected_clients.append(user_nick)
                    except Exception as e:
                        disconnected_clients.append(user_nick)
                        print(f"Error sending message to {user_nick}: {e}")

            # 연결이 끊어진 클라이언트 처리
            for user_nick in disconnected_clients:
                await robby_service.handle_user_disconnection(user_nick)

            await asyncio.sleep(1)  # 주기 조정

        except Exception as e:
            print(f"Unexpected error in broadcast_chat: {e}")
            await asyncio.sleep(1)

