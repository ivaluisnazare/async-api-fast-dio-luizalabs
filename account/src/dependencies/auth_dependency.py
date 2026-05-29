import logging
import os
import sys

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.messaging.consumer import token_storage as storage
from src.securities.token_validator import get_token_validator

security = HTTPBearer()
logger = logging.getLogger(__name__)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
        )

    token = credentials.credentials

    token_info = storage.get_token_info(token)
    if token_info:
        logger.info(f"Token found in storage for user: {token_info['username']}")
        return {
            "user_id": token_info["user_id"],
            "username": token_info["username"],
            "token_type": token_info["token_type"],
            "source": "rabbitmq_storage",
        }

    logger.info(f"Token not in storage, attempting JWT validation: {token[:20]}...")

    try:
        validator = get_token_validator()
        payload = await validator.validate_token(token)

        return {
            "user_id": payload["user_id"],
            "username": payload["username"],
            "email": payload.get("email"),
            "source": "jwt_validation",
        }

    except HTTPException as e:
        logger.error(f"Token validation failed: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in token validation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )


def get_current_user_id(current_user: dict = Depends(get_current_user)) -> int:
    return current_user["user_id"]


async def require_same_user(
    user_id: int, current_user: dict = Depends(get_current_user)
) -> dict:
    if current_user["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this resource",
        )
    return current_user
