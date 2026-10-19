import os
from datetime import datetime, timedelta, timezone

import jwt
from jwt import InvalidTokenError
from pwdlib import PasswordHash


ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = 60

password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    if not password or len(password) < 8:
        raise ValueError("Password must contain at least 8 characters.")

    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password, password_hash)
    except (ValueError, TypeError):
        return False


def get_jwt_secret() -> str:
    secret = os.environ.get("ATHENA_JWT_SECRET")

    if not secret or len(secret) < 32 or secret.startswith("REPLACE_"):
        raise RuntimeError(
            "ATHENA_JWT_SECRET must contain at least 32 characters."
        )

    return secret


def create_access_token(user_id: int, version: int = 0) -> str:
    if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id <= 0:
        raise ValueError("Invalid user ID.")

    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_MINUTES),
        "type": "access",
        "version": version,
    }

    return jwt.encode(
        payload,
        get_jwt_secret(),
        algorithm=ALGORITHM,
    )


def decode_access_token(token: str, with_version=False):
    try:
        payload = jwt.decode(
            token,
            get_jwt_secret(),
            algorithms=[ALGORITHM],
            options={"require": ["sub", "iat", "exp"]},
        )

        if payload.get("type") != "access":
            raise ValueError("Invalid token type.")

        subject = payload["sub"]

        if not isinstance(subject, str) or not subject.isdecimal():
            raise ValueError("Invalid token subject.")

        user_id = int(subject)

        if user_id <= 0:
            raise ValueError("Invalid token subject.")

        version = payload.get("version", 0)
        if type(version) is not int or version < 0:
            raise ValueError("Invalid token version.")
        return (user_id, version) if with_version else user_id

    except InvalidTokenError as exc:
        raise ValueError("Invalid or expired access token.") from exc
