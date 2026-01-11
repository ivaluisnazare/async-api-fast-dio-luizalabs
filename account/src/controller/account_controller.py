#account_controller.py
from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from typing import List

from shared.database import get_db
from account.src.schemas.account import AccountCreate, AccountUpdate, AccountResponse
from account.src.service.account_service import AccountService
from account.src.dependencies.auth_dependency import (
    get_current_user,
    get_current_user_id,
    require_same_user
)
from account.src.exceptions.custom_exceptions import (
    AccountNotFoundException,
    InsufficientBalanceException,
    DuplicateAccountException,
    InvalidAmountException
)

router = APIRouter(prefix="/accounts", tags=["accounts"])

@router.get("/", response_model=List[AccountResponse])
async def get_all_accounts(
        skip: int = Query(0, ge=0, description="Number of records to skip"),
        limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(get_current_user)  # Requer autenticação
):
    try:
        service = AccountService(db)
        return await service.get_all_accounts(skip=skip, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account_by_id(
        account_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    try:
        service = AccountService(db)
        account = await service.get_account_by_id(account_id)

        if account.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this account"
            )

        return account
    except AccountNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}", response_model=AccountResponse)
async def get_account_by_user_id(
        user_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(require_same_user)  # Requer ser o mesmo usuário
):
    try:
        service = AccountService(db)
        return await service.get_account_by_user_id(user_id)
    except AccountNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
        account_data: AccountCreate,
        db: AsyncSession = Depends(get_db),
        current_user_id: int = Depends(get_current_user_id)
):
    try:
        account_data.user_id = current_user_id

        service = AccountService(db)
        return await service.create_account(account_data)
    except DuplicateAccountException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(
        account_id: int,
        account_data: AccountUpdate,
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    try:
        service = AccountService(db)
        existing_account = await service.get_account_by_id(account_id)

        if existing_account.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this account"
            )

        return await service.update_account(account_id, account_data)
    except AccountNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
        account_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    try:
        service = AccountService(db)
        existing_account = await service.get_account_by_id(account_id)

        if existing_account.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this account"
            )

        await service.delete_account(account_id)
        return None
    except AccountNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{account_id}/deposit", response_model=AccountResponse)
async def deposit_to_account(
        account_id: int,
        amount: Decimal = Query(..., gt=0, description="Amount to deposit"),
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    try:
        # Verifica se a conta pertence ao usuário
        service = AccountService(db)
        existing_account = await service.get_account_by_id(account_id)

        if existing_account.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to deposit to this account"
            )

        return await service.deposit(account_id, amount)
    except AccountNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidAmountException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{account_id}/withdraw", response_model=AccountResponse)
async def withdraw_from_account(
        account_id: int,
        amount: Decimal = Query(..., gt=0, description="Amount to withdraw"),
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    try:
        # Verifica se a conta pertence ao usuário
        service = AccountService(db)
        existing_account = await service.get_account_by_id(account_id)

        if existing_account.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to withdraw from this account"
            )

        return await service.withdraw(account_id, amount)
    except (AccountNotFoundException, InvalidAmountException, InsufficientBalanceException) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{from_account_id}/transfer/{to_account_id}", status_code=status.HTTP_200_OK)
async def transfer_between_accounts(
        from_account_id: int,
        to_account_id: int,
        amount: Decimal = Query(..., gt=0, description="Amount to transfer"),
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    try:
        # Verifica se a conta de origem pertence ao usuário
        service = AccountService(db)
        from_account = await service.get_account_by_id(from_account_id)

        if from_account.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to transfer from this account"
            )

        return await service.transfer(from_account_id, to_account_id, amount)
    except (AccountNotFoundException, InvalidAmountException, InsufficientBalanceException) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))