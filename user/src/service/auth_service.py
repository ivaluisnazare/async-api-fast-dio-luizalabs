#auth_service.py
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from user.src.exceptions.custom_exceptions import InvalidCredentialsException
from user.src.repository.user_repository import UserRepository
from user.src.schemas.user import UserLogin, Token
from user.src.security.jwt_handler import create_access_token
from user.src.messaging.rabbitmq import send_login_message, send_token_to_account_service

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.repository = UserRepository(db)
        self.db = db

    async def login(self, user_data: UserLogin) -> Token:
        try:
            user = await self.repository.authenticate_user(
                user_data.username,
                user_data.password
            )

            if not user:
                raise InvalidCredentialsException(
                    "Invalid username or password"
                )

            access_token_expires = timedelta(minutes=30)
            access_token = create_access_token(
                data={
                    "sub": user['username'],
                    "user_id": user['id'],
                    "email": user.get('email', '')
                },
                expires_delta=access_token_expires
            )

            token = Token(
                access_token=access_token,
                token_type="bearer",
                user_id=user['id'],
                username=user['username'],
                expires_in=access_token_expires.total_seconds()
            )

            timestamp = datetime.utcnow().isoformat()

            login_data = {
                "username": user['username'],
                "user_id": user['id'],
                "action": "user_login",
                "timestamp": timestamp,
                "service": "user-service"
            }

            token_data = {
                "token": access_token,
                "user_id": user['id'],
                "username": user['username'],
                "token_type": "bearer",
                "expires_in": access_token_expires.total_seconds(),
                "issued_at": timestamp,
                "service": "user-service",
                "action": "validate_token"
            }

            try:
                asyncio.create_task(send_login_message(login_data))

                asyncio.create_task(send_token_to_account_service(token_data))

                logger.info(f"Login successful for user: {user['username']}")

            except Exception as e:
                logger.error(f"Failed to send RabbitMQ messages: {e}")

            return token

        except InvalidCredentialsException as e:
            logger.warning(f"Failed login attempt for username: {user_data.username}")
            raise

        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise Exception(f"Login failed: {str(e)}")

    @staticmethod
    async def verify_token(token: str) -> dict:
        from user.src.security.jwt_handler import verify_token
        return verify_token(token)