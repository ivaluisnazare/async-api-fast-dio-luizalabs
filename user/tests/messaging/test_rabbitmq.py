# tests/messaging/test_rabbitmq.py

import json
import logging
from unittest.mock import AsyncMock, patch

import pytest
from aio_pika import ExchangeType

from src.messaging.rabbitmq import (
    LOGIN_QUEUE,
    TOKEN_EXCHANGE,
    TOKEN_ROUTING_KEY,
    get_rabbitmq_connection,
    send_login_message,
    send_token_to_account_service,
    setup_rabbitmq,
)


@pytest.fixture
def mock_settings():
    """Mock RABBITMQ_URL to avoid real connection strings."""
    with patch("src.messaging.rabbitmq.RABBITMQ_URL", "amqp://test:test@localhost:5672/"):
        yield


@pytest.fixture
def mock_aio_pika():
    """Mock aio_pika.connect_robust and related classes."""
    mock_connection = AsyncMock()
    mock_connection.__aenter__ = AsyncMock(return_value=mock_connection)
    mock_connection.__aexit__ = AsyncMock()
    mock_channel = AsyncMock()
    mock_connection.channel = AsyncMock(return_value=mock_channel)

    mock_exchange = AsyncMock()
    mock_channel.declare_exchange = AsyncMock(return_value=mock_exchange)
    mock_queue = AsyncMock()
    mock_channel.declare_queue = AsyncMock(return_value=mock_queue)

    # mock default_exchange no channel (usado em send_token_to_account_service)
    mock_default_exchange = AsyncMock()
    mock_channel.default_exchange = mock_default_exchange

    with patch("aio_pika.connect_robust", AsyncMock(return_value=mock_connection)) as mock_connect:
        yield mock_connect, mock_connection, mock_channel, mock_exchange, mock_queue, mock_default_exchange


# ---------- Tests for get_rabbitmq_connection ----------
@pytest.mark.asyncio
async def test_get_rabbitmq_connection_success(mock_settings, mock_aio_pika):
    mock_connect, mock_connection, _, _, _, _ = mock_aio_pika

    async with get_rabbitmq_connection() as conn:
        assert conn is mock_connection

    mock_connect.assert_awaited_once()
    mock_connection.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_rabbitmq_connection_retry_success(mock_settings):
    mock_connection = AsyncMock()
    mock_connection.__aenter__ = AsyncMock(return_value=mock_connection)
    mock_connection.__aexit__ = AsyncMock()

    with patch(
        "aio_pika.connect_robust",
        AsyncMock(
            side_effect=[
                Exception("conn error 1"),
                Exception("conn error 2"),
                mock_connection,
            ]
        ),
    ) as mock_connect:
        async with get_rabbitmq_connection(max_retries=3) as conn:
            assert conn is mock_connection

        assert mock_connect.await_count == 3
        mock_connection.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_rabbitmq_connection_all_retries_fail(mock_settings):
    with patch(
        "aio_pika.connect_robust", AsyncMock(side_effect=Exception("always fails"))
    ):
        with pytest.raises(
            ConnectionError, match="Failed to connect to RabbitMQ after 3 attempts"
        ):
            async with get_rabbitmq_connection(max_retries=3):
                pass


# ---------- Tests for send_login_message ----------
@pytest.mark.asyncio
async def test_send_login_message_success(mock_settings, mock_aio_pika, caplog):
    # Configura o logger para capturar mensagens INFO
    caplog.set_level(logging.INFO, logger="src.messaging.rabbitmq")

    mock_connect, mock_connection, mock_channel, mock_exchange, mock_queue, _ = mock_aio_pika

    login_data = {
        "username": "alice",
        "timestamp": "2025-01-01T00:00:00",
        "event": "login",
    }

    result = await send_login_message(login_data)

    assert result is True
    mock_connect.assert_awaited_once()
    mock_connection.channel.assert_awaited_once()
    mock_channel.declare_exchange.assert_awaited_once_with(
        TOKEN_EXCHANGE, ExchangeType.DIRECT, durable=True, auto_delete=False
    )
    mock_channel.declare_queue.assert_awaited_once_with(
        LOGIN_QUEUE,
        durable=True,
        arguments={
            "x-dead-letter-exchange": "",
            "x-dead-letter-routing-key": f"{LOGIN_QUEUE}.dlq",
        },
    )
    mock_queue.bind.assert_awaited_once_with(mock_exchange, TOKEN_ROUTING_KEY)

    expected_body = json.dumps(login_data).encode()
    mock_exchange.publish.assert_awaited_once()
    args, kwargs = mock_exchange.publish.call_args
    published_message = args[0]
    assert published_message.body == expected_body
    assert published_message.content_type == "application/json"
    assert published_message.delivery_mode.value == 2  # PERSISTENT
    assert published_message.headers["service"] == "user-service"
    assert published_message.headers["event_type"] == "user_login"
    assert kwargs["routing_key"] == TOKEN_ROUTING_KEY

    assert "Login message sent for user: alice" in caplog.text


@pytest.mark.asyncio
async def test_send_login_message_failure(mock_settings, caplog):
    with patch(
        "aio_pika.connect_robust", AsyncMock(side_effect=Exception("Broker down"))
    ):
        result = await send_login_message({"username": "bob"})
        assert result is False
        assert (
            "Error sending message to RabbitMQ: Failed to connect to RabbitMQ after 3 attempts"
            in caplog.text
        )


# ---------- Tests for send_token_to_account_service ----------
@pytest.mark.asyncio
async def test_send_token_to_account_service_success(mock_settings, mock_aio_pika, caplog):
    caplog.set_level(logging.INFO, logger="src.messaging.rabbitmq")

    mock_connect, mock_connection, mock_channel, _, _, mock_default_exchange = mock_aio_pika

    token_data = {
        "username": "charlie",
        "token": "jwt.token.here",
        "timestamp": "2025-01-01T00:00:00",
    }

    result = await send_token_to_account_service(token_data)

    assert result is True
    mock_channel.declare_queue.assert_awaited_once_with(
        "account_auth_queue",
        durable=True,
        arguments={
            "x-dead-letter-exchange": "",
            "x-dead-letter-routing-key": "account_auth_queue.dlq",
        },
    )
    # Verifica o publish no default_exchange do channel, não no connection
    mock_default_exchange.publish.assert_awaited_once()
    args, kwargs = mock_default_exchange.publish.call_args
    published_message = args[0]
    assert published_message.body == json.dumps(token_data).encode()
    assert kwargs["routing_key"] == "account_auth_queue"
    assert "Token sent to account-service for user: charlie" in caplog.text


@pytest.mark.asyncio
async def test_send_token_to_account_service_failure(mock_settings, caplog):
    with patch(
        "aio_pika.connect_robust", AsyncMock(side_effect=Exception("Network error"))
    ):
        result = await send_token_to_account_service({"username": "dave"})
        assert result is False
        assert (
            "Error sending token to account-service: Failed to connect to RabbitMQ after 3 attempts"
            in caplog.text
        )


# ---------- Tests for setup_rabbitmq ----------
@pytest.mark.asyncio
async def test_setup_rabbitmq_success(mock_settings, mock_aio_pika, caplog):
    caplog.set_level(logging.INFO, logger="src.messaging.rabbitmq")

    mock_connect, mock_connection, mock_channel, mock_exchange, mock_login_queue, _ = mock_aio_pika

    mock_dlq_login = AsyncMock()
    mock_dlq_account = AsyncMock()
    mock_channel.declare_queue.side_effect = [
        mock_login_queue,  # LOGIN_QUEUE
        mock_dlq_login,    # LOGIN_QUEUE.dlq
        AsyncMock(),       # account_auth_queue
        mock_dlq_account,  # account_auth_queue.dlq
    ]

    result = await setup_rabbitmq()

    assert result is True

    mock_channel.declare_exchange.assert_awaited_once_with(
        TOKEN_EXCHANGE, ExchangeType.DIRECT, durable=True
    )

    calls = mock_channel.declare_queue.await_args_list
    assert len(calls) == 4

    # O primeiro argumento é posicional: o nome da queue
    assert calls[0].args[0] == LOGIN_QUEUE
    assert calls[0].kwargs["arguments"] == {
        "x-dead-letter-exchange": "",
        "x-dead-letter-routing-key": f"{LOGIN_QUEUE}.dlq",
    }
    assert calls[1].args[0] == f"{LOGIN_QUEUE}.dlq"
    assert calls[2].args[0] == "account_auth_queue"
    assert calls[3].args[0] == "account_auth_queue.dlq"

    mock_login_queue.bind.assert_awaited_once_with(mock_exchange, TOKEN_ROUTING_KEY)
    assert "RabbitMQ setup completed successfully" in caplog.text


@pytest.mark.asyncio
async def test_setup_rabbitmq_failure(mock_settings, caplog):
    with patch(
        "aio_pika.connect_robust", AsyncMock(side_effect=Exception("Setup error"))
    ):
        result = await setup_rabbitmq()
        assert result is False
        assert (
            "Error setting up RabbitMQ: Failed to connect to RabbitMQ after 3 attempts"
            in caplog.text
        )
