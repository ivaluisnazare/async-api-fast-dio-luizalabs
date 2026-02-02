#token_validator.py
import logging
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from datetime import datetime, UTC
import jwt

logger = logging.getLogger(__name__)


class TokenValidator:
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm

    async def validate_token(self, token: str) -> Dict[str, Any]:

        try:
            if token.startswith("Bearer "):
                token = token[7:]

            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )

            exp = payload.get("exp")
            if exp and datetime.now(UTC).timestamp() > exp:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token expired"
                )

            if "sub" not in payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: missing subject"
                )

            return {
                "username": payload.get("sub"),
                "user_id": payload.get("user_id"),
                "email": payload.get("email"),
                "exp": payload.get("exp"),
                "iat": payload.get("iat")
            }

        except jwt.ExpiredSignatureError:
            logger.warning(f"Token expired: {token[:50]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Token validation failed: {str(e)}"
            )


token_validator: Optional[TokenValidator] = None


def get_token_validator() -> TokenValidator:
    if not token_validator:
        raise RuntimeError("TokenValidator not initialized")
    return token_validator


async def initialize_token_validator(secret_key: str):
    global token_validator
    token_validator = TokenValidator(secret_key)
    logger.info("TokenValidator initialized")