import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from aiokafka import AIOKafkaConsumer
import asyncio
import json
import hashlib

from core.dealer import Dealer

app = FastAPI()
consumer = None

@app.on_event("startup")
async def startup_event():
    global consumer
    consumer = AIOKafkaConsumer(
        'dealer_topic',
        bootstrap_servers='localhost:9092',
        group_id="dealer_group"
    )
    await consumer.start()
    asyncio.create_task(consume_messages())

@app.on_event("shutdown")
async def shutdown_event():
    await consumer.stop()

async def consume_messages():
    async for msg in consumer:
        data = json.loads(msg.value.decode('utf-8'))
        table_id = data["table_id"]
        user_ids = data["user_ids"]
        stakes = data["stakes"]
        rings = data["rings"]
        agent = data["agent"]
        game_id = generate_unique_game_id()
        game_instance_url = f"ws://dealer-server.com/ws/{game_id}"

        # 웹소켓 URL과 함께 각 클라이언트에게 연결 정보를 전달
        for user_id in user_ids:
            notify_client(user_id, game_instance_url)

        # 새로운 게임 인스턴스 생성
        dealer_instance = Dealer(table_id = table_id, user_id_list=user_ids, rings=rings, stakes=stakes, ws_url=game_instance_url)
        await dealer_instance.async_init()
        asyncio.create_task(dealer_instance.go_street())

def generate_unique_game_id(table_id, user_ids):
    """
    Generate a unique game ID based on the table_id and user_ids.
    """
    # Convert user_ids to a sorted string
    sorted_user_ids = sorted(user_ids)
    user_ids_str = ",".join(sorted_user_ids)
    
    # Combine table_id and user_ids_str
    combined_str = f"{table_id}-{user_ids_str}"
    
    # Generate a SHA-256 hash of the combined string
    game_id_hash = hashlib.sha256(combined_str.encode()).hexdigest()
    
    return game_id_hash

def notify_client(user_id, game_instance_url):
    # 클라이언트에게 웹소켓 URL을 전달하는 로직
    print(f"Notifying user {user_id} to connect to {game_instance_url}")

async def websocket_endpoint(websocket: WebSocket, dealer_instance: Dealer):
    await websocket.accept()
    user_id = websocket.query_params['user_id']
    dealer_instance.websocket_clients[user_id] = websocket

    try:
        while True:
            data = await websocket.receive_text()
            # 받은 메시지를 처리하는 로직
    except WebSocketDisconnect:
        del dealer_instance.websocket_clients[user_id]

async def reconnect_websocket(dealer_instance: Dealer, user_id: str):
    for _ in range(2):  # 두 번 재시도
        try:
            await asyncio.sleep(2)  # 2초 대기
            uri = f"{dealer_instance.ws_url}/{user_id}"
            websocket = await websocket.connect(uri)
            dealer_instance.websocket_clients[user_id] = websocket
            return
        except Exception as e:
            print(f"Reconnect attempt failed: {e}")
    print(f"Failed to reconnect user {user_id} after 2 attempts.")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)