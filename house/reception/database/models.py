from sqlalchemy import Column, Integer, String, Boolean
from connection import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False) 
    password = Column(String, nullable=False)  
    nick_name = Column(String, unique=True, index=True)
    stk_size = Column(Integer, default=100)  
    connected = Column(Boolean, default=False)


