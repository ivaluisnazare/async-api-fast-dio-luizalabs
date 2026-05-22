import asyncio
from config.settings import settings


async def test_connection():
    print(f"Database URL: {settings.DATABASE_URL}")

    print(f"DB_USER: {settings.DB_USER}")
    print(f"DB_PASSWORD: {settings.DB_PASSWORD}")
    print(f"DB_HOST: {settings.DB_HOST}")
    print(f"DB_PORT: {settings.DB_PORT}")


if __name__ == "__main__":
    asyncio.run(test_connection())