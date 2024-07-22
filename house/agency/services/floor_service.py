from fastapi import Depends, HTTPException, status
from database import connection, manipulation
from schemas import floor

async def update_stack_size(data : floor.UpdateStackSize, 
                            db: manipulation.Database = Depends(connection.get_db)) -> dict:
    
    agents : list = await db.update_agents_stack_size(data)
    if not agents:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail="All agents do not exist.")
    elif len(agents) != len(data):
        raise HTTPException(status_code=status.HTTP_207_MULTI_STATUS, detail="Some agents do not exist.")
    return {"message": "Stack sizes updated", "updated agents": agents}

