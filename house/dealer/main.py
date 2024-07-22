from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import Dict, List
from core import dealer
import asyncio
import websockets
from producer import KafkaProducerClient
from consumer import KafkaConsumerClient
import json
import requests

app = FastAPI()

class DealerManager:
    def __init__(self, agent_addition_enabled: bool = True):
        self.active_connections: Dict[str, WebSocket] = {}
        self.agent_connections: Dict[str, WebSocket] = {}
        self.user_stacks: Dict[str, int] = {}
        self.expected_players: List[str] = []
        self.agent_ids: List[str] = []
        # self.dealer = None
        self.producer = KafkaProducerClient(bootstrap_servers='localhost:9092')
        self.retry_interval = 5  # 초
        self.retry_attempts = 3
        self.user_endpoints: Dict[str, str] = {}  # 유저 엔드포인트 저장
        self.agent_addition_enabled = agent_addition_enabled

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        client_ip = websocket.client.host
        client_port = websocket.client.port
        self.active_connections[client_id] = websocket
        self.user_endpoints[client_id] = f"{client_ip}:{client_port}"  # 클라이언트 엔드포인트 저장
        # 모든 예상 플레이어와 에이전트가 연결되면 게임 시작
        if self.check_all_connected():
            await self.start_game()

    async def disconnect(self, websocket: WebSocket):
        client_id = next(key for key, value in self.active_connections.items() if value == websocket)
        del self.active_connections[client_id]
        del self.user_endpoints[client_id]  # 엔드포인트 삭제

    def check_all_connected(self):
        all_players_connected = all(player in self.active_connections for player in self.expected_players)
        all_agents_connected = all(agent in self.active_connections for agent in self.agent_ids)
        return all_players_connected and all_agents_connected

    async def start_game(self):
        self.dealer = dealer.Dealer(self.user_stacks, self.active_connections, self.agent_connections)
        await self.dealer.go_street()

    async def handle_message(self, message):
        data = json.loads(message)
        self.user_stacks = data['user_stacks']
        self.expected_players = list(self.user_stacks.keys())
        self.agent_ids = list(data.get('agents', {}).keys())
        self.user_endpoints = data.get('user_endpoints', {})

        # 에이전트 연결 요청
        if self.agent_addition_enabled:
            for agent_id, agent_info in data.get('agents', {}).items():
                response = requests.post(f"http://agent_manager_address/request_agent", json={"uri": "ws://dealer_manager_address/ws/agent", "agent_id": agent_id})
                if response.status_code != 200:
                    print(f"Failed to connect agent {agent_id}")

        # 유저 엔드포인트로 웹소켓 연결 시도
        await self.retry_user_connections()

        # 클라이언트 수가 부족한 경우 에이전트 추가 요청
        if self.agent_addition_enabled:
            await self.check_and_request_additional_agents()

    async def retry_user_connections(self):
        for attempt in range(self.retry_attempts):
            if self.check_all_connected():
                return
            for player, endpoint in self.user_endpoints.items():
                if player not in self.active_connections:
                    # 여기에 유저에게 웹소켓 연결을 시도하도록 요청하는 로직을 추가
                    print(f"Requesting player {player} to connect to {endpoint}")
                    response = requests.post(endpoint, json={"message": "Please connect your websocket"})
                    if response.status_code != 200:
                        print(f"Failed to request player {player} to connect")
            await asyncio.sleep(self.retry_interval)

    async def check_and_request_additional_agents(self):
        if not self.check_all_connected():
            additional_agents_needed = len(self.user_stacks) - (len(self.expected_players) + len(self.agent_ids))
            for _ in range(additional_agents_needed):
                response = requests.post(f"http://agent_manager_address/request_additional_agent", json={"uri": "ws://dealer_manager_address/ws/agent"})
                if response.status_code != 200:
                    print(f"Failed to request additional agent")

    def start_consumer(self):
        consumer = KafkaConsumerClient(
            bootstrap_servers='localhost:9092',
            topic='game-start-topic',
            group_id='dealer-manager-group'
        )
        consumer.consume_messages(self.handle_message)

manager = DealerManager(agent_addition_enabled=True)

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received message from {client_id}: {data}")
    except WebSocketDisconnect:
        await manager.disconnect(websocket)

@app.websocket("/ws/agent/{agent_id}")
async def websocket_endpoint_agent(websocket: WebSocket, agent_id: str):
    await manager.connect(websocket, agent_id)
    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received message from {agent_id}: {data}")
    except WebSocketDisconnect:
        await manager.disconnect(websocket)

@app.on_event("startup")
async def startup_event():
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, manager.start_consumer)
