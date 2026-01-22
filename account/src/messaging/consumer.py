#consumer.py
import asyncio
import aio_pika
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
logger = logging.getLogger(__name__)

RABBITMQ_URL = "amqp://admin:rabbit123@localhost:5672/"
ACCOUNT_AUTH_QUEUE = "account_auth_queue"
TOKEN_EXCHANGE = "auth_tokens_exchange"
TOKEN_ROUTING_KEY = "auth.token"


class TokenStorage:

    def __init__(self):
        self.tokens: Dict[str, Dict[str, Any]] = {}
        self.user_tokens: Dict[int, str] = {}

    def store_token(self, token_data: Dict[str, Any]) -> None:
        token = token_data.get("token")
        user_id = token_data.get("user_id")

        if not token or not user_id:
            logger.error(f"Invalid token data received: {token_data}")
            return

        old_token = self.user_tokens.get(user_id)
        if old_token and old_token in self.tokens:
            del self.tokens[old_token]

        self.tokens[token] = {
            "user_id": user_id,
            "username": token_data.get("username"),
            "token_type": token_data.get("token_type"),
            "expires_in": token_data.get("expires_in"),
            "issued_at": token_data.get("issued_at"),
            "received_at": datetime.now().isoformat()
        }

        self.user_tokens[user_id] = token

        logger.info(f"Token stored for user_id: {user_id}, username: {token_data.get('username')}")

    def get_token_info(self, token: str) -> Optional[Dict[str, Any]]:
        if token.startswith("Bearer "):
            token = token[7:]
        return self.tokens.get(token)

    def get_user_token(self, user_id: int) -> Optional[str]:
        return self.user_tokens.get(user_id)

    def remove_token(self, token: str) -> None:
        token_info = self.tokens.get(token)
        if token_info:
            user_id = token_info.get("user_id")
            if user_id and self.user_tokens.get(user_id) == token:
                del self.user_tokens[user_id]
            del self.tokens[token]
            logger.info(f"Token removed for user_id: {user_id}")


token_storage = TokenStorage()


async def process_token_message(message: aio_pika.IncomingMessage):
    async with message.process():
        try:
            body = message.body.decode()
            token_data = json.loads(body)

            logger.info(f"Received token message: {token_data.get('username')}")

            required_fields = ["token", "user_id", "username"]
            for field in required_fields:
                if field not in token_data:
                    logger.error(f"Missing required field: {field} in data: {token_data}")
                    return

                token_storage.store_token(token_data)

                logger.info(f"Token processed successfully for user: {token_data['username']}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON: {e}, body: {message.body}")
        except Exception as e:
            logger.error(f"Error processing token message: {e}")


async def consume_token_messages():
    max_retries = 5
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting to connect to RabbitMQ (attempt {attempt + 1})")
            connection = await aio_pika.connect_robust(RABBITMQ_URL)
            logger.info("Connected to RabbitMQ for consuming")

            async with connection:
                channel = await connection.channel()

                # Declara exchange
                exchange = await channel.declare_exchange(
                    TOKEN_EXCHANGE,
                    aio_pika.ExchangeType.DIRECT,
                    durable=True
                )

                queue = await channel.declare_queue(
                    ACCOUNT_AUTH_QUEUE,
                    durable=True,
                    arguments={
                        'x-dead-letter-exchange': '',
                        'x-dead-letter-routing-key': f'{ACCOUNT_AUTH_QUEUE}.dlq'
                    }
                )

                await channel.declare_queue(
                    f'{ACCOUNT_AUTH_QUEUE}.dlq',
                    durable=True
                )

                await queue.bind(exchange, TOKEN_ROUTING_KEY)

                logger.info(
                    f"Queue {ACCOUNT_AUTH_QUEUE} bound to exchange {TOKEN_EXCHANGE} with routing key {TOKEN_ROUTING_KEY}")
                logger.info(f"Starting to consume from queue: {ACCOUNT_AUTH_QUEUE}")

                await queue.consume(process_token_message)
                logger.info("Consumer started successfully")

                try:
                    await asyncio.Future()
                except asyncio.CancelledError:
                    logger.info("Consumer task cancelled")
                    break

        except ConnectionError as e:
            logger.error(f"Connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay * (attempt + 1))
            else:
                logger.error(f"Failed to connect after {max_retries} attempts")
                raise
        except Exception as e:
            logger.error(f"Error in consumer: {e}")
            await asyncio.sleep(retry_delay)


async def start_rabbitmq_consumer():

    logger.info("Starting RabbitMQ consumer...")
    task = asyncio.create_task(consume_token_messages())
    logger.info("RabbitMQ consumer task created")
    return task