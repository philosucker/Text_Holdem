import pytest
import httpx
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from database.connection import settings
from main import app
from models.users import User
from models.events import Event

@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="module")
async def initialize_test_db():
    settings.DATABASE_URL = "mongodb://localhost:27017/testdb"
    await settings.initialize_database()
    yield
    await settings.close_database()

@pytest.fixture(scope="module")
async def async_client(initialize_test_db):
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client

async def create_users_and_login(client):
    user_emails = [f"user{i}@test.com" for i in range(1, 10)]
    tokens = []
    for email in user_emails:
        user_data = {"email": email, "password": "testpassword"}
        await client.post("/user/signup", json=user_data)
        response = await client.post("/user/signin", data={"username": email, "password": "testpassword"})
        tokens.append(response.json()["access_token"])
    return tokens

async def create_event(client, token, action, betting_size=None):
    event_data = {
        "action": action,
        "hands": ["4C", "KS"],
        "betting_size": betting_size,
        "stack": 10000
    }
    headers = {"Authorization": f"Bearer {token}"}
    await client.post("/event/new_event", json=event_data, headers=headers)

async def update_event(client, token, event_id, update_data):
    headers = {"Authorization": f"Bearer {token}"}
    await client.put(f"/event/edit_event/{event_id}", json=update_data, headers=headers)

async def get_events(client, token):
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/event/get_all_events", headers=headers)
    return response.json()

@pytest.mark.anyio
async def test_user_registration_and_events(async_client):
    tokens = await create_users_and_login(async_client)
    
    # Create initial events
    actions = ["bet", "raise", "all-in", "check", "fold", "call", "re-raise"]
    for i, token in enumerate(tokens):
        action = actions[i % len(actions)]
        betting_size = None
        if action in ["bet", "raise", "re-raise"]:
            betting_size = (i % 10 + 1) * 100
        await create_event(async_client, token, action, betting_size)

    # Retrieve all events
    initial_events = await get_events(async_client, tokens[0])
    assert len(initial_events) == 9

    # Update events
    for i, token in enumerate(tokens):
        event_id = initial_events[i]["id"]
        action = actions[(i + 1) % len(actions)]
        update_data = {"action": action}
        if action in ["bet", "raise", "re-raise"]:
            update_data["betting_size"] = (i % 10 + 1) * 100
        elif action == "all-in":
            update_data["betting_size"] = 10000
        await update_event(async_client, token, event_id, update_data)

    # Retrieve updated events
    updated_events = await get_events(async_client, tokens[0])
    assert len(updated_events) == 9

@pytest.mark.anyio
async def test_performance(async_client):
    import time
    start_time = time.time()
    await test_user_registration_and_events(async_client)
    end_time = time.time()
    print(f"Test completed in {end_time - start_time} seconds")
