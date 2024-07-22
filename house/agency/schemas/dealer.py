from pydantic import BaseModel, Field

# dealer에서 보내는 요청 스키마
class SummonAgent(BaseModel):
    agents: dict[str, int] = Field(None, json_schema_extra={"hard": 3, "easy": 1})

# 응답 스키마
class Agents(BaseModel):
    agents : dict[str, int] = Field(None, json_schema_extra={"nick_name" : 1000})