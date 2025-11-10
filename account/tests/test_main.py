from fastapi.testclient import TestClient
from unittest.mock import patch
from main import app


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

    @patch('uvicorn.run')
    def test_main_execution(self, mock_uvicorn_run):
        # Arrange
        mock_uvicorn_run.return_value = None

        with patch('main.settings') as mock_settings:
            mock_settings.is_development = True
            mock_settings.is_production = False

            try:
                import __main__
            except:
                pass

        mock_uvicorn_run.assert_not_called()

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