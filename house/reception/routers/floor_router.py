from fastapi import APIRouter, Depends, HTTPException, status
from database import connection, manipulation
from schemas import floor
from services import floor_service

router = APIRouter()

@router.post("/from_floor/update_stack_size", status_code=status.HTTP_200_OK)
async def update_stack_size(data : floor.UpdateStackSize, 
                            db: manipulation.Database = Depends(connection.get_db)) -> list:
    return await floor_service.update_stack_size(data, db)


