import os
import time
from datetime import datetime, timezone
from jose import JWTError, jwt
from fastapi import HTTPException, status
from cryptography.hazmat.primitives import serialization
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv(dotenv_path="./house/.env")

def _load_secret_key(algorithm):
    '''
    환경 변수에서 비밀 키 가져오기
    HS256 대칭키 암호화 알고리즘. 서명과 검증에 동일한 비밀 키를 사용
    ES256 비대칭키 암호와 알고리즘. 비밀 키로 서명하고, 공개 키로 검증. 서명 생성은 비교적 빠르지만, 검증은 상대적으로 더 느림

    ES256과 같은 비대칭 키 암호화에서 공개 키가 노출되어도 안전한 이유 : 서명과 검증의 분리

        비대칭 키 암호화에서는 두 개의 키 쌍을 사용합니다: 
            비밀 키는 기밀이며, 오직 서명(Signing)에만 사용됩니다. 
            반면에 공개 키는 공개적으로 배포되어 누구나 접근할 수 있습니다. 
            공개 키는 서명된 데이터의 서명을 검증하는 데 사용됩니다.

        공개 키를 사용하여 다음과 같은 작업이 가능합니다:
            서명된 데이터(예: JWT 토큰)의 무결성을 검증합니다
            서명이 올바르게 이루어졌는지, 
            데이터가 변경되지 않았는지 확인하는 역할을 합니다.
            서명이 올바르지 않거나 데이터가 변조된 경우, 공개 키로 검증이 실패합니다
            토큰의 유효성을 확인할 수 있습니다.

        그러나 공개 키를 가지고 할 수 없는 작업은 다음과 같습니다:
            새로운 데이터를 서명할 수 없습니다. 
            즉, 공개 키로 서명된 새로운 유효한 JWT 토큰을 생성할 수 없습니다. 
            이 작업은 오직 비밀 키로만 가능합니다.
            따라서 해커가 공개 키를 가지고 있다 해도, 비밀 키를 얻지 못하는 한 
            새로운 서명을 생성하거나 기존 서명을 변조하는 것은 불가능합니다.
    '''
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
    '''
    공개 키를 가지는 주체
        서비스 간의 통신:
            서버: 
            주로 JWT 토큰을 발행한 서버가 토큰을 검증해야 하는 다른 서버나 서비스에 공개 키를 배포합니다. 
            예를 들어, 여러 마이크로서비스가 함께 작동하는 시스템에서 인증 서버는 
            공개 키를 다른 서비스에 배포하여 토큰 검증을 수행할 수 있게 합니다.

        클라이언트:
            웹 브라우저 또는 모바일 애플리케이션: 
            클라이언트가 서버에서 발급한 JWT 토큰의 유효성을 자체적으로 검증해야 할 경우,
            공개 키를 사용하여 서명을 확인할 수 있습니다. 
            일반적인 시나리오에서는 클라이언트가 토큰을 직접 검증하지 않지만, 
            클라이언트-서버 간의 안전한 통신이 필요할 때 유용할 수 있습니다.
            
        제3자 서비스:
            외부 서비스: 
            공개 API를 제공하는 경우, 외부 서비스가 API 호출자의 JWT를 검증할 수 있도록 공개 키를 제공할 수 있습니다. 
            이를 통해 제3자 서비스는 요청이 정당한지 확인할 수 있습니다.

    공개 키 배포 및 관리

        안전한 배포:
        HTTPS를 사용하여 안전하게 공개 키를 전송합니다. 
        공개 키가 민감한 정보는 아니지만, 배포 중에 무단으로 변경되지 않도록 하는 것이 중요합니다.
        공개 키는 시스템의 보안 설정이나 문서화 자료에 포함될 수 있으며, 
        필요에 따라 다운로드할 수 있도록 웹 페이지나 API 엔드포인트를 통해 제공될 수 있습니다.

        키 관리 정책:
        공개 키를 주기적으로 회전(갱신)하는 키 회전 정책을 수립합니다. 
        이 과정에서 새로운 키를 발행하고, 이전 키는 일정 기간 동안 지원하도록 설정할 수 있습니다.
        공개 키의 변경 사항은 키를 사용하는 모든 주체에게 알리고, 새로운 키로 전환할 수 있도록 안내해야 합니다.
    '''
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
        
        '''
        한국 표준시(KST, Korea Standard Time)는 UTC+9로 표현됩니다. 
        이는 한국의 시간대가 UTC 시간보다 9시간 빠름을 의미합니다.
        UTC가 00:00일 때, 한국에서는 같은 시점이 09:00가 됩니다. 
        이는 한국이 UTC 기준보다 9시간 앞서 있다는 것을 나타냅니다. 
        따라서, 한국 표준시를 UTC 시간과 변환할 때는 9시간을 더하면 됩니다
        '''
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





