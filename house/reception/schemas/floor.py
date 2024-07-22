from pydantic import BaseModel, Field

# floor에서 보내는 요청 스키마
class UpdateStackSize(BaseModel):
    data: dict[str, int] = Field(None, json_schema_extra={"user_id" : 1000})  
