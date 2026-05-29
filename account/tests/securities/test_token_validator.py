# test_token_validator.py
import jwt
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from fastapi import HTTPException

from src.securities.token_validator import (
    TokenValidator,
    get_token_validator,
    initialize_token_validator,
    token_validator as global_token_validator,
)


# ---------- Fixtures ----------
@pytest.fixture
def secret_key():
    return "test-secret-key"


@pytest.fixture
def token_validator(secret_key):
    return TokenValidator(secret_key=secret_key, algorithm="HS256")


@pytest.fixture(autouse=True)
def reset_global_validator():
    global global_token_validator
    global_token_validator = None
    yield
    global_token_validator = None


def create_valid_token(secret_key, payload, exp_seconds=3600):
    """Cria um token JWT válido com expiração no futuro."""
    payload = payload.copy()
    if "exp" not in payload:
        payload["exp"] = datetime.now(timezone.utc) + timedelta(seconds=exp_seconds)
    if "iat" not in payload:
        payload["iat"] = datetime.now(timezone.utc)
    return jwt.encode(payload, secret_key, algorithm="HS256")


def create_expired_token(secret_key, payload):
    """Cria um token expirado."""
    payload = payload.copy()
    payload["exp"] = datetime.now(timezone.utc) - timedelta(seconds=1)
    payload["iat"] = datetime.now(timezone.utc) - timedelta(seconds=2)
    return jwt.encode(payload, secret_key, algorithm="HS256")


# ---------- Testes para TokenValidator.validate_token ----------
@pytest.mark.asyncio
async def test_validate_token_success_without_bearer(token_validator, secret_key):
    """Token válido sem o prefixo 'Bearer ' retorna o payload correto."""
    payload = {
        "sub": "john_doe",
        "user_id": 123,
        "email": "john@example.com",
    }
    token = create_valid_token(secret_key, payload)

    result = await token_validator.validate_token(token)

    assert result["username"] == "john_doe"
    assert result["user_id"] == 123
    assert result["email"] == "john@example.com"
    assert "exp" in result
    assert "iat" in result


@pytest.mark.asyncio
async def test_validate_token_success_with_bearer(token_validator, secret_key):
    """Token válido com o prefixo 'Bearer ' é processado corretamente."""
    payload = {"sub": "jane_doe", "user_id": 456, "email": "jane@example.com"}
    token = create_valid_token(secret_key, payload)
    bearer_token = f"Bearer {token}"

    result = await token_validator.validate_token(bearer_token)

    assert result["username"] == "jane_doe"
    assert result["user_id"] == 456
    assert result["email"] == "jane@example.com"


@pytest.mark.asyncio
async def test_validate_token_missing_exp_claim(token_validator, secret_key):
    """Token sem a claim 'exp' ainda é considerado válido."""
    payload = {"sub": "no_exp_user", "user_id": 789}
    token = jwt.encode(payload, secret_key, algorithm="HS256")

    result = await token_validator.validate_token(token)

    assert result["username"] == "no_exp_user"
    assert result["user_id"] == 789
    assert result.get("exp") is None


@pytest.mark.asyncio
async def test_validate_token_expired_signature_error(token_validator, secret_key):
    """Token expirado lança HTTPException 401 via jwt.ExpiredSignatureError."""
    payload = {"sub": "expired_user", "user_id": 999}
    token = create_expired_token(secret_key, payload)

    with pytest.raises(HTTPException) as exc_info:
        await token_validator.validate_token(token)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Token expired"


@pytest.mark.asyncio
async def test_validate_token_exp_claim_past_but_decode_does_not_raise(
    token_validator, secret_key
):
    """Valida a checagem manual de expiração (quando o jwt.decode não lança erro automaticamente)."""
    past_exp = datetime.now(timezone.utc).timestamp() - 100
    mock_payload = {
        "sub": "test_user",
        "exp": past_exp,
    }
    with patch("src.securities.token_validator.jwt.decode", return_value=mock_payload):
        with pytest.raises(HTTPException) as exc_info:
            await token_validator.validate_token("any.token")

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Token expired"


@pytest.mark.asyncio
async def test_validate_token_missing_sub_claim(token_validator, secret_key):
    payload = {"user_id": 111, "email": "no-sub@example.com"}
    token = jwt.encode(payload, secret_key, algorithm="HS256")

    with pytest.raises(HTTPException) as exc_info:
        await token_validator.validate_token(token)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid token: missing subject"


@pytest.mark.asyncio
async def test_validate_token_invalid_token_error(token_validator, secret_key):
    """Token malformado ou assinatura inválida lança HTTPException 401."""
    invalid_token = "this.is.not.a.valid.jwt"

    with pytest.raises(HTTPException) as exc_info:
        # CORRIGIDO: Removido o 'src.' e utilizada a chamada de método correta
        await token_validator.validate_token(invalid_token)

    assert exc_info.value.status_code == 401
    assert "Invalid token:" in exc_info.value.detail


@pytest.mark.asyncio
async def test_validate_token_generic_exception(token_validator, secret_key):
    with patch("src.securities.token_validator.jwt.decode", side_effect=ValueError("Unexpected error")):
        with pytest.raises(HTTPException) as exc_info:
            await token_validator.validate_token("some.token")

    assert exc_info.value.status_code == 500
    assert "Token validation failed: Unexpected error" == exc_info.value.detail


# ---------- Testes para o Estado Global e Helpers ----------
def test_get_token_validator_not_initialized():
    """Chamar get_token_validator antes de inicializar lança RuntimeError."""
    with pytest.raises(RuntimeError, match="TokenValidator not initialized"):
        get_token_validator()


@pytest.mark.asyncio
async def test_initialize_token_validator_and_get(secret_key, caplog):
    await initialize_token_validator(secret_key)

    validator = get_token_validator()
    assert isinstance(validator, TokenValidator)
    assert validator.secret_key == secret_key
    assert validator.algorithm == "HS256"



@pytest.mark.asyncio
async def test_initialize_token_validator_overwrites_global(secret_key):
    """Chamar initialize_token_validator novamente substitui a instância global anterior."""
    # CORRIGIDO: Adicionado await nas duas chamadas
    await initialize_token_validator("first-key")
    first_validator = get_token_validator()

    await initialize_token_validator("second-key")
    second_validator = get_token_validator()

    assert first_validator is not second_validator
    assert second_validator.secret_key == "second-key"


# ---------- Cobertura adicional para remoção do prefixo 'Bearer ' ----------
@pytest.mark.asyncio
async def test_validate_token_bearer_prefix_trimming(token_validator, secret_key):
    """O prefixo 'Bearer ' é removido de forma limpa da string do token."""
    payload = {"sub": "bearer_user"}
    token = create_valid_token(secret_key, payload)
    bearer_token = f"Bearer {token}"

    result = await token_validator.validate_token(bearer_token)
    assert result["username"] == "bearer_user"


@pytest.mark.asyncio
async def test_validate_token_only_bearer_word_not_removed(token_validator, secret_key):
    """Se o token começar com 'Bearer' grudado (sem espaço), ele não é removido e falha no decode."""
    payload = {"sub": "weird_user"}
    token = create_valid_token(secret_key, payload)
    weird_token = f"Bearer{token}"

    with pytest.raises(HTTPException) as exc_info:
        await token_validator.validate_token(weird_token)
    assert exc_info.value.status_code == 401
    assert "Invalid token:" in exc_info.value.detail