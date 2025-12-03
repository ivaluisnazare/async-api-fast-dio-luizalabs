from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

from user.src.repository.user_repository import UserRepository
from user.src.schemas.user import UserLogin, Token
from user.src.security.jwt_handler import create_access_token
from user.src.messaging.rabbitmq import send_login_message


class AuthService:
    def __init__(self, db: AsyncSession):
        self.repository = UserRepository(db)
        self.db = db

    async def login(self, user_data: UserLogin) -> Token:
        # Authenticate user
        user = await self.repository.authenticate_user(user_data.username, user_data.password)

        # Create access token
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": user['username'], "user_id": user['id']},
            expires_delta=access_token_expires
        )

        # Send login message to RabbitMQ for account service
        await send_login_message({
            "username": user['username'],
            "password": user_data.password,  # In production, consider what to send
            "user_id": user['id'],
            "action": "user_login"
        })

        return Token(
            access_token=access_token,
            token_type="bearer",
            user_id=user['id'],
            username=user['username']
        )

    @staticmethod
    async def verify_token(token: str) -> dict:
        from user.src.security.jwt_handler import verify_token
        return verify_token(token)