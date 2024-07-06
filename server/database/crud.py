from typing import Any, List
from beanie import PydanticObjectId
from pydantic import BaseModel


class Database:

    def __init__(self, model):
        self.model = model
         
    async def save(self, document) -> None:
        await document.create()
        return

    async def get(self, id: PydanticObjectId) -> Any:
        doc = await self.model.get(id)
        return doc

    async def get_all(self) -> List[Any]:
        docs = await self.model.find_all().to_list()
        return docs

    async def update(self, id: PydanticObjectId, body: BaseModel) -> Any:
        des_body = body.model_dump(exclude_unset=True)  
        update_query = {"$set": des_body}
        doc = await self.get(id)
        if not doc:
            return False
        await doc.update(update_query)
        return doc

    async def delete(self, id: PydanticObjectId) -> bool:
        doc = await self.get(id)
        if not doc:
            return False
        await doc.delete()
        return True