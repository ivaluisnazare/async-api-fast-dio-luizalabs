from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from src.config.settings import settings
from src.shared.init_db import close_db, init_db
from src.controller.user_controller import router as user_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title="User Management API",
    description="RESTful API for managing bank users",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(user_router)


@app.get("/")
async def root():
    return {"message": "User Management API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8081,
        reload=settings.is_development,
        log_level="info" if settings.is_development else "debug",
    )
