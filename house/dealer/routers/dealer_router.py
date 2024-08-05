# dealer/routers/dealer_router.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from reception.authentication import authenticate
from services import dealer_service

router = APIRouter()

async def get_dealer_manager() -> dealer_service.DealerManager:
    from main import app  # 순환 참조 문제를 피하기 위해 함수 내에서 임포트
    return app.state.dealer_manager

@router.websocket("/dealer/{table_id}/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str, table_id: str,
                             current_user: dict = Depends(authenticate.get_current_user),
                             dealer_manager: dealer_service.DealerManager = Depends(get_dealer_manager)):
    try:
        if current_user['user_nick'] == client_id:
            await websocket.accept()
            await dealer_manager.add_connection(table_id, client_id, websocket)

            while True:
                data = await websocket.receive_json()
                print(f"Received message from {client_id} at table {table_id}: {data}")

    except WebSocketDisconnect:
        await websocket.close()
    except ValueError as e:
        print(f"ValueError: {str(e)}")
    except TypeError as e:
        print (f"TypeError: {str(e)}")
    except KeyError as e:
        print(f"KeyError: {str(e)}")
    except Exception as e:
        await websocket.close()
        print(f"Unexpected error: {str(e)}")





