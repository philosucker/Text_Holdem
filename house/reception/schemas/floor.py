from pydantic import BaseModel, Field

# floor에서 게임이 끝난 유저들의 스택사이즈 업데이트 요청에 대한 요청 스키마
class UpdateStackSize(BaseModel):
    data: dict[str, int] = Field(None, json_schema_extra={"user_id" : 1000})  

# floor에서 테이블의 모든 자리에 앉은 유저들의 스택사이즈 요청에 대한 요청 스키마
class RequestStackSize(BaseModel):
    user_ids : list[str]