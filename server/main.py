from fastapi import FastAPI, Request, Depends
from api.router import router
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from core.settings import settings
from core.security import get_current_user          # for dependency
from jose import jwt, JWTError

def _rate_key(request: Request):
    auth = request.headers.get("Authorization")
    if auth and auth.startswith("Bearer "):
        token = auth.split(" ", 1)[1]
        try:
            payload = jwt.decode(token,
                                 settings.jwt_secret,
                                 algorithms=[settings.jwt_algo])
            return f"user:{payload.get('sub')}"
        except JWTError:
            pass
    return get_remote_address(request)

limiter = Limiter(key_func=_rate_key,
                  default_limits=["60/minute"])

app = FastAPI(title="OpenVimAI Proxy", version="0.1.0")
@app.get("/health")
def health():
    return {"status": "ok"}

app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.include_router(
    router,
    dependencies=[Depends(get_current_user)]   # JWT
)
