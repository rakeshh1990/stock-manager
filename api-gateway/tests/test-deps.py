"""
Unit tests for gateway JWT dependency.
Run with:  pytest api-gateway/tests/ -v
"""
import pytest
from datetime import datetime, timedelta
from jose import jwt
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

# We test the dep in isolation — no running services needed
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

SECRET = "supersecretjwt"
ALG    = "HS256"

os.environ["JWT_SECRET"] = SECRET
os.environ["JWT_ALG"]    = ALG

from app.deps import get_current_user, CurrentUser


def _make_token(sub="1", email="rakesh@example.com", expire_delta=timedelta(minutes=60)):
    payload = {
        "sub":   sub,
        "email": email,
        "exp":   datetime.utcnow() + expire_delta,
    }
    return jwt.encode(payload, SECRET, algorithm=ALG)


def _creds(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


# --- Happy path ---------------------------------------------------------

def test_valid_token_returns_user():
    token = _make_token()
    user  = get_current_user(_creds(token))
    assert isinstance(user, CurrentUser)
    assert user.user_id == 1
    assert user.email   == "rakesh@example.com"


# --- Failure cases ------------------------------------------------------

def test_missing_credentials_raises_401():
    with pytest.raises(HTTPException) as exc:
        get_current_user(None)
    assert exc.value.status_code == 401
    assert "Missing" in exc.value.detail


def test_expired_token_raises_401():
    token = _make_token(expire_delta=timedelta(seconds=-1))
    with pytest.raises(HTTPException) as exc:
        get_current_user(_creds(token))
    assert exc.value.status_code == 401
    assert "expired" in exc.value.detail.lower()


def test_tampered_token_raises_401():
    token = _make_token() + "tampered"
    with pytest.raises(HTTPException) as exc:
        get_current_user(_creds(token))
    assert exc.value.status_code == 401


def test_wrong_secret_raises_401():
    bad_token = jwt.encode(
        {"sub": "1", "email": "x@y.com", "exp": datetime.utcnow() + timedelta(minutes=5)},
        "wrong-secret",
        algorithm=ALG,
    )
    with pytest.raises(HTTPException) as exc:
        get_current_user(_creds(bad_token))
    assert exc.value.status_code == 401


def test_missing_sub_in_payload_raises_401():
    payload = {"email": "rakesh@example.com", "exp": datetime.utcnow() + timedelta(minutes=5)}
    token   = jwt.encode(payload, SECRET, algorithm=ALG)
    with pytest.raises(HTTPException) as exc:
        get_current_user(_creds(token))
    assert exc.value.status_code == 401
    assert "incomplete" in exc.value.detail.lower()