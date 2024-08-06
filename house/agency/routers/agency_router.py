# dealer/routers/dealer_router.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from reception.authentication import authenticate
from services import agency_service

router = APIRouter()

async def get_agent_manager() -> agency_service.AgentManager:
    from main import app  # 순환 참조 문제를 피하기 위해 함수 내에서 임포트
    return app.state.agent_manager

@router.websocket("/agency")
async def websocket_endpoint(websocket: WebSocket,
                             current_user: dict = Depends(authenticate.get_current_user),
                             agent_manager: agency_service.AgentManager = Depends(get_agent_manager)):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()

    except WebSocketDisconnect:
        pass
    except ValueError as e:
        print(f"ValueError: {str(e)}")
    except TypeError as e:
        print(f"TypeError: {str(e)}")
    except KeyError as e:
        print(f"KeyError: {str(e)}")
    except Exception as e:
        await websocket.close()
        print(f"Unexpected error: {str(e)}")





