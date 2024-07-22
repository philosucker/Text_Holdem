from pydantic import BaseModel

# dealer에서 보내는 요청 스키마
class RequestStackSize(BaseModel):
    user_ids : list[str]
