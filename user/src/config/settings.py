# settings.py
from typing import Literal
from urllib.parse import quote_plus

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )

    JWT_SECRET_KEY: str = Field(default="")
    JWT_ALGORITHM: str = "HS256"

    RABBITMQ_HOST: str = Field(default="localhost")
    RABBITMQ_PORT: str = Field(default="5672")
    RABBITMQ_USER: str = Field(default="admin")
    RABBITMQ_PASSWORD: str = Field(default="rabbit123")
    RABBITMQ_URL: str | None = None

    DB_USER: str = Field(default="banking_operations")
    DB_PASSWORD: str = Field(default="account123")
    DB_NAME: str = Field(default="bank_db")
    DB_HOST: str = Field(default="localhost")
    DB_PORT: str = Field(default="5432")

    DOCKER_MODE: bool = Field(default=False)

    DATABASE_URL: str | None = None

    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    @model_validator(mode="after")
    def build_database_url(self):
        if self.DATABASE_URL:
            return self

        print(f"Using DB host: {self.DB_HOST}")

        self.DATABASE_URL = f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        print(f"DATABASE_URL: {self.DATABASE_URL}")
        escaped_password = quote_plus(self.DB_PASSWORD)

        return self

    @model_validator(mode="after")
    def build_rabbitmq_url(self):
        if not self.RABBITMQ_URL:
            self.RABBITMQ_URL = f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/"
            print(f"Constructed RABBITMQ_URL: {self.RABBITMQ_URL}")
        return self

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


settings = Settings()
