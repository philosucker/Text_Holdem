# dealer/routers/dealer_router.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from reception.authentication import authenticate
from services import dealer_service
from schemas import user

router = APIRouter()

async def get_dealer_manager() -> dealer_service.DealerManager:
    from main import app  # 순환 참조 문제를 피하기 위해 함수 내에서 임포트
    return app.state.dealer_manager

@router.websocket("/dealer")
async def websocket_endpoint(websocket: WebSocket, message : user.TableID,
                             current_user: dict = Depends(authenticate.get_current_user),
                             dealer_manager: dealer_service.DealerManager = Depends(get_dealer_manager)):
    await websocket.accept()
    user_nick, table_id = await dealer_manager.handle_user_connection(current_user, message, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            print(f"Received message from {user_nick} at table {table_id}: {data}")

    except WebSocketDisconnect:
        if user_nick in dealer_manager.active_connections[table_id]:
            await dealer_manager.handle_user_disconnection(user_nick, table_id)
    except ValueError as e:
        print(f"ValueError: {str(e)}")
    except TypeError as e:
        print(f"TypeError: {str(e)}")
    except KeyError as e:
        print(f"KeyError: {str(e)}")
    except Exception as e:
        if user_nick in dealer_manager.active_connections[table_id]:
            await dealer_manager.handle_user_disconnection(user_nick, table_id)
            await websocket.close()
            print(f"Unexpected error: {str(e)}")





