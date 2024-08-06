from pydantic import BaseModel

# 클라이언트가 보내는 sign up 요청 바디에 대한 요청 스키마
class TableID(BaseModel):
    table_id : str
