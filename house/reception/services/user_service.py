from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from database import connection, manipulation, models
from authentication import password, jwt_handler
from schemas import user

async def register(user: user.SignUpUser, 
                   db: manipulation.Database = Depends(connection.get_db)) -> dict:
    db_user = await db.get_user_by_email(user.email)
    if db_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
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
async def login(user: user.SignInUser, 
                db: manipulation.Database = Depends(connection.get_db)) -> dict:
    db_user = await db.get_user_by_email(user.email)
    if not db_user: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email does not exist.")
    
    if password.verify_password(user.password, db_user.password):
        access_token = jwt_handler.create_access_token(db_user.email)

        return {"access_token": access_token, "token_type": "bearer"}
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password.")