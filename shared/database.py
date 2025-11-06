from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import Literal


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )

    DB_USER: str = Field(default="database", description="Usuário do banco de dados")
    DB_PASSWORD: str = Field(default="database", description="Senha do banco de dados")
    DB_NAME: str = Field(default="db", description="Nome do banco de dados")
    DB_HOST: str = Field(default="localhost", description="Host do banco de dados")
    DB_PORT: str = Field(default="5432", description="Porta do banco de dados")

    DATABASE_URL: str = Field(default="", description="URL de conexão com o banco de dados")

    ENVIRONMENT: Literal["development", "staging", "production"] = "production"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def build_database_url(cls, v, info):
        if v:
            return v

        data = info.data

        user = data.get("DB_USER", "database")
        password = data.get("DB_PASSWORD", "database")
        name = data.get("DB_NAME", "db")
        host = data.get("DB_HOST", "localhost")
        port = data.get("DB_PORT", "5432")

        return f"postgresql://{user}:{password}@{host}:{port}/{name}"

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v):
        if not v.startswith("postgresql://"):
            raise ValueError("DATABASE_URL must use the protocol postgresql://")
        return v

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

settings = Settings()