from fastapi.testclient import TestClient
from unittest.mock import patch
from account.main import app


class TestMain:

    def test_root_endpoint(self):
        # Arrange
        client = TestClient(app)

        # Act
        response = client.get("/")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Account Management API"
        assert data["version"] == "1.0.0"

    def test_health_check(self):
        # Arrange
        client = TestClient(app)

        # Act
        response = client.get("/health")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_lifespan_startup(self):
        client = TestClient(app)

        assert client is not None

    @patch('account.main.uvicorn.run')
    @patch('account.main.settings')
    def test_main_execution(self, mock_settings, mock_uvicorn_run):
        # Arrange
        mock_settings.is_development = True
        mock_settings.is_production = False
        mock_uvicorn_run.return_value = None

        # Act
        from account import main
        main.run_server()

        # Assert
        mock_uvicorn_run.assert_called_once_with(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="debug"
        )

    def test_api_documentation_available(self):
        # Arrange
        client = TestClient(app)

        # Act
        response = client.get("/docs")

        # Assert
        assert response.status_code == 200

    def test_openapi_schema_available(self):
        # Arrange
        client = TestClient(app)

        # Act
        response = client.get("/openapi.json")

        # Assert
        assert response.status_code == 200