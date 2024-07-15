import re
import models, schemas
from database import database

async def get_user_by_email(email: str):
    query = models.users.select().where(models.users.c.email == email)
    return await database.fetch_one(query)

async def create_user(user: schemas.UserCreate):
    query = models.users.insert().values(email=user.email, password=user.password, nickname=user.nickname, stack_size=100)
    await database.execute(query)
    return {"email": user.email, "nickname": user.nickname, "stack_size": 100}

async def authenticate_user(email: str, password: str):
    query = models.users.select().where(models.users.c.email == email).where(models.users.c.password == password)
    return await database.fetch_one(query)

def validate_email(email: str):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

def validate_password(password: str):
    return re.match(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$', password) is not None

def validate_nickname(nickname: str):
    return re.match(r'^[a-z0-9]+$', nickname) is not None
