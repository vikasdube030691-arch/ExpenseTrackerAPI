import uuid
from datetime import timedelta

import jwt
from pydantic import BaseModel

from app.core.config import settings
from app.models.common import utcnow

ACCESS_TOKEN_TYPE = "access"


class TokenError(Exception):
    pass


class ExpiredTokenError(TokenError):
    pass


class InvalidTokenError(TokenError):
    pass


class AccessTokenPayload(BaseModel):
    sub: str
    iat: int
    exp: int
    jti: str
    type: str = ACCESS_TOKEN_TYPE


def create_access_token(subject: str, *, expires_delta: timedelta | None = None) -> str:
    now = utcnow()
    expire = now + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    payload = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        # Unique per token so two tokens issued for the same user in the same second
        # are still distinct strings (also useful for log correlation).
        "jti": uuid.uuid4().hex,
        "type": ACCESS_TOKEN_TYPE,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> AccessTokenPayload:
    try:
        raw_payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError as exc:
        raise ExpiredTokenError("Access token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise InvalidTokenError("Invalid access token") from exc

    if raw_payload.get("type") != ACCESS_TOKEN_TYPE:
        raise InvalidTokenError("Invalid access token")

    return AccessTokenPayload.model_validate(raw_payload)
