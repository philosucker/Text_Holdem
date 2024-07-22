from fastapi import Depends, HTTPException, status
from database import connection, manipulation
from schemas import floor

async def update_stack_size(data : floor.UpdateStackSize, 
                            db: manipulation.Database = Depends(connection.get_db)) -> list:
    
    users : list = await db.update_users_stack_size(data)
    if not users:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail="All users do not exist.")
    elif len(users) != len(data):
        raise HTTPException(status_code=status.HTTP_207_MULTI_STATUS, detail="Some users do not exist.")
    return users

