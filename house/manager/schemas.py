from pydantic import BaseModel

class UserBase(BaseModel):
    email: str
    nickname: str

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class User(UserBase):
    id: int
    stack_size: int

    class Config:
        orm_mode = True
