from passlib.context import CryptContext
from fastapi import HTTPException, status

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(self, password: str) -> str:
    try:
        return self.pwd_context.hash(password)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to hash password"
        ) from e
    
def verify_password(self, plain_password: str, hashed_password: str) -> bool:
    try:
        return self.pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify password"
        ) from e
    

