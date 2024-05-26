import pytest
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from database.connection import settings
from main import app
from httpx import AsyncClient, ASGITransport
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 사용자 및 토큰 저장용 전역 변수
user_emails = [f"user{i}@test.com" for i in range(1, 10)]
user_tokens = []
initial_events = []

# 커스텀 이벤트 루프 정의
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# 테스트 DB를 초기화하고 정리하는 fixture
@pytest.fixture(scope="session")
async def initialize_test_db(event_loop):
    settings.DATABASE_URL = "mongodb://localhost:27017/testdb"
    client = AsyncIOMotorClient(settings.DATABASE_URL)
    await client.drop_database("testdb")  # 각 테스트 전 DB 초기화
    await settings.initialize_database()
    yield
    await client.drop_database("testdb")  # 각 테스트 후 DB 정리
    client.close()

# 비동기 클라이언트를 생성하는 fixture
@pytest.fixture(scope="session")
async def async_client(initialize_test_db, event_loop):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

@pytest.mark.order(1)
@pytest.mark.asyncio
async def test_user_registration(async_client):
    global user_tokens
    for email in user_emails:
        user_data = {"email": email, "password": "testpassword"}
        response = await async_client.post("/user/signup", json=user_data)
        assert response.status_code == 200  # 사용자 생성 확인

@pytest.mark.order(2)
@pytest.mark.asyncio
async def test_user_login(async_client):
    global user_tokens
    for email in user_emails:
        response = await async_client.post("/user/signin", data={"username": email, "password": "testpassword"})
        assert response.status_code == 200  # 로그인 성공 확인
        try:
            user_tokens.append(response.json()["access_token"])
        except KeyError:
            pytest.fail("access_token not found in the response")

@pytest.mark.order(3)
@pytest.mark.asyncio
async def test_create_events(async_client):
    global initial_events
    actions = ["bet", "raise", "all-in", "check", "fold", "call", "re-raise"]
    for i, token in enumerate(user_tokens):
        action = actions[i % len(actions)]
        betting_size = None
        if action in ["bet", "raise", "re-raise"]:
            betting_size = (i % 10 + 1) * 100
        event_data = {
            "action": action,
            "hands": ["4C", "KS"],
            "betting_size": betting_size,
            "stack": 10000
        }
        headers = {"Authorization": f"Bearer {token}"}
        response = await async_client.post("/event/new_event", json=event_data, headers=headers)
        assert response.status_code == 200  # 이벤트 생성 확인

@pytest.mark.order(4)
@pytest.mark.asyncio
async def test_get_initial_events(async_client):
    global initial_events
    headers = {"Authorization": f"Bearer {user_tokens[0]}"}
    response = await async_client.get("/event/get_all_events", headers=headers)
    assert response.status_code == 200  # 이벤트 조회 성공 확인
    initial_events = response.json()
    assert len(initial_events) == len(user_tokens), f"Not all events were created. Expected: {len(user_tokens)}, Got: {len(initial_events)}"

@pytest.mark.order(5)
@pytest.mark.asyncio
async def test_update_events(async_client):
    actions = ["bet", "raise", "all-in", "check", "fold", "call", "re-raise"]
    for i, token in enumerate(user_tokens):
        event_id = initial_events[i]["_id"]
        action = actions[(i + 1) % len(actions)]
        update_data = {"action": action}
        if action in ["bet", "raise", "re-raise"]:
            update_data["betting_size"] = (i % 10 + 1) * 100
        elif action == "all-in":
            update_data["betting_size"] = 10000
        headers = {"Authorization": f"Bearer {token}"}
        response = await async_client.put(f"/event/edit_event/{event_id}", json=update_data, headers=headers)
        assert response.status_code == 200  # 이벤트 업데이트 성공 확인

@pytest.mark.order(6)
@pytest.mark.asyncio
async def test_get_updated_events(async_client):
    headers = {"Authorization": f"Bearer {user_tokens[0]}"}
    response = await async_client.get("/event/get_all_events", headers=headers)
    assert response.status_code == 200  # 이벤트 조회 성공 확인
    updated_events = response.json()
    assert len(updated_events) == len(user_tokens), f"Not all events were updated. Expected: {len(user_tokens)}, Got: {len(updated_events)}"
