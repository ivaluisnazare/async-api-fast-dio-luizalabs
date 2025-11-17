# account_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from decimal import Decimal
from typing import List, Optional

from account.src.models.account import accounts
from account.src.schemas.account import AccountCreate, AccountUpdate
from account.src.exceptions.custom_exceptions import (
    AccountNotFoundException,
    DuplicateAccountException
)


class AccountRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[dict]:
        query = select(accounts).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return [dict(account._mapping) for account in result.fetchall()]

    async def get_by_id(self, account_id: int) -> dict:
        """Get account by ID - throws exception if not found"""
        query = select(accounts).where(accounts.c.id == account_id)
        result = await self.db.execute(query)
        account = result.fetchone()

        if not account:
            raise AccountNotFoundException(account_id=account_id)

        return dict(account._mapping)

    async def get_by_user_id(self, user_id: int) -> dict:
        """Get account by user ID - throws exception if not found"""
        query = select(accounts).where(accounts.c.user_id == user_id)
        result = await self.db.execute(query)
        account = result.fetchone()

        if not account:
            raise AccountNotFoundException(user_id=user_id)

        return dict(account._mapping)

    async def create(self, account_data: AccountCreate) -> dict:
        # Check if account already exists for this user
        try:
            await self.get_by_user_id(account_data.user_id)
            raise DuplicateAccountException(account_data.user_id)
        except AccountNotFoundException:
            # Account doesn't exist, we can proceed
            pass

        query = accounts.insert().values(
            user_id=account_data.user_id,
            balance=account_data.balance
        ).returning(accounts)

        result = await self.db.execute(query)
        account = result.fetchone()
        return dict(account._mapping)

    async def update(self, account_id: int, account_data: AccountUpdate) -> dict:
        # This will raise AccountNotFoundException if account doesn't exist
        await self.get_by_id(account_id)

        update_data = account_data.model_dump(exclude_unset=True)

        if not update_data:
            return await self.get_by_id(account_id)

        query = (
            update(accounts)
            .where(accounts.c.id == account_id)
            .values(**update_data)
            .returning(accounts)
        )

        result = await self.db.execute(query)
        account = result.fetchone()

        if not account:
            raise AccountNotFoundException(account_id=account_id)

        return dict(account._mapping)

    async def delete(self, account_id: int) -> bool:
        # This will raise AccountNotFoundException if account doesn't exist
        await self.get_by_id(account_id)

        query = delete(accounts).where(accounts.c.id == account_id)
        result = await self.db.execute(query)
        return result.rowcount > 0

    async def update_balance(self, account_id: int, new_balance: Decimal) -> dict:
        # This will raise AccountNotFoundException if account doesn't exist
        await self.get_by_id(account_id)

        query = (
            update(accounts)
            .where(accounts.c.id == account_id)
            .values(balance=new_balance)
            .returning(accounts)
        )

        result = await self.db.execute(query)
        account = result.fetchone()

        if not account:
            raise AccountNotFoundException(account_id=account_id)

        return dict(account._mapping)

    async def get_balance(self, account_id: int) -> Decimal:
        # This will raise AccountNotFoundException if account doesn't exist
        account = await self.get_by_id(account_id)
        return account['balance']

    async def account_exists_by_id(self, account_id: int) -> bool:
        """Check if account exists without throwing exception"""
        try:
            await self.get_by_id(account_id)
            return True
        except AccountNotFoundException:
            return False

    async def account_exists_by_user_id(self, user_id: int) -> bool:
        """Check if account exists without throwing exception"""
        try:
            await self.get_by_user_id(user_id)
            return True
        except AccountNotFoundException:
            return False