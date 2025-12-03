import aio_pika
import json
from typing import Dict, Any

RABBITMQ_URL = "amqp://guest:guest@localhost/"
LOGIN_QUEUE = "user_login_queue"


async def get_rabbitmq_connection():
    """Create RabbitMQ connection"""
    return await aio_pika.connect_robust(RABBITMQ_URL)


async def send_login_message(login_data: Dict[str, Any]):
    """Send login message to RabbitMQ queue"""
    try:
        connection = await get_rabbitmq_connection()
        async with connection:
            channel = await connection.channel()

            queue = await channel.declare_queue(LOGIN_QUEUE, durable=True)

            # Create message
            message_body = json.dumps(login_data).encode()
            message = aio_pika.Message(
                body=message_body,
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )

            # Send message
            await channel.default_exchange.publish(
                message,
                routing_key=LOGIN_QUEUE
            )
            print(f"Login message sent for user: {login_data['username']}")

    except Exception as e:
        print(f"Error sending message to RabbitMQ: {e}")
        raise


async def setup_rabbitmq():
    """Setup RabbitMQ connection and queues"""
    try:
        connection = await get_rabbitmq_connection()
        async with connection:
            channel = await connection.channel()
            # Declare the login queue
            await channel.declare_queue(LOGIN_QUEUE, durable=True)
            print("RabbitMQ setup completed")
    except Exception as e:
        print(f"Error setting up RabbitMQ: {e}")
        raise