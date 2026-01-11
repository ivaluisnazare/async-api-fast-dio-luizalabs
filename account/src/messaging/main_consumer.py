# main_consumer.py (no account-service)
import asyncio
import os
from consumer import start_consumer

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://banking_operations:account123@localhost:5432/bank_db")

if __name__ == "__main__":
    print("🚀 Starting Account Service RabbitMQ Consumer...")
    asyncio.run(start_consumer(DATABASE_URL))