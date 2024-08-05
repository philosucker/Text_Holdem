import os
import time
from datetime import datetime, timezone
from jose import JWTError, jwt
from fastapi import HTTPException, status
from cryptography.hazmat.primitives import serialization
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv(dotenv_path="./house/.env")

def _load_secret_key(algorithm: str):

    if algorithm == "HS256":
        secret_key = os.getenv("SECRET_KEY")
        if not secret_key:
            raise ValueError("SECRET_KEY is not set in the environment variables.")
        return secret_key
    
    elif algorithm == "ES256":
        pem_private_key = os.getenv("PRIVATE_KEY")
        if not pem_private_key:
            raise ValueError("PRIVATE_KEY is not set in the environment variables.")
        private_key = serialization.load_pem_private_key(
            pem_private_key.encode('utf-8'),
            password=None
        )
        return private_key

    raise ValueError("Unsupported algorithm. Please use 'HS256' or 'ES256'.")


def _load_public_key(algorithm):

    if algorithm == "HS256":
        return _load_secret_key(algorithm)  # HS256은 동일한 키를 사용

    elif algorithm == "ES256":
        try:
            with open("./house/public_key.pem", "rb") as key_file:
                public_key = serialization.load_pem_public_key(
                    key_file.read()
                )
            return public_key
        except FileNotFoundError:
            raise ValueError("Public key file not found.")

    raise ValueError("Unsupported algorithm. Please use 'HS256' or 'ES256'.")


def create_access_token(email: str, nick: str, algorithm = "HS256"):

    key = _load_secret_key(algorithm)

    payload = {
        "user_email": email,
        "user_nick" : nick,
        "expires": time.time() + 86400 # 86400 seconds == 24 hours
    }
    token = jwt.encode(payload, key, algorithm=algorithm)
    return token


def verify_access_token(token: str, algorithm = "HS256"):
    try:
        public_key = _load_public_key(algorithm)

        data = jwt.decode(token, public_key, algorithms=[algorithm])

        expire = data.get("expires")
        if expire is None: 
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token."
            )
        
        current_time = datetime.now(timezone.utc)
        expire_time = datetime.fromtimestamp(expire, timezone.utc)     

        if current_time > expire_time:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="For security reasons, your token has expired. Please take a moment to get some fresh air and then log in again."
            )
        return data
    
    except JWTError as e: 
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token"
        ) from e





