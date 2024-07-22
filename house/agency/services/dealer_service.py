from fastapi import Depends, HTTPException, status
from database import connection, manipulation
from schemas import dealer

async def summon_agents(data : dealer.SummonAgent, 
                        db: manipulation.Database = Depends(connection.get_db)) -> dict:
    agents = await db.get_available_agents_by_difficulty(data)
    if not agents:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail="All agents do not exist.")
    return agents

