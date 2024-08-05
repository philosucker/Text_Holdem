from fastapi import HTTPException, status
from ..database import manipulation
from ..schemas import floor

async def stk_size_query(table_info: floor.UserNickList, db: manipulation.Database) -> dict:
    user_nick_list = table_info.user_nick_list
    nick_stk_dict = await db.match_nick_stk(user_nick_list)
    if not nick_stk_dict:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail="All users do not exist.")
    elif len(nick_stk_dict) != len(user_nick_list):
        raise HTTPException(status_code=status.HTTP_207_MULTI_STATUS, detail="Some users do not exist.")
    
    return nick_stk_dict


async def stk_size_update(data: floor.NickStkDict, db: manipulation.Database) -> None:
    users = await db.update_stk_size(data)
    if not users:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail="All users do not exist.")
    elif len(users) != len(data.nick_stk_dict):
        raise HTTPException(status_code=status.HTTP_207_MULTI_STATUS, detail="Some users do not exist.")

