import os
import pytest
from pydantic import ValidationError
from shared.database import Settings


class TestSettings:

    def test_default_values(self):
        settings = Settings()

        assert settings.DB_USER == "database"
        assert settings.DB_PASSWORD == "database"
        assert settings.DB_NAME == "db"
        assert settings.DB_HOST == "localhost"
        assert settings.DB_PORT == "5432"
        assert settings.ENVIRONMENT == "production"
        assert settings.is_production is True
        assert settings.is_development is False

    def test_build_database_url_from_components(self):
        settings = Settings(
            DB_USER="testuser",
            DB_PASSWORD="testpass",
            DB_NAME="testdb",
            DB_HOST="testhost",
            DB_PORT="5433"
        )

        expected_url = "postgresql://testuser:testpass@testhost:5433/testdb"
        assert settings.DATABASE_URL == expected_url

    def test_provided_database_url_takes_precedence(self):
        provided_url = "postgresql://customuser:custompass@customhost:5434/customdb"

        settings = Settings(
            DATABASE_URL=provided_url,
            DB_USER="ignoreduser",
            DB_PASSWORD="ignoredpass",
            DB_NAME="ignoreddb",
            DB_HOST="ignoredhost",
            DB_PORT="9999"
        )

        assert settings.DATABASE_URL == provided_url

    def test_validate_database_url_valid(self):
        valid_url = "postgresql://user:pass@host:5432/db"

        settings = Settings(DATABASE_URL=valid_url)
        assert settings.DATABASE_URL == valid_url

    def test_validate_database_url_invalid_protocol(self):
        """Test that invalid DATABASE_URL protocol raises ValidationError"""
        invalid_url = "mysql://user:pass@host:5432/db"

        with pytest.raises(ValidationError) as exc_info:
            Settings(DATABASE_URL=invalid_url)

        assert "DATABASE_URL must use the protocol postgresql://" in str(exc_info.value)

    def test_environment_properties(self):

        dev_settings = Settings(ENVIRONMENT="development")
        assert dev_settings.is_development is True
        assert dev_settings.is_production is False

        prod_settings = Settings(ENVIRONMENT="production")
        assert prod_settings.is_development is False
        assert prod_settings.is_production is True

        staging_settings = Settings(ENVIRONMENT="staging")
        assert staging_settings.is_development is False
        assert staging_settings.is_production is False

    def test_environment_variables_loading(self, monkeypatch):
        monkeypatch.setenv("DB_USER", "envuser")
        monkeypatch.setenv("DB_PASSWORD", "envpass")
        monkeypatch.setenv("DB_NAME", "envdb")
        monkeypatch.setenv("DB_HOST", "envhost")
        monkeypatch.setenv("DB_PORT", "5444")
        monkeypatch.setenv("ENVIRONMENT", "development")

        settings = Settings()

        assert settings.DB_USER == "envuser"
        assert settings.DB_PASSWORD == "envpass"
        assert settings.DB_NAME == "envdb"
        assert settings.DB_HOST == "envhost"
        assert settings.DB_PORT == "5444"
        assert settings.ENVIRONMENT == "development"
        assert settings.is_development is True

    def test_env_file_loading(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("""
DB_USER=fileuser
DB_PASSWORD=filepass
DB_NAME=filedb
DB_HOST=filehost
DB_PORT=5455
ENVIRONMENT=staging
DATABASE_URL=postgresql://fileuser:filepass@filehost:5455/filedb
""")

        # Change to temporary directory to find the .env file
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            settings = Settings(_env_file=".env")

            assert settings.DB_USER == "fileuser"
            assert settings.DB_PASSWORD == "filepass"
            assert settings.DB_NAME == "filedb"
            assert settings.DB_HOST == "filehost"
            assert settings.DB_PORT == "5455"
            assert settings.ENVIRONMENT == "staging"
            assert settings.DATABASE_URL == "postgresql://fileuser:filepass@filehost:5455/filedb"
        finally:
            os.chdir(original_cwd)

    def test_case_insensitive_config(self):
        settings = Settings(
            db_user="database",  # lowercase
            db_password="database",  # lowercase
            db_name="db",  # lowercase
            environment="development"  # lowercase
        )

        assert settings.DB_USER == "database"
        assert settings.DB_PASSWORD == "database"
        assert settings.DB_NAME == "db"
        assert settings.ENVIRONMENT == "production"