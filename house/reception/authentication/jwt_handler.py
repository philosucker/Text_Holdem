import os
import time
from datetime import datetime, timezone
from jose import JWTError, jwt
from typing import Union
from fastapi import HTTPException, status
from dotenv import load_dotenv

load_dotenv(dotenv_path="./house/.env")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256" # algorithms=["HS256"] 충분히 안전한지 확인 필요

def create_access_token(user: str):
    payload = {
        "user": user,
        "expires": time.time() + 86400 # 86400 seconds == 24 hours
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

def verify_access_token(token: str):
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        expire = data.get("expires")
        if expire is None: 
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No access token supplied"
            )
        
        current_time = datetime.now(timezone.utc)
        expire_time = datetime.fromtimestamp(expire, timezone.utc)     

        if current_time > expire_time: 
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token expired!"
            )
        return data    
         
    except JWTError: 
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token"
        )    

class TokenData:
    username: Union[str, None] = None
