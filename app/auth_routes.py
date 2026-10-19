from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy import select, update
import base64
import os
import secrets
from urllib.parse import quote
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.database.database import get_db
from app.database.models import User, UserSecurity
from app.security import cipher, verify_totp
from app.settings import clearance_for_username


router = APIRouter(prefix="/auth", tags=["Authentication"])
bearer = HTTPBearer(auto_error=False)


class Credentials(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=100,
        pattern=r"^[a-zA-Z0-9_]+$",
    )
    password: str = Field(min_length=8, max_length=128)
    otp: str | None = Field(default=None, max_length=6)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required.")

    try:
        user_id, version = decode_access_token(credentials.credentials, with_version=True)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid access token.")

    user = db.get(User, user_id)

    if user is None or user.username == "__athena_legacy__":
        raise HTTPException(status_code=401, detail="Invalid access token.")

    state = db.get(UserSecurity, user_id)
    if version != (state.token_version if state else 0):
        raise HTTPException(status_code=401, detail="Session revoked. Sign in again.")

    return user


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(request: Credentials, db: Session = Depends(get_db)):
    if os.environ.get("ATHENA_ALLOW_REGISTRATION", "1") != "1":
        raise HTTPException(status_code=403, detail="Registration is disabled.")
    username = request.username.lower()

    if username == "__athena_legacy__":
        raise HTTPException(status_code=400, detail="Reserved username.")

    user = User(
        username=username,
        password_hash=hash_password(request.password),
    )

    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Username unavailable.")

    return TokenResponse(access_token=create_access_token(user.id))


@router.post("/login", response_model=TokenResponse)
def login(request: Credentials, db: Session = Depends(get_db)):
    user = db.execute(
        select(User).where(User.username == request.username.lower())
    ).scalar_one_or_none()

    if (
        user is None
        or user.username == "__athena_legacy__"
        or not verify_password(request.password, user.password_hash)
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password.",
        )

    state = db.get(UserSecurity, user.id)
    if state and state.totp_enabled:
        step = verify_totp(state.totp_secret, request.otp, state.last_totp_step)
        if step is None:
            raise HTTPException(status_code=401, detail="Valid authenticator code required.")
        changed = db.execute(update(UserSecurity).where(
            UserSecurity.user_id == user.id, UserSecurity.last_totp_step < step
        ).values(last_totp_step=step))
        if changed.rowcount != 1:
            db.rollback()
            raise HTTPException(status_code=401, detail="Authenticator code already used.")
        db.commit()
    return TokenResponse(access_token=create_access_token(user.id, state.token_version if state else 0))


@router.get("/me")
def me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    state = db.get(UserSecurity, current_user.id)
    return {
        "id": current_user.id,
        "username": current_user.username,
        "clearance": clearance_for_username(current_user.username),
        "mfa_enabled": bool(state and state.totp_enabled),
        "auto_collect": bool(state and state.auto_collect),
    }


class SecurityChange(BaseModel):
    password: str = Field(min_length=8, max_length=128)
    otp: str | None = Field(default=None, max_length=6)


def security_state(db, user_id):
    state = db.get(UserSecurity, user_id)
    if state is None:
        state = UserSecurity(user_id=user_id, token_version=0, last_totp_step=-1)
        db.add(state)
        db.flush()
    return state


@router.post("/mfa/setup")
def setup_mfa(request: SecurityChange, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(401, "Invalid password.")
    state = security_state(db, user.id)
    if state.totp_enabled:
        raise HTTPException(409, "MFA is already enabled.")
    secret = base64.b32encode(secrets.token_bytes(20)).decode()
    state.totp_secret = cipher().encrypt(secret.encode()).decode()
    db.commit()
    return {"secret": secret, "uri": f"otpauth://totp/Athena:{quote(user.username)}?secret={secret}&issuer=Athena"}


@router.post("/mfa/confirm", response_model=TokenResponse)
def confirm_mfa(request: SecurityChange, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    state = security_state(db, user.id)
    if not verify_password(request.password, user.password_hash) or not state.totp_secret or state.totp_enabled:
        raise HTTPException(400, "Invalid MFA setup.")
    step = verify_totp(state.totp_secret, request.otp)
    if step is None:
        raise HTTPException(400, "Invalid authenticator code.")
    state.totp_enabled = True
    state.last_totp_step = step
    state.token_version += 1
    db.commit()
    return TokenResponse(access_token=create_access_token(user.id, state.token_version))


@router.post("/logout")
def logout(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    state = security_state(db, user.id)
    db.execute(update(UserSecurity).where(UserSecurity.user_id == user.id).values(
        token_version=UserSecurity.token_version + 1))
    db.commit()
    return {"message": "All sessions signed out."}
