# test_consumer.py
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import aio_pika
import pytest

from src.messaging.consumer import (
    TokenStorage,
    process_token_message,
    consume_token_messages,
    start_rabbitmq_consumer,
    ACCOUNT_AUTH_QUEUE,
    TOKEN_EXCHANGE,
    TOKEN_ROUTING_KEY,
)


@pytest.fixture
def token_storage():
    return TokenStorage()


@pytest.fixture
def sample_token_data():
    return {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
        "user_id": 123,
        "username": "john_doe",
        "token_type": "bearer",
        "expires_in": 3600,
        "issued_at": "2025-01-01T00:00:00",
    }


class TestTokenStorage:
    def test_store_new_token(self, token_storage, sample_token_data):
        token_storage.store_token(sample_token_data)

        assert sample_token_data["token"] in token_storage.tokens
        stored = token_storage.tokens[sample_token_data["token"]]
        assert stored["user_id"] == 123
        assert stored["username"] == "john_doe"
        assert stored["token_type"] == "bearer"
        assert "received_at" in stored
        assert token_storage.user_tokens[123] == sample_token_data["token"]

    def test_store_token_missing_token(self, token_storage, caplog):
        data = {"user_id": 123, "username": "john"}
        token_storage.store_token(data)
        assert "Invalid token data received" in caplog.text
        assert len(token_storage.tokens) == 0

    def test_store_token_missing_user_id(self, token_storage, caplog):
        data = {"token": "abc", "username": "john"}
        token_storage.store_token(data)
        assert "Invalid token data received" in caplog.text
        assert len(token_storage.tokens) == 0

    def test_store_token_replaces_old_token(self, token_storage, sample_token_data):
        token_storage.store_token(sample_token_data)
        assert token_storage.user_tokens[123] == sample_token_data["token"]

        new_token_data = sample_token_data.copy()
        new_token_data["token"] = "new_token_value"
        token_storage.store_token(new_token_data)

        assert sample_token_data["token"] not in token_storage.tokens
        assert token_storage.user_tokens[123] == "new_token_value"
        assert "new_token_value" in token_storage.tokens

    def test_get_token_info_without_bearer(self, token_storage, sample_token_data):
        token_storage.store_token(sample_token_data)
        info = token_storage.get_token_info(sample_token_data["token"])
        assert info["user_id"] == 123

    def test_get_token_info_with_bearer_prefix(self, token_storage, sample_token_data):
        token_storage.store_token(sample_token_data)
        info = token_storage.get_token_info(f"Bearer {sample_token_data['token']}")
        assert info["user_id"] == 123

    def test_get_token_info_not_found(self, token_storage):
        assert token_storage.get_token_info("nonexistent") is None

    def test_get_user_token(self, token_storage, sample_token_data):
        token_storage.store_token(sample_token_data)
        assert token_storage.get_user_token(123) == sample_token_data["token"]
        assert token_storage.get_user_token(999) is None

    def test_remove_token_existing(self, token_storage, sample_token_data):
        token_storage.store_token(sample_token_data)
        token_storage.remove_token(sample_token_data["token"])
        assert sample_token_data["token"] not in token_storage.tokens
        assert 123 not in token_storage.user_tokens

    def test_remove_token_nonexistent(self, token_storage, caplog):
        token_storage.remove_token("missing")
        assert len(token_storage.tokens) == 0


class TestProcessTokenMessage:
    @pytest.fixture
    def mock_async_context(self):
        mock_cm = AsyncMock()
        mock_cm.__aenter__ = AsyncMock(return_value=None)
        mock_cm.__aexit__ = AsyncMock(return_value=None)
        return mock_cm

    @pytest.mark.asyncio
    async def test_process_valid_message(self, sample_token_data, mock_async_context):
        mock_message = AsyncMock(spec=aio_pika.IncomingMessage)
        mock_message.body = json.dumps(sample_token_data).encode()
        mock_message.process = MagicMock(return_value=mock_async_context)

        with patch("src.messaging.consumer.token_storage") as mock_storage:
            await process_token_message(mock_message)

            mock_message.process.assert_called_once()
            mock_async_context.__aenter__.assert_awaited_once()
            mock_async_context.__aexit__.assert_awaited_once()
            mock_storage.store_token.assert_called_once_with(sample_token_data)

    @pytest.mark.asyncio
    async def test_missing_required_field(self, caplog, mock_async_context):
        invalid_data = {"token": "abc", "user_id": 123}
        mock_message = AsyncMock()
        mock_message.body = json.dumps(invalid_data).encode()
        mock_message.process = MagicMock(return_value=mock_async_context)

        with patch("src.messaging.consumer.token_storage") as mock_storage:
            await process_token_message(mock_message)

            mock_storage.store_token.assert_not_called()
            assert "Missing required field: username" in caplog.text

    @pytest.mark.asyncio
    async def test_json_decode_error(self, caplog, mock_async_context):
        mock_message = AsyncMock()
        mock_message.body = b"not json"
        mock_message.process = MagicMock(return_value=mock_async_context)

        with patch("src.messaging.consumer.token_storage") as mock_storage:
            await process_token_message(mock_message)

            mock_storage.store_token.assert_not_called()
            assert "Failed to decode JSON" in caplog.text

    @pytest.mark.asyncio
    async def test_general_exception(self, caplog, mock_async_context):
        mock_message = AsyncMock()
        mock_message.body = json.dumps({"token": "a", "user_id": 1, "username": "u"}).encode()
        mock_message.process = MagicMock(return_value=mock_async_context)

        with patch("src.messaging.consumer.token_storage.store_token", side_effect=RuntimeError("DB error")):
            await process_token_message(mock_message)

            assert "Error processing token message" in caplog.text
            assert "DB error" in caplog.text


class TestConsumeTokenMessages:

    @pytest.mark.asyncio
    async def test_connection_retries_and_success(self):
        mock_connection = AsyncMock()
        mock_connection.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_connection.__aexit__ = AsyncMock(return_value=None)

        mock_channel = AsyncMock()
        mock_queue = AsyncMock()
        mock_channel.declare_queue.return_value = mock_queue

        with patch("src.messaging.consumer.aio_pika.connect_robust") as mock_connect, \
                patch("src.messaging.consumer.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            mock_connect.side_effect = [
                ConnectionError("Fail 1"),
                ConnectionError("Fail 2"),
                mock_connection,
            ]

            task = asyncio.create_task(consume_token_messages())
            await asyncio.sleep(0.2)
            task.cancel()

            with pytest.raises(asyncio.CancelledError):
                await task

            assert mock_connect.call_count == 0
            assert mock_sleep.call_count == 1

    @pytest.mark.asyncio
    async def test_connection_retries_exhausted(self):
        with patch("src.messaging.consumer.aio_pika.connect_robust", side_effect=ConnectionError("Always fails")), \
                patch("src.messaging.consumer.asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(ConnectionError):
                await consume_token_messages()

    @pytest.mark.asyncio
    async def test_unexpected_exception_during_connection(self):
        with patch("src.messaging.consumer.aio_pika.connect_robust", side_effect=RuntimeError("Unexpected")), \
                patch("src.messaging.consumer.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            task = asyncio.create_task(consume_token_messages())
            await asyncio.sleep(0.01)
            task.cancel()

            with pytest.raises(asyncio.CancelledError):
                await task

            assert mock_sleep.call_count >= 1


class TestStartRabbitmqConsumer:
    @pytest.mark.asyncio
    async def test_creates_task(self):
        # Usamos uma função fake para evitar que o create_task execute um AsyncMock de forma indefinida
        async def fake_consume():
            raise asyncio.CancelledError()

        with patch("src.messaging.consumer.consume_token_messages", side_effect=fake_consume) as mock_consume:
            task = await start_rabbitmq_consumer()
            assert isinstance(task, asyncio.Task)

            with pytest.raises(asyncio.CancelledError):
                await task

            mock_consume.assert_called_once()