from sqlalchemy import Column, Integer, String, Boolean, DateTime
from database.connection import Base

'''
SQLAlchemy에서 String 타입을 사용할 때 MySQL에서는 이를 VARCHAR로 매핑하고, 길이를 지정해야 합니다.
따라서 모든 String 타입 열에 대해 길이를 지정해야 합니다.
'''

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    nick_name = Column(String(255), unique=True, index=True)
    stk_size = Column(Integer, default=100)
    connected = Column(Boolean, default=False)
    last_login_ip = Column(String(45), default=None)  # IP 주소는 최대 45자로 제한
    failed_login_attempts = Column(Integer, default=0)  
    unlock_time = Column(DateTime, nullable=True)  # 계정 잠금 해제 시간


