from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy import text
from config.settings import settings
import backoff
import logging

logger = logging.getLogger(__name__)


@backoff.on_exception(backoff.expo, Exception, max_tries=3)
async def init_db() -> AsyncEngine:
    engine = None
    original_error = None

    try:
        logger.info(f"Trying to connect with {settings.DATABASE_URL}")
        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.is_development,
            pool_pre_ping=True,
            pool_recycle=3600
        )

        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))

        logger.info("Connection to database successfully established!")
        return engine

    except Exception as e:
        original_error = e
        logger.warning(f"Error connecting to the database: {e}")

        if settings.DB_HOST == "localhost":
            fallback_url = settings.DATABASE_URL.replace("localhost", "127.0.0.1")
            logger.info(f"Trying fallback: {fallback_url}")

            try:
                engine = create_async_engine(
                    fallback_url,
                    echo=settings.is_development,
                    pool_pre_ping=True
                )
                async with engine.begin() as conn:
                    await conn.execute(text("SELECT 1"))

                logger.info("Fallback connection successfully established!")
                return engine
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")

        raise ConnectionError(
            f"Failed to connect to database after fallback attempts: {original_error}") from original_error


async def close_db(engine: AsyncEngine | None):
    if engine:
        await engine.dispose()
        logger.info("Database connection closed.")
