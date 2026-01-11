#user_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from user.src.repository.user_repository import UserRepository
from user.src.schemas.user import UserCreate, UserUpdate, UserResponse
from user.src.security.jwt_handler import get_password_hash

class UserService:
    def __init__(self, db: AsyncSession):
        self.repository = UserRepository(db)
        self.db = db

    async def get_all_users(self, skip: int = 0, limit: int = 100) -> List[UserResponse]:
        user_records = await self.repository.get_all(skip, limit)
        return [UserResponse.model_validate(user) for user in user_records]

    async def get_user_by_id(self, user_id: int) -> UserResponse:
        user_record = await self.repository.get_by_id(user_id)
        return UserResponse.model_validate(user_record)

    async def get_user_by_username(self, username: str) -> UserResponse:
        user_record = await self.repository.get_by_username(username)
        return UserResponse.model_validate(user_record)

    async def create_user(self, user_data: UserCreate) -> UserResponse:
        try:
            hashed_password = get_password_hash(user_data.password)
            user_record = await self.repository.create(user_data, hashed_password)
            await self.db.commit()
            return UserResponse.model_validate(user_record)
        except Exception:
            await self.db.rollback()
            raise

    async def update_user(self, user_id: int, user_data: UserUpdate) -> UserResponse:
        try:
            user_record = await self.repository.update(user_id, user_data)
            await self.db.commit()
            return UserResponse.model_validate(user_record)
        except Exception:
            await self.db.rollback()
            raise

    async def delete_user(self, user_id: int) -> bool:
        try:
            result = await self.repository.delete(user_id)
            await self.db.commit()
            return result
        except Exception:
            await self.db.rollback()
            raise