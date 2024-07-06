import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager 
from database.connection import settings 
from routes.events import event_router
from routes.users import user_router

from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    await settings.initialize_database()
    print("Connected to MongoDB")  
    try:
        yield 
    finally:
        print("Closing database connection...")  
        await settings.close_database()  

app = FastAPI(lifespan=lifespan)

app.include_router(user_router, prefix="/user")
app.include_router(event_router, prefix="/event")

@app.get("/")
async def welcome() -> dict:
    return {
        "message": "Hello World"
    }

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    )

if __name__ == '__main__':
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)