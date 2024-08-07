from fastapi import Depends, HTTPException, status, Request
# from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timezone
import time
import re
from ..database import manipulation, models
from ..authentication import password, jwt_handler
from ..schemas import user


async def register(user: user.SignUpUser, db: manipulation.Database) -> str:
    db_user = await db.get_user_by_email(user.email)
    if db_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered.")

# 닉네임 특수문자 검사
    if re.search(r'[!@#$%^&*]+', user.nick_name):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nickname cannot contain special characters: !@#$%^&*")

    existing_nick = await db.get_user_by_nick(user.nick_name)
    if existing_nick:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Nickname already taken.")

    hashed_password = password.hash_password(user.password)
    new_user = models.User(
        email=user.email,
        password=hashed_password,
        nick_name=user.nick_name,
    )
    await db.create_user(new_user)

    return f'welcome {user.nick_name}'

async def _notify_user_new_ip(email: str, ip_address: str):
    pass
    """
    새로운 IP 주소에서 로그인 시도가 발생했음을 사용자에게 알림.
    이메일이나 다른 알림 시스템을 통해 알림을 보낼 수 있습니다.
    """
    # 이메일 전송 또는 다른 알림 방법 구현
    print(f"Notification: New IP address {ip_address} detected for user {email}")

# async def login(user: OAuth2PasswordRequestForm = Depends(), db: manipulation.Database = Depends(connection.get_db)):
async def login(user: user.SignInUser, db: manipulation.Database, request: Request) -> dict:
    db_user = await db.get_user_by_email(user.email)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist.")

    # 계정 잠금 확인
    current_time = datetime.now(timezone.utc)
    if db_user.unlock_time and db_user.unlock_time > current_time:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is locked due to too many failed login attempts. Please try again in 15 minutes."
        )

    # 비밀번호 검증
    if password.verify_password(user.password, db_user.password):
        # 로그인 성공 시 실패 횟수 초기화
        db_user.failed_login_attempts = 0
        db_user.unlock_time = None
        
        # IP 주소 업데이트 및 알림 처리
        ip_address = request.client.host
        message = None
        if db_user.last_login_ip != ip_address:
            db_user.last_login_ip = ip_address
            await db.update_user(db_user)
            message = "The last connected IP address and the current connected IP address are different. If your connection environment has not changed, change your password."

        # JWT 토큰 생성
        access_token = jwt_handler.create_access_token(db_user.email, db_user.nick_name)
        await db.update_user_connection_status(db_user.id, True)
        
        return {"access_token": access_token, "token_type": "bearer", "message" : message}

    # 비밀번호가 틀린 경우
    db_user.failed_login_attempts += 1
    if db_user.failed_login_attempts > 5:
        expire = time.time() + 900
        expire_time = datetime.fromtimestamp(expire, timezone.utc)     
        db_user.unlock_time = expire_time
        await db.update_user(db_user)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Your account is temporarily locked."
        )
    
    # 실패 횟수 업데이트
    await db.update_user(db_user)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password.")

async def update_nick(new_nick: user.UpdateNick, current_user : dict,  db: manipulation.Database) -> str:
    
    db_user = await db.get_user_by_email(current_user["user_email"])
    if not db_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication is required.")
    
    existing_nick = await db.get_user_by_nick(new_nick.nick_name)
    if existing_nick:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Nickname already taken.")

    db_user.nick_name = new_nick.nick_name
    await db.update_user(db_user)
    return "Nickname updated successfully."

async def update_pw(new_pw: user.UpdatePW, current_user: dict, db: manipulation.Database) -> str:
    
    db_user = await db.get_user_by_email(current_user["user_email"])
    if not db_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication is required.")
    
    if password.verify_password(new_pw.password, db_user.password):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="New password cannot be the same as the old password.")
    
    db_user.password = password.hash_password(new_pw.password)
    await db.update_user(db_user)
    return "Password updated successfully."

async def delete_user(user: user.DeleteUser, current_user: dict, db: manipulation.Database) -> str:
    if current_user["user_email"] != user.email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication is required.")

    db_user = await db.get_user_by_email(user.email)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist.")
    
    await db.delete_user(db_user)
    return "Account deleted"

async def get_connected_users(db: manipulation.Database) -> list[user.ConnectedUser]:
    '''
    connected_users : User.connected == True인 User 모델 객체들의 리스트
    user.ConnectedUser.from_orm(user): 각 user 객체를 Pydantic 모델인 ConnectedUser로 변환
        from_orm 메서드 : 주어진 ORM 객체에서 Pydantic 모델로 데이터를 변환하는 메서드
    '''
    try:
        connected_users : list[models.User] = await db.get_connected_users()
        # return [user.ConnectedUser.from_orm(user) for user in connected_users]
        '''
        The from_orm method is deprecated; set model_config['from_attributes']=True and use model_validate instead.
        '''
        return [user.ConnectedUser.model_validate(user_instance) for user_instance in connected_users]
    except Exception as e:
        # 일반 예외 처리
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"An unexpected error occurred: {str(e)}")