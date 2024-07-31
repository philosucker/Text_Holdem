from fastapi import HTTPException, status
from database import manipulation
from schemas import floor

async def update_stack_size(data: floor.UpdateStackSize, db: manipulation.Database) -> None:
    users = await db.update_users_stack_size(data)
    if not users:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail="All users do not exist.")
    elif len(users) != len(data.data):
        raise HTTPException(status_code=status.HTTP_207_MULTI_STATUS, detail="Some users do not exist.")
    print("All users' stack sizes updated successfully.")

async def request_stack_size(user_ids: floor.RequestStackSize, db: manipulation.Database) -> dict:
    users_stk_size = await db.request_users_stack_size(user_ids)
    if not users_stk_size:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail="All users do not exist.")
    elif len(users_stk_size) != len(user_ids.user_ids):
        raise HTTPException(status_code=status.HTTP_207_MULTI_STATUS, detail="Some users do not exist.")
    return users_stk_size
