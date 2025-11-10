from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn

from shared.database import engine, metadata
from account.src.controller.account_controller import router as account_router
from config.settings import settings


@asynccontextmanager
async def lifespan():
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="Account Management API",
    description="RESTful API for managing bank accounts",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(account_router)


@app.get("/")
async def root():
    return {"message": "Account Management API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        log_level="info" if settings.is_production else "debug"
    )