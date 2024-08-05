from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
import json
from services import robby_service
from reception.authentication import authenticate


router = APIRouter()

connected_clients = {}

@router.websocket("/robby")
async def websocket_endpoint(websocket: WebSocket, 
                             current_user: dict = Depends(authenticate.get_current_user)):
    
    user_nick = await robby_service.handle_user_connection(current_user, websocket)
    await websocket.accept() 
    try:
        while True:
            '''
            await websocket.accept() 에서 웹소켓 연결이 되고 나면 
            아래 robby_service 함수들의 user_nick과 websocket 인자는 
            await websocket.accept() 호출전 설정된 user_nick과, 호출후 설정된 websocket 값을 넘겨 받게 된다.
            '''
            data : dict= await websocket.receive_json()
            action = data.get('action')
            '''
            data = {"action" : "create_table", "details" = {"rings" : int, "stake" : str, "agent" = {"hard" : 2, "easy" :1}}
            data = {"action" : "join_table", "table_id" : int}
            data = {"action" : "cancel_table", "table_id" : int}
            data = {"action" : "search_table", "details" = {"rings" : int, "stake" : str, "agent" = {"hard" : 2, "easy" :1}}
            data = {"action" : "input_chat", "content" : str}
            '''
            if not action:
                continue
            websocket = connected_clients.get(user_nick)
            if action == 'create_table':
                await robby_service.create_table(data, user_nick, websocket)
            elif action == 'join_table':
                await robby_service.join_table(data, user_nick, websocket)
            elif action == 'cancel_table':
                await robby_service.cancel_table(data, user_nick, websocket)
            elif action == 'search_table':
                await robby_service.search_table(data, websocket)
            elif action == 'input_chat':
                await robby_service.input_chat(data, user_nick)
            else:
                error_message = json.dumps({"Error": "Invalid action"})
                await websocket.send_json(error_message)
                await websocket.close(code=1003)  # 1003: Unsupported Data

    except WebSocketDisconnect:
        if user_nick in connected_clients:
            await robby_service.handle_user_disconnection(user_nick)
    except ValueError as e:
        print(f"ValueError: {str(e)}")
    except TypeError as e:
        print(f"TypeError: {str(e)}")
    except KeyError as e:
        print(f"KeyError: {str(e)}")
    except Exception as e:
        await robby_service.handle_user_disconnection(user_nick)
        await websocket.close()
        print(f"Unexpected error: {str(e)}")

