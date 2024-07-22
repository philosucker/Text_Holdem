from fastapi import APIRouter, Depends, HTTPException, status
from database import connection, manipulation
from schemas import dealer
from services import dealer_service

router = APIRouter()

@router.post("/from_dealer/request_stack_size", status_code=status.HTTP_200_OK)
async def request_stack_size(user_ids: dealer.RequestStackSize, 
                             db: manipulation.Database = Depends(connection.get_db)) -> dict:
    return await dealer_service.request_stack_size(user_ids, db)


