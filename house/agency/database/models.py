from sqlalchemy import Column, Integer, String
from connection import Base

class Agent(Base):
    __tablename__ = "agents"
    id = Column(Integer, primary_key=True, index=True)
    nick_name = Column(String, unique=True, index=True)
    stack_size = Column(Integer)
    difficulty = Column(String)
    available = Column(String)