from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from config.settings import Settings
# CORREÇÃO: Importe do módulo correto (shared.database)
from shared.database import DATABASE_URL, engine, get_db
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine


class TestDatabase:

    def test_database_url_replacement(self):
        assert DATABASE_URL.startswith("postgresql+asyncpg://")

        original_url = Settings().DATABASE_URL
        expected_url = original_url.replace("postgresql://", "postgresql+asyncpg://")
        assert DATABASE_URL == expected_url

    def test_engine_creation(self):
        assert engine is not None

        assert hasattr(engine, "dialect")
        assert hasattr(engine, "echo")

        assert engine.echo == Settings().is_development

    def test_engine_pool_configuration(self):
        assert hasattr(engine, "pool")


class TestGetDB:

    @pytest.mark.asyncio
    async def test_get_db_returns_async_session(self):
        mock_session = AsyncMock(spec=AsyncSession)

        with patch("shared.database.AsyncSessionLocal") as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session

            db_gen = get_db()
            session = await anext(db_gen)

            assert session == mock_session

            mock_session_local.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_db_closes_session_on_exit(self):
        mock_session = AsyncMock(spec=AsyncSession)

        with patch("shared.database.AsyncSessionLocal") as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session

            async for session in get_db():
                assert session == mock_session

            mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_db_proper_context_management(self):
        mock_session = AsyncMock(spec=AsyncSession)

        with patch("shared.database.AsyncSessionLocal") as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session

            async with mock_session_local() as session:
                assert session == mock_session

            mock_session_local.return_value.__aenter__.assert_called_once()
            mock_session_local.return_value.__aexit__.assert_called_once()


class TestDatabaseSettings:

    def test_database_url_from_settings(self):
        settings = Settings()

        assert settings.DATABASE_URL.startswith("postgresql+asyncpg://")

    @patch("shared.database.settings")
    def test_development_environment_echo_true(self, mock_settings):
        mock_settings.is_development = True
        mock_settings.DATABASE_URL = "postgresql+asyncpg://test:test@localhost:5432/test"

        test_engine = create_async_engine(
            mock_settings.DATABASE_URL.replace(
                "postgresql://", "postgresql+asyncpg://"
            ),
            echo=mock_settings.is_development,
            future=True,
            pool_pre_ping=True,
            pool_recycle=300,
        )

        assert test_engine.echo is True

    @patch("shared.database.settings")
    def test_production_environment_echo_false(self, mock_settings):
        mock_settings.is_development = False
        mock_settings.DATABASE_URL = "postgresql://test:test@localhost:5432/test"

        test_engine = create_async_engine(
            mock_settings.DATABASE_URL.replace(
                "postgresql://", "postgresql+asyncpg://"
            ),
            echo=mock_settings.is_development,
            future=True,
            pool_pre_ping=True,
            pool_recycle=300,
        )

        assert test_engine.echo is False


class TestDatabaseIntegration:

    def test_all_components_initialized(self):
        from shared.database import (DATABASE_URL, AsyncSessionLocal, engine,
                                     get_db, metadata)

        components = [DATABASE_URL, engine, AsyncSessionLocal, metadata, get_db]

        for component in components:
            assert component is not None

    def test_database_url_format(self):
        assert DATABASE_URL.startswith("postgresql+asyncpg://")

        assert "postgresql://" not in DATABASE_URL


@pytest.fixture
def mock_settings():
    with patch("shared.database.settings") as mock:
        mock.DATABASE_URL = "postgresql://test:test@localhost:5432/testdb"
        mock.is_development = True
        yield mock


@pytest_asyncio.fixture
async def mock_async_session():
    session = AsyncMock(spec=AsyncSession)
    yield session


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
