import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from database.models import TableLog, ChatLog
from routers import robby_router
from services import robby_service
import json
import zlib

async def broadcast_table_list():
    while True:
        try:
            # 필터 조건 정의: now < max 이고, status가 "waiting"인 테이블만 선택
            filters = {"now": {"$lt": "max"}, "status": "waiting"}
            projection = {"table_id": 1, "creation_time": 1, "rings": 1, "stakes": 1, "agent": 1, "now": 1, "max": 1, "status": 1}

            # 필터 조건을 사용하여 테이블 로그 검색 (필드 선택 포함)
            table_logs = await TableLog.find(filters, projection=projection).to_list()
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


async def broadcast_table_ready():
    while True:
        try:
            # 필터 조건 정의: now == max 이고, status가 "waiting"인 테이블만 선택
            filters = {"now": {"$eq": "max"}, "status": "waiting"}
            projection = {"table_id": 1, "now": 1, "max": 1, "new_players": 1, "continuing_players": 1, "status": 1}

            # 필터 조건을 사용하여 테이블 로그 검색 (필드 선택 포함)
            ready_tables = await TableLog.find(filters, projection=projection).to_list()

            # 각 테이블에 대한 작업
            for log in ready_tables:
                # 테이블에 포함된 유저 목록
                players = list(log.new_players.keys()) + list(log.continuing_players.keys())
                message = {"Message": "Table Ready", "Table id": str(log.table_id)}
                compressed_data = zlib.compress(json.dumps(message).encode('utf-8'))
                count = 0
                # 일치하는 웹소켓 클라이언트를 찾아 메시지 전송
                for user_nick in players:
                    websocket: WebSocket = robby_router.connected_clients.get(user_nick)
                    if websocket:
                        try:
                            await websocket.send_bytes(compressed_data)
                            count += 1
                        except WebSocketDisconnect:
                            await robby_service.handle_user_disconnection(user_nick)
                        except Exception as e:
                            print(f"Error sending message to {user_nick}: {e}")

                # 테이블 상태를 "playing"으로 업데이트
                if count == len(players):
                    log.status = "playing"
                    await log.save()
                else:
                    log.now = count
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

