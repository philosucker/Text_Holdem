from fastapi import Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordRequestForm
from database import manipulation, models
from authentication import password, jwt_handler
from schemas import user
from database import models

async def register(user: user.SignUpUser, db: manipulation.Database) -> dict:
    db_user = await db.get_user_by_email(user.email)
    if db_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered.")
    hashed_password = password.hash_password(user.password)
    new_user = models.User(
        email=user.email,
        password=hashed_password,
        nickname=user.nick_name,
        stack_size=user.stk_size
    )
    await db.create_user(new_user)

    return {"nick_name" : user.nick_name, "stk_size" : user.stk_size}

# async def login(user: OAuth2PasswordRequestForm = Depends(), db: manipulation.Database = Depends(connection.get_db)):
async def login(user: user.SignInUser, db: manipulation.Database) -> dict:
    db_user = await db.get_user_by_email(user.email)
    if not db_user: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist.")
    
    if password.verify_password(user.password, db_user.password):
        access_token = jwt_handler.create_access_token(db_user.email)

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

