from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt_handler import verify_access_token

class Authenticator:

    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/from_user/sign_in")

    def get_current_user(self, token: str = Depends(oauth2_scheme)):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            return verify_access_token(token)

        except HTTPException:
            raise credentials_exception
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to validate token"
            ) from e
        
authenticator = Authenticator()
