from fastapi import APIRouter, Depends, HTTPException, status
from database import connection, manipulation
from schemas import dealer
from services import dealer_service

router = APIRouter()

@router.post("/from_dealer/summon_agents", response_model=dealer.Agents)
async def summon_agents(data : dealer.SummonAgent, 
                        db: manipulation.Database = Depends(connection.get_db)) -> dict:
    return await dealer_service.summon_agents(data, db)


