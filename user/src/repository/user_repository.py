#user_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import List

from user.src.models.users import users
from user.src.schemas.user import UserCreate, UserUpdate
from user.src.exceptions.custom_exceptions import (
    UserNotFoundException,
    DuplicateUserException, InvalidCredentialsException, InactiveUserException
)


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[dict]:
        query = select(users).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return [dict(user._mapping) for user in result.fetchall()]

    async def get_by_id(self, user_id: int) -> dict:
        query = select(users).where(users.c.id == user_id)
        result = await self.db.execute(query)
        user = result.fetchone()

        if not user:
            raise UserNotFoundException(user_id=user_id)

        return dict(user._mapping)

    async def get_by_username(self, username: str) -> dict:
        query = select(users).where(users.c.username == username)
        result = await self.db.execute(query)
        user = result.fetchone()

        if not user:
            raise UserNotFoundException(username=username)

        return dict(user._mapping)

    async def get_by_email(self, email: str) -> dict:
        query = select(users).where(users.c.email == email)
        result = await self.db.execute(query)
        user = result.fetchone()

        if not user:
            raise UserNotFoundException()

        return dict(user._mapping)

    async def create(self, user_data: UserCreate, hashed_password: str) -> dict:
        try:
            await self.get_by_username(user_data.username)
            raise DuplicateUserException(username=user_data.username)
        except UserNotFoundException:
            pass

        try:
            await self.get_by_email(user_data.email)
            raise DuplicateUserException(email=user_data.email)
        except UserNotFoundException:
            pass

        query = users.insert().values(
            username=user_data.username,
            email=user_data.email,
            password=hashed_password,
            full_name=user_data.full_name
        ).returning(users)

        result = await self.db.execute(query)
        user = result.fetchone()

        return dict(user._mapping)

    async def update(self, user_id: int, user_data: UserUpdate) -> dict:
        await self.get_by_id(user_id)

        update_data = user_data.model_dump(exclude_unset=True)

        if not update_data:
            return await self.get_by_id(user_id)

        query = (
            update(users)
            .where(users.c.id == user_id)
            .values(**update_data)
            .returning(users)
        )

        result = await self.db.execute(query)
        user = result.fetchone()

        if not user:
            raise UserNotFoundException(user_id=user_id)

        return dict(user._mapping)

    async def delete(self, user_id: int) -> bool:
        await self.get_by_id(user_id)

        query = delete(users).where(users.users.c.id == user_id)
        result = await self.db.execute(query)
        return result.rowcount > 0

    async def authenticate_user(self, username: str, password: str) -> dict:
        from user.src.security.jwt_handler import verify_password

        try:
            user = await self.get_by_username(username)
            if not verify_password(password, user['password']):
                raise InvalidCredentialsException()

            if not user['is_active']:
                raise InactiveUserException()

            return user
        except UserNotFoundException:
            raise InvalidCredentialsException()