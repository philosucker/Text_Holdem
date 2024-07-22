from pydantic import BaseModel, Field

# floor에서 보내는 요청 스키마
class UpdateStackSize(BaseModel):
    stk_size : dict[str, int] = Field(None, json_schema_extra={"agent_id" : 1000})  
