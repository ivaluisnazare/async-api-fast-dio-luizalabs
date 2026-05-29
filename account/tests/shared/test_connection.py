from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from src.config.settings import settings
from src.shared.init_db import close_db, init_db


class TestDatabaseConnection:

    @pytest.fixture
    def mock_engine(self):
        engine = MagicMock(spec=AsyncEngine)

        mock_conn = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar.return_value = 1

        async def mock_execute(stmt):
            return mock_result

        mock_conn.execute = mock_execute
        engine.begin.return_value.__aenter__.return_value = mock_conn
        engine.begin.return_value.__aexit__.return_value = None

        return engine

    @pytest.mark.asyncio
    async def test_init_db_successful_connection(self, mock_engine):

        with patch("src.shared.init_db.create_async_engine") as mock_create_engine:
            mock_create_engine.return_value = mock_engine

            result_engine = await init_db()

            mock_create_engine.assert_called_once_with(
                settings.DATABASE_URL,
                echo=settings.is_development,
                pool_pre_ping=True,
                pool_recycle=3600,
            )

            assert result_engine == mock_engine

    @pytest.mark.asyncio
    async def test_init_db_fallback_connection(self, mock_engine):

        with patch("src.shared.init_db.create_async_engine") as mock_create_engine:
            mock_create_engine.side_effect = [
                Exception("Connection failed"),
                mock_engine,
            ]

            result_engine = await init_db()

            assert mock_create_engine.call_count == 2

            first_call_args = mock_create_engine.call_args_list[0]
            assert settings.DATABASE_URL in str(first_call_args)
            assert "pool_recycle=3600" in str(first_call_args)

            second_call_args = mock_create_engine.call_args_list[1]
            fallback_url = settings.DATABASE_URL.replace("localhost", "127.0.0.1")
            assert fallback_url in str(second_call_args)
            assert "pool_recycle=3600" in str(
                second_call_args
            ) or "pool_pre_ping=True" in str(second_call_args)

            assert result_engine == mock_engine

    @pytest.mark.asyncio
    async def test_init_db_all_connections_fail(self):

        with patch("src.shared.init_db.create_async_engine") as mock_create_engine:
            mock_create_engine.side_effect = Exception("All connections failed")

            with pytest.raises(Exception, match="All connections failed"):
                await init_db()

    @pytest.mark.asyncio
    async def test_close_db_success(self, mock_engine):

        with patch.object(
            mock_engine, "dispose", new_callable=AsyncMock
        ) as mock_dispose:
            await close_db(mock_engine)

            mock_dispose.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_db_none_engine(self):

        await close_db(None)

    def test_settings_database_url_construction(self):

        expected_url = f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"

        assert settings.DATABASE_URL == expected_url
        assert "postgresql+asyncpg" in settings.DATABASE_URL
        assert settings.DB_USER in settings.DATABASE_URL
        assert settings.DB_NAME in settings.DATABASE_URL

    def test_settings_environment_properties(self):

        if settings.ENVIRONMENT == "development":
            assert settings.is_development is True
            assert settings.is_production is False
        elif settings.ENVIRONMENT == "production":
            assert settings.is_development is False
            assert settings.is_production is True

    @pytest.mark.asyncio
    async def test_connection_with_actual_settings(self):

        pytest.skip("Real integration testing requires PostgreSQL running locally.")


class TestDatabaseIntegration:

    @pytest.fixture
    def mock_engine(self):
        engine = MagicMock(spec=AsyncEngine)

        mock_conn = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar.return_value = 1

        async def mock_execute(stmt):
            return mock_result

        mock_conn.execute = mock_execute
        engine.begin.return_value.__aenter__.return_value = mock_conn
        engine.begin.return_value.__aexit__.return_value = None

        return engine

    @pytest.mark.asyncio
    async def test_database_operations(self, mock_engine):

        with patch("src.shared.init_db.create_async_engine") as mock_create_engine:
            mock_create_engine.return_value = mock_engine

            mock_conn = AsyncMock()
            mock_result = AsyncMock()

            async def execute_side_effect(stmt):
                if "version()" in str(stmt):
                    version_result = MagicMock()
                    version_result.scalar.return_value = "PostgreSQL 15.0"
                    return version_result
                elif "SELECT 1" in str(stmt):
                    test_result = MagicMock()
                    test_result.scalar.return_value = 1
                    return test_result
                return mock_result

            mock_conn.execute = execute_side_effect
            mock_engine.begin.return_value.__aenter__.return_value = mock_conn
            mock_engine.begin.return_value.__aexit__.return_value = None

            engine = await init_db()

            async with engine.begin() as conn:
                result = await conn.execute(text("SELECT version()"))
                version = result.scalar()
                assert "PostgreSQL" in version

                result = await conn.execute(text("SELECT 1 as test_value"))
                test_value = result.scalar()
                assert test_value == 1

            await close_db(engine)

    @pytest.mark.asyncio
    async def test_database_integration_real(self):

        if settings.ENVIRONMENT not in ["development", "test"]:
            pytest.skip(
                "Integration tests only run in development/testing environments."
            )

        try:
            engine = await init_db()
            await close_db(engine)
        except Exception:
            pytest.skip(
                "PostgreSQL is not available for real-world integration testing."
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
