from sqlalchemy import update
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi import HTTPException, status
from database.models import User

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
        try:
            result = await self.session.execute(select(User).filter(User.connected == True))
            return result.scalars().all()
        except SQLAlchemyError as e:
            # SQLAlchemy 관련 예외 처리
            raise RuntimeError(f"Database error occurred: {str(e)}")
        except Exception as e:
            # 기타 예외 처리
            raise RuntimeError(f"An unexpected error occurred: {str(e)}")
        
    # from_floor
    async def match_nick_stk(self, nick_list: list[str]) -> dict[str, int]:
        result = await self.session.execute(select(User).filter(User.nick_name.in_(nick_list)))
        users = result.scalars().all()  # 조건에 맞는 Users 객체들을 list에 담는다
        nick_stk_dict = {user.nick_name: user.stk_size for user in users}
        return nick_stk_dict
    
    # from_floor
    async def update_stk_size(self, data: dict[str, int]) -> list[User]:
        nick_list = list(data.keys())
        result = await self.session.execute(select(User).filter(User.nick_name.in_(nick_list)))
        users = result.scalars().all() # 조건에 맞는 Users 객체들을 list에 담는다

        for user in users:
            if user.nick_name in data:
                user.stk_size = data[user.nick_name]
        try:
            await self.session.commit()
            return users
        except IntegrityError:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Integrity error occurred while updating users' stack sizes."
            )