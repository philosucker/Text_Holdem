import pytest
from motor.motor_asyncio import AsyncIOMotorClient
from database.connection import settings
from main import app
from httpx import AsyncClient, ASGITransport
import logging
import os

# 로깅 설정
log_file = os.path.abspath('test_log.log')  # 절대 경로로 수정
if os.path.exists(log_file):
    os.remove(log_file)

# 기본 로거 설정
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 파일 핸들러 설정
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# 스트림 핸들러 설정
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# 테스트 DB를 초기화하고 정리하는 fixture
@pytest.fixture(scope="function")
async def initialize_test_db():
    settings.DATABASE_URL = "mongodb://localhost:27017/testdb"
    client = AsyncIOMotorClient(settings.DATABASE_URL)
    await client.drop_database("testdb")  # 각 테스트 전 DB 초기화
    await settings.initialize_database()
    yield
    await client.drop_database("testdb")  # 각 테스트 후 DB 정리
    client.close()

# 비동기 클라이언트를 생성하는 fixture
@pytest.fixture(scope="function")
async def async_client(initialize_test_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

# 각 테스트 시작과 종료 시 로그를 초기화하는 fixture
@pytest.fixture(autouse=True)
def reset_logging(capsys):
    with capsys.disabled():
        logger.handlers = []
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.DEBUG)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
    yield
    with capsys.disabled():
        logger.handlers = []

# DB 상태를 조회하여 출력하는 함수
async def print_db_state():
    client = AsyncIOMotorClient(settings.DATABASE_URL)
    db = client.get_database("testdb")
    users = await db["users"].find().to_list(length=None)
    events = await db["events"].find().to_list(length=None)
    logger.debug("Current Users: %s", users)
    logger.debug("Current Events: %s", events)
    client.close()

# 사용자 생성 및 로그인 후 토큰 반환
async def create_users_and_login(client):
    user_emails = [f"user{i}@test.com" for i in range(1, 10)]
    tokens = []
    for email in user_emails:
        user_data = {"email": email, "password": "testpassword"}
        await client.post("/user/signup", json=user_data)
        response = await client.post("/user/signin", data={"username": email, "password": "testpassword"})
        tokens.append(response.json()["access_token"])
    return tokens

# 새로운 이벤트 생성
async def create_event(client, token, action, betting_size=None):
    event_data = {
        "action": action,
        "hands": ["4C", "KS"],
        "betting_size": betting_size,
        "stack": 10000
    }
    headers = {"Authorization": f"Bearer {token}"}
    await client.post("/event/new_event", json=event_data, headers=headers)

# 이벤트 업데이트
async def update_event(client, token, event_id, update_data):
    headers = {"Authorization": f"Bearer {token}"}
    await client.put(f"/event/edit_event/{event_id}", json=update_data, headers=headers)

# 모든 이벤트 조회
async def get_events(client, token):
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/event/get_all_events", headers=headers)
    return response.json()

# 테스트 함수
@pytest.mark.asyncio
async def test_user_registration_and_events(async_client: AsyncClient):
    # 사용자 생성 및 로그인
    tokens = await create_users_and_login(async_client)
    await print_db_state()  # 초기 DB 상태 출력
    
    # 초기 이벤트 생성
    actions = ["bet", "raise", "all-in", "check", "fold", "call", "re-raise"]
    for i, token in enumerate(tokens):
        action = actions[i % len(actions)]
        betting_size = None
        if action in ["bet", "raise", "re-raise"]:
            betting_size = (i % 10 + 1) * 100
        await create_event(async_client, token, action, betting_size)
    await print_db_state()  # 이벤트 생성 후 DB 상태 출력

    # 모든 이벤트 조회
    initial_events = await get_events(async_client, tokens[0])
    logger.debug("Initial events: %s", initial_events)

    # 이벤트가 모두 생성되었는지 확인
    assert len(initial_events) == len(tokens), f"Not all events were created. Expected: {len(tokens)}, Got: {len(initial_events)}"

    # 응답 구조 확인
    for event in initial_events:
        assert '_id' in event, "Event '_id' not found in the response"
    
    # 이벤트 업데이트
    for i, token in enumerate(tokens):
        event_id = initial_events[i]["_id"]
        action = actions[(i + 1) % len(actions)]
        update_data = {"action": action}
        if action in ["bet", "raise", "re-raise"]:
            update_data["betting_size"] = (i % 10 + 1) * 100
        elif action == "all-in":
            update_data["betting_size"] = 10000
        await update_event(async_client, token, event_id, update_data)


    # 업데이트된 이벤트 조회
    updated_events = await get_events(async_client, tokens[0])
    logger.debug("Updated events: %s", updated_events)

    # 이벤트가 모두 업데이트되었는지 확인
    assert len(updated_events) == len(tokens), f"Not all events were updated. Expected: {len(tokens)}, Got: {len(updated_events)}"

    await print_db_state()  # 최종 DB 상태 출력
