from fastapi import Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordRequestForm
from database import manipulation, models
from authentication import password, jwt_handler
from schemas import user
from database import models

async def register(user: user.SignUpUser, db: manipulation.Database) -> str:
    db_user = await db.get_user_by_email(user.email)
    if db_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered.")
    
    existing_nick = await db.get_user_by_nick(user.nick_name)
    if existing_nick:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Nickname already taken.")

    hashed_password = password.hash_password(user.password)
    new_user = models.User(
        email=user.email,
        password=hashed_password,
        nickname=user.nick_name,
    )
    await db.create_user(new_user)

    return f'welcome {user.nick_name}'

# async def login(user: OAuth2PasswordRequestForm = Depends(), db: manipulation.Database = Depends(connection.get_db)):
async def login(user: user.SignInUser, db: manipulation.Database) -> dict:
    '''
    보완할 수 있는 부분
    유효성 검사 강화: 사용자 입력 값에 대한 추가적인 유효성 검사가 필요할 수 있습니다. 
    예를 들어, 비밀번호 복잡도 검사를 추가하여 더 강력한 비밀번호를 요구할 수 있습니다.
    로그인 시도 제한: 로그인 시도 횟수를 제한하여 무차별 대입 공격(Brute-force attack)을 방지할 수 있습니다.
    '''
    db_user = await db.get_user_by_email(user.email)
    if not db_user: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist.")
    
    if password.verify_password(user.password, db_user.password):
        access_token = jwt_handler.create_access_token(db_user.email, db_user.nick_name)
        await db.update_user_connection_status(db_user.id, True)  # connected 상태를 True로 업데이트

        return {"access_token": access_token, "token_type": "bearer"}
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password.")

async def update_nick(new_nick: user.UpdateNick, current_user : dict,  db: manipulation.Database) -> str:
    
    db_user = await db.get_user_by_email(current_user["user_email"])
    if not db_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication is required.")
    
    existing_nick = await db.get_user_by_nick(new_nick.nick_name)
    if existing_nick:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Nickname already taken.")

    db_user.nick_name = new_nick.nick_name
    await db.update_user(db_user)
    return "Nickname updated successfully."

async def update_pw(new_pw: user.UpdatePW, current_user: dict, db: manipulation.Database) -> str:
    
    db_user = await db.get_user_by_email(current_user["user_email"])
    if not db_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication is required.")
    
    if password.verify_password(new_pw.password, db_user.password):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="New password cannot be the same as the old password.")
    
    db_user.password = password.hash_password(new_pw.password)
    await db.update_user(db_user)
    return "Password updated successfully."

async def delete_user(user: user.DeleteUser, current_user: dict, db: manipulation.Database) -> str:
    if current_user["user_email"] != user.email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication is required.")

    db_user = await db.get_user_by_email(user.email)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist.")
    
    await db.delete_user(db_user)
    return "Account deleted"

async def get_connected_users(db: manipulation.Database) -> list[user.ConnectedUser]:
    connected_users = await db.get_connected_users()
    return [user.ConnectedUser.from_orm(user) for user in connected_users]
