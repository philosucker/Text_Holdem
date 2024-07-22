from pydantic import BaseModel, EmailStr, Field

# 클라이언트가 보내는 요청 바디에 대한 요청 스키마
class SignUpUser(BaseModel):
    email: EmailStr
    password: str
    nick_name: str
    stk_size: int = Field(default = 100) 

# 클라이언트가 보내는 요청 바디에 대한 요청 스키마
class SignInUser(BaseModel):
    email: EmailStr
    password: str

# 클라이언트 요청에 대한 응답 스키마        
class Account(BaseModel):
    nick_name: str
    stk_size: int

# 클라이언트 요청에 대한 응답 스키마        
class Token(BaseModel):
    access_token: str
    token_type: str