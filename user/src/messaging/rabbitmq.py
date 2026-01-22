#rabbitmq.py
import asyncio
import aio_pika
import json
from typing import Dict, Any
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)

RABBITMQ_URL = "amqp://admin:rabbit123@localhost:5672/"
LOGIN_QUEUE = "user_login_queue"
TOKEN_EXCHANGE = "auth_tokens_exchange"
TOKEN_ROUTING_KEY = "auth.token"


@asynccontextmanager
async def get_rabbitmq_connection(max_retries=3):
    for attempt in range(max_retries):
        try:
            connection = await aio_pika.connect_robust(
                RABBITMQ_URL,
                timeout=10
            )
            yield connection
            await connection.close()
            return
        except Exception as e:
            logger.error(f"Connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
            else:
                raise ConnectionError(
                    f"Failed to connect to RabbitMQ after {max_retries} attempts"
                ) from e


async def send_login_message(login_data: Dict[str, Any]):
    """Send login message to RabbitMQ queue"""
    try:
        async with get_rabbitmq_connection() as connection:
            async with connection:
                channel = await connection.channel()

                exchange = await channel.declare_exchange(
                    TOKEN_EXCHANGE,
                    aio_pika.ExchangeType.DIRECT,
                    durable=True,
                    auto_delete=False
                )

                queue = await channel.declare_queue(
                    LOGIN_QUEUE,
                    durable=True,
                    arguments={
                        'x-dead-letter-exchange': '',  # DLQ config
                        'x-dead-letter-routing-key': f'{LOGIN_QUEUE}.dlq'
                    }
                )

                await queue.bind(exchange, TOKEN_ROUTING_KEY)

                message_body = json.dumps(login_data).encode()
                message = aio_pika.Message(
                    body=message_body,
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    content_type="application/json",
                    headers={
                        "service": "user-service",
                        "event_type": "user_login",
                        "timestamp": login_data.get("timestamp")
                    }
                )

                await exchange.publish(
                    message,
                    routing_key=TOKEN_ROUTING_KEY
                )

                logger.info(f"Login message sent for user: {login_data['username']}")
                return True

    except Exception as e:
        logger.error(f"Error sending message to RabbitMQ: {e}")
        return False


async def send_token_to_account_service(token_data: Dict[str, Any]):
    """Send token directly to account-service queue"""
    try:
        async with get_rabbitmq_connection() as connection:
            async with connection:
                channel = await connection.channel()

                account_queue_name = "account_auth_queue"
                account_queue = await channel.declare_queue(
                    account_queue_name,
                    durable=True,
                    arguments={
                        'x-dead-letter-exchange': '',
                        'x-dead-letter-routing-key': f'{account_queue_name}.dlq'
                    }
                )

                message_body = json.dumps(token_data).encode()
                message = aio_pika.Message(
                    body=message_body,
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    content_type="application/json",
                    headers={
                        "service": "user-service",
                        "event_type": "auth_token",
                        "timestamp": token_data.get("timestamp")
                    }
                )

                await channel.default_exchange.publish(
                    message,
                    routing_key=account_queue_name
                )

                logger.info(f"Token sent to account-service for user: {token_data['username']}")
                return True

    except Exception as e:
        logger.error(f"Error sending token to account-service: {e}")
        return False


async def setup_rabbitmq():
    """Setup RabbitMQ connection, exchanges and queues"""
    try:
        async with get_rabbitmq_connection() as connection:
            async with connection:
                channel = await connection.channel()

                exchange = await channel.declare_exchange(
                    TOKEN_EXCHANGE,
                    aio_pika.ExchangeType.DIRECT,
                    durable=True
                )

                login_queue = await channel.declare_queue(
                    LOGIN_QUEUE,
                    durable=True,
                    arguments={
                        'x-dead-letter-exchange': '',
                        'x-dead-letter-routing-key': f'{LOGIN_QUEUE}.dlq'
                    }
                )

                # DLQ (Dead Letter Queue)
                dlq = await channel.declare_queue(
                    f'{LOGIN_QUEUE}.dlq',
                    durable=True
                )

                await login_queue.bind(exchange, TOKEN_ROUTING_KEY)

                account_queue = await channel.declare_queue(
                    "account_auth_queue",
                    durable=True,
                    arguments={
                        'x-dead-letter-exchange': '',
                        'x-dead-letter-routing-key': 'account_auth_queue.dlq'
                    }
                )

                # DLQ account-service
                account_dlq = await channel.declare_queue(
                    "account_auth_queue.dlq",
                    durable=True
                )

                logger.info("RabbitMQ setup completed successfully")
                return True

    except Exception as e:
        logger.error(f"Error setting up RabbitMQ: {e}")
        return False