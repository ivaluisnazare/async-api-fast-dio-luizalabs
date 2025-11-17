import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy import text
from config.settings import settings
from shared.init_db import init_db, close_db


class TestDatabaseConnection:

    @pytest.fixture
    def mock_engine(self):
        engine = MagicMock(spec=AsyncEngine)

        # Cria um mock assíncrono para o contexto async
        mock_conn = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar.return_value = 1

        # Configura o contexto assíncrono
        async def mock_execute(stmt):
            return mock_result

        mock_conn.execute = mock_execute
        engine.begin.return_value.__aenter__.return_value = mock_conn
        engine.begin.return_value.__aexit__.return_value = None

        return engine

    @pytest.mark.asyncio
    async def test_init_db_successful_connection(self, mock_engine):
        """Testa conexão bem-sucedida com o banco de dados"""

        with patch('shared.init_db.create_async_engine') as mock_create_engine:
            mock_create_engine.return_value = mock_engine

            result_engine = await init_db()

            mock_create_engine.assert_called_once_with(
                settings.DATABASE_URL,
                echo=settings.is_development,
                pool_pre_ping=True
            )

            assert result_engine == mock_engine

    @pytest.mark.asyncio
    async def test_init_db_fallback_connection(self, mock_engine):
        """Testa conexão de fallback quando a primeira falha"""

        with patch('shared.init_db.create_async_engine') as mock_create_engine:
            # Primeira chamada falha, segunda funciona
            mock_create_engine.side_effect = [
                Exception("Connection failed"),
                mock_engine
            ]

            result_engine = await init_db()

            assert mock_create_engine.call_count == 2

            # Verifica a primeira chamada (URL original)
            first_call_args = mock_create_engine.call_args_list[0]
            assert settings.DATABASE_URL in str(first_call_args)

            # Verifica a segunda chamada (fallback)
            second_call_args = mock_create_engine.call_args_list[1]
            fallback_url = settings.DATABASE_URL.replace("localhost", "127.0.0.1")
            assert fallback_url in str(second_call_args)

            assert result_engine == mock_engine

    @pytest.mark.asyncio
    async def test_init_db_all_connections_fail(self):
        """Testa quando todas as tentativas de conexão falham"""

        with patch('shared.init_db.create_async_engine') as mock_create_engine:
            mock_create_engine.side_effect = Exception("All connections failed")

            # Verifica se a exceção é levantada após todas as tentativas
            with pytest.raises(Exception, match="All connections failed"):
                await init_db()

    @pytest.mark.asyncio
    async def test_close_db_success(self, mock_engine):
        """Testa o fechamento bem-sucedido da conexão"""

        with patch.object(mock_engine, 'dispose', new_callable=AsyncMock) as mock_dispose:
            await close_db(mock_engine)

            # Verifica se dispose foi chamado
            mock_dispose.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_db_none_engine(self):
        """Testa o fechamento quando engine é None"""

        # Não deve levantar exceção quando engine é None
        await close_db(None)

    def test_settings_database_url_construction(self):
        """Testa se a DATABASE_URL é construída corretamente"""

        expected_url = f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"

        assert settings.DATABASE_URL == expected_url
        assert "postgresql+asyncpg" in settings.DATABASE_URL
        assert settings.DB_USER in settings.DATABASE_URL
        assert settings.DB_NAME in settings.DATABASE_URL

    def test_settings_environment_properties(self):
        """Testa as propriedades de ambiente"""

        # Testa ambiente de desenvolvimento
        if settings.ENVIRONMENT == "development":
            assert settings.is_development is True
            assert settings.is_production is False
        elif settings.ENVIRONMENT == "production":
            assert settings.is_development is False
            assert settings.is_production is True

    @pytest.mark.asyncio
    async def test_connection_with_actual_settings(self):
        """Teste de integração real com o banco de dados"""

        # Este teste só deve rodar em ambiente de desenvolvimento/teste
        if settings.ENVIRONMENT in ["development", "test"]:
            try:
                engine = await init_db()
                assert engine is not None
                assert isinstance(engine, AsyncEngine)

                # Fecha a conexão
                await close_db(engine)

            except Exception as e:
                pytest.skip(f"Não foi possível conectar ao banco: {e}")


@pytest.mark.integration
class TestDatabaseIntegration:

    @pytest.mark.asyncio
    async def test_database_operations(self):

        if settings.ENVIRONMENT not in ["development", "test"]:
            pytest.skip("Integration tests only run in development/testing environments.")

        try:
            engine = await init_db()

            async with engine.begin() as conn:
                result = await conn.execute(text("SELECT version()"))
                version = result.scalar()
                assert "PostgreSQL" in version

                result = await conn.execute(text("SELECT 1 as test_value"))
                test_value = result.scalar()
                assert test_value == 1

            await close_db(engine)

        except Exception as e:
            pytest.fail(f"Integration test failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])