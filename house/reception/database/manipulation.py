from sqlalchemy import update
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from models import User


class Database:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_email(self, email: str):
        result = await self.session.execute(select(User).filter(User.email == email))
        return result.scalars().first()

    async def get_user_by_nick(self, nick_name: str):
        result = await self.session.execute(select(User).filter(User.nick_name == nick_name))
        return result.scalars().first()
    

    # 이 함수를 쓰는 라우터는 아직 미구현. 관리자용
    async def get_user_by_id(self, user_id: int):
        result = await self.session.execute(select(User).filter(User.id == user_id))
        return result.scalars().first()

    # 이 함수를 쓰는 라우터는 아직 미구현. 관리자용
    async def get_all_users(self):
        result = await self.session.execute(select(User))
        return result.scalars().all()

    '''
    add(): 
    이 메서드는 비동기 메서드가 아니므로 await를 사용하지 않습니다. 
    이는 단순히 SQLAlchemy 세션에 task 객체를 추가하는 작업을 수행합니다. 
    이 작업은 메모리 내에서 이루어지며, 데이터베이스와의 네트워크 통신을 포함하지 않으므로 비동기 처리가 필요하지 않습니다.

    commit(): 
    이 메서드는 데이터베이스에 변경 사항을 커밋하는 비동기 작업입니다. 
    이는 실제로 데이터베이스에 변경 사항을 반영하기 위해 네트워크 통신을 필요로 하므로 await 키워드를 사용합니다.

    refresh(): 
    이 메서드는 데이터베이스에서 해당 객체의 최신 상태를 가져오는 비동기 작업입니다. 
    이 작업 역시 데이터베이스와의 상호작용을 포함하므로 await 키워드를 사용합니다.

    async def 는 함수가 비동기 처리를 할 수 있는 코루틴 함수 임을 나타낸다
    await는 DB 접속(IO)처리가 발생하므로 
    '대기 시간이 발생하는 처리를 할게요'라고 비동기 처리를 알리는 역할을 한다
    이를 통해 파이썬은 이 코루틴의 처리에서 벗어나
    이벤트 루프 내에서 다른 코루틴의 처리를 수행할 수 있게 된다
    이것이 비동기/병렬 처리의 핵심이다
    '''
    
    async def create_user(self, user: User):
        self.session.add(user)
        try:
            await self.session.commit()
            await self.session.refresh(user)
            return user
        except IntegrityError: # 데이터베이스에서 고유 필드 제약 조건을 위반하여 발생하는 IntegrityError 예외를 처리합니다.
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with the same email already exists."
            )

    async def update_user(self, user: User):
        try:
            await self.session.commit()
            await self.session.refresh(user)
            return user
        except IntegrityError:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Integrity error occurred while updating user."
            )
        
    async def delete_user(self, user: User):
        try:
            await self.session.delete(user)
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Integrity error occurred while deleting user."
            )

    # 관리자용
    async def update_user_connection_status(self, user_id: int, status: bool):
        try:
            await self.session.execute(update(User).where(User.id == user_id).values(connected=status))
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update connection status."
            )

    # 관리자용
    async def get_connected_users(self) -> list[User]:
        result = await self.session.execute(select(User).filter(User.connected == True))
        return result.scalars().all()

    # from_floor
    async def request_users_stack_size(self, data: list[int]) -> dict[int, int]:
        result = await self.session.execute(select(User).filter(User.id.in_(data)))
        users = result.scalars().all()  # 조건에 맞는 Users 객체들을 list에 담는다
        users_stk_size = {user.id: user.stk_size for user in users}
        return users_stk_size

    # from_floor
    async def update_users_stack_size(self, data: dict[int, int]) -> list[User]:
        user_ids = list(data.keys())
        result = await self.session.execute(select(User).filter(User.id.in_(user_ids)))
        db_user = result.scalars().all() # 조건에 맞는 Users 객체들을 list에 담는다

        for user in db_user:
            if user.id in data:
                user.stk_size = data[user.id]
        try:
            await self.session.commit()
            return db_user
        except IntegrityError:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Integrity error occurred while updating users' stack sizes."
            )