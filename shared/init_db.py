from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy import text
from config.settings import settings
import backoff


@backoff.on_exception(backoff.expo, Exception, max_tries=3)
async def init_db():
    engine = None
    try:
        print(f"Trying to connect with {settings.DATABASE_URL}")
        engine = create_async_engine(settings.DATABASE_URL, echo=settings.is_development, pool_pre_ping=True)
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        print("Connection to database successfully established!")
        return engine

    except Exception as e:
        print(f"Error connecting to the database: {e}")

        if "localhost" in settings.DATABASE_URL:
            fallback_url = settings.DATABASE_URL.replace("localhost", "127.0.0.1")
            print(f"Trying fallback: {fallback_url}")

            try:
                engine = create_async_engine(fallback_url, echo=settings.is_development, pool_pre_ping=True)
                async with engine.begin() as conn:
                    await conn.execute(text("SELECT 1"))
                print("Fallback connection successfully established!")
                return engine
            except Exception as fallback_error:
                print(f"Error fallback: {fallback_error}")

        raise


async def close_db(engine: AsyncEngine):
    if engine:
        await engine.dispose()
        print("Connection to the database closed.")