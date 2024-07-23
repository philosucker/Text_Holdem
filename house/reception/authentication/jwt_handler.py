import os
import time
from datetime import datetime, timezone
from jose import JWTError, jwt
from fastapi import HTTPException, status
from dotenv import load_dotenv

load_dotenv(dotenv_path="./house/.env")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256" # algorithms=["HS256"] 충분히 안전한지 확인 필요

# 로그인시 클라이언트에게 반환되는 토큰에는 유저의 이메일과 만료기한이 담긴 딕셔너리가 인코딩되어 있다.
def create_access_token(email: str):
    payload = {
        "user_email": email,
        "expires": time.time() + 86400 # 86400 seconds == 24 hours
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

# 로그인 후 유저 인증이 필요할 때 사용하는 함수
# 
def verify_access_token(token: str):
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        expire = data.get("expires")
        if expire is None: 
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token."
            )
        
        current_time = datetime.now(timezone.utc)
        expire_time = datetime.fromtimestamp(expire, timezone.utc)     

        if current_time > expire_time:
            # 만료기한 초과시 토큰 만료 처리 
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token expired!"
            )
        return data    
    # jwt.decode 함수는 토큰의 구조와 서명을 검증합니다. 
    # 이 과정에서 발생할 수 있는 에러를 JWTError로 처리합니다.
    # JWTError는 잘못된 서명, 페이로드가 변조된 토큰, 잘못된 알고리즘 등의 문제를 나타냅니다.
    except JWTError as e: 
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token"
        ) from e

