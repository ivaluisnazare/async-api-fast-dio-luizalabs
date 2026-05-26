# main_consumer.py
import asyncio

from consumer import start_consumer

from src.config.settings import settings

DATABASE_URL = settings.DATABASE_URL

if __name__ == "__main__":
    print("🚀 Starting Account Service RabbitMQ Consumer...")
    asyncio.run(start_consumer(DATABASE_URL))
