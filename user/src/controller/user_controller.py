from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from shared.database import get_db
from user.src.schemas.user import UserCreate, UserUpdate, UserResponse, UserLogin, Token
from user.src.service.user_service import UserService
from user.src.service.auth_service import AuthService
from user.src.exceptions.custom_exceptions import (
    UserNotFoundException,
    DuplicateUserException,
    InvalidCredentialsException
)

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/", response_model=List[UserResponse])
async def get_all_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    db: AsyncSession = Depends(get_db)
):
    try:
        service = UserService(db)
        return await service.get_all_users(skip=skip, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(user_id: int, db: AsyncSession = Depends(get_db)):
    try:
        service = UserService(db)
        return await service.get_user_by_id(user_id)
    except UserNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        service = UserService(db)
        return await service.create_user(user_data)
    except DuplicateUserException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db)
):
    try:
        service = UserService(db)
        return await service.update_user(user_id, user_data)
    except UserNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    try:
        service = UserService(db)
        await service.delete_user(user_id)
        return None
    except UserNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    try:
        auth_service = AuthService(db)
        return await auth_service.login(user_data)
    except InvalidCredentialsException as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))