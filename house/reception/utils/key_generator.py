import secrets
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from dotenv import load_dotenv, set_key
from pathlib import Path

def generate_secret_key(length: int = 64, algorithm: str = "HS256", env_file: str = './house/.env', public_key_file: str = './house/public_key.pem'):
    """
    비밀 키를 생성하고 .env 파일에 저장합니다.
    알고리즘에 따라 대칭 키(HS256) 또는 비대칭 키(ES256)를 생성합니다.
    - HS256: 암호화적으로 안전한 URL-safe 비밀 키를 생성하여 저장합니다.
    - ES256: 비밀 키와 공개 키 쌍을 생성하여 비밀 키는 환경 변수에, 공개 키는 파일에 저장합니다.
    """
    env_path = Path(env_file).resolve()
    public_key_path = Path(public_key_file).resolve()

    if not env_path.exists():
        env_path.parent.mkdir(parents=True, exist_ok=True)
        env_path.touch()
        print(f"Created .env file at {env_path}")

    load_dotenv(dotenv_path=env_path)
    
    if algorithm == "HS256":
        secret_key = secrets.token_urlsafe(length)
        set_key(env_path, "SECRET_KEY", secret_key)
        print(f"SECRET_KEY saved to environment variable in {env_path}")

    elif algorithm == "ES256":
        # 비밀 키 생성
        private_key = ec.generate_private_key(ec.SECP256R1())
        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # 공개 키 추출
        public_key = private_key.public_key()
        public_key_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        # 비밀 키를 환경 변수에 저장 (환경 변수 파일에 저장)
        set_key(env_path, "PRIVATE_KEY", private_key_pem.decode('utf-8'))
        print(f"PRIVATE_KEY saved to environment variable in {env_path}")
        
        # 공개 키를 별도의 파일에 저장
        public_key_path.parent.mkdir(parents=True, exist_ok=True)
        with open(public_key_path, 'wb') as f:
            f.write(public_key_pem)
        print(f"Public key saved to file: {public_key_path}")

    else:
        raise ValueError("Unsupported algorithm. Please use 'HS256' or 'ES256'.")

# 함수 호출
if __name__ == "__main__":
    generate_secret_key(algorithm="ES256")
