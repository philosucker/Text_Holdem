from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, MetaData
from database import Database
import models, schemas, crud
from database import database, get_engine
import uvicorn

app = FastAPI()

DATABASE_URL = "mysql+aiomysql://username:password@localhost/dbname"
database = Database(DATABASE_URL)
metadata = MetaData()

models.metadata.create_all(bind=get_engine())

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.post("/signup/")
async def signup(user: schemas.UserCreate):
    db_user = await crud.get_user_by_email(user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    if not crud.validate_email(user.email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    if not crud.validate_password(user.password):
        raise HTTPException(status_code=400, detail="Invalid password format")
    if not crud.validate_nickname(user.nickname):
        raise HTTPException(status_code=400, detail="Invalid nickname format")
    return await crud.create_user(user)

@app.post("/login/")
async def login(user: schemas.UserLogin):
    db_user = await crud.authenticate_user(user.email, user.password)
    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    if db_user["stack_size"] < 100:
        return {"status": "low_stack_size", "message": "Stack size is below 100. Only singleplay is allowed."}
    return {"status": "success", "message": "Login successful", "stack_size": db_user["stack_size"]}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)