from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn
from shared.init_db import init_db, close_db
from user.src.controller.user_controller import (router as user_router)
from config.settings import settings

@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_db()
    yield
    await close_db()

app = FastAPI(
    title="User Management API",
    description="RESTful API for managing bank users",
    version="1.0.0",
    lifespan=lifespan
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
        host="0.0.0.0",
        port=8081,
        reload=settings.is_development,
        log_level="info" if settings.is_production else "debug"
    )