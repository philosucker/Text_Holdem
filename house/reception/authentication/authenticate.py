from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from reception.authentication import jwt_handler

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="reception/sign_in")

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        return jwt_handler.verify_access_token(token)

    except HTTPException:
        raise credentials_exception
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate token"
        ) from e
        

