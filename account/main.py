import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from src.controller.account_controller import router as account_router
from src.messaging.consumer import start_rabbitmq_consumer
from src.securities.token_validator import initialize_token_validator
from src.config.settings import settings
from src.shared.init_db import close_db, init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_db()
    initialize_token_validator(settings.JWT_SECRET_KEY)
    asyncio.create_task(start_rabbitmq_consumer())
    logger.info("RabbitMQ consumer started")
    yield
    await close_db()


app = FastAPI(
    title="Account Management API",
    description="RESTful API for managing bank accounts",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(account_router)


@app.get("/")
async def root():
    return {"message": "Account Management API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/ready")
async def ready():
    return {"status": "ready"}


def run_server():
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        log_level="info" if settings.is_production else "debug",
    )


if __name__ == "__main__":
    run_server()
