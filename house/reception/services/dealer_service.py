from fastapi import Depends, HTTPException, status
from database import connection, manipulation
from schemas import dealer

async def request_stack_size(user_ids: dealer.RequestStackSize, 
                             db: manipulation.Database = Depends(connection.get_db)) -> dict:
    users_stk_size = await db.request_users_stack_size(user_ids)
    if not users_stk_size:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail="All users do not exist.")
    elif len(users_stk_size) != len(user_ids):
        raise HTTPException(status_code=status.HTTP_207_MULTI_STATUS, detail="Some users do not exist.")
    return users_stk_size

