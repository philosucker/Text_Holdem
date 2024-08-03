from pydantic import BaseModel, Field

# floor에서 테이블의 모든 자리에 앉은 유저들의 스택사이즈 요청에 대한 요청 스키마
class UserNickList(BaseModel):
    table_id : str
    user_nick_list : list[str]


# floor에서 게임이 끝난 유저들의 스택사이즈 업데이트 요청에 대한 요청 스키마
class NickStkDict(BaseModel):
    nick_stk_dict: dict[str, int] = Field(None, json_schema_extra={"user_nick" : 1000})  

