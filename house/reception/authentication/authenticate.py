from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt_handler import verify_access_token

class Authenticator:
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/from_user/sign_in")

    '''
    클라이언트는 로그인 시 JWT 토큰을 발급받습니다. 
    이 토큰은 추후 인증이 필요한 요청의 Authorization 헤더에 포함됩니다.
    OAuth2PasswordBearer는 클라이언트가 Authorization 헤더에 Bearer <token> 형식으로 보낸 JWT 토큰을 추출하는 역할을 합니다.
    '''
    def get_current_user(self, token: str = Depends(oauth2_scheme)):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            return verify_access_token(token, credentials_exception)
        except HTTPException:
            raise credentials_exception
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to validate token"
            ) from e

# Authenticator 인스턴스 생성
authenticator = Authenticator()
