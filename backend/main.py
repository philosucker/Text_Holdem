# main.py
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import User, GameRoom, Player
from pydantic import BaseModel
from auth import verify_password, get_password_hash, create_access_token, oauth2_scheme # 추가1
from fastapi.security import OAuth2PasswordRequestForm # 추가1
from jose import JWTError, jwt # 추가2
from datetime import datetime, timedelta # 추가2
from typing import Optional # 추가2

app = FastAPI()

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

# 의존성 주입을 위한 데이터베이스 세션 생성 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic 모델 정의 (요청 및 응답 검증을 위해 사용)
class UserCreate(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel): # 추가4
    username: str

class GameRoomCreate(BaseModel):
    name: str
    max_players: int = 9

class Token(BaseModel): # 추가1
    access_token: str
    token_type: str

class TokenData(BaseModel): # 추가1
    # username: str | None = None
    username: Optional[str] = None # 추가2

SECRET_KEY = "your_secret_key" # 추가2
ALGORITHM = "HS256" # 추가2
ACCESS_TOKEN_EXPIRE_MINUTES = 30 # 추가2

#추가 2
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user

# 루트 엔드포인트 추가
@app.get("/")
def read_root():
    return {"message": "Welcome to the Holdem Game API"}

# 엔드포인트 정의
# 사용자 생성 엔드포인트
# @app.post("/users/", response_model=UserCreate) 
@app.post("/users/", response_model=UserResponse) # 추가4
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first() #추가3
    if db_user: # 추가3
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    # 사용자 생성 로직
    # hashed_password = user.password  # 실제로는 비밀번호를 해시해야 합니다.
    hashed_password = get_password_hash(user.password) # 추가
    db_user = User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# 사용자 로그인 엔드포인트 추가1
@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# 게임 방 생성 엔드포인트
@app.post("/gamerooms/", response_model=GameRoomCreate)
def create_gameroom(gameroom: GameRoomCreate, db: Session = Depends(get_db)):
    # 게임 방 생성 로직
    db_gameroom = GameRoom(name=gameroom.name, max_players=gameroom.max_players)
    db.add(db_gameroom)
    db.commit()
    db.refresh(db_gameroom)
    return db_gameroom

# 게임 방 참여 엔드포인트
@app.post("/gamerooms/{gameroom_id}/join")
def join_gameroom(gameroom_id: int, user_id: int, db: Session = Depends(get_db)):
    # 게임 방 참여 로직
    db_gameroom = db.query(GameRoom).filter(GameRoom.id == gameroom_id).first()
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_gameroom or not db_user:
        raise HTTPException(status_code=404, detail="Game room or user not found")
    if db_gameroom.current_players >= db_gameroom.max_players:
        raise HTTPException(status_code=400, detail="Game room is full")
    db_player = Player(user_id=user_id, gameroom_id=gameroom_id)
    db.add(db_player)
    db_gameroom.current_players += 1
    db.commit()
    return {"message": "User joined the game room"}

# 사용자 정보 확인 엔드포인트 추가2
# @app.get("/users/me/", response_model=UserCreate)
@app.get("/users/me/", response_model=UserResponse) # 추가4
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user