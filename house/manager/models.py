from sqlalchemy import Column, Integer, String, Table
from database import metadata

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("email", String(255), unique=True, index=True),
    Column("password", String(255)),
    Column("nickname", String(50), unique=True, index=True),
    Column("stack_size", Integer, default=100),
)
