# models.py
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

class GameRoom(Base):
    __tablename__ = 'gamerooms'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    is_active = Column(Boolean, default=True)
    max_players = Column(Integer, default=9)
    current_players = Column(Integer, default=0)

class Player(Base):
    __tablename__ = 'players'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    gameroom_id = Column(Integer, ForeignKey('gamerooms.id'))
    chips = Column(Float, default=1000.0)
    is_ai = Column(Boolean, default=False)
    user = relationship("User")
    gameroom = relationship("GameRoom")
