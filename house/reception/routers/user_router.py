from fastapi import APIRouter, Depends, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from database import connection, manipulation
from schemas import user
from services import user_service
from authentication import authenticate

router = APIRouter()

@router.post("/sign_up", status_code=status.HTTP_201_CREATED, response_model=user.NickStk)
async def register(user: user.SignUpUser, 
                   db: manipulation.Database = Depends(connection.get_db)) -> str:
    return await user_service.register(user, db)

'''
Swagger UI의 Authorize 버튼을 사용할 때 Unprocessable Entity 오류가 발생하는 이유는, 
OAuth2PasswordBearer가 폼 데이터 형식을 기대하기 때문입니다. 
이 경우, FastAPI에서 OAuth2PasswordRequestForm을 사용하여 폼 데이터를 처리해야 합니다.
'''

@router.post("/sign_in", status_code=status.HTTP_200_OK, response_model=user.Token)
async def login(request: Request,
                db: manipulation.Database = Depends(connection.get_db),
                form_data: OAuth2PasswordRequestForm = Depends()
                ):
    data = user.SignInUser(email=form_data.username, password=form_data.password)
    return await user_service.login(data, request, db)
'''
OAuth2PasswordRequestForm 대신 사용자가 정의한 구조의 데이터를 받게 하려면
직접 스키마를 정의해서 라우트 요청시 json 형태로 전달시키면 된다
'''
# async def login(user: user.SignInUser,
#                 request: Request,
#                 db: manipulation.Database = Depends(connection.get_db)
#                 ) -> dict:
    # return await user_service.login(user, request, db)

# 서비스와 라우터를 분리한 경우, 종속성은 라우터에만 주입해도 된다.
@router.patch("/update_nick", status_code=status.HTTP_200_OK)
async def update_nick(new_nick : user.UpdateNick, 
                      current_user : dict = Depends(authenticate.get_current_user),
                      db: manipulation.Database = Depends(connection.get_db)) -> str:
    return await user_service.update_nick(new_nick, current_user, db)

# current_user는 JWT 토큰을 디코딩한 결과로 인증된 사용자의 정보(여기서는 이메일, 닉네임, 토큰 만료기한)을 담고 있는 딕셔너리다.
@router.patch("/update_pw", status_code=status.HTTP_200_OK)
async def update_pw(new_pw : user.UpdatePW,
                    current_user : dict = Depends(authenticate.get_current_user),
                    db: manipulation.Database = Depends(connection.get_db)) -> str:
    return await user_service.update_pw(new_pw, current_user, db)

@router.delete("/delete_user", status_code=status.HTTP_200_OK)
async def delete_user(user : user.DeleteUser, 
                      current_user : dict = Depends(authenticate.get_current_user), 
                      db: manipulation.Database = Depends(connection.get_db)) -> str:
    return await user_service.delete_user(user, current_user, db)

# 비밀번호 재설정. 구현 필요
@router.patch("/reset_pw ", status_code=status.HTTP_200_OK)
async def reset_pw(user: user.SignUpUser,
                   db: manipulation.Database = Depends(connection.get_db)):
    pass

# 관리자용
@router.get("/get_all_users", response_model=list)
async def get_all_users(db: manipulation.Database = Depends(connection.get_db)):
    return await user_service.get_all_users(db)

