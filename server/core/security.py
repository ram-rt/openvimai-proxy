from fastapi import Request, HTTPException, status
from jose import jwt, JWTError
from core.settings import settings

def get_current_user(request: Request):
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Missing bearer token")

    token = auth.split(" ", 1)[1]
    try:
        payload = jwt.decode(token,
                    settings.jwt_secret,
                    algorithms=[settings.jwt_algo])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid token")

    request.state.user_id = payload.get("sub")
    return payload