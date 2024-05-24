from typing import Optional, List
from beanie import Document
from pydantic import BaseModel
# PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. 
# Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.7/migration/warnings.warn(DEPRECATION_MESSAGE, DeprecationWarning)
# 확인 필요

class Event(Document): 
    creator: Optional[str] = None 
    action: str
    hands: List[str]
    betting_size: Optional[int] = None 
    stack: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "action": "raise",
                "hands": ["4C", "KS"],
                "betting_size": 500,
                "stack": 10000,
            }
        }

    class Settings:
        name = "events"


class EventUpdate(BaseModel):
    action: Optional[str] = None
    hands: Optional[List[str]] = None
    betting_size: Optional[int] = None 
    stack: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "action": "fold",
                "hands": ["4C", "KS", "AH"],
                "betting_size": 0,
                "stack": 0,
            }
        }
