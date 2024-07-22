from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from database import connection, manipulation
from schemas import user
from services import user_service

router = APIRouter()

@router.post("/from_user/sign_up", status_code=status.HTTP_201_CREATED, response_model=user.Account)
async def register(user: user.SignUpUser, 
                   db: manipulation.Database = Depends(connection.get_db)) -> str:
    return await user_service.register(user, db)

@router.post("/from_user/sign_in", status_code=status.HTTP_200_OK, response_model=user.Token)
# async def login(user: OAuth2PasswordRequestForm = Depends(), db: manipulation.Database = Depends(connection.get_db)):
async def login(user: user.SignInUser, 
                db: manipulation.Database = Depends(connection.get_db)) -> dict:
    return await user_service.login(user, db)