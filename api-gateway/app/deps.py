from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt, ExpiredSignatureError
from pydantic import BaseModel
import os

JWT_SECRET = os.getenv("JWT_SECRET", "supersecretjwt")
JWT_ALG    = os.getenv("JWT_ALG", "HS256")

# Extracts Bearer token from Authorization header
bearer_scheme = HTTPBearer(auto_error=False)


class CurrentUser(BaseModel):
    user_id: int
    email: str


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> CurrentUser:
    """
    Validate the JWT and return the decoded user context.
    Raises 401 if the token is missing, expired, or invalid.
    The gateway decodes the token locally (no round-trip to auth-service)
    and injects X-User-Id into downstream requests.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str = payload.get("sub")
    email: str   = payload.get("email")

    if user_id is None or email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload incomplete",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return CurrentUser(user_id=int(user_id), email=email)