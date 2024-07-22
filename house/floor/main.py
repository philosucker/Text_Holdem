from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from aiokafka import AIOKafkaProducer
import json
import os
from pymongo import MongoClient
import uuid
import uvicorn

app = FastAPI()
producer = None

client = MongoClient('mongodb://localhost:27017/')
db = client.poker_db

@app.on_event("startup")
async def startup_event():
    global producer
    kafka_bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    producer = AIOKafkaProducer(
        bootstrap_servers=kafka_bootstrap_servers
    )
    await producer.start()

@app.on_event("shutdown")
async def shutdown_event():
    await producer.stop()

@app.post("/create_table")
async def create_table(request: dict):
    table_id = str(uuid.uuid4())
    table_data = {
        "table_id": table_id,
        "rings": request["rings"],
        "stakes": request["stakes"],
        "ai": request["ai"],
        "now": 0,
        "max": request["rings"],
        "private": request.get("private", "no"),
        "pw": request.get("pw", None),
        "status": "waiting",
        "players": []
    }
    db.tables.insert_one(table_data)
    await broadcast_table_update()
    return {"status": "table created", "table_id": table_id}

@app.post("/join_table")
async def join_table(table_id: str, user_id: str, nickname: str, pw: str = None):
    table = db.tables.find_one({"table_id": table_id})
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")
    if table["private"] == "yes" and table["pw"] != pw:
        raise HTTPException(status_code=403, detail="Invalid password")
    if any(player["user_id"] == user_id for player in table["players"]):
        raise HTTPException(status_code=400, detail="User already joined")
    if table["now"] >= table["max"]:
        raise HTTPException(status_code=403, detail="Table is full")

    table["players"].append({"user_id": user_id, "nickname": nickname})
    table["now"] += 1
    db.tables.update_one({"table_id": table_id}, {"$set": {"players": table["players"], "now": table["now"]}})
    await broadcast_table_update()

    if table["now"] == table["max"]:
        await notify_dealer(table)
    return {"status": "joined"}

@app.post("/notify_dealer")
async def notify_dealer(table: dict):
    if not producer:
        return {"status": "producer not initialized"}
    message = json.dumps(table).encode('utf-8')
    await producer.send_and_wait("dealer_topic", message)
    return {"status": "message sent"}

async def broadcast_table_update():
    tables = list(db.tables.find({}, {"_id": 0}))
    for table in tables:
        await notify_all_clients(table)

async def notify_all_clients(table):
    # 클라이언트 업데이트 로직 (예: WebSocket을 통해 클라이언트들에게 테이블 정보 전송)
    pass

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # 메시지 처리 로직
    except WebSocketDisconnect:
        await handle_disconnect(user_id)

async def handle_disconnect(user_id):
    # 클라이언트 연결 끊김 처리 로직
    pass

@app.post("/game_ended")
async def game_ended(table_id: str, keep_playing: bool):
    table = db.tables.find_one({"table_id": table_id})
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")

    if keep_playing:
        db.tables.update_one({"table_id": table_id}, {"$set": {"status": "waiting"}})
        await broadcast_table_update()
    else:
        await send_logs_to_manager(table_id)
        db.tables.delete_one({"table_id": table_id})
        await broadcast_table_update()

async def send_logs_to_manager(table_id: str):
    logs = list(db.logs.find({"table_id": table_id}, {"_id": 0}))
    # manager 서버로 로그 전송 로직
    pass

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)