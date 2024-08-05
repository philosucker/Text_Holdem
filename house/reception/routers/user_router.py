from fastapi import APIRouter, Depends, status, Request
# from fastapi.security import OAuth2PasswordRequestForm
from ..database import connection, manipulation
from ..schemas import user
from ..services import user_service
from ..authentication import authenticate

router = APIRouter()

@router.post("/from_user/sign_up", status_code=status.HTTP_201_CREATED, response_model=user.NickStk)
async def register(user: user.SignUpUser, 
                   db: manipulation.Database = Depends(connection.get_db)) -> str:
    return await user_service.register(user, db)

@router.post("/from_user/sign_in", status_code=status.HTTP_200_OK, response_model=user.Token)
# async def login(user: OAuth2PasswordRequestForm = Depends(), db: manipulation.Database = Depends(connection.get_db)):
async def login(user: user.SignInUser, 
                db: manipulation.Database = Depends(connection.get_db),
                request: Request = Depends()) -> dict:
    return await user_service.login(user, db, request)

# 서비스와 라우터를 분리한 경우, 종속성은 라우터에만 주입해도 된다.
@router.patch("/from_user/update_nick", status_code=status.HTTP_200_OK)
async def update_nick(new_nick : user.UpdateNick, 
                      current_user : dict = Depends(authenticate.get_current_user),
                      db: manipulation.Database = Depends(connection.get_db)) -> str:
    return await user_service.update_nick(new_nick, current_user, db)

# current_user는 JWT 토큰을 디코딩한 결과로 인증된 사용자의 정보(여기서는 이메일, 닉네임, 토큰 만료기한)을 담고 있는 딕셔너리다.
@router.patch("/from_user/update_pw", status_code=status.HTTP_200_OK)
async def update_pw(new_pw : user.UpdatePW,
                    current_user : dict = Depends(authenticate.get_current_user),
                    db: manipulation.Database = Depends(connection.get_db)) -> str:
    return await user_service.update_pw(new_pw, current_user, db)

@router.delete("/from_user/delete_user", status_code=status.HTTP_200_OK)
async def delete_user(user : user.DeleteUser, 
                      current_user : dict = Depends(authenticate.get_current_user), 
                      db: manipulation.Database = Depends(connection.get_db)) -> str:
    return await user_service.delete_user(user, current_user, db)

# 비밀번호 재설정. 구현 필요
@router.delete("/from_user/reset_pw ", status_code=status.HTTP_200_OK)
async def reset_pw(user: user.SignUpUser,
                   db: manipulation.Database = Depends(connection.get_db)):
    pass

# 관리자용
@router.get("/from_user/connected_users", response_model=list[user.ConnectedUser])
async def get_connected_users(db: manipulation.Database = Depends(connection.get_db)):
    return await user_service.get_connected_users(db)

