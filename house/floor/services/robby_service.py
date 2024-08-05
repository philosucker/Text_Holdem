from fastapi import WebSocket, WebSocketDisconnect, HTTPException
from datetime import datetime, timezone
from database import models
from routers import robby_router

async def handle_user_connection(current_user: dict, websocket: WebSocket) -> str:
    '''
    기능: 현재 사용자가 연결될 때 사용자 정보를 확인하고, 
    사용자가 없으면 새 문서를 생성하고 저장하고
    사용자가 있으면 필요시 사용자 닉네임을 갱신 후
    연결로그를 업데이트 하고
    필요시 이미 연결된 동일 사용자를 처리한 다음
    새 연결을 등록합니다.
    '''
    user_nick = current_user.get("user_nick")
    user_email = current_user.get("user_email")

    if not user_nick or not user_email:
        raise HTTPException(status_code=400, detail="Invalid token")
    
    # MongoDB에서 이메일을 기반으로 사용자를 확인
    db_user = await models.UserLog.find_one({"user_email": user_email})
    # DB에 유저가 없으면 DB에 유저 문서 생성
    if not db_user:
        user_log = models.UserLog(
            user_email=user_email,
            user_nick=user_nick,
            connection_log=models.Connection(
                connected=True,
                entry_time=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
            )
        )
        await user_log.save()
    # 유저가 존재하면 
    else:
        # 필요시 닉네임을 업데이트
        if db_user.user_nick != user_nick:
            db_user.user_nick = user_nick
        # 연결 로그 업데이트
        db_user.connection_log.connected = True
        db_user.connection_log.entry_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        await db_user.save()
    
    # 중복 연결 방지: 동일 닉네임으로 다른 연결이 이미 존재하는 경우, 기존 연결 종료
    if user_nick in robby_router.connected_clients:
        old_websocket: WebSocket = robby_router.connected_clients[user_nick]
        try:
            await old_websocket.close()
            await handle_user_disconnection(user_nick)
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
            del robby_router.connected_clients[user_nick]

    # 새 웹소켓 연결을 등록
    robby_router.connected_clients[user_nick] = websocket

    return user_nick

async def handle_user_disconnection(user_nick: str) -> None:
    '''
    기능: 사용자가 연결을 끊었을 때 호출되며, 사용자 로그를 업데이트하고 연결 목록에서 제거합니다.
    '''
    db_user = await models.UserLog.find_one({"user_nick": user_nick})
    if db_user:
        db_user.connection_log.connected = False
        db_user.connection_log.exit_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        await db_user.save()
        del robby_router.connected_clients[user_nick]
    else:
        print(f"User with user_nick '{user_nick}' not found in the database.")


async def create_table(data: dict, user_nick: str, websocket: WebSocket):
    '''
    기능: 새로운 테이블을 생성하고, 생성된 테이블 ID를 클라이언트에게 반환합니다.
    '''
    # data = {"action" : "create_table", "details" = {"rings" : int, "stakes" : str, "agent" = {"hard" : 2, "easy" :1}}
    table_log = models.TableLog(
        creation_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        rings = data.get("details").get("rings"),
        stakes = data.get("details").get("stakes"),
        agent = data.get("details").get("agent"),
        now = 1,
        max = data.get("details").get("rings"),
        status = "waiting",
        new_players = {user_nick: 0}
    )
    
    # MongoDB에 테이블 삽입
    await table_log.insert()
    table_log.table_id = str(table_log.id)
    await table_log.save()

    # 클라이언트에게 생성된 테이블 ID 반환
    await websocket.send_json({"Message": "Table created", "Table id": table_log.table_id})

async def join_table(data: dict, user_nick: str, websocket: WebSocket):
    '''
    기능: 사용자가 테이블에 참가하도록 처리합니다.
    '''
    # data = {"action" : "join_table", "table_id" : int}
    table_id = data.get("table_id")
    table_log = await models.TableLog.find_one({"table_id": table_id})
    if table_log and table_log.now < table_log.max:
        table_log.now += 1
        table_log.new_players[user_nick] = 0
        await table_log.save()
        await websocket.send_json({"Message": "Joined table"})
    else:
        await websocket.send_json({"Message": "The table is full"})

async def cancel_table(data: dict, user_nick: str, websocket: WebSocket):
    '''
    기능: 사용자가 테이블에서 나가는 것을 처리합니다.
    '''
    # data = {"action" : "cancel_table", "table_id" : int}
    table_id = data.get("table_id")
    table_log = await models.TableLog.find_one({"table_id": table_id})
    if table_log:
        table_log.now -= 1
        del table_log.new_players[user_nick]
        await table_log.save()
        await websocket.send_json({"Message": "Cancelled table"})

async def search_table(data: dict, websocket: WebSocket):
    # data = {"action" : "search_table", "details" = {"rings" : int, "stake" : str, "agent" = {"hard" : 2, "easy" :1}}
    rings = data.get('rings')
    stakes = data.get('stakes')
    agent = data.get('agent')
    
    # 필터 조건 생성
    filters = {"table_log.rings": rings, "table_log.stakes": stakes, "table_log.agent": agent}
    
    # 필터에 맞는 테이블 조회 및 정렬
    matching_tables = await models.TableLog.find(filters).to_list()
    
    sorted_tables = sorted(
        matching_tables, 
        # 남은 자리가 적은 테이블이 리스트의 앞에 오도록 오름차순 정렬
        key=lambda table_log : (table_log.max-table_log.now, table_log.creation_time)
    )

    # 테이블 리스트 형식으로 변환
    table_list = [
        {
            "table_id": table_log.table_id,
            "rings": table_log.rings,
            "stakes": table_log.stakes,
            "agent": table_log.agent,
            "now": table_log.now,
            "max": table_log.max,
            "status": table_log.status
        }
        # 참가할 수 있는 자리가 있는 테이블만 골라 클라이언트에게 전달할 필드만 추려서 리스트로 변환
        for table_log in sorted_tables if table_log.now < table_log.max
        ]
    if table_list:
        await websocket.send_json({"Message": "Searched table", "Table_list": table_list})
    else:
        await websocket.send_json({"Message": "No tables matching your search criteria"})

async def input_chat(data: dict, user_nick: str):
    # data = {"action" : "input_chat", "content" : str}
    chat_log = models.ChatLog(
        user_nick = user_nick,
        content = data.get("content"),
        time_stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
    )

    await chat_log.insert()
    chat_log.chat_id = str(chat_log.id)
    await chat_log.save()