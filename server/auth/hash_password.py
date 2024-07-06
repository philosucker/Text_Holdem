from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# DeprecationWarning: 'crypt' is deprecated and slated for removal in Python 3.13 변경 필요

class HashPassword:

    
    def create_hash(self, password: str):
        try:
            return pwd_context.hash(password)
        except UnknownHashError as e:
            # 예외 처리 로직 추가 필요
            raise ValueError("An error occurred during hashing..") from e

    def verify_hash(self, plain_password: str, hashed_password: str):
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except ValueError as e:
            raise ValueError("An error occurred during password verification.") from e