from sqlalchemy import Column, Integer, String, Boolean
from connection import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False) 
    password = Column(String, nullable=False)  
    nick_name = Column(String, unique=True, index=True)
    stack_size = Column(Integer, default=100)  
    is_active = Column(Boolean, default=True)


